"""
Twitter Archive → Obsidian Vault Ingestion

Parses a downloaded Twitter/X data archive and converts it into
structured Obsidian vault notes for the Second Brain system.

What gets ingested:
  - Your tweets → individual notes grouped by month + thread detection
  - Liked tweets → "resonance library" of ideas that caught your attention
  - Note tweets (long-form) → full articles with metadata
  - Profile & account info → identity reference note
  - Bookmarks / saved searches → research trails

What gets SKIPPED (privacy):
  - Direct messages (opt-in only via flag)
  - Ad data, device tokens, IP logs

Usage:
    from layer_04_ingestion.twitter_archive_ingest import TwitterArchiveIngest
    ingest = TwitterArchiveIngest('/path/to/twitter-archive/data')
    stats = ingest.ingest_all()
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from html import unescape

logger = logging.getLogger('content-os.twitter-ingest')

# ── Obsidian vault target ──
OBSIDIAN_VAULT = Path(__file__).parent.parent / 'obsidian_vault'

# ── Twitter vault sub-folders ──
TWITTER_VAULT = OBSIDIAN_VAULT / '10-Twitter-Archive'
TWEETS_DIR = TWITTER_VAULT / 'Tweets'
LIKED_DIR = TWITTER_VAULT / 'Liked'
NOTES_DIR = TWITTER_VAULT / 'Long-Form'
THREADS_DIR = TWITTER_VAULT / 'Threads'

# ── Manifest to track what's been ingested ──
INGEST_MANIFEST = Path(__file__).parent.parent / 'twitter_ingest_manifest.json'

# ── Knowledge taxonomy tags (maps keywords to vault tags) ──
THEME_KEYWORDS = {
    'sovereign': '#sovereignty',
    'ownership': '#ownership',
    'cognition': '#cognition-key',
    'pattern': '#pattern-recognition',
    'ai': '#artificial-intelligence',
    'artificial intelligence': '#artificial-intelligence',
    'blockchain': '#blockchain',
    'crypto': '#crypto',
    'bitcoin': '#bitcoin',
    'wealth': '#wealth-building',
    'generational': '#generational-wealth',
    'invest': '#investing',
    'business': '#business',
    'entrepreneur': '#entrepreneurship',
    'freedom': '#freedom',
    'consciousness': '#consciousness',
    'knowledge': '#knowledge',
    'education': '#education',
    'mental': '#mental-infrastructure',
    'framework': '#frameworks',
    'book': '#book',
    'content': '#content-creation',
    'community': '#community',
    'technology': '#technology',
    'defi': '#defi',
    'nft': '#nft',
    'web3': '#web3',
    'power': '#power-dynamics',
    'history': '#history',
    'media': '#media',
    'money': '#money',
    'real estate': '#real-estate',
    'property': '#real-estate',
    'clubhouse': '#clubhouse',
    'twitter': '#twitter',
    'youtube': '#youtube',
}


def _parse_js_file(filepath: Path) -> list:
    """Parse Twitter archive .js files (window.YTD.xxx.partN = [...])."""
    if not filepath.exists():
        logger.warning(f'File not found: {filepath}')
        return []
    text = filepath.read_text(encoding='utf-8')
    # Strip the "window.YTD.xxx.partN = " prefix to get raw JSON
    idx = text.find('[')
    if idx == -1:
        idx = text.find('{')
    if idx == -1:
        return []
    try:
        return json.loads(text[idx:])
    except json.JSONDecodeError as e:
        logger.error(f'JSON parse error in {filepath.name}: {e}')
        return []


def _clean_source(source_html: str) -> str:
    """Extract clean source name from HTML anchor tag."""
    match = re.search(r'>(.+?)<', source_html)
    return match.group(1) if match else source_html


def _extract_tags(text: str) -> list:
    """Extract relevant knowledge tags from tweet text."""
    tags = set()
    text_lower = text.lower()
    for keyword, tag in THEME_KEYWORDS.items():
        if keyword in text_lower:
            tags.add(tag)
    return sorted(tags)


def _sanitize_filename(text: str, max_len: int = 60) -> str:
    """Create a safe filename from tweet text."""
    # Take first line or first N chars
    clean = text.split('\n')[0].strip()
    clean = re.sub(r'https?://\S+', '', clean).strip()
    clean = re.sub(r'[^\w\s\-]', '', clean).strip()
    clean = re.sub(r'\s+', ' ', clean)
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0]
    return clean or 'tweet'


def _parse_twitter_date(date_str: str) -> datetime:
    """Parse Twitter's date format: 'Tue Mar 17 22:05:32 +0000 2026'."""
    try:
        return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
    except (ValueError, TypeError):
        return datetime.now()


