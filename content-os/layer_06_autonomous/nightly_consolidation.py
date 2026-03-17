"""
Nightly Consolidation — 2 AM Knowledge Base Sync
Processes OpenClaw session memory files into the Obsidian knowledge graph.

Flow:
  ~/.openclaw/memory/sessions/*.md  →  Claude extraction  →  obsidian_vault/

What gets extracted:
  - Decisions made (→ 08-Raw-Notes/)
  - Predictions surfaced (→ 01-Predictions/)
  - Quotes generated (→ 03-Quotes/)
  - Tasks/action items (→ 09-Daily-Briefs/)
  - New concepts/frameworks (→ 02-Frameworks/)
  - Links between existing vault notes (wiki-link updates)

Runs via cron at 2:00 AM or on-demand: python nightly_consolidation.py
"""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger('content-os.consolidation')

# ── Paths ──
BASE_DIR = Path(__file__).parent.parent
OBSIDIAN_VAULT = BASE_DIR / 'obsidian_vault'
CONSOLIDATION_LOG = BASE_DIR / 'consolidation_log.json'

# OpenClaw memory paths (Mac Mini)
OPENCLAW_MEMORY_DB = Path.home() / '.openclaw' / 'memory' / 'main.sqlite'
OPENCLAW_SESSION_DIR = Path.home() / '.openclaw' / 'memory'
OPENCLAW_WORKSPACE = Path.home() / 'clawd'

# Session memory files written by OpenClaw's session-memory hook
SESSION_MEMORY_DIR = OPENCLAW_WORKSPACE / 'memory'


