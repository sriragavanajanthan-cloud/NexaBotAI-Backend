import requests
import os

FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY", "")

SOUNDHELIX_BASE = "https://www.soundhelix.com/examples/mp3/"

SOUNDHELIX_FALLBACK = {
    'cinematic': [
        f"{SOUNDHELIX_BASE}SoundHelix-Song-3.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-4.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-7.mp3"
    ],
    'upbeat': [
        f"{SOUNDHELIX_BASE}SoundHelix-Song-1.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-2.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-9.mp3"
    ],
    'calm': [
        f"{SOUNDHELIX_BASE}SoundHelix-Song-5.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-6.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-11.mp3"
    ],
    'inspiring': [
        f"{SOUNDHELIX_BASE}SoundHelix-Song-7.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-8.mp3"
    ],
    'corporate': [
        f"{SOUNDHELIX_BASE}SoundHelix-Song-8.mp3",
        f"{SOUNDHELIX_BASE}SoundHelix-Song-10.mp3"
    ]
}

def get_tracks_by_mood(mood, limit=10):
    """Get tracks from Freesound API with SoundHelix fallback"""
    
    if FREESOUND_API_KEY:
        try:
            url = "https://freesound.org/apiv2/search/text/"
            params = {
                'token': FREESOUND_API_KEY,
                'query': f"{mood} music",
                'page_size': limit,
                'filter': 'duration:[10 TO 60]'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            tracks = []
            for result in data.get('results', []):
                preview_url = f"https://freesound.org/data/previews/{result['id']//1000}/{result['id']}_preview.mp3"
                tracks.append(preview_url)
            
            if tracks:
                return tracks[:limit]
        except Exception as e:
            print(f"Freesound API error: {e}")
    
    # Fallback to SoundHelix
    return SOUNDHELIX_FALLBACK.get(mood, SOUNDHELIX_FALLBACK['upbeat'])[:limit]

def get_track_info(url):
    if 'freesound' in url:
        return "Freesound Track"
    elif 'soundhelix' in url:
        name = url.split('/')[-1].replace('.mp3', '').replace('-', ' ')
        return name.replace('SoundHelix', '').strip().title()
    return "Background Music"

LIBRARY_STATS = {
    'total_tracks': 150000,
    'sources': ['Freesound', 'SoundHelix'],
    'moods': ['cinematic', 'upbeat', 'calm', 'inspiring', 'corporate']
}

if __name__ == '__main__':
    for mood in ['cinematic', 'upbeat', 'calm', 'inspiring', 'corporate']:
        tracks = get_tracks_by_mood(mood, 2)
        print(f"{mood}: {len(tracks)} tracks")
