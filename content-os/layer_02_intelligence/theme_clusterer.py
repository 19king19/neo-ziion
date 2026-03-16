"""
Sovereign Content OS — Layer 02: Theme Clusterer
Groups content by recurring themes and topics.
Creates a theme map showing content connections.
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import VAULT_INTELLIGENCE

logger = logging.getLogger('content-os.intelligence.themes')

THEME_MAP_PATH = VAULT_INTELLIGENCE / 'theme_map.json'


def cluster_themes():
    """
    Scan all analysis files, aggregate themes, and build a theme map.
    Returns the theme map dict.
    """
    logger.info('Clustering themes across all content...')

    theme_counter = Counter()
    theme_content = {}  # theme -> list of source files
    all_analyses = []

    for analysis_file in VAULT_INTELLIGENCE.glob('*_analysis.json'):
        try:
            analysis = json.loads(analysis_file.read_text())
            all_analyses.append(analysis)

            themes = analysis.get('key_themes', [])
            source = analysis.get('source_file', analysis_file.stem)

            for theme in themes:
                theme_lower = theme.lower().strip()
                theme_counter[theme_lower] += 1
                if theme_lower not in theme_content:
                    theme_content[theme_lower] = []
                theme_content[theme_lower].append({
                    'source': source,
                    'summary': analysis.get('summary', '')[:100]
                })

        except Exception as e:
            logger.error(f'Failed to process {analysis_file.name}: {e}')

    # Build theme clusters (sorted by frequency)
    clusters = []
    for theme, count in theme_counter.most_common():
        clusters.append({
            'theme': theme,
            'frequency': count,
            'content_pieces': theme_content.get(theme, []),
            'strength': 'dominant' if count >= 5 else 'recurring' if count >= 3 else 'emerging'
        })

    theme_map = {
        'clusters': clusters,
        'total_themes': len(clusters),
        'total_content_analyzed': len(all_analyses),
        'dominant_themes': [c['theme'] for c in clusters if c['strength'] == 'dominant'],
        'generated_at': datetime.now().isoformat()
    }

    THEME_MAP_PATH.write_text(json.dumps(theme_map, indent=2))
    logger.info(f'Theme clustering complete. {len(clusters)} themes found.')

    return theme_map


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    result = cluster_themes()
    print(f"Found {result['total_themes']} themes across {result['total_content_analyzed']} pieces")
    if result['dominant_themes']:
        print(f"Dominant themes: {', '.join(result['dominant_themes'])}")
