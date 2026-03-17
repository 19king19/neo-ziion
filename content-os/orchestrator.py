"""
Sovereign Content OS — Orchestrator
Main daemon that runs all pipeline layers on a schedule.
Designed to run 24/7 on Mac Mini (OpenClaw bot).

Usage:
  python orchestrator.py          # Run daemon
  python orchestrator.py --once   # Run all layers once then exit
"""

import json
import logging
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

import schedule

from config.settings import (
    GDRIVE_SYNC_INTERVAL,
    YT_ANALYTICS_INTERVAL,
    INTELLIGENCE_INTERVAL,
    STATUS_FILE,
    STATUS_PORT,
    STATUS_HOST,
    VAULT_RAW,
    VAULT_TRANSCRIPTS,
    VAULT_INTELLIGENCE
)

from layer_01_ingestion.gdrive_sync import sync_drive
from layer_01_ingestion.whisper_runner import run_transcription
from layer_01_ingestion.yt_analytics import pull_analytics
from layer_02_intelligence.claude_analyzer import run_analysis
from layer_02_intelligence.quote_extractor import extract_quotes
from layer_02_intelligence.theme_clusterer import cluster_themes
from layer_03_vault.vault_publisher import VaultPublisher
from layer_04_ingestion.brain_ingest import run_ingestion
from layer_05_distribution.twitter_agent import run_twitter_schedule
from layer_06_autonomous.nightly_consolidation import run_consolidation
from layer_06_autonomous.heartbeat_monitor import run_heartbeat
from layer_06_autonomous.semantic_search import build_search_index, search_vault
from layer_06_autonomous.codex_delegator import run_delegation_check

# ── Logging Setup ──
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / 'orchestrator.log')
    ]
)
logger = logging.getLogger('content-os.orchestrator')


def count_files(directory: Path, pattern='*') -> int:
    """Count files in a directory."""
    try:
        return len(list(directory.glob(pattern)))
    except Exception:
        return 0


def update_status(layer=None, status='idle', detail=''):
    """Update the global status file."""
    try:
        if STATUS_FILE.exists():
            current = json.loads(STATUS_FILE.read_text())
        else:
            current = {
                'system': 'online',
                'started_at': datetime.now().isoformat(),
                'layers': {},
                'last_run': {}
            }

        if layer:
            current['layers'][layer] = {
                'status': status,
                'detail': detail,
                'updated_at': datetime.now().isoformat()
            }
            current['last_run'][layer] = datetime.now().isoformat()

        # Update counts
        current['total_assets'] = count_files(VAULT_RAW)
        current['processed'] = count_files(VAULT_TRANSCRIPTS, '*.json')
        current['outputs'] = count_files(VAULT_INTELLIGENCE, '*.json')
        current['updated_at'] = datetime.now().isoformat()

        # Build module status array for frontend
        modules = []
        for i in range(31):  # 31 total module cards in UI
            modules.append('idle')
        # Map layer statuses to module indices
        layer_map = {
            'gdrive': [0], 'youtube': [1], 'whisper': [2],
            'fingerprint': [3], 'archive': [4],
            'analyzer': [5], 'predictions': [6], 'quotes': [7],
            'themes': [8], 'analytics_intel': [9]
        }
        for lname, indices in layer_map.items():
            if lname in current.get('layers', {}):
                s = current['layers'][lname].get('status', 'idle')
                for idx in indices:
                    modules[idx] = s

        current['modules'] = modules

        STATUS_FILE.write_text(json.dumps(current, indent=2))

    except Exception as e:
        logger.error(f'Failed to update status: {e}')


# ── Pipeline Jobs ──

def job_gdrive_sync():
    """Scheduled: Google Drive sync."""
    update_status('gdrive', 'active', 'Syncing...')
    try:
        count = sync_drive()
        update_status('gdrive', 'idle', f'{count} new files')
    except Exception as e:
        update_status('gdrive', 'error', str(e))
        logger.error(f'GDrive sync job failed: {e}')