class NightlyConsolidator:
    """
    Processes daily session memory into structured vault knowledge.
    """

    def __init__(self):
        self.log = self._load_log()
        self.stats = {
            'sessions_processed': 0,
            'notes_created': 0,
            'insights_extracted': 0,
            'decisions_logged': 0,
            'tasks_captured': 0,
        }

    def _load_log(self) -> dict:
        if CONSOLIDATION_LOG.exists():
            return json.loads(CONSOLIDATION_LOG.read_text())
        return {'last_run': None, 'processed_files': [], 'processed_db_rows': 0}

    def _save_log(self):
        self.log['last_run'] = datetime.now().isoformat()
        CONSOLIDATION_LOG.write_text(json.dumps(self.log, indent=2))

    # ──────────────────────────────────────────────
    # Source 1: Session Memory Markdown Files
    # ──────────────────────────────────────────────

    def process_session_files(self) -> int:
        """Process session .md files from OpenClaw workspace memory dir."""
        count = 0

        # Check multiple possible session memory locations
        search_dirs = [
            SESSION_MEMORY_DIR,
            OPENCLAW_MEMORY_DB.parent,
            OPENCLAW_WORKSPACE,
        ]

        session_files = []
        for search_dir in search_dirs:
            if search_dir.exists():
                # Pattern: YYYY-MM-DD.md or session-*.md
                for pattern in ['????-??-??.md', 'session-*.md', 'session_*.md']:
                    session_files.extend(search_dir.glob(pattern))

        for session_file in session_files:
            if str(session_file) in self.log.get('processed_files', []):
                continue

            try:
                content = session_file.read_text(encoding='utf-8')
                if len(content.strip()) < 50:
                    continue

                # Extract structured knowledge from the session
                extracted = self._extract_from_session(content, session_file.stem)

                # Write to vault
                notes_created = self._write_session_to_vault(extracted, session_file.stem)

                self.log.setdefault('processed_files', []).append(str(session_file))
                self.stats['sessions_processed'] += 1
                count += notes_created

            except Exception as e:
                logger.error(f'Failed to process session {session_file}: {e}')

        return count

    # ──────────────────────────────────────────────
    # Source 2: SQLite Memory Database
    # ──────────────────────────────────────────────

    def process_sqlite_memory(self) -> int:
        """Process conversations from OpenClaw's main.sqlite."""
        count = 0
        if not OPENCLAW_MEMORY_DB.exists():
            logger.info('No SQLite memory DB found')
            return count

        try:
            conn = sqlite3.connect(str(OPENCLAW_MEMORY_DB))
            cursor = conn.cursor()

            # Try to find the conversations/messages table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f'SQLite tables found: {tables}')

            # Common table patterns for chat/memory DBs
            msg_table = None
            for candidate in ['messages', 'conversations', 'memory', 'sessions', 'chat_history']:
                if candidate in tables:
                    msg_table = candidate
                    break

            if not msg_table:
                logger.info(f'No recognized message table in SQLite. Tables: {tables}')
                conn.close()
                return count

            # Get columns
            cursor.execute(f'PRAGMA table_info({msg_table})')
            columns = [col[1] for col in cursor.fetchall()]
            logger.info(f'Columns in {msg_table}: {columns}')

            # Determine which columns to query
            content_col = next((c for c in columns if c in ['content', 'message', 'text', 'body']), None)
            time_col = next((c for c in columns if c in ['created_at', 'timestamp', 'date', 'time']), None)
            role_col = next((c for c in columns if c in ['role', 'sender', 'type', 'author']), None)

            if not content_col:
                logger.info(f'No content column found in {msg_table}')
                conn.close()
                return count

            # Query new rows since last consolidation
            last_row_id = self.log.get('processed_db_rows', 0)
            query = f'SELECT rowid, {content_col}'
            if role_col:
                query += f', {role_col}'
            if time_col:
                query += f', {time_col}'
            query += f' FROM {msg_table} WHERE rowid > ? ORDER BY rowid'

            cursor.execute(query, (last_row_id,))
            rows = cursor.fetchall()

            if not rows:
                conn.close()
                return count

            # Group by day and extract
            daily_content = {}
            max_rowid = last_row_id

            for row in rows:
                rowid = row[0]
                content = row[1] or ''
                max_rowid = max(max_rowid, rowid)

                # Determine date key
                if time_col and len(row) > 3:
                    try:
                        dt = datetime.fromisoformat(str(row[3 if role_col else 2]))
                        date_key = dt.strftime('%Y-%m-%d')
                    except Exception:
                        date_key = datetime.now().strftime('%Y-%m-%d')
                else:
                    date_key = datetime.now().strftime('%Y-%m-%d')

                daily_content.setdefault(date_key, []).append(content)

            # Process each day's conversations
            for date_key, messages in daily_content.items():
                combined = '\n\n---\n\n'.join(messages)
                if len(combined.strip()) < 100:
                    continue

                extracted = self._extract_from_session(combined, f'sqlite-{date_key}')
                notes = self._write_session_to_vault(extracted, f'session-db-{date_key}')
                count += notes

            self.log['processed_db_rows'] = max_rowid
            conn.close()

        except Exception as e:
            logger.error(f'SQLite processing failed: {e}')

        return count

    # ──────────────────────────────────────────────
    # Extraction Engine (uses Claude or local patterns)
    # ──────────────────────────────────────────────

    def _extract_from_session(self, content: str, session_id: str) -> dict:
        """
        Extract structured knowledge from a session transcript.
        Uses pattern matching first, upgrades to Claude API when available.
        """
        extracted = {
            'session_id': session_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'decisions': [],
            'insights': [],
            'tasks': [],
            'predictions': [],
            'quotes': [],
            'topics': [],
            'summary': '',
        }

        # ── Pattern-based extraction (always runs, no API needed) ──

        lines = content.split('\n')

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Decisions: lines with decision-like language
            if any(kw in line_clean.lower() for kw in [
                'decided to', 'decision:', 'we agreed', 'going with',
                'chosen approach', 'will use', "let's go with", 'final call'
            ]):
                extracted['decisions'].append(line_clean)

            # Tasks: lines with action items
            if any(kw in line_clean.lower() for kw in [
                'todo:', 'action:', 'need to', 'should do', 'next step',
                '- [ ]', 'task:', 'follow up', 'deadline'
            ]):
                extracted['tasks'].append(line_clean)

            # Predictions: forward-looking statements
            if any(kw in line_clean.lower() for kw in [
                'will happen', 'predict', 'by 2', 'in the next',
                'expect', 'forecast', 'going to see', 'mark my words'
            ]):
                extracted['predictions'].append(line_clean)

            # Insights: analytical observations
            if any(kw in line_clean.lower() for kw in [
                'insight:', 'key takeaway', 'important:', 'realized that',
                'the pattern', 'what this means', 'breakthrough'
            ]):
                extracted['insights'].append(line_clean)

        # Topics: extract from headings and bold text
        heading_matches = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
        extracted['topics'] = heading_matches[:10]

        # Summary: first substantial paragraph
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            extracted['summary'] = paragraphs[0][:500]

        # ── Claude API extraction (when available) ──
        try:
            claude_extraction = self._extract_with_claude(content, session_id)
            if claude_extraction:
                # Merge Claude results (Claude finds things patterns miss)
                for key in ['decisions', 'insights', 'tasks', 'predictions', 'quotes']:
                    claude_items = claude_extraction.get(key, [])
                    existing = set(str(x) for x in extracted[key])
                    for item in claude_items:
                        if str(item) not in existing:
                            extracted[key].append(item)
                if claude_extraction.get('summary'):
                    extracted['summary'] = claude_extraction['summary']
        except Exception as e:
            logger.debug(f'Claude extraction skipped: {e}')

        return extracted

    def _extract_with_claude(self, content: str, session_id: str) -> Optional[dict]:
        """Use Claude API to extract structured knowledge from session content."""
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            return None

        try:
            import anthropic
        except ImportError:
            return None

        # Truncate very long sessions
        if len(content) > 15000:
            content = content[:15000] + '\n\n[... truncated for analysis ...]'

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Analyze this OpenClaw session transcript and extract structured knowledge.

Return JSON with these keys:
- "summary": 2-3 sentence summary of what happened in this session
- "decisions": list of decisions made (strings)
- "insights": list of key insights or realizations (strings)
- "tasks": list of action items or todos (strings)
- "predictions": list of forward-looking predictions (strings)
- "quotes": list of quotable statements (strings)

Only include items that are genuinely present. Empty lists are fine.

SESSION ({session_id}):
{content}

