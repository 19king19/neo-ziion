"""
Sovereign Content OS — Google API Setup Wizard
Run this once to connect Google Drive + YouTube APIs.

Usage:
  python setup_google.py

What this does:
  1. Guides you to create a Google Cloud project (if needed)
  2. Opens browser for OAuth consent
  3. Saves credentials locally
  4. Tests the connection
"""

import json
import sys
import webbrowser
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / 'config'
CREDENTIALS_PATH = CONFIG_DIR / 'google_credentials.json'
GDRIVE_TOKEN_PATH = CONFIG_DIR / 'gdrive_token.json'
YOUTUBE_TOKEN_PATH = CONFIG_DIR / 'youtube_token.json'
ENV_PATH = CONFIG_DIR / '.env'


def print_banner():
    print()
    print('╔══════════════════════════════════════════════╗')
    print('║   SOVEREIGN CONTENT OS — Google API Setup    ║')
    print('╚══════════════════════════════════════════════╝')
    print()


def step_1_credentials():
    """Check for or guide creation of Google OAuth credentials."""
    if CREDENTIALS_PATH.exists():
        print('✅ Google credentials file found!')
        creds = json.loads(CREDENTIALS_PATH.read_text())
        if 'installed' in creds or 'web' in creds:
            print('   Credentials look valid.')
            return True
        else:
            print('   ⚠️  Credentials file format looks wrong.')

    print()
    print('━━━ STEP 1: Get Google OAuth Credentials ━━━')
    print()
    print('You need a Google Cloud OAuth client ID. Here\'s the fastest way:')
    print()
    print('  1. Go to: https://console.cloud.google.com/apis/credentials')
    print('  2. Create a project (or select existing one)')
    print('  3. Click "+ CREATE CREDENTIALS" → "OAuth client ID"')
    print('  4. Application type: "Desktop app"')
    print('  5. Name it: "Sovereign Content OS"')
    print('  6. Click CREATE')
    print('  7. Click "DOWNLOAD JSON"')
    print(f'  8. Save the file to: {CREDENTIALS_PATH}')
    print()
    print('  ⚡ ALSO enable these APIs in your project:')
    print('     - Google Drive API')
    print('     - YouTube Data API v3')
    print('     (APIs & Services → Library → search each one → Enable)')
    print()

    open_browser = input('Open Google Cloud Console in browser? (y/n): ').strip().lower()
    if open_browser == 'y':
        webbrowser.open('https://console.cloud.google.com/apis/credentials')

    print()
    input('Press ENTER when you\'ve saved the credentials JSON file...')

    if CREDENTIALS_PATH.exists():
        print('✅ Credentials file found!')
        return True
    else:
        manual = input(f'File not found at {CREDENTIALS_PATH}. Paste the full path to your downloaded JSON: ').strip()
        if manual:
            import shutil
            src = Path(manual.strip('"').strip("'"))
            if src.exists():
                shutil.copy(src, CREDENTIALS_PATH)
                print('✅ Credentials copied!')
                return True
        print('❌ Could not find credentials file.')
        return False


def step_2_gdrive_auth():
    """Authenticate with Google Drive."""
    print()
    print('━━━ STEP 2: Connect Google Drive ━━━')
    print()

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        print('Opening browser for Google Drive authorization...')
        creds = flow.run_local_server(port=8820)

        GDRIVE_TOKEN_PATH.write_text(creds.to_json())
        print('✅ Google Drive connected!')

        # Test it
        service = build('drive', 'v3', credentials=creds)
        about = service.about().get(fields='user').execute()
        user = about.get('user', {})
        print(f'   Logged in as: {user.get("displayName", "Unknown")} ({user.get("emailAddress", "")})')

        # List root folders to help pick one
        print()
        print('   Your top-level Drive folders:')
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
            pageSize=15,
            fields='files(id, name)'
        ).execute()
        folders = results.get('files', [])
        for i, f in enumerate(folders):
            print(f'   [{i+1}] {f["name"]}  (ID: {f["id"]})')

        print()
        choice = input('Which folder should Content OS sync from? (enter number or paste folder ID): ').strip()

        folder_id = ''
        if choice.isdigit() and 1 <= int(choice) <= len(folders):
            folder_id = folders[int(choice) - 1]['id']
            print(f'   Selected: {folders[int(choice) - 1]["name"]}')
        elif len(choice) > 10:
            folder_id = choice

        if folder_id:
            update_env('GOOGLE_DRIVE_FOLDER_ID', folder_id)
            print('✅ Drive folder saved!')

        return True

    except ImportError:
        print('❌ Google API libraries not installed.')
        print('   Run: pip install google-api-python-client google-auth-oauthlib')
        return False
    except Exception as e:
        print(f'❌ Drive auth failed: {e}')
        return False


