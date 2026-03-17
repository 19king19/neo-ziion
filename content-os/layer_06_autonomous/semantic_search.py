"""
QMD Semantic Search — Vector Search Across the Knowledge Vault
Fast semantic search over all Obsidian vault notes using embeddings.

Uses chromadb (lightweight, local vector database) to:
  - Index all vault markdown notes
  - Build embeddings from note content
  - Search by meaning, not just keywords
  - Find related notes across the graph

Integration:
  - OpenClaw calls search() for any knowledge query
  - Status server exposes /api/search endpoint
  - Nightly re-index keeps embeddings fresh

Requirements:
  pip install chromadb sentence-transformers

Usage:
  from layer_06_autonomous.semantic_search import VaultSearchEngine
  engine = VaultSearchEngine()
  engine.build_index()                    # Index all vault notes
  results = engine.search("ownership")    # Semantic search
  related = engine.find_related(note_id)  # Find related notes
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger('content-os.semantic-search')

BASE_DIR = Path(__file__).parent.parent
OBSIDIAN_VAULT = BASE_DIR / 'obsidian_vault'
SEARCH_INDEX_DIR = BASE_DIR / 'search_index'
INDEX_MANIFEST = SEARCH_INDEX_DIR / 'manifest.json'


class VaultSearchEngine:
    """
    Semantic search across the Obsidian knowledge vault.
    Uses chromadb for vector storage and sentence-transformers for embeddings.
    Falls back to keyword search if dependencies aren't available.
    """

    def __init__(self):
        self.collection = None
        self.use_vectors = False
        self.manifest = self._load_manifest()
        self._init_vector_db()

    def _load_manifest(self) -> dict:
        SEARCH_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        if INDEX_MANIFEST.exists():
            return json.loads(INDEX_MANIFEST.read_text())
        return {'last_indexed': None, 'note_count': 0, 'indexed_files': {}}

    def _save_manifest(self):
        self.manifest['last_indexed'] = datetime.now().isoformat()
        INDEX_MANIFEST.write_text(json.dumps(self.manifest, indent=2))

    def _init_vector_db(self):
        """Initialize ChromaDB if available."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl='duckdb+parquet',
                persist_directory=str(SEARCH_INDEX_DIR / 'chroma'),
                anonymized_telemetry=False,
            ))

            self.collection = self.chroma_client.get_or_create_collection(
                name='vault_notes',
                metadata={'description': 'Sovereign Content OS vault notes'}
            )

            self.use_vectors = True
            logger.info(f'ChromaDB initialized ({self.collection.count()} documents indexed)')

        except ImportError:
            logger.info('chromadb not installed — using keyword search fallback')
            logger.info('Install for vector search: pip install chromadb sentence-transformers')
            self.use_vectors = False
        except Exception as e:
            logger.warning(f'ChromaDB init failed: {e} — using keyword fallback')
            self.use_vectors = False

    # ──────────────────────────────────────────────
    # Indexing
    # ──────────────────────────────────────────────

    def _parse_note(self, filepath: Path) -> dict:
        """Parse an Obsidian note into structured data."""
        content = filepath.read_text(encoding='utf-8')

        # Extract frontmatter
        frontmatter = {}
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
                body = parts[2].strip()

        # Extract title (first heading or filename)
        title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        title = title_match.group(1) if title_match else filepath.stem

        # Extract tags
        tags = frontmatter.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        # Extract wiki-links
        links = re.findall(r'\[\[([^\]]+)\]\]', body)

        # Clean content for indexing (strip markdown formatting)
        clean = re.sub(r'#{1,6}\s+', '', body)  # Remove headings
        clean = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', clean)  # Flatten wiki-links
        clean = re.sub(r'[*_`~]', '', clean)  # Remove formatting
        clean = re.sub(r'\n{3,}', '\n\n', clean)  # Collapse whitespace

        relative_path = str(filepath.relative_to(OBSIDIAN_VAULT))
        folder = filepath.parent.name

        return {
            'id': relative_path,
            'title': title,
            'folder': folder,
            'tags': tags,
            'links': links,
            'content': clean[:5000],  # Cap at 5K chars for embedding
            'full_content': body,
            'frontmatter': frontmatter,
            'mtime': filepath.stat().st_mtime,
        }

    def build_index(self, force: bool = False) -> int:
        """Index all vault notes. Returns count of notes indexed."""
        if not OBSIDIAN_VAULT.exists():
            logger.warning(f'Vault not found: {OBSIDIAN_VAULT}')
            return 0

        count = 0
        notes = list(OBSIDIAN_VAULT.rglob('*.md'))

        for note_path in notes:
            note_id = str(note_path.relative_to(OBSIDIAN_VAULT))

            # Skip if already indexed and not modified
            if not force:
                indexed_mtime = self.manifest.get('indexed_files', {}).get(note_id, 0)
                if note_path.stat().st_mtime <= indexed_mtime:
                    continue

            try:
                parsed = self._parse_note(note_path)

                if self.use_vectors and self.collection:
                    # Upsert into ChromaDB
                    metadata = {
                        'title': parsed['title'],
                        'folder': parsed['folder'],
                        'tags': json.dumps(parsed['tags']),
                        'links': json.dumps(parsed['links'][:20]),
                    }
                    self.collection.upsert(
                        ids=[note_id],
                        documents=[parsed['content']],
                        metadatas=[metadata],
                    )

                # Update manifest
                self.manifest.setdefault('indexed_files', {})[note_id] = parsed['mtime']
                count += 1

            except Exception as e:
                logger.error(f'Failed to index {note_id}: {e}')

        self.manifest['note_count'] = len(self.manifest.get('indexed_files', {}))
        self._save_manifest()

        if self.use_vectors and hasattr(self, 'chroma_client'):
            try:
                self.chroma_client.persist()
            except Exception:
                pass

        logger.info(f'Indexed {count} notes ({self.manifest["note_count"]} total)')
        return count

    # ──────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────

    def search(self, query: str, limit: int = 10, folder: str = None) -> list[dict]:
        """
        Semantic search across the vault.
        Returns list of matching notes with relevance scores.
        """
        if self.use_vectors and self.collection and self.collection.count() > 0:
            return self._vector_search(query, limit, folder)
        else:
            return self._keyword_search(query, limit, folder)

    def _vector_search(self, query: str, limit: int, folder: str = None) -> list[dict]:
        """Search using ChromaDB vector similarity."""
        try:
            where = None
            if folder:
                where = {'folder': folder}

            results = self.collection.query(
                query_texts=[query],
                n_results=min(limit, self.collection.count()),
                where=where,
            )

            matches = []
            if results and results.get('ids') and results['ids'][0]:
                for i, note_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    document = results['documents'][0][i] if results.get('documents') else ''

                    matches.append({
                        'id': note_id,
                        'title': metadata.get('title', note_id),
                        'folder': metadata.get('folder', ''),
                        'relevance': round(1 - (distance / 2), 3),  # Normalize to 0-1
                        'snippet': document[:200] + '...' if len(document) > 200 else document,
                        'tags': json.loads(metadata.get('tags', '[]')),
                    })

            return matches

        except Exception as e:
            logger.error(f'Vector search failed: {e}')
            return self._keyword_search(query, limit, folder)

    def _keyword_search(self, query: str, limit: int, folder: str = None) -> list[dict]:
        """Fallback keyword search when vector DB isn't available."""
        if not OBSIDIAN_VAULT.exists():
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())
        matches = []

        for note_path in OBSIDIAN_VAULT.rglob('*.md'):
            if folder and note_path.parent.name != folder:
                continue

            try:
                content = note_path.read_text(encoding='utf-8').lower()

                # Score based on word matches
                score = 0
                for word in query_words:
                    count = content.count(word)
                    if count > 0:
                        score += count

                    # Bonus for title match
                    if word in note_path.stem.lower():
                        score += 10

                if score > 0:
                    # Extract snippet around first match
                    snippet = ''
                    for word in query_words:
                        idx = content.find(word)
                        if idx >= 0:
                            start = max(0, idx - 50)
                            end = min(len(content), idx + 150)
                            snippet = content[start:end].strip()
                            break

                    matches.append({
                        'id': str(note_path.relative_to(OBSIDIAN_VAULT)),
                        'title': note_path.stem,
                        'folder': note_path.parent.name,
                        'relevance': min(1.0, score / 20),  # Normalize
                        'snippet': snippet[:200],
                        'tags': [],
                    })

            except Exception:
                continue

        # Sort by relevance
        matches.sort(key=lambda x: x['relevance'], reverse=True)
        return matches[:limit]

    def find_related(self, note_id: str, limit: int = 5) -> list[dict]:
        """Find notes related to a given note."""
        note_path = OBSIDIAN_VAULT / note_id
        if not note_path.exists():
            return []

        try:
            parsed = self._parse_note(note_path)
            # Search using note's content
            query = f'{parsed["title"]} {" ".join(parsed["tags"][:5])}'
            results = self.search(query, limit + 1)
            # Exclude the source note
            return [r for r in results if r['id'] != note_id][:limit]
        except Exception as e:
            logger.error(f'find_related failed: {e}')
            return []

    # ──────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return search engine statistics."""
        return {
            'engine': 'chromadb' if self.use_vectors else 'keyword',
            'indexed_notes': self.manifest.get('note_count', 0),
            'last_indexed': self.manifest.get('last_indexed'),
            'vector_count': self.collection.count() if self.collection else 0,
        }


def build_search_index() -> int:
    """Convenience function for orchestrator."""
    engine = VaultSearchEngine()
    return engine.build_index()


def search_vault(query: str, limit: int = 10) -> list[dict]:
    """Convenience function for API/OpenClaw."""
    engine = VaultSearchEngine()
    return engine.search(query, limit)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    engine = VaultSearchEngine()

    if '--index' in sys.argv:
        count = engine.build_index(force=True)
        print(f'Indexed {count} notes')
    elif '--search' in sys.argv and len(sys.argv) > 2:
        query = ' '.join(sys.argv[sys.argv.index('--search') + 1:])
        results = engine.search(query)
        for r in results:
            print(f'  [{r["relevance"]:.2f}] {r["title"]} ({r["folder"]})')
            print(f'         {r["snippet"][:100]}')
    else:
        print(json.dumps(engine.get_stats(), indent=2))

import sys
