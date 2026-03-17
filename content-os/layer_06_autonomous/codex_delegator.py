"""
Codex Delegator — Automatic Task Routing to ACP Agents
Routes long-running build tasks to Claude Codex (ACP runtime) for
autonomous execution while OpenClaw continues handling other work.

Task Categories:
  - QUICK (< 5 min): OpenClaw handles directly
  - MEDIUM (5-30 min): Optional delegation, based on current load
  - LONG (30+ min): Auto-delegate to Codex agent
  - BUILD (code generation): Always delegate to Codex

Delegation Rules:
  - Never delegate: file reads, simple queries, status checks
  - Always delegate: multi-file code generation, full page builds, refactors
  - Conditional: analysis tasks, content generation (based on queue depth)

Integration with OpenClaw:
  - Uses sessions_spawn with runtime="acp" capability
  - Monitors spawned agent status
  - Collects results and logs to vault

Usage:
  from layer_06_autonomous.codex_delegator import CodexDelegator
  delegator = CodexDelegator()
  should_delegate, reason = delegator.should_delegate(task)
  if should_delegate:
      result = delegator.delegate(task)
"""

import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger('content-os.codex-delegator')

BASE_DIR = Path(__file__).parent.parent
DELEGATION_LOG = BASE_DIR / 'delegation_log.json'
OPENCLAW_WORKSPACE = Path.home() / 'clawd'

# ── Task Classification Rules ──
TASK_PATTERNS = {
    'build': {
        'keywords': [
            'build', 'create page', 'generate code', 'write script',
            'implement', 'scaffold', 'new feature', 'refactor',
            'create component', 'build system', 'write module',
            'full page', 'html page', 'python script',
        ],
        'delegation': 'always',
        'estimated_minutes': 30,
    },
    'analysis': {
        'keywords': [
            'analyze', 'review', 'audit', 'examine', 'investigate',
            'research', 'compare', 'evaluate', 'assess', 'report on',
        ],
        'delegation': 'conditional',
        'estimated_minutes': 15,
    },
    'content': {
        'keywords': [
            'write article', 'draft post', 'compose thread',
            'generate content', 'create outline', 'write chapter',
            'blog post', 'newsletter', 'email campaign',
        ],
        'delegation': 'conditional',
        'estimated_minutes': 20,
    },
    'quick': {
        'keywords': [
            'check', 'status', 'read', 'list', 'show', 'get',
            'what is', 'how to', 'explain', 'find', 'search',
            'fix typo', 'small change', 'update text',
        ],
        'delegation': 'never',
        'estimated_minutes': 2,
    },
    'system': {
        'keywords': [
            'restart', 'deploy', 'install', 'configure', 'setup',
            'migrate', 'backup', 'update dependencies',
        ],
        'delegation': 'never',  # System tasks stay local
        'estimated_minutes': 10,
    },
}

# ── Codex Agent Configuration ──
CODEX_CONFIG = {
    'runtime': 'acp',
    'model': 'claude-sonnet-4-20250514',
    'max_tokens': 16000,
    'timeout_minutes': 60,
    'workspace': str(OPENCLAW_WORKSPACE),
    'environment': {
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
    },
}