def _parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date from DMs/notes: '2023-02-14T08:16:35.000Z'."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return datetime.now()


class TwitterArchiveIngest:
    """
    Ingests a Twitter/X data archive into the Obsidian vault.

    Creates structured notes organized by type with full metadata,
    cross-links to vault themes, and engagement analytics.
    """

    def __init__(self, archive_data_path: str):
        self.data_path = Path(archive_data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f'Archive data path not found: {archive_data_path}')
        self.manifest = self._load_manifest()
        self.account_id = None
        self.username = None
        self.stats = {
            'tweets_ingested': 0,
            'threads_detected': 0,
            'likes_ingested': 0,
            'notes_ingested': 0,
            'notes_created': 0,
            'tags_applied': 0,
            'skipped_already_ingested': 0,
        }

    def _load_manifest(self) -> dict:
        if INGEST_MANIFEST.exists():
            return json.loads(INGEST_MANIFEST.read_text())
        return {'ingested_tweets': set(), 'ingested_likes': set(),
                'ingested_notes': set(), 'last_run': None}

    def _save_manifest(self):
        # Convert sets to lists for JSON serialization
        saveable = {
            'ingested_tweets': list(self.manifest.get('ingested_tweets', set())),
            'ingested_likes': list(self.manifest.get('ingested_likes', set())),
            'ingested_notes': list(self.manifest.get('ingested_notes', set())),
            'last_run': datetime.now().isoformat(),
        }
        INGEST_MANIFEST.write_text(json.dumps(saveable, indent=2))

    def _ensure_dirs(self):
        """Create vault sub-directories if they don't exist."""
        for d in [TWITTER_VAULT, TWEETS_DIR, LIKED_DIR, NOTES_DIR, THREADS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Account Info ──

    def _load_account(self):
        """Load account metadata (username, ID)."""
        data = _parse_js_file(self.data_path / 'account.js')
        if data:
            acct = data[0].get('account', {})
            self.account_id = acct.get('accountId', '')
            self.username = acct.get('username', '')
            logger.info(f'Account: @{self.username} (ID: {self.account_id})')

    # ── Tweet Ingestion ──

    def _ingest_tweets(self):
        """Parse tweets.js → individual Obsidian notes + thread detection."""
        raw = _parse_js_file(self.data_path / 'tweets.js')
        if not raw:
            logger.warning('No tweets found in archive')
            return

        logger.info(f'Processing {len(raw)} tweets...')

        # Ensure ingested_tweets is a set
        if isinstance(self.manifest.get('ingested_tweets'), list):
            self.manifest['ingested_tweets'] = set(self.manifest['ingested_tweets'])
        elif not isinstance(self.manifest.get('ingested_tweets'), set):
            self.manifest['ingested_tweets'] = set()

        # First pass: organize tweets and detect threads
        tweets = []
        reply_map = defaultdict(list)  # parent_id -> [child tweets]

        for item in raw:
            t = item.get('tweet', {})
            tweet_id = t.get('id_str', '')

            if tweet_id in self.manifest['ingested_tweets']:
                self.stats['skipped_already_ingested'] += 1
                continue

            text = t.get('full_text', '')
            dt = _parse_twitter_date(t.get('created_at', ''))
            source = _clean_source(t.get('source', ''))
            fav_count = int(t.get('favorite_count', 0))
            rt_count = int(t.get('retweet_count', 0))
            reply_to = t.get('in_reply_to_status_id_str', '')
            is_retweet = t.get('retweeted', False) or text.startswith('RT @')

            # Extract hashtags from entities
            hashtags = [h.get('text', '') for h in
                        t.get('entities', {}).get('hashtags', [])]

            # Extract URLs
            urls = [u.get('expanded_url', u.get('url', ''))
                    for u in t.get('entities', {}).get('urls', [])]

            # Extract mentions
            mentions = [m.get('screen_name', '')
                        for m in t.get('entities', {}).get('user_mentions', [])]

            tweet_obj = {
                'id': tweet_id,
                'text': text,
                'date': dt,
                'source': source,
                'fav_count': fav_count,
                'rt_count': rt_count,
                'reply_to': reply_to,
                'is_retweet': is_retweet,
                'hashtags': hashtags,
                'urls': urls,
                'mentions': mentions,
                'engagement': fav_count + rt_count,
            }
            tweets.append(tweet_obj)

            if reply_to and reply_to != '':
                reply_map[reply_to].append(tweet_obj)

        # Detect threads (self-replies)
        threads = defaultdict(list)
        threaded_ids = set()
        for tweet in sorted(tweets, key=lambda x: x['date']):
            if tweet['reply_to'] and tweet['reply_to'] in {t['id'] for t in tweets}:
                # This is a self-reply (part of a thread)
                # Find the root
                root_id = tweet['reply_to']
                # Walk up to find original root
                parent_ids = {t['id']: t.get('reply_to', '') for t in tweets}
                while parent_ids.get(root_id, '') in parent_ids:
                    root_id = parent_ids[root_id]
                threads[root_id].append(tweet)
                threaded_ids.add(tweet['id'])

        # Add root tweets to their threads
        for tweet in tweets:
            if tweet['id'] in threads and tweet['id'] not in threaded_ids:
                threads[tweet['id']].insert(0, tweet)
                threaded_ids.add(tweet['id'])

        # Write thread notes
        for root_id, thread_tweets in threads.items():
            if len(thread_tweets) < 2:
                continue
            self._write_thread(thread_tweets)
            self.stats['threads_detected'] += 1

        # Write individual tweet notes (non-threaded, non-RT, with substance)
        for tweet in tweets:
            if tweet['id'] in threaded_ids:
                continue
            if tweet['is_retweet']:
                continue
            # Skip very short tweets with no engagement
            if len(tweet['text']) < 20 and tweet['engagement'] < 5:
                continue
            self._write_tweet_note(tweet)

    def _write_tweet_note(self, tweet: dict):
        """Write a single tweet as an Obsidian note."""
        dt = tweet['date']
        text = tweet['text']
        tags = _extract_tags(text)
        tags.append('#twitter-archive')

        # Determine engagement tier
        eng = tweet['engagement']
        if eng >= 100:
            tags.append('#high-engagement')
            tier = 'viral'
        elif eng >= 25:
            tags.append('#notable')
            tier = 'notable'
        else:
            tier = 'standard'

        title = _sanitize_filename(text)
        date_str = dt.strftime('%Y-%m-%d')
        month_str = dt.strftime('%Y-%m')

        # Build note
        tag_yaml = '\n'.join(f'  - "{t}"' for t in tags)
        hashtag_str = ', '.join(f'#{h}' for h in tweet['hashtags']) if tweet['hashtags'] else 'none'
        url_str = '\n'.join(f'  - {u}' for u in tweet['urls']) if tweet['urls'] else ''
        mentions_str = ', '.join(f'@{m}' for m in tweet['mentions']) if tweet['mentions'] else 'none'

        note = f"""---
type: tweet
tags:
{tag_yaml}
date: "{date_str}"
tweet_id: "{tweet['id']}"
source: "{tweet['source']}"
engagement_tier: "{tier}"
favorites: {tweet['fav_count']}
retweets: {tweet['rt_count']}
---

# {title}

> {text}

---

| Metric | Value |
|--------|-------|
| Date | {dt.strftime('%B %d, %Y at %I:%M %p')} |
| Likes | {tweet['fav_count']} |
| Retweets | {tweet['rt_count']} |
| Source | {tweet['source']} |
| Hashtags | {hashtag_str} |
| Mentions | {mentions_str} |

"""
        if url_str:
            note += f"""**Links shared:**
{url_str}

"""

        note += f"""---
_Part of [[Twitter Archive — {month_str}]] · [[Twitter Archive MOC]]_
"""

        # Write file
        month_dir = TWEETS_DIR / month_str
        month_dir.mkdir(parents=True, exist_ok=True)
        filepath = month_dir / f'{date_str} — {title}.md'

        # Avoid filename collisions
        counter = 1
        while filepath.exists():
            filepath = month_dir / f'{date_str} — {title} ({counter}).md'
            counter += 1

        filepath.write_text(note, encoding='utf-8')
        self.manifest['ingested_tweets'].add(tweet['id'])
        self.stats['tweets_ingested'] += 1
        self.stats['notes_created'] += 1
        self.stats['tags_applied'] += len(tags)

    def _write_thread(self, thread_tweets: list):
        """Write a thread (self-reply chain) as a single Obsidian note."""
        thread_tweets.sort(key=lambda x: x['date'])
        root = thread_tweets[0]
        dt = root['date']
        date_str = dt.strftime('%Y-%m-%d')

        # Combine text for tag extraction
        full_text = '\n\n'.join(t['text'] for t in thread_tweets)
        tags = _extract_tags(full_text)
        tags.append('#twitter-archive')
        tags.append('#thread')

        total_fav = sum(t['fav_count'] for t in thread_tweets)
        total_rt = sum(t['rt_count'] for t in thread_tweets)
        total_eng = total_fav + total_rt
        if total_eng >= 100:
            tags.append('#high-engagement')

        title = _sanitize_filename(root['text'])
        tag_yaml = '\n'.join(f'  - "{t}"' for t in tags)

        note = f"""---
type: thread
tags:
{tag_yaml}
date: "{date_str}"
thread_length: {len(thread_tweets)}
total_favorites: {total_fav}
total_retweets: {total_rt}
root_tweet_id: "{root['id']}"
---

# Thread: {title}

> **{len(thread_tweets)}-tweet thread** — {dt.strftime('%B %d, %Y')}
> Total engagement: {total_fav} likes, {total_rt} retweets

---

"""
        for i, t in enumerate(thread_tweets, 1):
            note += f"### {i}/{len(thread_tweets)}\n\n"
            note += f"> {t['text']}\n\n"
            note += f"_{t['fav_count']} likes · {t['rt_count']} RT · {t['date'].strftime('%I:%M %p')}_\n\n"

        note += f"""---
_Part of [[Twitter Archive — {dt.strftime('%Y-%m')}]] · [[Twitter Archive MOC]]_
"""

        filepath = THREADS_DIR / f'{date_str} — Thread — {title}.md'
        filepath.write_text(note, encoding='utf-8')

        for t in thread_tweets:
            self.manifest['ingested_tweets'].add(t['id'])
        self.stats['tweets_ingested'] += len(thread_tweets)
        self.stats['notes_created'] += 1

    # ── Liked Tweets ──

    def _ingest_likes(self):
        """Parse like.js → Resonance Library (ideas that caught your eye)."""
        raw = _parse_js_file(self.data_path / 'like.js')
        if not raw:
            return

        logger.info(f'Processing {len(raw)} liked tweets...')

        if isinstance(self.manifest.get('ingested_likes'), list):
            self.manifest['ingested_likes'] = set(self.manifest['ingested_likes'])
        elif not isinstance(self.manifest.get('ingested_likes'), set):
            self.manifest['ingested_likes'] = set()

        # Group likes by month for digestible notes
        monthly_likes = defaultdict(list)
        for item in raw:
            like = item.get('like', {})
            tweet_id = like.get('tweetId', '')
            if tweet_id in self.manifest['ingested_likes']:
                self.stats['skipped_already_ingested'] += 1
                continue

            text = like.get('fullText', '')
            url = like.get('expandedUrl', '')
            if not text:
                continue

            # Estimate date from URL or use current
            monthly_likes['all'].append({
                'id': tweet_id,
                'text': text,
                'url': url,
                'tags': _extract_tags(text),
            })
            self.manifest['ingested_likes'].add(tweet_id)

        # Write resonance library as chunked notes (50 likes per note)
        all_likes = monthly_likes['all']
        chunk_size = 50
        for i in range(0, len(all_likes), chunk_size):
            chunk = all_likes[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (len(all_likes) + chunk_size - 1) // chunk_size

            # Collect all tags from this chunk
            all_tags = set()
            for like in chunk:
                all_tags.update(like['tags'])
            all_tags.add('#twitter-archive')
            all_tags.add('#resonance-library')
            tag_yaml = '\n'.join(f'  - "{t}"' for t in sorted(all_tags))

            note = f"""---
type: liked-tweets
tags:
{tag_yaml}
date: "{datetime.now().strftime('%Y-%m-%d')}"
chunk: {chunk_num}
total_chunks: {total_chunks}
likes_in_chunk: {len(chunk)}
---

# Resonance Library — Part {chunk_num}/{total_chunks}

> Ideas, insights, and moments that resonated enough to save.
> These likes reveal patterns in what captures your attention.

---

"""
            for j, like in enumerate(chunk, 1):
                idx = i + j
                note += f"### {idx}. {_sanitize_filename(like['text'], 50)}\n\n"
                note += f"> {like['text']}\n\n"
                if like['url']:
                    note += f"[Original Tweet]({like['url']})\n\n"
                if like['tags']:
                    note += f"Tags: {' '.join(like['tags'])}\n\n"
                note += "---\n\n"

            note += f"_Part of [[Twitter Archive MOC]] · [[Resonance Library Index]]_\n"

            filepath = LIKED_DIR / f'Resonance Library — Part {chunk_num:03d}.md'
            filepath.write_text(note, encoding='utf-8')
            self.stats['likes_ingested'] += len(chunk)
            self.stats['notes_created'] += 1

    # ── Note Tweets (Long-Form) ──

    def _ingest_note_tweets(self):
        """Parse note-tweet.js → long-form content articles."""
        raw = _parse_js_file(self.data_path / 'note-tweet.js')
        if not raw:
            return

        logger.info(f'Processing {len(raw)} note tweets...')

        if isinstance(self.manifest.get('ingested_notes'), list):
            self.manifest['ingested_notes'] = set(self.manifest['ingested_notes'])
        elif not isinstance(self.manifest.get('ingested_notes'), set):
            self.manifest['ingested_notes'] = set()

        for item in raw:
            nt = item.get('noteTweet', {})
            note_id = nt.get('noteTweetId', '')

            if note_id in self.manifest['ingested_notes']:
                self.stats['skipped_already_ingested'] += 1
                continue

            core = nt.get('core', {})
            text = core.get('text', '')
            if not text or len(text) < 50:
                continue

            dt = _parse_iso_date(nt.get('createdAt', ''))
            date_str = dt.strftime('%Y-%m-%d')
            tags = _extract_tags(text)
            tags.append('#twitter-archive')
            tags.append('#long-form')
            tag_yaml = '\n'.join(f'  - "{t}"' for t in tags)

            title = _sanitize_filename(text, 70)

            note = f"""---
type: note-tweet
tags:
{tag_yaml}
date: "{date_str}"
note_tweet_id: "{note_id}"
word_count: {len(text.split())}
---

# {title}

{text}

---

| Metric | Value |
|--------|-------|
| Written | {dt.strftime('%B %d, %Y')} |
| Word Count | {len(text.split())} |
| Format | X/Twitter Long-Form Note |

---
_Part of [[Twitter Archive MOC]]_
"""

            filepath = NOTES_DIR / f'{date_str} — {title}.md'
            filepath.write_text(note, encoding='utf-8')
            self.manifest['ingested_notes'].add(note_id)
            self.stats['notes_ingested'] += 1
            self.stats['notes_created'] += 1

    # ── MOC (Map of Content) ──

    def _write_moc(self):
        """Generate the Twitter Archive Map of Content index note."""

        # Count files in each dir
        tweet_count = sum(1 for _ in TWEETS_DIR.rglob('*.md'))
        thread_count = sum(1 for _ in THREADS_DIR.rglob('*.md'))
        liked_count = sum(1 for _ in LIKED_DIR.rglob('*.md'))
        notes_count = sum(1 for _ in NOTES_DIR.rglob('*.md'))

        # List month folders
        month_dirs = sorted([d.name for d in TWEETS_DIR.iterdir() if d.is_dir()])
        month_links = '\n'.join(f'  - [[Twitter Archive — {m}]]' for m in month_dirs)

        note = f"""---
type: moc
tags:
  - "#twitter-archive"
  - "#map-of-content"
  - "#second-brain"
date: "{datetime.now().strftime('%Y-%m-%d')}"
---

# Twitter Archive — @{self.username or '19keys_'}

> Complete archive of your Twitter/X presence, ingested into the Second Brain.
> Account created: December 2009 · Account ID: {self.account_id or '95606513'}

---

## Overview

| Section | Notes |
|---------|-------|
| Original Tweets | {tweet_count} |
| Threads | {thread_count} |
| Liked Tweets (Resonance Library) | {liked_count} chunks |
| Long-Form Notes | {notes_count} |

---

## Tweets by Month

{month_links if month_links else '_No monthly archives yet_'}

---

## Key Sections

### Threads
Self-reply chains where you developed ideas in depth.
→ See [[Threads]] folder

### Resonance Library
Tweets you liked reveal patterns in what captures your attention.
These are ideas, insights, and moments from others that resonated.
→ See [[Resonance Library Index]]

### Long-Form Notes
Extended writing published as X Notes/Articles.
→ See [[Long-Form]] folder

---

## Connected Vault Notes

- [[Dashboard]]
- [[Quote Bank]]
- [[Framework Index]]
- [[Prediction Tracker]]

---

## Stats

- Last ingested: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
- Tweets processed: {self.stats['tweets_ingested']}
- Threads detected: {self.stats['threads_detected']}
- Likes catalogued: {self.stats['likes_ingested']}
- Long-form notes: {self.stats['notes_ingested']}
- Total vault notes created: {self.stats['notes_created']}

---
_Generated by Sovereign Content OS — Twitter Archive Ingestion Pipeline_
"""

        filepath = TWITTER_VAULT / 'Twitter Archive MOC.md'
        filepath.write_text(note, encoding='utf-8')
        logger.info('Twitter Archive MOC written')

    def _write_monthly_indexes(self):
        """Generate monthly index notes for tweet navigation."""
        for month_dir in sorted(TWEETS_DIR.iterdir()):
            if not month_dir.is_dir():
                continue
            month = month_dir.name
            notes = sorted(month_dir.glob('*.md'))

            note = f"""---
type: index
tags:
  - "#twitter-archive"
date: "{month}-01"
---

# Twitter Archive — {month}

> {len(notes)} tweets from {month}

---

"""
            for n in notes:
                title = n.stem
                note += f"- [[{title}]]\n"

            note += f"\n---\n_Part of [[Twitter Archive MOC]]_\n"

            filepath = TWEETS_DIR / f'Twitter Archive — {month}.md'
            filepath.write_text(note, encoding='utf-8')

    # ── Main Entry Point ──

    def ingest_all(self) -> dict:
        """Run full Twitter archive ingestion pipeline."""
        logger.info('═══ Twitter Archive Ingestion Starting ═══')

        self._ensure_dirs()
        self._load_account()

        # Phase 1: Your tweets
        logger.info('Phase 1/4: Ingesting tweets...')
        self._ingest_tweets()

        # Phase 2: Liked tweets (resonance library)
        logger.info('Phase 2/4: Ingesting likes (Resonance Library)...')
        self._ingest_likes()

        # Phase 3: Long-form note tweets
        logger.info('Phase 3/4: Ingesting long-form notes...')
        self._ingest_note_tweets()

        # Phase 4: Generate indexes
        logger.info('Phase 4/4: Writing MOC and indexes...')
        self._write_moc()
        self._write_monthly_indexes()

        # Save manifest
        self._save_manifest()

        logger.info(f'═══ Twitter Archive Ingestion Complete ═══')
        logger.info(f'  Tweets: {self.stats["tweets_ingested"]}')
        logger.info(f'  Threads: {self.stats["threads_detected"]}')
        logger.info(f'  Likes: {self.stats["likes_ingested"]}')
        logger.info(f'  Long-form: {self.stats["notes_ingested"]}')
        logger.info(f'  Notes created: {self.stats["notes_created"]}')
        logger.info(f'  Skipped (already ingested): {self.stats["skipped_already_ingested"]}')

        return self.stats


# ── Orchestrator-compatible entry point ──

def run_twitter_archive_ingest(archive_path: str = None) -> dict:
    """
    Entry point for orchestrator integration.
    If no path given, looks for the latest Twitter archive in ~/Downloads.
    """
    if archive_path is None:
        # Auto-detect latest Twitter archive in Downloads
        downloads = Path.home() / 'Downloads'
        archives = sorted(downloads.glob('twitter-*/data'), reverse=True)
        if not archives:
            logger.warning('No Twitter archive found in ~/Downloads')
            return {'status': 'no_archive_found'}
        archive_path = str(archives[0])
        logger.info(f'Auto-detected archive: {archive_path}')

    ingest = TwitterArchiveIngest(archive_path)
    stats = ingest.ingest_all()
    stats['status'] = 'success'
    return stats


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
    result = run_twitter_archive_ingest()
    print(json.dumps(result, indent=2))
