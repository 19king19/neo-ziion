"""
Sovereign Content OS — Layer 01: Whisper Transcription
Watches vault/raw for new audio/video files and transcribes them.
Saves transcripts to vault/transcripts/ as JSON with timestamps.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import VAULT_RAW, VAULT_TRANSCRIPTS, WHISPER_MODEL

logger = logging.getLogger('content-os.ingestion.whisper')

# Audio/video extensions to transcribe
TRANSCRIBABLE = {'.mp4', '.mov', '.avi', '.mp3', '.wav', '.m4a', '.webm', '.mkv'}


def get_pending_files():
    """Find files in vault/raw that haven't been transcribed yet."""
    pending = []
    for f in VAULT_RAW.iterdir():
        if f.suffix.lower() in TRANSCRIBABLE:
            transcript_path = VAULT_TRANSCRIPTS / f'{f.stem}.json'
            if not transcript_path.exists():
                pending.append(f)
    return pending


def transcribe_file(file_path: Path):
    """
    Transcribe a single audio/video file using Whisper.
    Returns transcript dict with segments.
    """
    import whisper

    logger.info(f'Transcribing: {file_path.name} (model: {WHISPER_MODEL})')

    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(
        str(file_path),
        language='en',
        verbose=False
    )

    transcript = {
        'source_file': file_path.name,
        'source_path': str(file_path),
        'model': WHISPER_MODEL,
        'language': result.get('language', 'en'),
        'full_text': result['text'],
        'segments': [
            {
                'id': seg['id'],
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            }
            for seg in result.get('segments', [])
        ],
        'transcribed_at': datetime.now().isoformat(),
        'duration_seconds': result['segments'][-1]['end'] if result.get('segments') else 0
    }

    return transcript


def run_transcription():
    """
    Process all pending files.
    Returns count of newly transcribed files.
    """
    pending = get_pending_files()

    if not pending:
        logger.info('No new files to transcribe')
        return 0

    logger.info(f'Found {len(pending)} files to transcribe')
    count = 0

    for file_path in pending:
        try:
            transcript = transcribe_file(file_path)

            # Save transcript
            output_path = VAULT_TRANSCRIPTS / f'{file_path.stem}.json'
            output_path.write_text(json.dumps(transcript, indent=2))

            logger.info(f'Saved transcript: {output_path.name}')
            count += 1

        except Exception as e:
            logger.error(f'Failed to transcribe {file_path.name}: {e}')

    logger.info(f'Transcription complete. {count} files processed.')
    return count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    count = run_transcription()
    print(f'Transcribed {count} files')