class CodexDelegator:
    """Routes tasks to Codex agents based on complexity and type."""

    def __init__(self):
        self.log = self._load_log()
        self.active_tasks = {}

    def _load_log(self) -> dict:
        if DELEGATION_LOG.exists():
            try:
                return json.loads(DELEGATION_LOG.read_text())
            except Exception:
                pass
        return {
            'delegated': [],
            'completed': [],
            'failed': [],
            'total_delegated': 0,
            'total_completed': 0,
            'total_time_saved_minutes': 0,
        }

    def _save_log(self):
        DELEGATION_LOG.write_text(json.dumps(self.log, indent=2))

    # ──────────────────────────────────────────────
    # Task Classification
    # ──────────────────────────────────────────────

    def classify_task(self, task_description: str) -> dict:
        """
        Classify a task by type, complexity, and delegation recommendation.
        """
        desc_lower = task_description.lower()
        best_match = 'quick'
        best_score = 0

        for task_type, config in TASK_PATTERNS.items():
            score = sum(1 for kw in config['keywords'] if kw in desc_lower)
            if score > best_score:
                best_score = score
                best_match = task_type

        config = TASK_PATTERNS[best_match]

        # Estimate complexity from description length and keywords
        complexity = 'low'
        est_minutes = config['estimated_minutes']

        if len(task_description) > 200 or any(w in desc_lower for w in ['multiple', 'several', 'all', 'comprehensive', 'full']):
            complexity = 'high'
            est_minutes *= 2
        elif len(task_description) > 100 or any(w in desc_lower for w in ['with', 'including', 'also']):
            complexity = 'medium'
            est_minutes = int(est_minutes * 1.5)

        return {
            'type': best_match,
            'delegation': config['delegation'],
            'complexity': complexity,
            'estimated_minutes': est_minutes,
            'score': best_score,
        }

    def should_delegate(self, task_description: str, force: bool = False) -> tuple[bool, str]:
        """
        Determine if a task should be delegated to Codex.
        Returns (should_delegate, reason).
        """
        if force:
            return True, 'Forced delegation requested'

        classification = self.classify_task(task_description)

        if classification['delegation'] == 'always':
            return True, f'Build task ({classification["type"]}) — auto-delegating to Codex ({classification["estimated_minutes"]}+ min estimated)'

        if classification['delegation'] == 'never':
            return False, f'Quick task ({classification["type"]}) — handling locally'

        if classification['delegation'] == 'conditional':
            # Delegate if high complexity or many active tasks
            if classification['complexity'] == 'high':
                return True, f'High complexity {classification["type"]} task — delegating to Codex'

            active_count = len(self.active_tasks)
            if active_count >= 2:
                return True, f'OpenClaw busy ({active_count} active tasks) — delegating to Codex'

            return False, f'Manageable {classification["type"]} task — handling locally'

        return False, 'Default: handle locally'

    # ──────────────────────────────────────────────
    # Delegation
    # ──────────────────────────────────────────────

    def delegate(self, task_description: str, context: dict = None) -> dict:
        """
        Delegate a task to a Codex agent.
        Returns task tracking info.
        """
        task_id = f'codex-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        classification = self.classify_task(task_description)

        # Build the agent prompt
        agent_prompt = self._build_agent_prompt(task_description, context)

        task_record = {
            'id': task_id,
            'description': task_description[:200],
            'classification': classification,
            'status': 'delegated',
            'delegated_at': datetime.now().isoformat(),
            'completed_at': None,
            'result': None,
            'agent_prompt_length': len(agent_prompt),
        }

        # Attempt delegation via OpenClaw's sessions_spawn
        spawn_result = self._spawn_codex_agent(task_id, agent_prompt)

        if spawn_result.get('success'):
            task_record['agent_id'] = spawn_result.get('agent_id')
            task_record['status'] = 'running'
            self.active_tasks[task_id] = task_record
            logger.info(f'Task delegated to Codex: {task_id}')
        else:
            task_record['status'] = 'failed'
            task_record['error'] = spawn_result.get('error', 'Unknown error')
            logger.error(f'Delegation failed: {spawn_result.get("error")}')

        self.log.setdefault('delegated', []).append(task_record)
        self.log['total_delegated'] = self.log.get('total_delegated', 0) + 1
        self._save_log()

        return task_record

    def _build_agent_prompt(self, task: str, context: dict = None) -> str:
        """Build a comprehensive prompt for the Codex agent."""
        prompt = f"""You are a Codex agent working for 19 Keys' Sovereign Content OS.

TASK: {task}

CONTEXT:
- Workspace: {OPENCLAW_WORKSPACE}
- Content OS: {BASE_DIR}
- Obsidian Vault: {BASE_DIR / 'obsidian_vault'}
- Design: Dark theme, #0F0E12 bg, #D5FF5A green accents
- Brand: 19 Keys / ZIION / T1 Energy

RULES:
1. Complete the task fully — don't leave TODOs
2. Follow existing code patterns and style
3. Test your work before reporting completion
4. Save all outputs to the appropriate vault directory
5. Report what you did in structured JSON when done

"""
        if context:
            prompt += f"\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2)}\n"

        return prompt

    def _spawn_codex_agent(self, task_id: str, prompt: str) -> dict:
        """
        Spawn a Codex agent via OpenClaw's sessions_spawn capability.
        Falls back to local Claude API execution if OpenClaw isn't available.
        """
        # Method 1: Try OpenClaw's sessions_spawn (ACP runtime)
        try:
            openclaw_config = Path.home() / '.openclaw' / 'clawdbot.json'
            if openclaw_config.exists():
                config = json.loads(openclaw_config.read_text())
                gateway_port = config.get('gateway', {}).get('port', 18789)

                # Check if OpenClaw gateway is running
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', gateway_port))
                sock.close()

                if result == 0:
                    # Gateway is running — spawn via API
                    import requests
                    auth_token = config.get('gateway', {}).get('auth_token', '')
                    response = requests.post(
                        f'http://127.0.0.1:{gateway_port}/api/sessions/spawn',
                        json={
                            'task_id': task_id,
                            'runtime': 'acp',
                            'prompt': prompt,
                            'timeout': CODEX_CONFIG['timeout_minutes'] * 60,
                        },
                        headers={'Authorization': f'Bearer {auth_token}'},
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'success': True,
                            'agent_id': data.get('session_id', task_id),
                            'method': 'openclaw_spawn',
                        }
        except Exception as e:
            logger.debug(f'OpenClaw spawn failed: {e}')

        # Method 2: Direct Claude API execution (synchronous fallback)
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            if api_key:
                # Save prompt to file for async execution
                task_dir = BASE_DIR / 'codex_tasks' / task_id
                task_dir.mkdir(parents=True, exist_ok=True)
                (task_dir / 'prompt.txt').write_text(prompt)
                (task_dir / 'status.json').write_text(json.dumps({
                    'status': 'queued',
                    'created': datetime.now().isoformat(),
                }))

                # Launch background process
                script = f"""
import json, os, sys
sys.path.insert(0, '{BASE_DIR}')
os.environ['ANTHROPIC_API_KEY'] = '{api_key}'

import anthropic
client = anthropic.Anthropic()

prompt = open('{task_dir}/prompt.txt').read()
response = client.messages.create(
    model='{CODEX_CONFIG["model"]}',
    max_tokens={CODEX_CONFIG["max_tokens"]},
    messages=[{{'role': 'user', 'content': prompt}}]
)

result = response.content[0].text
open('{task_dir}/result.txt', 'w').write(result)
open('{task_dir}/status.json', 'w').write(json.dumps({{
    'status': 'completed',
    'completed': __import__('datetime').datetime.now().isoformat(),
}}))
"""
                script_path = task_dir / 'run.py'
                script_path.write_text(script)

                subprocess.Popen(
                    ['python3', str(script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                return {
                    'success': True,
                    'agent_id': task_id,
                    'method': 'claude_api_background',
                }

        except Exception as e:
            logger.error(f'Claude API fallback failed: {e}')

        return {
            'success': False,
            'error': 'No delegation method available (OpenClaw gateway down, no API key)',
        }

    # ──────────────────────────────────────────────
    # Task Monitoring
    # ──────────────────────────────────────────────

    def check_task_status(self, task_id: str) -> dict:
        """Check the status of a delegated task."""
        task_dir = BASE_DIR / 'codex_tasks' / task_id

        if not task_dir.exists():
            return {'status': 'not_found'}

        status_file = task_dir / 'status.json'
        if status_file.exists():
            status = json.loads(status_file.read_text())
        else:
            status = {'status': 'unknown'}

        result_file = task_dir / 'result.txt'
        if result_file.exists():
            status['result_preview'] = result_file.read_text()[:500]
            status['result_length'] = len(result_file.read_text())

        return status

    def collect_completed(self) -> list[dict]:
        """Collect results from all completed Codex tasks."""
        completed = []
        tasks_dir = BASE_DIR / 'codex_tasks'

        if not tasks_dir.exists():
            return completed

        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            status = self.check_task_status(task_dir.name)
            if status.get('status') == 'completed':
                task_id = task_dir.name
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]

                completed.append({
                    'id': task_id,
                    'status': status,
                    'completed_at': status.get('completed'),
                })

                self.log.setdefault('completed', []).append({
                    'id': task_id,
                    'completed_at': status.get('completed'),
                })
                self.log['total_completed'] = self.log.get('total_completed', 0) + 1

        self._save_log()
        return completed

    # ──────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            'active_tasks': len(self.active_tasks),
            'total_delegated': self.log.get('total_delegated', 0),
            'total_completed': self.log.get('total_completed', 0),
            'total_failed': len(self.log.get('failed', [])),
            'time_saved_minutes': self.log.get('total_time_saved_minutes', 0),
        }


def run_delegation_check() -> dict:
    """Convenience function for orchestrator — collect completed tasks."""
    delegator = CodexDelegator()
    completed = delegator.collect_completed()
    return {
        'collected': len(completed),
        'stats': delegator.get_stats(),
    }


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    delegator = CodexDelegator()

    if '--classify' in sys.argv and len(sys.argv) > 2:
        task = ' '.join(sys.argv[sys.argv.index('--classify') + 1:])
        result = delegator.classify_task(task)
        should, reason = delegator.should_delegate(task)
        print(f'Classification: {json.dumps(result, indent=2)}')
        print(f'Should delegate: {should}')
        print(f'Reason: {reason}')
    else:
        print(json.dumps(delegator.get_stats(), indent=2))