def step_3_youtube_auth():
    """Authenticate with YouTube."""
    print()
    print('━━━ STEP 3: Connect YouTube ━━━')
    print()

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        print('Opening browser for YouTube authorization...')
        creds = flow.run_local_server(port=8821)

        YOUTUBE_TOKEN_PATH.write_text(creds.to_json())
        print('✅ YouTube connected!')

        # Get channel info
        service = build('youtube', 'v3', credentials=creds)
        request = service.channels().list(part='snippet,statistics', mine=True)
        response = request.execute()

        if response.get('items'):
            channel = response['items'][0]
            channel_id = channel['id']
            channel_name = channel['snippet']['title']
            subs = channel['statistics'].get('subscriberCount', '?')
            print(f'   Channel: {channel_name}')
            print(f'   Subscribers: {subs}')
            print(f'   Channel ID: {channel_id}')

            update_env('YOUTUBE_CHANNEL_ID', channel_id)
            print('✅ YouTube channel saved!')

        return True

    except ImportError:
        print('❌ Google API libraries not installed.')
        print('   Run: pip install google-api-python-client google-auth-oauthlib')
        return False
    except Exception as e:
        print(f'❌ YouTube auth failed: {e}')
        return False


def step_4_anthropic():
    """Set up Anthropic API key."""
    print()
    print('━━━ STEP 4: Connect Claude / Anthropic ━━━')
    print()

    # Check if already set
    if ENV_PATH.exists():
        env_content = ENV_PATH.read_text()
        if 'ANTHROPIC_API_KEY=sk-' in env_content:
            print('✅ Anthropic API key already configured!')
            return True

    print('Get your API key from: https://console.anthropic.com/settings/keys')
    print()

    open_browser = input('Open Anthropic Console in browser? (y/n): ').strip().lower()
    if open_browser == 'y':
        webbrowser.open('https://console.anthropic.com/settings/keys')

    print()
    api_key = input('Paste your Anthropic API key (starts with sk-ant-): ').strip()

    if api_key and api_key.startswith('sk-'):
        update_env('ANTHROPIC_API_KEY', api_key)
        print('✅ Anthropic API key saved!')
        return True
    else:
        print('⚠️  Key doesn\'t look right. You can set it later in config/.env')
        return False


def update_env(key, value):
    """Update or create .env file with a key=value pair."""
    if not ENV_PATH.exists():
        # Copy from template
        template = CONFIG_DIR / '.env.template'
        if template.exists():
            ENV_PATH.write_text(template.read_text())
        else:
            ENV_PATH.write_text('')

    content = ENV_PATH.read_text()
    lines = content.split('\n')
    found = False

    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}'
            found = True
            break

    if not found:
        lines.append(f'{key}={value}')

    ENV_PATH.write_text('\n'.join(lines))


def print_summary():
    """Print setup status summary."""
    print()
    print('╔══════════════════════════════════════════════╗')
    print('║            SETUP STATUS SUMMARY              ║')
    print('╚══════════════════════════════════════════════╝')
    print()

    checks = [
        ('Google Credentials', CREDENTIALS_PATH.exists()),
        ('Google Drive Token', GDRIVE_TOKEN_PATH.exists()),
        ('YouTube Token', YOUTUBE_TOKEN_PATH.exists()),
    ]

    # Check .env for API key
    has_anthropic = False
    has_drive_folder = False
    has_yt_channel = False
    if ENV_PATH.exists():
        env = ENV_PATH.read_text()
        has_anthropic = 'ANTHROPIC_API_KEY=sk-' in env
        has_drive_folder = 'GOOGLE_DRIVE_FOLDER_ID=' in env and 'your_drive_folder_id_here' not in env
        has_yt_channel = 'YOUTUBE_CHANNEL_ID=' in env and 'your_channel_id_here' not in env

    checks.extend([
        ('Anthropic API Key', has_anthropic),
        ('Drive Folder ID', has_drive_folder),
        ('YouTube Channel ID', has_yt_channel),
    ])

    all_good = True
    for name, status in checks:
        icon = '✅' if status else '❌'
        if not status:
            all_good = False
        print(f'  {icon}  {name}')

    print()
    if all_good:
        print('🚀 All connectors ready! Run: python orchestrator.py')
    else:
        print('⚠️  Some connectors not set up yet. Run this script again to continue.')
    print()


if __name__ == '__main__':
    print_banner()

    # Check what's already set up
    if '--status' in sys.argv:
        print_summary()
        sys.exit(0)

    if not step_1_credentials():
        print('\n⚠️  Cannot continue without Google credentials. Run again when ready.')
        print_summary()
        sys.exit(1)

    step_2_gdrive_auth()
    step_3_youtube_auth()
    step_4_anthropic()
    print_summary()
