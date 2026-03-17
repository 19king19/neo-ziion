"""
Twitter/X Autonomous Posting Agent
Composes, schedules, and posts content to X from the knowledge vault.

Content Sources:
  - Quote Bank (vault/intelligence/quote_bank.json)
  - Predictions (vault/intelligence/*.json)
  - Themes (vault/intelligence/theme_map.json)
  - Daily Briefs (obsidian_vault/09-Daily-Briefs/)
  - Claude-generated threads from transcripts

Engagement Rules:
  - Max 3 posts per day (configurable)
  - No posting between 11 PM - 7 AM
  - Quote posts get hashtags from theme clusters
  - Prediction posts tagged with timeline
  - Thread posts max 5 tweets
  - All posts logged to vault for tracking

Requirements:
  pip install tweepy
  Set in .env: TWITTER_API_KEY, TWITTER_API_SECRET,
               TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET,
               TWITTER_BEARER_TOKEN

Usage:
  from layer_05_distribution.twitter_agent import TwitterAgent
  agent = TwitterAgent()
  agent.post_quote()          # Post a quote from the bank
  agent.post_prediction()     # Post a prediction
  agent.compose_thread(topic) # Generate and post a thread
  agent.run_daily_schedule()  # Run the full daily posting schedule
"""

import json
import logging
import os
import random
import re
from datetime import datetime, time
from pathlib import Path
from typing import Optional

logger = logging.getLogger('content-os.twitter')

BASE_DIR = Path(__file__).parent.parent
VAULT_INTELLIGENCE = BASE_DIR / 'vault' / 'intelligence'
OBSIDIAN_VAULT = BASE_DIR / 'obsidian_vault'
TWITTER_LOG = BASE_DIR / 'twitter_post_log.json'

# ── Engagement Rules ──
RULES = {
    'max_posts_per_day': 3,
    'quiet_hours_start': 23,  # 11 PM
    'quiet_hours_end': 7,     # 7 AM
    'max_thread_tweets': 5,
    'min_hours_between_posts': 3,
    'hashtag_limit': 3,
    'preferred_post_times': ['09:00', '13:00', '18:00'],  # EST
    'content_mix': {
        'quote': 0.4,       # 40% quotes
        'prediction': 0.2,  # 20% predictions
        'thread': 0.2,      # 20% threads
        'insight': 0.2,     # 20% insights/frameworks
    },
}

# ── Brand Voice Templates ──
TEMPLATES = {
    'quote_intro': [
        '',  # No intro, just the quote
        '💎',
        'Pattern recognized:',
        'Think about this:',
        'This is the key:',
        'Sovereignty starts here:',
    ],
    'prediction_intro': [
        '🔮 Prediction:',
        'Watch this space:',
        'Mark this:',
        'The pattern says:',
    ],
    'thread_hook': [
        'Thread: {topic} 🧵',
        'Let me break this down. {topic} 🧵',
        "Here's what most people don't understand about {topic} 🧵",
        'The {topic} pattern nobody is talking about 🧵',
    ],
    'cta': [
        '\n\nFollow for more pattern recognition.',
        '\n\nSovereignty is a decision.',
        '\n\nOwn your mind. Own your future.',
        '',  # No CTA
    ],
}


