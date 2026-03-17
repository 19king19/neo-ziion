"""
Brain Ingest — Knowledge Ingestion Pipeline
Feeds documents, transcripts, and extracted content into the Obsidian vault
as properly formatted, linked, and tagged markdown notes.

This is Gap 3: the pipeline that transforms raw content into graph-ready knowledge.

Usage:
    from layer_04_ingestion.brain_ingest import BrainIngest
    ingest = BrainIngest()
    ingest.ingest_all()
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import (
    VAULT_TRANSCRIPTS,
    VAULT_INTELLIGENCE,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
)

logger = logging.getLogger('content-os.brain-ingest')

# ── Obsidian vault path ──
OBSIDIAN_VAULT = Path(__file__).parent.parent / 'obsidian_vault'

# ── Ingestion manifest (tracks what's been ingested) ──
INGEST_MANIFEST = Path(__file__).parent.parent / 'ingest_manifest.json'

# ── Source libraries ──
IP_EBOOK_VAULT = Path.home() / 'Documents' / 'IP-Ebook-Vault'


class BrainIngest:
    """
    Ingestion pipeline that converts raw content into Obsidian vault notes.

    Sources:
      1. Content OS transcripts (vault/transcripts/*.json)
      2. Content OS intelligence outputs (vault/intelligence/*.json)
      3. IP-Ebook-Vault documents (~/Documents/IP-Ebook-Vault/)
      4. Manual drops (any .md, .txt, .json placed in vault/raw/)

    Output:
      - Formatted Obsidian notes with YAML frontmatter
      - Wiki-links between related concepts
      - Tags from the knowledge taxonomy
      - Backlinks to source material
    """

    def __init__(self):
        self.manifest = self._load_manifest()
        self.stats = {
            'transcripts_ingested': 0,
            'intelligence_ingested': 0,
            'documents_ingested': 0,
            'notes_created': 0,
            'links_created': 0,
        }

    def _load_manifest(self) -> dict:
        """Load the ingestion manifest (tracks already-processed files)."""
        if INGEST_MANIFEST.exists():
            return json.loads(INGEST_MANIFEST.read_text())
        return {'ingested_files': {}, 'last_run': None}

    def _save_manifest(self):
        """Save the ingestion manifest."""
        self.manifest['last_run'] = datetime.now().isoformat()
        INGEST_MANIFEST.write_text(json.dumps(self.manifest, indent=2))

    def _is_ingested(self, file_path: Path) -> bool:
        """Check if a file has already been ingested."""
        key = str(file_path)
        if key not in self.manifest['ingested_files']:
            return False
        # Re-ingest if file was modified since last ingestion
        recorded_mtime = self.manifest['ingested_files'][key].get('mtime', 0)
        current_mtime = file_path.stat().st_mtime
        return current_mtime <= recorded_mtime

    def _mark_ingested(self, file_path: Path, note_path: str):
        """Mark a file as ingested in the manifest."""
        self.manifest['ingested_files'][str(file_path)] = {
            'mtime': file_path.stat().st_mtime,
            'ingested_at': datetime.now().isoformat(),
            'output_note': note_path,
        }

    def _slugify(self, text: str) -> str:
        """Convert text to a clean filename."""
        slug = re.sub(r'[^\w\s-]', '', text)
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        return slug[:80]

    def _write_note(self, folder: str, title: str, content: str, frontmatter: dict) -> str:
        """Write a note to the Obsidian vault."""
        vault_folder = OBSIDIAN_VAULT / folder
        vault_folder.mkdir(parents=True, exist_ok=True)

        # Build YAML frontmatter
        fm_lines = ['---']
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f'{key}: [{", ".join(str(v) for v in value)}]')
            elif isinstance(value, dict):
                fm_lines.append(f'{key}:')
                for k, v in value.items():
                    fm_lines.append(f'  {k}: {v}')
            else:
                fm_lines.append(f'{key}: {value}')
        fm_lines.append('---')
        fm_lines.append('')

        full_content = '\n'.join(fm_lines) + content

        note_path = vault_folder / f'{title}.md'
        note_path.write_text(full_content, encoding='utf-8')

        self.stats['notes_created'] += 1
        return str(note_path.relative_to(OBSIDIAN_VAULT))

    # ──────────────────────────────────────────────
    # Source 1: Content OS Transcripts
    # ──────────────────────────────────────────────

    def ingest_transcripts(self) -> int:
        """Ingest Whisper transcripts into the vault as Raw Notes."""
        count = 0
        if not VAULT_TRANSCRIPTS.exists():
            return count

        for transcript_file in VAULT_TRANSCRIPTS.glob('*.json'):
            if self._is_ingested(transcript_file):
                continue

            try:
                data = json.loads(transcript_file.read_text())
                title = data.get('title', transcript_file.stem)
                text = data.get('text', data.get('transcript', ''))
                source = data.get('source_file', transcript_file.stem)
                duration = data.get('duration', 'unknown')

                if not text:
                    continue

                # Truncate very long transcripts for the note (full text in source)
                preview = text[:3000] + ('...\n\n> Full transcript available in source file.' if len(text) > 3000 else '')

                note_content = f"""# {title}

> Transcript ingested from Content OS pipeline

## Source
- **File**: {source}
- **Duration**: {duration}
- **Transcribed**: {datetime.now().strftime('%Y-%m-%d')}

## Transcript

{preview}

## Extracted Intelligence

_Run Claude analysis to extract predictions, quotes, and frameworks from this transcript._

See: [[Dashboard]] | [[Prediction Tracker]] | [[Quote Bank]]
"""
                note_title = self._slugify(title) or transcript_file.stem
                note_path = self._write_note('08-Raw-Notes', note_title, note_content, {
                    'tags': ['transcript', 'raw', 'ingested'],
                    'created': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'transcript',
                    'source': source,
                    'status': 'needs-analysis',
                })

                self._mark_ingested(transcript_file, note_path)
                count += 1

            except Exception as e:
                logger.error(f'Failed to ingest transcript {transcript_file}: {e}')

        self.stats['transcripts_ingested'] = count
        return count

    # ──────────────────────────────────────────────
    # Source 2: Intelligence Outputs
    # ──────────────────────────────────────────────

    def ingest_intelligence(self) -> int:
        """Ingest Claude analysis outputs into categorized vault notes."""
        count = 0
        if not VAULT_INTELLIGENCE.exists():
            return count

        for intel_file in VAULT_INTELLIGENCE.glob('*.json'):
            if intel_file.name in ('quote_bank.json', 'theme_map.json'):
                continue  # These are aggregates, handled separately
            if self._is_ingested(intel_file):
                continue

            try:
                data = json.loads(intel_file.read_text())
                count += self._ingest_analysis(intel_file, data)
            except Exception as e:
                logger.error(f'Failed to ingest intelligence {intel_file}: {e}')

        # Ingest the quote bank
        quote_bank = VAULT_INTELLIGENCE / 'quote_bank.json'
        if quote_bank.exists() and not self._is_ingested(quote_bank):
            count += self._ingest_quote_bank(quote_bank)

        # Ingest the theme map
        theme_map = VAULT_INTELLIGENCE / 'theme_map.json'
        if theme_map.exists() and not self._is_ingested(theme_map):
            count += self._ingest_theme_map(theme_map)

        self.stats['intelligence_ingested'] = count
        return count

    def _ingest_analysis(self, file_path: Path, data: dict) -> int:
        """Ingest a single Claude analysis output."""
        count = 0
        source_title = data.get('source', file_path.stem)
        analysis = data.get('analysis', data)

        # Extract predictions
        predictions = analysis.get('predictions', [])
        for pred in predictions:
            claim = pred.get('claim', pred.get('prediction', ''))
            if not claim:
                continue
            timeline = pred.get('timeline', 'unspecified')
            confidence = pred.get('confidence', 'medium')

            note_content = f"""# {claim[:80]}

> Prediction extracted by Content OS Intelligence Engine

## Claim
{claim}

## Details
- **Timeline**: {timeline}
- **Confidence**: {confidence}
- **Source**: {source_title}
- **Extracted**: {datetime.now().strftime('%Y-%m-%d')}

## Verification Status
🟡 PENDING — Not yet verifiable

## Connected Themes
{self._link_themes(pred.get('themes', []))}

[[Prediction Tracker]] | [[Dashboard]]
"""
            title = self._slugify(claim[:60]) or f'prediction-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            note_path = self._write_note('01-Predictions', title, note_content, {
                'tags': ['prediction', f'confidence-{confidence}'],
                'created': datetime.now().strftime('%Y-%m-%d'),
                'type': 'prediction',
                'source': source_title,
                'status': 'pending',
                'timeline': timeline,
            })
            self._mark_ingested(file_path, note_path)
            count += 1

        # Extract frameworks
        frameworks = analysis.get('frameworks', [])
        for fw in frameworks:
            name = fw.get('name', fw.get('framework', ''))
            if not name:
                continue
            description = fw.get('description', '')
            steps = fw.get('steps', [])

            steps_md = ''
            if steps:
                steps_md = '\n## Steps\n' + '\n'.join(f'{i+1}. {s}' for i, s in enumerate(steps))

            note_content = f"""# {name}

> Framework extracted by Content OS Intelligence Engine

## Description
{description}
{steps_md}

## Source
- **From**: {source_title}
- **Extracted**: {datetime.now().strftime('%Y-%m-%d')}

## Connected Concepts
{self._link_themes(fw.get('themes', []))}

[[Framework Index]] | [[Dashboard]]
"""
            title = self._slugify(name)
            note_path = self._write_note('02-Frameworks', title, note_content, {
                'tags': ['framework', 'extracted'],
                'created': datetime.now().strftime('%Y-%m-%d'),
                'type': 'framework',
                'source': source_title,
            })
            count += 1

        return count

    def _ingest_quote_bank(self, file_path: Path) -> int:
        """Ingest the aggregate quote bank into individual quote notes."""
        count = 0
        data = json.loads(file_path.read_text())
        quotes = data.get('quotes', [])

        for quote in quotes:
            text = quote.get('text', quote.get('quote', ''))
            if not text or len(text) < 10:
                continue

            source = quote.get('source', 'unknown')
            theme = quote.get('theme', 'general')
            score = quote.get('score', quote.get('quotability', 5))

            note_content = f"""# "{text[:60]}..."

> Quote captured by Content OS Intelligence Engine

## Full Quote
> "{text}"

## Metadata
- **Source**: {source}
- **Theme**: {theme}
- **Quotability Score**: {score}/10
- **Captured**: {datetime.now().strftime('%Y-%m-%d')}

## Usage Suggestions
- Social media post
- Book inclusion (see [[Book Outline — Cognition Key]])
- Merch / visual content

[[Quote Bank]] | [[Dashboard]]
"""
            title = self._slugify(text[:50]) or f'quote-{count}'
            self._write_note('03-Quotes', title, note_content, {
                'tags': ['quote', theme],
                'created': datetime.now().strftime('%Y-%m-%d'),
                'type': 'quote',
                'source': source,
                'score': score,
            })
            count += 1

        self._mark_ingested(file_path, '03-Quotes/')
        return count

    def _ingest_theme_map(self, file_path: Path) -> int:
        """Ingest the theme map into individual theme notes."""
        count = 0
        data = json.loads(file_path.read_text())
        clusters = data.get('clusters', [])

        for cluster in clusters:
            theme_name = cluster.get('theme', cluster.get('name', ''))
            if not theme_name:
                continue

            keywords = cluster.get('keywords', [])
            sources = cluster.get('sources', [])
            description = cluster.get('description', '')

            keywords_md = ', '.join(f'`{k}`' for k in keywords) if keywords else '_none identified_'
            sources_md = '\n'.join(f'- {s}' for s in sources) if sources else '_none linked_'

            note_content = f"""# {theme_name}

> Theme cluster identified by Content OS Intelligence Engine

## Description
{description}

## Keywords
{keywords_md}

## Source Content
{sources_md}

## Related Predictions
_Auto-linked when predictions share this theme_

## Related Quotes
_Auto-linked when quotes share this theme_

## Related Frameworks
_Auto-linked when frameworks share this theme_

[[Dashboard]] | [[Quote Bank]] | [[Prediction Tracker]]
"""
            title = self._slugify(theme_name)
            self._write_note('04-Themes', title, note_content, {
                'tags': ['theme', 'cluster'],
                'created': datetime.now().strftime('%Y-%m-%d'),
                'type': 'theme',
                'keywords': keywords,
            })
            count += 1

        self._mark_ingested(file_path, '04-Themes/')
        return count

    # ──────────────────────────────────────────────
    # Source 3: IP-Ebook-Vault Documents
    # ──────────────────────────────────────────────

    def ingest_documents(self) -> int:
        """Ingest documents from the IP-Ebook-Vault into Raw Notes."""
        count = 0
        if not IP_EBOOK_VAULT.exists():
            logger.info(f'IP-Ebook-Vault not found at {IP_EBOOK_VAULT}')
            return count

        # Ingest markdown files
        for md_file in IP_EBOOK_VAULT.rglob('*.md'):
            if self._is_ingested(md_file):
                continue
            if md_file.name.startswith('.'):
                continue

            try:
                content = md_file.read_text(encoding='utf-8')
                relative = md_file.relative_to(IP_EBOOK_VAULT)
                folder = relative.parent.name or 'IP-Ebook-Vault'

                note_content = f"""# {md_file.stem}

> Ingested from IP-Ebook-Vault / {folder}

## Source
- **File**: {relative}
- **Ingested**: {datetime.now().strftime('%Y-%m-%d')}

## Content

{content[:5000]}{'...\n\n> Full content available in source file.' if len(content) > 5000 else ''}

## Analysis Status
_Awaiting Claude analysis for extraction of predictions, quotes, and frameworks_

[[Dashboard]]
"""
                title = self._slugify(md_file.stem)
                note_path = self._write_note('08-Raw-Notes', title, note_content, {
                    'tags': ['document', 'ip-vault', 'ingested'],
                    'created': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'document',
                    'source': str(relative),
                    'status': 'needs-analysis',
                })
                self._mark_ingested(md_file, note_path)
                count += 1

            except Exception as e:
                logger.error(f'Failed to ingest document {md_file}: {e}')

        # Ingest extracted text files
        for txt_file in IP_EBOOK_VAULT.rglob('*.txt'):
            if self._is_ingested(txt_file):
                continue
            if txt_file.name.startswith('.'):
                continue

            try:
                content = txt_file.read_text(encoding='utf-8', errors='replace')
                relative = txt_file.relative_to(IP_EBOOK_VAULT)

                note_content = f"""# {txt_file.stem}

> Ingested from IP-Ebook-Vault

## Source
- **File**: {relative}
- **Ingested**: {datetime.now().strftime('%Y-%m-%d')}

## Content

{content[:5000]}{'...\n\n> Full content available in source file.' if len(content) > 5000 else ''}

[[Dashboard]]
"""
                title = self._slugify(txt_file.stem)
                note_path = self._write_note('08-Raw-Notes', title, note_content, {
                    'tags': ['document', 'extracted-text', 'ingested'],
                    'created': datetime.now().strftime('%Y-%m-%d'),
                    'type': 'extracted-text',
                    'source': str(relative),
                    'status': 'needs-analysis',
                })
                self._mark_ingested(txt_file, note_path)
                count += 1

            except Exception as e:
                logger.error(f'Failed to ingest text file {txt_file}: {e}')

        self.stats['documents_ingested'] = count
        return count

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _link_themes(self, themes: list) -> str:
        """Convert theme list to wiki-links."""
        if not themes:
            return '_No themes identified_'
        return '\n'.join(f'- [[{theme}]]' for theme in themes)

    # ──────────────────────────────────────────────
    # Main Entry Point
    # ──────────────────────────────────────────────

    def ingest_all(self) -> dict:
        """Run the full ingestion pipeline."""
        logger.info('═══ Brain Ingest: Starting full ingestion ═══')

        # Source 1: Transcripts
        logger.info('Ingesting transcripts...')
        t_count = self.ingest_transcripts()
        logger.info(f'  → {t_count} transcripts ingested')

        # Source 2: Intelligence outputs
        logger.info('Ingesting intelligence outputs...')
        i_count = self.ingest_intelligence()
        logger.info(f'  → {i_count} intelligence items ingested')

        # Source 3: IP-Ebook-Vault documents
        logger.info('Ingesting documents from IP-Ebook-Vault...')
        d_count = self.ingest_documents()
        logger.info(f'  → {d_count} documents ingested')

        # Save manifest
        self._save_manifest()

        logger.info(f'═══ Brain Ingest Complete: {self.stats["notes_created"]} notes created ═══')
        return self.stats


def run_ingestion() -> dict:
    """Convenience function for the orchestrator."""
    ingest = BrainIngest()
    return ingest.ingest_all()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    stats = run_ingestion()
    print(json.dumps(stats, indent=2))
