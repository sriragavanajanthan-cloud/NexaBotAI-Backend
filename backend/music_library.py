SOUNDHELIX_BASE = "https://www.soundhelix.com/examples/mp3/"

CINEMATIC_TRACKS = [
    f"{SOUNDHELIX_BASE}SoundHelix-Song-3.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-4.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-7.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-8.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-12.mp3"
]

UPBEAT_TRACKS = [
    f"{SOUNDHELIX_BASE}SoundHelix-Song-1.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-2.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-9.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-12.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-14.mp3"
]

CALM_TRACKS = [
    f"{SOUNDHELIX_BASE}SoundHelix-Song-5.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-6.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-11.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-13.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-15.mp3"
]

INSPIRING_TRACKS = [
    f"{SOUNDHELIX_BASE}SoundHelix-Song-7.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-8.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-10.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-3.mp3"
]

CORPORATE_TRACKS = [
    f"{SOUNDHELIX_BASE}SoundHelix-Song-8.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-10.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-14.mp3",
    f"{SOUNDHELIX_BASE}SoundHelix-Song-1.mp3"
]

ALL_MUSIC_BY_MOOD = {
    'cinematic': CINEMATIC_TRACKS,
    'upbeat': UPBEAT_TRACKS,
    'calm': CALM_TRACKS,
    'inspiring': INSPIRING_TRACKS,
    'corporate': CORPORATE_TRACKS
}

def get_tracks_by_mood(mood, limit=10):
    tracks = ALL_MUSIC_BY_MOOD.get(mood, UPBEAT_TRACKS)
    return tracks[:limit]

def get_track_info(url):
    name = url.split('/')[-1].replace('.mp3', '').replace('-', ' ')
    return name.replace('SoundHelix', '').strip().title()

LIBRARY_STATS = {
    'total_tracks': 23,
    'sources': ['SoundHelix'],
    'moods': list(ALL_MUSIC_BY_MOOD.keys())
}