def job_whisper():
    """Scheduled: Whisper transcription."""
    update_status('whisper', 'active', 'Transcribing...')
    try:
        count = run_transcription()
        update_status('whisper', 'idle', f'{count} transcribed')
    except Exception as e:
        update_status('whisper', 'error', str(e))
        logger.error(f'Whisper job failed: {e}')


def job_youtube():
    """Scheduled: YouTube analytics pull."""
    update_status('youtube', 'active', 'Pulling analytics...')
    try:
        data = pull_analytics()
        detail = f"{len(data.get('recent_videos', []))} videos" if data else 'No data'
        update_status('youtube', 'idle', detail)
    except Exception as e:
        update_status('youtube', 'error', str(e))
        logger.error(f'YouTube job failed: {e}')


def job_intelligence():
    """Scheduled: Claude analysis + quote extraction + theme clustering."""
    update_status('analyzer', 'active', 'Analyzing content...')
    try:
        analyzed = run_analysis()
        update_status('analyzer', 'idle', f'{analyzed} analyzed')
    except Exception as e:
        update_status('analyzer', 'error', str(e))

    update_status('quotes', 'active', 'Extracting quotes...')
    try:
        quotes = extract_quotes()
        update_status('quotes', 'idle', f'{quotes} new quotes')
    except Exception as e:
        update_status('quotes', 'error', str(e))

    update_status('themes', 'active', 'Clustering themes...')
    try:
        themes = cluster_themes()
        update_status('themes', 'idle', f"{themes.get('total_themes', 0)} themes")
    except Exception as e:
        update_status('themes', 'error', str(e))


def job_vault_publish():
    """Scheduled: Publish intelligence to Obsidian vault."""
    update_status('vault', 'active', 'Publishing to Obsidian vault...')
    try:
        publisher = VaultPublisher()
        stats = publisher.publish_all()
        total = stats.get('total', 0)
        update_status('vault', 'idle', f'{total} notes published')
    except Exception as e:
        update_status('vault', 'error', str(e))
        logger.error(f'Vault publish job failed: {e}')


def job_brain_ingest():
    """Scheduled: Brain ingestion — feed knowledge into Obsidian vault."""
    update_status('brain_ingest', 'active', 'Ingesting knowledge...')
    try:
        stats = run_ingestion()
        total = stats.get('notes_created', 0)
        update_status('brain_ingest', 'idle', f'{total} notes ingested')
    except Exception as e:
        update_status('brain_ingest', 'error', str(e))
        logger.error(f'Brain ingest job failed: {e}')


def job_twitter():
    """Scheduled: Autonomous Twitter/X posting."""
    update_status('twitter', 'active', 'Posting to X...')
    try:
        result = run_twitter_schedule()
        posted = result.get('posted', 0)
        update_status('twitter', 'idle', f'{posted} posts sent')
    except Exception as e:
        update_status('twitter', 'error', str(e))
        logger.error(f'Twitter job failed: {e}')


def job_nightly_consolidation():
    """Scheduled: 2 AM nightly session → vault sync."""
    update_status('consolidation', 'active', 'Consolidating sessions...')
    try:
        stats = run_consolidation()
        notes = stats.get('notes_created', 0)
        update_status('consolidation', 'idle', f'{notes} notes consolidated')
    except Exception as e:
        update_status('consolidation', 'error', str(e))
        logger.error(f'Nightly consolidation failed: {e}')


def job_heartbeat():
    """Scheduled: Health check all services."""
    try:
        result = run_heartbeat()
        unhealthy = sum(1 for s in result.get('services', {}).values()
                        if s.get('status') != 'healthy')
        if unhealthy > 0:
            update_status('heartbeat', 'pending', f'{unhealthy} services unhealthy')
        else:
            update_status('heartbeat', 'idle', 'All systems healthy')
    except Exception as e:
        update_status('heartbeat', 'error', str(e))
        logger.error(f'Heartbeat check failed: {e}')


def job_search_index():
    """Scheduled: Rebuild semantic search index."""
    update_status('search', 'active', 'Indexing vault...')
    try:
        stats = build_search_index()
        indexed = stats.get('total_indexed', 0)
        update_status('search', 'idle', f'{indexed} notes indexed')
    except Exception as e:
        update_status('search', 'error', str(e))
        logger.error(f'Search index rebuild failed: {e}')


