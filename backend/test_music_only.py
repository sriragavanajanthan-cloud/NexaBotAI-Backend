from music_library import get_tracks_by_mood, get_track_info, LIBRARY_STATS

# Test all moods
moods = ['cinematic', 'upbeat', 'calm', 'inspiring', 'corporate']

print("=" * 50)
print("🎵 Music Library Test")
print("=" * 50)

for mood in moods:
    tracks = get_tracks_by_mood(mood, limit=3)
    print(f"\n📀 {mood.upper()}: {len(tracks)} tracks available")
    for track in tracks[:2]:
        print(f"   🎵 {get_track_info(track)}")

print(f"\n✅ Total tracks: {LIBRARY_STATS['total_tracks']}")
print("✅ Music library is working!")
