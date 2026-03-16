"""
Sovereign Content OS — Layer 02: Quote Extractor
Extracts powerful, quotable moments from analyzed content.
Builds a quote bank for social media, books, and products.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import VAULT_INTELLIGENCE

logger = logging.getLogger('content-os.intelligence.quotes')

QUOTE_BANK_PATH = VAULT_INTELLIGENCE / 'quote_bank.json'


def load_quote_bank():
    """Load existing quote bank."""
    if QUOTE_BANK_PATH.exists():
        return json.loads(QUOTE_BANK_PATH.read_text())
    return {'quotes': [], 'last_updated': None, 'total_sources': 0}


def save_quote_bank(bank):
    """Save quote bank."""
    bank['last_updated'] = datetime.now().isoformat()
    QUOTE_BANK_PATH.write_text(json.dumps(bank, indent=2))


def extract_quotes():
    """
    Scan all analysis files and compile quotes into a central bank.
    Deduplicates by quote text.
    """
    logger.info('Extracting quotes from analyses...')

    bank = load_quote_bank()
    existing_quotes = {q['quote'] for q in bank['quotes']}
    new_count = 0
    sources_scanned = 0

    for analysis_file in VAULT_INTELLIGENCE.glob('*_analysis.json'):
        sources_scanned += 1
        try:
            analysis = json.loads(analysis_file.read_text())
            quotable_moments = analysis.get('quotable_moments', [])

            for moment in quotable_moments:
                quote_text = moment.get('quote', '').strip()
                if not quote_text or quote_text in existing_quotes:
                    continue

                bank['quotes'].append({
                    'quote': quote_text,
                    'context': moment.get('context', ''),
                    'timestamp_ref': moment.get('timestamp_ref', ''),
                    'source': analysis.get('source_file', analysis_file.stem),
                    'extracted_at': datetime.now().isoformat(),
                    'used_count': 0,
                    'platforms_posted': []
                })
                existing_quotes.add(quote_text)
                new_count += 1

        except Exception as e:
            logger.error(f'Failed to process {analysis_file.name}: {e}')

    bank['total_sources'] = sources_scanned
    save_quote_bank(bank)

    logger.info(f'Quote extraction complete. {new_count} new quotes. Total: {len(bank["quotes"])}')
    return new_count


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    count = extract_quotes()
    print(f'Extracted {count} new quotes')