def job_delegation_check():
    """Scheduled: Collect results from delegated Codex tasks."""
    try:
        result = run_delegation_check()
        collected = result.get('collected', 0)
        if collected > 0:
            update_status('codex', 'idle', f'{collected} tasks completed')
            logger.info(f'Collected {collected} completed Codex tasks')
    except Exception as e:
        update_status('codex', 'error', str(e))
        logger.error(f'Delegation check failed: {e}')


def run_all_once():
    """Run all pipeline layers once (useful for testing)."""
    logger.info('═══ Running all layers once ═══')
    job_gdrive_sync()
    job_whisper()
    job_youtube()
    job_intelligence()
    job_vault_publish()
    job_brain_ingest()
    job_search_index()
    job_delegation_check()
    job_heartbeat()
    logger.info('═══ All layers complete ═══')


def start_status_server():
    """Start the FastAPI status server in a background thread."""
    try:
        from status_server import app
        import uvicorn
        uvicorn.run(app, host=STATUS_HOST, port=STATUS_PORT, log_level='warning')
    except Exception as e:
        logger.error(f'Status server failed to start: {e}')


def run_daemon():
    """Main daemon loop — schedules all jobs and runs forever."""
    logger.info('╔══════════════════════════════════════════╗')
    logger.info('║   SOVEREIGN CONTENT OS — DAEMON START    ║')
    logger.info('╚══════════════════════════════════════════╝')

    # Initialize status
    update_status()

    # Start status server in background
    server_thread = threading.Thread(target=start_status_server, daemon=True)
    server_thread.start()
    logger.info(f'Status server started on port {STATUS_PORT}')

    # Schedule jobs — Core Pipeline
    schedule.every(GDRIVE_SYNC_INTERVAL).minutes.do(job_gdrive_sync)
    schedule.every(GDRIVE_SYNC_INTERVAL).minutes.do(job_whisper)  # Run after gdrive
    schedule.every(YT_ANALYTICS_INTERVAL).minutes.do(job_youtube)
    schedule.every(INTELLIGENCE_INTERVAL).minutes.do(job_intelligence)
    schedule.every(INTELLIGENCE_INTERVAL).minutes.do(job_vault_publish)
    schedule.every(INTELLIGENCE_INTERVAL).minutes.do(job_brain_ingest)

    # Schedule jobs — Distribution
    schedule.every(4).hours.do(job_twitter)  # 3x/day max, every 4 hours

    # Schedule jobs — Autonomous Layer
    schedule.every(5).minutes.do(job_heartbeat)  # Every 5 minutes
    schedule.every(60).minutes.do(job_search_index)  # Rebuild index hourly
    schedule.every(5).minutes.do(job_delegation_check)  # Check for completed Codex tasks
    schedule.every().day.at('02:00').do(job_nightly_consolidation)  # 2 AM daily

    logger.info(f'Schedules set:')
    logger.info(f'  GDrive sync:     every {GDRIVE_SYNC_INTERVAL} min')
    logger.info(f'  Whisper:         every {GDRIVE_SYNC_INTERVAL} min')
    logger.info(f'  YouTube:         every {YT_ANALYTICS_INTERVAL} min')
    logger.info(f'  Intelligence:    every {INTELLIGENCE_INTERVAL} min')
    logger.info(f'  Vault publish:   every {INTELLIGENCE_INTERVAL} min')
    logger.info(f'  Brain ingest:    every {INTELLIGENCE_INTERVAL} min')
    logger.info(f'  Twitter/X:       every 4 hours')
    logger.info(f'  Heartbeat:       every 5 min')
    logger.info(f'  Search index:    every 60 min')
    logger.info(f'  Codex check:     every 5 min')
    logger.info(f'  Consolidation:   daily at 2:00 AM')

    # Run all immediately on startup
    run_all_once()

    # Main loop
    logger.info('Entering main loop...')
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    if '--once' in sys.argv:
        run_all_once()
    else:
        run_daemon()