Return ONLY valid JSON, no markdown fences."""

        try:
            response = client.messages.create(
                model=os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            result_text = response.content[0].text.strip()
            # Clean up potential markdown fences
            if result_text.startswith('```'):
                result_text = re.sub(r'^```\w*\n?', '', result_text)
                result_text = re.sub(r'\n?```$', '', result_text)
            return json.loads(result_text)
        except Exception as e:
            logger.debug(f'Claude extraction failed: {e}')
            return None

    # ──────────────────────────────────────────────
    # Vault Writer
    # ──────────────────────────────────────────────

    def _write_session_to_vault(self, extracted: dict, session_id: str) -> int:
        """Write extracted knowledge to the Obsidian vault."""
        notes_created = 0
        date_str = extracted.get('date', datetime.now().strftime('%Y-%m-%d'))

        # 1. Session consolidation note (always created)
        consolidation_dir = OBSIDIAN_VAULT / '08-Raw-Notes'
        consolidation_dir.mkdir(parents=True, exist_ok=True)

        decisions_md = '\n'.join(f'- {d}' for d in extracted['decisions']) or '_None_'
        insights_md = '\n'.join(f'- {i}' for i in extracted['insights']) or '_None_'
        tasks_md = '\n'.join(f'- [ ] {t}' for t in extracted['tasks']) or '_None_'
        topics_md = ', '.join(f'[[{t}]]' for t in extracted['topics']) or '_None_'

        note = f"""---
tags: [session, consolidated, auto-generated]
created: {date_str}
type: session-consolidation
session_id: {session_id}
---

# Session Consolidation — {session_id}

> Auto-consolidated at {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
{extracted.get('summary', '_No summary available_')}

## Decisions Made
{decisions_md}

## Key Insights
{insights_md}

## Action Items
{tasks_md}

## Topics Discussed
{topics_md}

## Predictions Surfaced
{chr(10).join(f'- {p}' for p in extracted['predictions']) or '_None_'}

## Quotable Moments
{chr(10).join(f'> "{q}"' for q in extracted['quotes']) or '_None_'}

[[Dashboard]] | [[Prediction Tracker]] | [[Quote Bank]]
"""
        note_path = consolidation_dir / f'consolidated-{session_id}.md'
        note_path.write_text(note, encoding='utf-8')
        notes_created += 1

        # 2. Spin off predictions as individual notes
        for pred in extracted['predictions']:
            pred_dir = OBSIDIAN_VAULT / '01-Predictions'
            pred_dir.mkdir(parents=True, exist_ok=True)
            slug = re.sub(r'[^\w\s-]', '', pred[:50]).strip().replace(' ', '-')
            pred_note = f"""---
tags: [prediction, auto-extracted, session]
created: {date_str}
type: prediction
source: session-{session_id}
status: pending
---

# {pred[:80]}

> Extracted from session {session_id}

## Claim
{pred}

## Verification Status
🟡 PENDING

[[Prediction Tracker]] | [[Dashboard]]
"""
            pred_path = pred_dir / f'{slug[:60]}.md'
            if not pred_path.exists():
                pred_path.write_text(pred_note, encoding='utf-8')
                notes_created += 1
                self.stats['insights_extracted'] += 1

        # 3. Spin off quotes
        for quote in extracted['quotes']:
            quote_dir = OBSIDIAN_VAULT / '03-Quotes'
            quote_dir.mkdir(parents=True, exist_ok=True)
            slug = re.sub(r'[^\w\s-]', '', quote[:40]).strip().replace(' ', '-')
            quote_note = f"""---
tags: [quote, auto-extracted, session]
created: {date_str}
type: quote
source: session-{session_id}
---

# "{quote[:60]}..."

> "{quote}"

— 19 Keys (session {session_id})

[[Quote Bank]] | [[Dashboard]]
"""
            quote_path = quote_dir / f'{slug[:50]}.md'
            if not quote_path.exists():
                quote_path.write_text(quote_note, encoding='utf-8')
                notes_created += 1

        self.stats['decisions_logged'] += len(extracted['decisions'])
        self.stats['tasks_captured'] += len(extracted['tasks'])
        self.stats['notes_created'] += notes_created

        return notes_created

    # ──────────────────────────────────────────────
    # Main Entry Point
    # ──────────────────────────────────────────────

    def run(self) -> dict:
        """Run the full nightly consolidation."""
        logger.info('═══ Nightly Consolidation: Starting ═══')

        # Process session memory files
        logger.info('Processing session memory files...')
        file_count = self.process_session_files()
        logger.info(f'  → {file_count} notes from session files')

        # Process SQLite memory database
        logger.info('Processing SQLite memory database...')
        db_count = self.process_sqlite_memory()
        logger.info(f'  → {db_count} notes from SQLite')

        # Save log
        self._save_log()

        logger.info(f'═══ Consolidation Complete: {self.stats} ═══')
        return self.stats


def run_consolidation() -> dict:
    """Convenience function for cron/orchestrator."""
    consolidator = NightlyConsolidator()
    return consolidator.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    stats = run_consolidation()
    print(json.dumps(stats, indent=2))
