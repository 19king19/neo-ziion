"""
Sovereign Content OS — Configuration
Loads environment variables from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from config directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ── Google APIs ──
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', './config/google_credentials.json')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

# ── YouTube ──
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID', '')

# ── Anthropic / Claude ──
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

# ── Whisper ──
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')

# ── Vault Paths ──
BASE_DIR = Path(__file__).parent.parent
VAULT_RAW = Path(os.getenv('VAULT_RAW', str(BASE_DIR / 'vault' / 'raw')))
VAULT_TRANSCRIPTS = Path(os.getenv('VAULT_TRANSCRIPTS', str(BASE_DIR / 'vault' / 'transcripts')))
VAULT_INTELLIGENCE = Path(os.getenv('VAULT_INTELLIGENCE', str(BASE_DIR / 'vault' / 'intelligence')))

# Ensure vault directories exist
VAULT_RAW.mkdir(parents=True, exist_ok=True)
VAULT_TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
VAULT_INTELLIGENCE.mkdir(parents=True, exist_ok=True)

# ── Status Server ──
STATUS_PORT = int(os.getenv('STATUS_PORT', '8819'))
STATUS_HOST = os.getenv('STATUS_HOST', '0.0.0.0')

# ── Schedule Intervals (minutes) ──
GDRIVE_SYNC_INTERVAL = int(os.getenv('GDRIVE_SYNC_INTERVAL', '15'))
YT_ANALYTICS_INTERVAL = int(os.getenv('YT_ANALYTICS_INTERVAL', '60'))
INTELLIGENCE_INTERVAL = int(os.getenv('INTELLIGENCE_INTERVAL', '30'))

# ── Status file ──
STATUS_FILE = BASE_DIR / 'status.json'
SYNC_MANIFEST = BASE_DIR / 'sync_manifest.json'
