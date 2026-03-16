"""
Sovereign Content OS — Layer 01: YouTube Analytics
Pulls channel analytics, video performance data, and top-performing content.
Saves structured analytics JSON to vault/intelligence/.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import (
    GOOGLE_CREDENTIALS_PATH,
    YOUTUBE_CHANNEL_ID,
    VAULT_INTELLIGENCE
)

logger = logging.getLogger('content-os.ingestion.youtube')

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
TOKEN_PATH = Path(__file__).parent.parent / 'config' / 'youtube_token.json'


def get_youtube_service():
    """Authenticate and return YouTube Data API service."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return build('youtube', 'v3', credentials=creds)


def pull_channel_stats(service):
    """Get overall channel statistics."""
    request = service.channels().list(
        part='statistics,snippet,contentDetails',
        id=YOUTUBE_CHANNEL_ID
    )
    response = request.execute()

    if not response.get('items'):
        logger.warning('No channel data returned')
        return None

    channel = response['items'][0]
    stats = channel['statistics']

    return {
        'channel_name': channel['snippet']['title'],
        'subscribers': int(stats.get('subscriberCount', 0)),
        'total_views': int(stats.get('viewCount', 0)),
        'total_videos': int(stats.get('videoCount', 0)),
        'pulled_at': datetime.now().isoformat()
    }


def pull_recent_videos(service, max_results=20):
    """Get recent video performance data."""
    # Get recent uploads
    request = service.search().list(
        part='id,snippet',
        channelId=YOUTUBE_CHANNEL_ID,
        order='date',
        maxResults=max_results,
        type='video'
    )
    response = request.execute()

    videos = []
    video_ids = []

    for item in response.get('items', []):
        video_ids.append(item['id']['videoId'])
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'published_at': item['snippet']['publishedAt'],
            'description': item['snippet']['description'][:200],
            'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', '')
        })

    # Get detailed stats for each video
    if video_ids:
        stats_request = service.videos().list(
            part='statistics,contentDetails',
            id=','.join(video_ids)
        )
        stats_response = stats_request.execute()

        stats_map = {}
        for item in stats_response.get('items', []):
            stats_map[item['id']] = {
                'views': int(item['statistics'].get('viewCount', 0)),
                'likes': int(item['statistics'].get('likeCount', 0)),
                'comments': int(item['statistics'].get('commentCount', 0)),
                'duration': item['contentDetails'].get('duration', '')
            }

        for video in videos:
            if video['video_id'] in stats_map:
                video.update(stats_map[video['video_id']])

    return videos


def pull_analytics():
    """
    Main analytics pull — channel stats + recent video performance.
    Returns analytics dict.
    """
    logger.info('Pulling YouTube analytics...')

    if not YOUTUBE_CHANNEL_ID:
        logger.warning('YOUTUBE_CHANNEL_ID not set, skipping')
        return None

    try:
        service = get_youtube_service()

        channel_stats = pull_channel_stats(service)
        recent_videos = pull_recent_videos(service)

        # Sort by views to find top performers
        top_videos = sorted(recent_videos, key=lambda v: v.get('views', 0), reverse=True)

        analytics = {
            'channel': channel_stats,
            'recent_videos': recent_videos,
            'top_performers': top_videos[:5],
            'total_recent_views': sum(v.get('views', 0) for v in recent_videos),
            'pulled_at': datetime.now().isoformat()
        }

        # Save to vault
        output_path = VAULT_INTELLIGENCE / 'youtube_analytics.json'
        output_path.write_text(json.dumps(analytics, indent=2))

        logger.info(f'YouTube analytics saved. {len(recent_videos)} videos tracked.')
        return analytics

    except Exception as e:
        logger.error(f'YouTube analytics pull failed: {e}')
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    data = pull_analytics()
    if data:
        print(f"Channel: {data['channel']['channel_name']}")
        print(f"Subscribers: {data['channel']['subscribers']:,}")
        print(f"Recent videos tracked: {len(data['recent_videos'])}")
