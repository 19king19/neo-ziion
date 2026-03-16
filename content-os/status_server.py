"""
Sovereign Content OS — Status API Server
FastAPI server on port 8819 that serves pipeline status to the ZIION UI.
Runs as part of the orchestrator daemon.
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import STATUS_FILE, VAULT_RAW, VAULT_TRANSCRIPTS, VAULT_INTELLIGENCE

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


if __name__ == '__main__':
    import uvicorn
    from config.settings import STATUS_PORT, STATUS_HOST
    uvicorn.run(app, host=STATUS_HOST, port=STATUS_PORT)
