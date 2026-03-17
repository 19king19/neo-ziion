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


@app.get('/api/search')
def search_notes(q: str = '', limit: int = 10, folder: str = ''):
    """Semantic search across the Obsidian vault."""
    if not q:
        return {'results': [], 'query': '', 'error': 'No query provided'}
    try:
        from layer_06_autonomous.semantic_search import search_vault
        results = search_vault(q, limit=limit)
        # Optional folder filter
        if folder:
            results = [r for r in results if folder.lower() in r.get('folder', '').lower()]
        return {'results': results, 'query': q, 'total': len(results)}
    except Exception as e:
        return {'results': [], 'query': q, 'error': str(e)}


@app.get('/api/heartbeat')
def get_heartbeat():
    """Return current heartbeat / system health status."""
    try:
        heartbeat_file = Path(__file__).parent / 'HEARTBEAT.md'
        heartbeat_log = Path(__file__).parent / 'heartbeat_log.json'

        result = {'status': 'unknown'}

        if heartbeat_log.exists():
            log_data = json.loads(heartbeat_log.read_text())
            checks = log_data.get('checks', [])
            if checks:
                result['last_check'] = checks[-1]
            result['total_checks'] = len(checks)
            result['total_restarts'] = len(log_data.get('restarts', []))

        if heartbeat_file.exists():
            result['heartbeat_file'] = heartbeat_file.read_text()[:500]
            result['status'] = 'active'

        return result
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@app.get('/api/twitter')
def get_twitter_stats():
    """Return Twitter/X posting stats."""
    try:
        log_file = Path(__file__).parent / 'twitter_post_log.json'
        if log_file.exists():
            return json.loads(log_file.read_text())
        return {'posts': [], 'total_posted': 0}
    except Exception as e:
        return {'error': str(e)}


@app.get('/api/delegation')
def get_delegation_stats():
    """Return Codex delegation stats."""
    try:
        log_file = Path(__file__).parent / 'delegation_log.json'
        if log_file.exists():
            return json.loads(log_file.read_text())
        return {'total_delegated': 0, 'total_completed': 0}
    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    import uvicorn
    from config.settings import STATUS_PORT, STATUS_HOST
    uvicorn.run(app, host=STATUS_HOST, port=STATUS_PORT)