class TwitterAgent:
    """Autonomous Twitter/X posting agent for 19 Keys."""

    def __init__(self):
        self.client = None
        self.api = None
        self.post_log = self._load_log()
        self._init_client()

    def _init_client(self):
        """Initialize Twitter API client."""
        try:
            import tweepy
        except ImportError:
            logger.warning('tweepy not installed. Run: pip install tweepy')
            return

        api_key = os.getenv('TWITTER_API_KEY', '')
        api_secret = os.getenv('TWITTER_API_SECRET', '')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN', '')
        access_secret = os.getenv('TWITTER_ACCESS_SECRET', '')
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')

        if not all([api_key, api_secret, access_token, access_secret]):
            logger.warning('Twitter API credentials not configured in .env')
            return

        try:
            # v2 client for tweeting
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret,
            )
            logger.info('Twitter client initialized')
        except Exception as e:
            logger.error(f'Twitter client init failed: {e}')

    def _load_log(self) -> dict:
        if TWITTER_LOG.exists():
            return json.loads(TWITTER_LOG.read_text())
        return {'posts': [], 'daily_counts': {}, 'total_posted': 0}

    def _save_log(self):
        TWITTER_LOG.write_text(json.dumps(self.post_log, indent=2))

    # ──────────────────────────────────────────────
    # Guard Rails
    # ──────────────────────────────────────────────

    def _can_post(self) -> tuple[bool, str]:
        """Check if posting is allowed right now."""
        now = datetime.now()

        # Quiet hours
        if RULES['quiet_hours_start'] <= now.hour or now.hour < RULES['quiet_hours_end']:
            return False, f'Quiet hours ({RULES["quiet_hours_start"]}:00-{RULES["quiet_hours_end"]}:00)'

        # Daily limit
        today = now.strftime('%Y-%m-%d')
        today_count = self.post_log.get('daily_counts', {}).get(today, 0)
        if today_count >= RULES['max_posts_per_day']:
            return False, f'Daily limit reached ({today_count}/{RULES["max_posts_per_day"]})'

        # Min hours between posts
        if self.post_log.get('posts'):
            last_post = self.post_log['posts'][-1]
            last_time = datetime.fromisoformat(last_post['posted_at'])
            hours_since = (now - last_time).total_seconds() / 3600
            if hours_since < RULES['min_hours_between_posts']:
                return False, f'Too soon since last post ({hours_since:.1f}h < {RULES["min_hours_between_posts"]}h)'

        # Client check
        if not self.client:
            return False, 'Twitter client not initialized (check API keys)'

        return True, 'OK'

    def _log_post(self, content_type: str, text: str, tweet_id: str = None):
        """Log a posted tweet."""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        self.post_log['posts'].append({
            'type': content_type,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'tweet_id': tweet_id,
            'posted_at': now.isoformat(),
        })

        self.post_log['daily_counts'][today] = self.post_log.get('daily_counts', {}).get(today, 0) + 1
        self.post_log['total_posted'] = self.post_log.get('total_posted', 0) + 1

        # Keep log manageable (last 500 posts)
        if len(self.post_log['posts']) > 500:
            self.post_log['posts'] = self.post_log['posts'][-500:]

        self._save_log()

    # ──────────────────────────────────────────────
    # Content Composers
    # ──────────────────────────────────────────────

    def _get_random_quote(self) -> Optional[dict]:
        """Pull a random quote from the quote bank."""
        quote_bank = VAULT_INTELLIGENCE / 'quote_bank.json'
        if not quote_bank.exists():
            return None
        data = json.loads(quote_bank.read_text())
        quotes = data.get('quotes', [])
        if not quotes:
            return None

        # Avoid recently posted quotes
        recent_texts = set()
        for post in self.post_log.get('posts', [])[-50:]:
            if post['type'] == 'quote':
                recent_texts.add(post.get('text', '')[:50])

        available = [q for q in quotes if q.get('text', '')[:50] not in recent_texts]
        return random.choice(available) if available else random.choice(quotes)

    def _get_random_prediction(self) -> Optional[dict]:
        """Pull a random prediction from intelligence outputs."""
        predictions = []
        for f in VAULT_INTELLIGENCE.glob('*.json'):
            if f.name in ('quote_bank.json', 'theme_map.json'):
                continue
            try:
                data = json.loads(f.read_text())
                analysis = data.get('analysis', data)
                preds = analysis.get('predictions', [])
                predictions.extend(preds)
            except Exception:
                continue
        return random.choice(predictions) if predictions else None

    def _get_theme_hashtags(self, themes: list = None) -> str:
        """Generate hashtags from themes."""
        if themes:
            tags = [f'#{t.replace(" ", "")}' for t in themes[:RULES['hashtag_limit']]]
            return ' '.join(tags)

        # Default hashtags
        default_tags = [
            '#Sovereignty', '#PatternRecognition', '#Ownership',
            '#GenerationalWealth', '#CognitionKey', '#19Keys',
            '#WealthBuilding', '#MentalSovereignty', '#Empire',
        ]
        selected = random.sample(default_tags, min(RULES['hashtag_limit'], len(default_tags)))
        return ' '.join(selected)

    def compose_quote_tweet(self) -> Optional[str]:
        """Compose a tweet from the quote bank."""
        quote = self._get_random_quote()
        if not quote:
            logger.info('No quotes available for posting')
            return None

        text = quote.get('text', quote.get('quote', ''))
        if not text:
            return None

        intro = random.choice(TEMPLATES['quote_intro'])
        cta = random.choice(TEMPLATES['cta'])
        hashtags = self._get_theme_hashtags(quote.get('themes', []))

        tweet = f'{intro}\n\n"{text}"'
        if cta:
            tweet += cta
        tweet += f'\n\n{hashtags}'

        # Enforce 280 char limit
        if len(tweet) > 280:
            # Trim quote to fit
            max_quote_len = 280 - len(intro) - len(cta) - len(hashtags) - 20
            text = text[:max_quote_len] + '...'
            tweet = f'{intro}\n\n"{text}"'
            if cta:
                tweet += cta
            tweet += f'\n\n{hashtags}'

        return tweet.strip()

    def compose_prediction_tweet(self) -> Optional[str]:
        """Compose a tweet from predictions."""
        pred = self._get_random_prediction()
        if not pred:
            logger.info('No predictions available for posting')
            return None

        claim = pred.get('claim', pred.get('prediction', ''))
        timeline = pred.get('timeline', '')
        intro = random.choice(TEMPLATES['prediction_intro'])
        hashtags = self._get_theme_hashtags()

        tweet = f'{intro}\n\n{claim}'
        if timeline:
            tweet += f'\n\nTimeline: {timeline}'
        tweet += f'\n\n{hashtags}'

        if len(tweet) > 280:
            max_claim = 280 - len(intro) - len(hashtags) - 30
            claim = claim[:max_claim] + '...'
            tweet = f'{intro}\n\n{claim}\n\n{hashtags}'

        return tweet.strip()

    def compose_thread(self, topic: str = None) -> Optional[list[str]]:
        """Compose a thread on a topic using Claude API."""
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        if not api_key:
            logger.warning('No Anthropic API key for thread generation')
            return None

        if not topic:
            # Pick from theme map
            theme_map = VAULT_INTELLIGENCE / 'theme_map.json'
            if theme_map.exists():
                data = json.loads(theme_map.read_text())
                clusters = data.get('clusters', [])
                if clusters:
                    topic = random.choice(clusters).get('theme', 'sovereignty')
            if not topic:
                topic = random.choice([
                    'pattern recognition', 'ownership', 'sovereignty',
                    'generational wealth', 'mental frameworks'
                ])

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            prompt = f"""Write a Twitter/X thread for 19 Keys about: {topic}

Rules:
- Exactly {RULES['max_thread_tweets']} tweets (including the hook)
- Each tweet MUST be under 270 characters (leave room for numbering)
- First tweet is the hook — attention-grabbing, ends with 🧵
- Voice: confident, strategic, ownership-focused. NOT preachy or academic.
- Include 1-2 concrete examples or historical references
- Last tweet = call to action (follow, share, or reflection question)
- No hashtags except on the last tweet (max 2)

Return JSON array of strings, each string = one tweet. No markdown fences."""

            response = client.messages.create(
                model=os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )

            result = response.content[0].text.strip()
            if result.startswith('```'):
                result = re.sub(r'^```\w*\n?', '', result)
                result = re.sub(r'\n?```$', '', result)

            tweets = json.loads(result)

            # Validate lengths
            valid_tweets = []
            for t in tweets:
                if len(t) <= 280:
                    valid_tweets.append(t)
                else:
                    valid_tweets.append(t[:277] + '...')

            return valid_tweets[:RULES['max_thread_tweets']]

        except Exception as e:
            logger.error(f'Thread composition failed: {e}')
            return None

    # ──────────────────────────────────────────────
    # Posting
    # ──────────────────────────────────────────────

    def post_tweet(self, text: str, content_type: str = 'general', reply_to: str = None) -> Optional[str]:
        """Post a single tweet. Returns tweet ID or None."""
        can_post, reason = self._can_post()
        if not can_post:
            logger.info(f'Cannot post: {reason}')
            return None

        try:
            kwargs = {'text': text}
            if reply_to:
                kwargs['in_reply_to_tweet_id'] = reply_to

            response = self.client.create_tweet(**kwargs)
            tweet_id = response.data.get('id', 'unknown')
            logger.info(f'Posted tweet ({content_type}): {tweet_id}')

            self._log_post(content_type, text, tweet_id)
            return tweet_id

        except Exception as e:
            logger.error(f'Failed to post tweet: {e}')
            return None

    def post_thread(self, tweets: list[str]) -> list[str]:
        """Post a thread (list of tweets). Returns list of tweet IDs."""
        if not tweets:
            return []

        can_post, reason = self._can_post()
        if not can_post:
            logger.info(f'Cannot post thread: {reason}')
            return []

        tweet_ids = []
        reply_to = None

        for i, tweet_text in enumerate(tweets):
            try:
                kwargs = {'text': tweet_text}
                if reply_to:
                    kwargs['in_reply_to_tweet_id'] = reply_to

                response = self.client.create_tweet(**kwargs)
                tweet_id = response.data.get('id', 'unknown')
                tweet_ids.append(tweet_id)
                reply_to = tweet_id

                logger.info(f'Posted thread tweet {i+1}/{len(tweets)}: {tweet_id}')

            except Exception as e:
                logger.error(f'Thread tweet {i+1} failed: {e}')
                break

        if tweet_ids:
            self._log_post('thread', tweets[0], tweet_ids[0])

        return tweet_ids

    def post_quote(self) -> Optional[str]:
        """Compose and post a quote tweet."""
        tweet = self.compose_quote_tweet()
        if tweet:
            return self.post_tweet(tweet, 'quote')
        return None

    def post_prediction(self) -> Optional[str]:
        """Compose and post a prediction tweet."""
        tweet = self.compose_prediction_tweet()
        if tweet:
            return self.post_tweet(tweet, 'prediction')
        return None

    # ──────────────────────────────────────────────
    # Daily Schedule
    # ──────────────────────────────────────────────

    def run_daily_schedule(self) -> dict:
        """Run the full daily posting schedule."""
        logger.info('═══ Twitter Agent: Running daily schedule ═══')

        results = {
            'quotes_posted': 0,
            'predictions_posted': 0,
            'threads_posted': 0,
            'skipped': 0,
        }

        # Determine content mix for today
        roll = random.random()
        cumulative = 0
        content_type = 'quote'

        for ctype, weight in RULES['content_mix'].items():
            cumulative += weight
            if roll <= cumulative:
                content_type = ctype
                break

        if content_type == 'quote':
            result = self.post_quote()
            if result:
                results['quotes_posted'] = 1
            else:
                results['skipped'] = 1

        elif content_type == 'prediction':
            result = self.post_prediction()
            if result:
                results['predictions_posted'] = 1
            else:
                results['skipped'] = 1

        elif content_type == 'thread':
            tweets = self.compose_thread()
            if tweets:
                ids = self.post_thread(tweets)
                if ids:
                    results['threads_posted'] = 1
                else:
                    results['skipped'] = 1
            else:
                results['skipped'] = 1

        elif content_type == 'insight':
            # Post a quote as fallback for now
            result = self.post_quote()
            if result:
                results['quotes_posted'] = 1
            else:
                results['skipped'] = 1

        logger.info(f'═══ Twitter Agent Complete: {results} ═══')
        return results

    def get_status(self) -> dict:
        """Return current agent status."""
        today = datetime.now().strftime('%Y-%m-%d')
        return {
            'client_ready': self.client is not None,
            'posts_today': self.post_log.get('daily_counts', {}).get(today, 0),
            'max_posts_per_day': RULES['max_posts_per_day'],
            'total_posted': self.post_log.get('total_posted', 0),
            'last_post': self.post_log['posts'][-1] if self.post_log.get('posts') else None,
        }


def run_twitter_schedule() -> dict:
    """Convenience function for the orchestrator."""
    agent = TwitterAgent()
    return agent.run_daily_schedule()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    agent = TwitterAgent()
    status = agent.get_status()
    print(json.dumps(status, indent=2))
