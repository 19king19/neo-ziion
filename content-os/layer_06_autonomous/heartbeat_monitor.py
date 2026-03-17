"""
Heartbeat Monitor — Process Health Checker with Auto-Restart
Monitors critical Content OS services and auto-restarts crashed ones.

Checks:
  1. Orchestrator daemon (orchestrator.py)
  2. Status API server (FastAPI on port 8819)
  3. OpenClaw gateway (port 18789)
  4. Disk space
  5. Memory usage
  6. Last pipeline run freshness

Auto-restart:
  - If orchestrator is down → restart it
  - If status server is down → restart it
  - If pipeline hasn't run in 2x interval → alert

Alerting:
  - Writes to HEARTBEAT.md in OpenClaw workspace
  - Posts to Telegram via OpenClaw bot (when configured)
  - Logs all events

Usage:
  python heartbeat_monitor.py          # Run continuous monitoring
  python heartbeat_monitor.py --once   # Single health check
"""

import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger('content-os.heartbeat')

BASE_DIR = Path(__file__).parent.parent
HEARTBEAT_FILE = BASE_DIR / 'HEARTBEAT.md'
HEARTBEAT_LOG = BASE_DIR / 'heartbeat_log.json'
STATUS_FILE = BASE_DIR / 'status.json'

# ── Config ──
CHECKS_INTERVAL = 60  # seconds between health checks
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN = 300  # 5 min between restart attempts
STALE_PIPELINE_THRESHOLD = 3600  # 1 hour = pipeline is stale

SERVICES = {
    'orchestrator': {
        'name': 'Content OS Orchestrator',
        'process_name': 'orchestrator.py',
        'restart_cmd': f'cd {BASE_DIR} && nohup python3 orchestrator.py > /dev/null 2>&1 &',
        'critical': True,
    },
    'status_server': {
        'name': 'Status API Server',
        'port': 8819,
        'restart_cmd': f'cd {BASE_DIR} && nohup python3 -m uvicorn status_server:app --host 0.0.0.0 --port 8819 > /dev/null 2>&1 &',
        'critical': True,
    },
    'openclaw_gateway': {
        'name': 'OpenClaw Gateway',
        'port': 18789,
        'restart_cmd': None,  # Managed externally
        'critical': False,
    },
}


