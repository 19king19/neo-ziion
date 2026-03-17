"""
Sovereign Content OS — Status API Server
FastAPI server on port 8819 that serves pipeline status to the ZIION UI.
Runs as part of the orchestrator daemon.
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import STATUS_FILE, VAULT_RAW, VAULT_TRANSCRIPTS, VAULT_INTELLIGENCE, OBSIDIAN_VAULT_PATH

app = FastAPI(title='Sovereign Content OS', version='1.0.0')

# Allow CORS from ZIION frontend (GitHub Pages + localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'https://19king19.github.io',
        'http://localhost:*',
        'http://127.0.0.1:*',
        '*'  # Development — tighten in production
    ],
    allow_methods=['GET'],
    allow_headers=['*'],
)


def count_files(directory: Path, pattern='*') -> int:
    """Count files in a directory."""
    try:
        return len(list(directory.glob(pattern)))
    except Exception:
        return 0


@app.get('/api/status')
def get_status():
    """Return current pipeline status for the ZIION dashboard."""
    try:
        if STATUS_FILE.exists():
            status = json.loads(STATUS_FILE.read_text())
        else:
            status = {'system': 'starting'}

        # Always include fresh counts
        status['total_assets'] = count_files(VAULT_RAW)
        status['processed'] = count_files(VAULT_TRANSCRIPTS, '*.json')
        status['outputs'] = count_files(VAULT_INTELLIGENCE, '*.json')

        return status

    except Exception as e:
        return {
            'system': 'error',
            'error': str(e),
            'total_assets': 0,
            'processed': 0,
            'outputs': 0
        }


@app.get('/api/health')
def health_check():
    """Simple health check endpoint."""
    return {'status': 'ok', 'service': 'sovereign-content-os'}


@app.get('/api/quotes')
def get_quotes():
    """Return the quote bank."""
    quote_bank = VAULT_INTELLIGENCE / 'quote_bank.json'
    if quote_bank.exists():
        return json.loads(quote_bank.read_text())
    return {'quotes': [], 'total_sources': 0}


@app.get('/api/themes')
def get_themes():
    """Return the theme map."""
    theme_map = VAULT_INTELLIGENCE / 'theme_map.json'
    if theme_map.exists():
        return json.loads(theme_map.read_text())
    return {'clusters': [], 'total_themes': 0}


@app.get('/api/vault')
def get_vault():
    """Return the Obsidian vault structure and notes for the IP Vault page."""
    vault_path = OBSIDIAN_VAULT_PATH
    if not vault_path.exists():
        return {'status': 'empty', 'folders': [], 'notes': []}

    folders = []
    notes = []

    for item in sorted(vault_path.iterdir()):
        if item.name.startswith('.') or item.name.startswith('_'):
            continue
        if item.is_dir():
            folder_notes = []
            for note_file in sorted(item.glob('*.md')):
                content = note_file.read_text(encoding='utf-8')
                # Parse frontmatter
                frontmatter = {}
                body = content
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        import yaml
                        try:
                            frontmatter = yaml.safe_load(parts[1]) or {}
                        except Exception:
                            frontmatter = {}
                        body = parts[2].strip()

                note_data = {
                    'id': f"{item.name}/{note_file.stem}",
                    'title': note_file.stem,
                    'folder': item.name,
                    'content': body,
                    'frontmatter': frontmatter,
                    'tags': frontmatter.get('tags', []),
                    'path': str(note_file.relative_to(vault_path))
                }
                folder_notes.append(note_data)
                notes.append(note_data)

            folders.append({
                'name': item.name,
                'count': len(folder_notes),
                'notes': [n['id'] for n in folder_notes]
            })

    return {
        'status': 'live',
        'total_notes': len(notes),
        'folders': folders,
        'notes': notes
    }


if __name__ == '__main__':
    import uvicorn
    from config.settings import STATUS_PORT, STATUS_HOST
    uvicorn.run(app, host=STATUS_HOST, port=STATUS_PORT)
