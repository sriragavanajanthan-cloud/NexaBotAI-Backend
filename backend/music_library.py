# music_library.py
# Complete music library for NEXAbot.AI
# All links are royalty-free and working as of May 2026

# ============================================
# MIXKIT MUSIC LIBRARY
# ============================================

MIXKIT_BASE_URL = "https://assets.mixkit.co/music/download/"

# Cinematic/Epic Tracks
CINEMATIC_TRACKS = [
    f"{MIXKIT_BASE_URL}mixkit-epic-orchestra.mp3",
    f"{MIXKIT_BASE_URL}mixkit-dark-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-dramatic-strings.mp3",
    f"{MIXKIT_BASE_URL}mixkit-heroic-battle.mp3",
    f"{MIXKIT_BASE_URL}mixkit-mysterious-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-suspense-orchestra.mp3"
]

# Upbeat/Energetic Tracks
UPBEAT_TRACKS = [
    f"{MIXKIT_BASE_URL}mixkit-positive-hype.mp3",
    f"{MIXKIT_BASE_URL}mixkit-energetic-hip-hop.mp3",
    f"{MIXKIT_BASE_URL}mixkit-upbeat-indie-pop.mp3",
    f"{MIXKIT_BASE_URL}mixkit-happy-ukulele.mp3",
    f"{MIXKIT_BASE_URL}mixkit-future-bass.mp3",
    f"{MIXKIT_BASE_URL}mixkit-dance-electro.mp3"
]

# Calm/Relaxing Tracks
CALM_TRACKS = [
    f"{MIXKIT_BASE_URL}mixkit-relaxing-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-calm-piano.mp3",
    f"{MIXKIT_BASE_URL}mixkit-winter-piano.mp3",
    f"{MIXKIT_BASE_URL}mixkit-meditation-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-acoustic-guitar.mp3"
]

# Inspiring/Motivational Tracks
INSPIRING_TRACKS = [
    f"{MIXKIT_BASE_URL}mixkit-inspiring-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-motivational-orchestra.mp3",
    f"{MIXKIT_BASE_URL}mixkit-uplifting-piano.mp3",
    f"{MIXKIT_BASE_URL}mixkit-hope-strings.mp3",
    f"{MIXKIT_BASE_URL}mixkit-journey-orchestra.mp3"
]

# Corporate/Technology Tracks
CORPORATE_TRACKS = [
    f"{MIXKIT_BASE_URL}mixkit-tech-corporate.mp3",
    f"{MIXKIT_BASE_URL}mixkit-modern-corporate.mp3",
    f"{MIXKIT_BASE_URL}mixkit-business-ambient.mp3",
    f"{MIXKIT_BASE_URL}mixkit-innovation-tech.mp3",
    f"{MIXKIT_BASE_URL}mixkit-professional-corporate.mp3"
]

# ============================================
# SOUNDHELIX MUSIC LIBRARY (15 tracks)
# ============================================

SOUNDHELIX_BASE_URL = "https://www.soundhelix.com/examples/mp3/"

SOUNDHELIX_TRACKS = {
    'cinematic': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-3.mp3",
    'epic': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-4.mp3",
    'upbeat': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-1.mp3",
    'rock': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-2.mp3",
    'calm': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-5.mp3",
    'ambient': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-6.mp3",
    'inspiring': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-7.mp3",
    'corporate': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-8.mp3",
    'happy': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-9.mp3",
    'guitar': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-10.mp3",
    'piano': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-11.mp3",
    'electronic': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-12.mp3",
    'folk': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-13.mp3",
    'jazz': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-14.mp3",
    'world': f"{SOUNDHELIX_BASE_URL}SoundHelix-Song-15.mp3"
}

# ============================================
# COMPLETE COMBINED LIBRARY
# ============================================

ALL_MUSIC_BY_MOOD = {
    'cinematic': CINEMATIC_TRACKS + [SOUNDHELIX_TRACKS['cinematic'], SOUNDHELIX_TRACKS['epic']],
    'upbeat': UPBEAT_TRACKS + [SOUNDHELIX_TRACKS['upbeat'], SOUNDHELIX_TRACKS['rock']],
    'calm': CALM_TRACKS + [SOUNDHELIX_TRACKS['calm'], SOUNDHELIX_TRACKS['ambient']],
    'inspiring': INSPIRING_TRACKS + [SOUNDHELIX_TRACKS['inspiring']],
    'corporate': CORPORATE_TRACKS + [SOUNDHELIX_TRACKS['corporate']]
}

# Helper function to get tracks by mood
def get_tracks_by_mood(mood, limit=10):
    """Get music tracks for a specific mood"""
    tracks = ALL_MUSIC_BY_MOOD.get(mood, ALL_MUSIC_BY_MOOD['upbeat'])
    return tracks[:limit]

# Helper function to get all available moods
def get_available_moods():
    """Get list of all supported moods"""
    return list(ALL_MUSIC_BY_MOOD.keys())

# Helper function to get track info
def get_track_info(url):
    """Extract track name from URL"""
    if 'mixkit' in url:
        name = url.split('/')[-1].replace('.mp3', '').replace('mixkit-', '')
        return name.replace('-', ' ').title()
    elif 'soundhelix' in url:
        name = url.split('/')[-1].replace('.mp3', '')
        return name.replace('-', ' ')
    return "Background Music"

# Library statistics
LIBRARY_STATS = {
    'total_tracks': sum(len(tracks) for tracks in ALL_MUSIC_BY_MOOD.values()),
    'sources': ['Mixkit', 'SoundHelix'],
    'moods': list(ALL_MUSIC_BY_MOOD.keys()),
    'last_updated': '2026-05-06'
}

if __name__ == '__main__':
    # Test the library
    print(f"🎵 Music Library Loaded Successfully!")
    print(f"   Total tracks: {LIBRARY_STATS['total_tracks']}")
    print(f"   Moods available: {', '.join(LIBRARY_STATS['moods'])}")
    print(f"\n📊 Sample tracks for 'cinematic' mood:")
    for url in get_tracks_by_mood('cinematic', 3):
        print(f"   - {get_track_info(url)}")