class HeartbeatMonitor:
    """Monitors service health and auto-restarts crashed processes."""

    def __init__(self):
        self.log = self._load_log()
        self.alerts = []

    def _load_log(self) -> dict:
        if HEARTBEAT_LOG.exists():
            try:
                return json.loads(HEARTBEAT_LOG.read_text())
            except Exception:
                pass
        return {
            'checks': [],
            'restarts': [],
            'last_check': None,
            'consecutive_failures': {},
        }

    def _save_log(self):
        self.log['last_check'] = datetime.now().isoformat()
        # Keep last 1000 checks
        if len(self.log.get('checks', [])) > 1000:
            self.log['checks'] = self.log['checks'][-1000:]
        if len(self.log.get('restarts', [])) > 200:
            self.log['restarts'] = self.log['restarts'][-200:]
        HEARTBEAT_LOG.write_text(json.dumps(self.log, indent=2))

    # ──────────────────────────────────────────────
    # Health Checks
    # ──────────────────────────────────────────────

    def check_port(self, port: int, host: str = '127.0.0.1', timeout: float = 3.0) -> bool:
        """Check if a port is accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def check_process(self, process_name: str) -> bool:
        """Check if a process is running by name."""
        try:
            result = subprocess.run(
                ['pgrep', '-f', process_name],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_disk_space(self, path: str = '/') -> dict:
        """Check disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            pct_used = (used / total) * 100
            return {
                'total_gb': round(total / (1024**3), 1),
                'used_gb': round(used / (1024**3), 1),
                'free_gb': round(free / (1024**3), 1),
                'pct_used': round(pct_used, 1),
                'healthy': pct_used < 90,
            }
        except Exception as e:
            return {'error': str(e), 'healthy': False}

    def check_pipeline_freshness(self) -> dict:
        """Check when the pipeline last ran."""
        if not STATUS_FILE.exists():
            return {'status': 'no_status_file', 'healthy': False, 'stale': True}

        try:
            status = json.loads(STATUS_FILE.read_text())
            updated_at = status.get('updated_at', '')
            if not updated_at:
                return {'status': 'no_timestamp', 'healthy': False, 'stale': True}

            last_update = datetime.fromisoformat(updated_at)
            age_seconds = (datetime.now() - last_update).total_seconds()
            stale = age_seconds > STALE_PIPELINE_THRESHOLD

            return {
                'last_update': updated_at,
                'age_seconds': int(age_seconds),
                'age_human': self._human_time(age_seconds),
                'healthy': not stale,
                'stale': stale,
                'system_status': status.get('system', 'unknown'),
            }
        except Exception as e:
            return {'error': str(e), 'healthy': False, 'stale': True}

    def check_memory_usage(self) -> dict:
        """Check system memory usage."""
        try:
            # macOS: use vm_stat
            result = subprocess.run(
                ['vm_stat'], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Parse page size and counts
                page_size = 16384  # default for Apple Silicon
                free_pages = 0
                active_pages = 0
                for line in lines:
                    if 'page size of' in line:
                        try:
                            page_size = int(line.split('page size of')[1].strip().rstrip('.'))
                        except ValueError:
                            pass
                    if 'Pages free' in line:
                        free_pages = int(line.split(':')[1].strip().rstrip('.'))
                    if 'Pages active' in line:
                        active_pages = int(line.split(':')[1].strip().rstrip('.'))

                free_mb = (free_pages * page_size) / (1024 * 1024)
                active_mb = (active_pages * page_size) / (1024 * 1024)

                return {
                    'free_mb': round(free_mb),
                    'active_mb': round(active_mb),
                    'healthy': free_mb > 500,  # Alert if < 500 MB free
                }
            return {'status': 'vm_stat_failed', 'healthy': True}
        except Exception as e:
            return {'error': str(e), 'healthy': True}

    # ──────────────────────────────────────────────
    # Auto-Restart
    # ──────────────────────────────────────────────

    def restart_service(self, service_key: str) -> bool:
        """Attempt to restart a crashed service."""
        service = SERVICES.get(service_key)
        if not service or not service.get('restart_cmd'):
            logger.warning(f'No restart command for {service_key}')
            return False

        # Check cooldown
        recent_restarts = [
            r for r in self.log.get('restarts', [])
            if r['service'] == service_key
            and (datetime.now() - datetime.fromisoformat(r['time'])).total_seconds() < RESTART_COOLDOWN
        ]
        if len(recent_restarts) >= MAX_RESTART_ATTEMPTS:
            logger.error(f'{service_key} exceeded restart limit ({MAX_RESTART_ATTEMPTS} in {RESTART_COOLDOWN}s)')
            self.alerts.append(f'🔴 CRITICAL: {service["name"]} keeps crashing — manual intervention needed')
            return False

        logger.info(f'Restarting {service["name"]}...')
        try:
            subprocess.Popen(
                service['restart_cmd'],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(3)

            # Verify restart
            if service.get('port'):
                alive = self.check_port(service['port'])
            elif service.get('process_name'):
                alive = self.check_process(service['process_name'])
            else:
                alive = True

            self.log.setdefault('restarts', []).append({
                'service': service_key,
                'time': datetime.now().isoformat(),
                'success': alive,
            })

            if alive:
                logger.info(f'  ✓ {service["name"]} restarted successfully')
                self.alerts.append(f'🟢 {service["name"]} auto-restarted successfully')
            else:
                logger.error(f'  ✗ {service["name"]} failed to restart')
                self.alerts.append(f'🔴 {service["name"]} failed to restart')

            return alive

        except Exception as e:
            logger.error(f'Restart failed for {service_key}: {e}')
            return False

    # ──────────────────────────────────────────────
    # Full Health Check
    # ──────────────────────────────────────────────

    def run_health_check(self) -> dict:
        """Run all health checks and auto-restart if needed."""
        now = datetime.now()
        report = {
            'timestamp': now.isoformat(),
            'services': {},
            'system': {},
            'overall': 'healthy',
        }

        # Check each service
        for key, service in SERVICES.items():
            alive = False

            if service.get('port'):
                alive = self.check_port(service['port'])
            elif service.get('process_name'):
                alive = self.check_process(service['process_name'])

            report['services'][key] = {
                'name': service['name'],
                'alive': alive,
                'critical': service.get('critical', False),
            }

            if not alive:
                logger.warning(f'{service["name"]} is DOWN')
                self.log.setdefault('consecutive_failures', {})[key] = \
                    self.log.get('consecutive_failures', {}).get(key, 0) + 1

                if service.get('critical') and service.get('restart_cmd'):
                    restarted = self.restart_service(key)
                    report['services'][key]['restarted'] = restarted
                    if not restarted:
                        report['overall'] = 'critical'
                elif service.get('critical'):
                    report['overall'] = 'degraded'
            else:
                self.log.setdefault('consecutive_failures', {})[key] = 0

        # System checks
        report['system']['disk'] = self.check_disk_space()
        report['system']['memory'] = self.check_memory_usage()
        report['system']['pipeline'] = self.check_pipeline_freshness()

        if not report['system']['disk'].get('healthy'):
            report['overall'] = 'warning'
            self.alerts.append(f'⚠️ Disk space low: {report["system"]["disk"].get("free_gb", "?")} GB free')

        if report['system']['pipeline'].get('stale'):
            if report['overall'] == 'healthy':
                report['overall'] = 'warning'
            self.alerts.append(f'⚠️ Pipeline stale: last run {report["system"]["pipeline"].get("age_human", "unknown")} ago')

        # Log the check
        self.log.setdefault('checks', []).append({
            'time': now.isoformat(),
            'overall': report['overall'],
            'services_up': sum(1 for s in report['services'].values() if s['alive']),
            'services_total': len(report['services']),
        })

        self._save_log()

        return report

    # ──────────────────────────────────────────────
    # HEARTBEAT.md Writer
    # ──────────────────────────────────────────────

    def write_heartbeat_file(self, report: dict):
        """Update HEARTBEAT.md with current status."""
        now = datetime.now()
        overall = report.get('overall', 'unknown')
        emoji = {'healthy': '🟢', 'warning': '⚠️', 'degraded': '🟡', 'critical': '🔴'}.get(overall, '❓')

        services_md = ''
        for key, svc in report.get('services', {}).items():
            status = '🟢 UP' if svc['alive'] else '🔴 DOWN'
            if svc.get('restarted'):
                status += ' (auto-restarted)'
            services_md += f'| {svc["name"]} | {status} | {"Critical" if svc["critical"] else "Normal"} |\n'

        disk = report.get('system', {}).get('disk', {})
        pipeline = report.get('system', {}).get('pipeline', {})

        alerts_md = '\n'.join(f'- {a}' for a in self.alerts) if self.alerts else '- None'

        content = f"""# 💓 HEARTBEAT — System Health Status

> Last check: {now.strftime('%Y-%m-%d %H:%M:%S')}
> Overall: {emoji} **{overall.upper()}**

---

## Services

| Service | Status | Priority |
|---------|--------|----------|
{services_md}

## System Resources

| Resource | Value | Status |
|----------|-------|--------|
| Disk Used | {disk.get('pct_used', '?')}% ({disk.get('free_gb', '?')} GB free) | {'🟢' if disk.get('healthy') else '🔴'} |
| Pipeline | Last run {pipeline.get('age_human', 'never')} ago | {'🟢' if pipeline.get('healthy') else '🔴'} |

## Recent Alerts

{alerts_md}

## Auto-Restart Log (Last 24h)

"""
        recent_restarts = [
            r for r in self.log.get('restarts', [])
            if (now - datetime.fromisoformat(r['time'])).total_seconds() < 86400
        ]
        if recent_restarts:
            for r in recent_restarts:
                emoji_r = '✅' if r.get('success') else '❌'
                content += f'- {emoji_r} {r["service"]} at {r["time"]}\n'
        else:
            content += '- No restarts in last 24 hours\n'

        content += f"""
---

## Stats

- Total health checks: {len(self.log.get('checks', []))}
- Total auto-restarts: {len(self.log.get('restarts', []))}
- Monitor uptime: continuous
- Check interval: {CHECKS_INTERVAL}s
"""

        HEARTBEAT_FILE.write_text(content, encoding='utf-8')

        # Also write to OpenClaw workspace if available
        openclaw_heartbeat = Path.home() / 'clawd' / 'HEARTBEAT.md'
        try:
            openclaw_heartbeat.write_text(content, encoding='utf-8')
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _human_time(self, seconds: float) -> str:
        if seconds < 60:
            return f'{int(seconds)}s'
        elif seconds < 3600:
            return f'{int(seconds/60)}m'
        elif seconds < 86400:
            return f'{int(seconds/3600)}h {int((seconds%3600)/60)}m'
        else:
            return f'{int(seconds/86400)}d {int((seconds%86400)/3600)}h'

    # ──────────────────────────────────────────────
    # Main Loop
    # ──────────────────────────────────────────────

    def run_once(self) -> dict:
        """Single health check cycle."""
        self.alerts = []
        report = self.run_health_check()
        self.write_heartbeat_file(report)
        return report

    def run_daemon(self):
        """Continuous monitoring loop."""
        logger.info('╔══════════════════════════════════════════╗')
        logger.info('║  HEARTBEAT MONITOR — STARTING            ║')
        logger.info(f'║  Check interval: {CHECKS_INTERVAL}s                   ║')
        logger.info('╚══════════════════════════════════════════╝')

        while True:
            try:
                report = self.run_once()
                overall = report.get('overall', 'unknown')
                services_up = sum(1 for s in report.get('services', {}).values() if s['alive'])
                total = len(report.get('services', {}))
                logger.info(f'Health: {overall} | Services: {services_up}/{total}')
            except Exception as e:
                logger.error(f'Health check failed: {e}')

            time.sleep(CHECKS_INTERVAL)


def run_heartbeat() -> dict:
    """Convenience function for orchestrator."""
    monitor = HeartbeatMonitor()
    return monitor.run_once()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [HEARTBEAT] %(levelname)s: %(message)s'
    )

    if '--once' in sys.argv:
        monitor = HeartbeatMonitor()
        report = monitor.run_once()
        print(json.dumps(report, indent=2))
    else:
        monitor = HeartbeatMonitor()
        monitor.run_daemon()
