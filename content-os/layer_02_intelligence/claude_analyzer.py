"""
Sovereign Content OS — Layer 02: Claude Content Analyzer
Sends transcripts to Claude API for deep content analysis.
Extracts predictions, themes, insights, and actionable intelligence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    VAULT_TRANSCRIPTS,
    VAULT_INTELLIGENCE
)

logger = logging.getLogger('content-os.intelligence.claude')

ANALYSIS_PROMPT = """You are the intelligence engine for a sovereign content production system.
Analyze this transcript and extract structured intelligence.

Return a JSON object with these fields:
{
  "summary": "2-3 sentence overview of the content",
  "key_themes": ["theme1", "theme2", ...],
  "predictions": [
    {"claim": "what was predicted", "confidence": "high/medium/low", "timestamp_ref": "approximate time"}
  ],
  "quotable_moments": [
    {"quote": "exact quote", "context": "why it's powerful", "timestamp_ref": "approximate time"}
  ],
  "content_opportunities": [
    {"type": "clip/article/thread/book-chapter", "description": "what could be created", "priority": "high/medium/low"}
  ],
  "audience_hooks": ["hook1", "hook2", ...],
  "sentiment": "overall tone/energy of the content",
  "monetization_angles": ["angle1", "angle2", ...]
}

TRANSCRIPT:
"""


def analyze_transcript(transcript_path: Path):
    """
    Send a transcript to Claude for deep analysis.
    Returns structured intelligence dict.
    """
    transcript_data = json.loads(transcript_path.read_text())
    full_text = transcript_data.get('full_text', '')

    if not full_text:
        logger.warning(f'Empty transcript: {transcript_path.name}')
        return None

    # Truncate if too long (keep under 100k chars for context)
    if len(full_text) > 95000:
        full_text = full_text[:95000] + '\n\n[TRUNCATED]'

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    logger.info(f'Analyzing: {transcript_path.stem} ({len(full_text)} chars)')

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[
            {
                'role': 'user',
                'content': ANALYSIS_PROMPT + full_text
            }
        ]
    )

    # Parse the response
    response_text = message.content[0].text

    # Try to extract JSON from response
    try:
        # Handle case where Claude wraps in markdown code block
        if '```json' in response_text:
            json_str = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            json_str = response_text.split('```')[1].split('```')[0]
        else:
            json_str = response_text

        analysis = json.loads(json_str.strip())
    except json.JSONDecodeError:
        logger.warning('Could not parse Claude response as JSON, saving raw')
        analysis = {'raw_analysis': response_text}

    # Add metadata
    analysis['source_file'] = transcript_data.get('source_file', transcript_path.stem)
    analysis['analyzed_at'] = datetime.now().isoformat()
    analysis['model_used'] = CLAUDE_MODEL
    analysis['transcript_duration'] = transcript_data.get('duration_seconds', 0)

    return analysis


def run_analysis():
    """
    Analyze all transcripts that haven't been analyzed yet.
    Returns count of newly analyzed files.
    """
    logger.info('Starting intelligence analysis...')

    if not ANTHROPIC_API_KEY:
        logger.warning('ANTHROPIC_API_KEY not set, skipping analysis')
        return 0

    count = 0
    for transcript_file in VAULT_TRANSCRIPTS.glob('*.json'):
        analysis_path = VAULT_INTELLIGENCE / f'{transcript_file.stem}_analysis.json'

        if analysis_path.exists():
            continue  # Already analyzed

        try:
            analysis = analyze_transcript(transcript_file)
            if analysis:
                analysis_path.write_text(json.dumps(analysis, indent=2))
                logger.info(f'Analysis saved: {analysis_path.name}')
                count += 1

        except Exception as e:
            logger.error(f'Analysis failed for {transcript_file.name}: {e}')

    logger.info(f'Analysis complete. {count} files processed.')
    return count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    count = run_analysis()
    print(f'Analyzed {count} transcripts')
