import requests
import sys
import os
import re
import tempfile
from moviepy import VideoFileClip, concatenate_videoclips

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"  # use your actual key

# High‑priority keywords for sunset/lighting
PRIORITY_KEYWORDS = ['sunset', 'sunrise', 'golden', 'evening', 'dusk', 'twilight', 'golden hour']

def search_pixabay_videos(keyword, per_page=5):
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        if 'error' in data:
            return []
        videos = []
        for hit in data.get('hits', []):
            vid = hit.get('videos', {})
            url = vid.get('medium', {}).get('url') or vid.get('small', {}).get('url')
            if url:
                videos.append({
                    'url': url,
                    'duration': hit.get('duration', 0),
                    'tags': hit.get('tags', '').lower()
                })
        return videos
    except Exception:
        return []

def extract_keywords(prompt):
    """Extract important visual keywords from prompt."""
    prompt = prompt.lower()
    stop = {'a','an','the','of','and','or','but','so','for','nor','yet','with','without','by','in','on','at','to','from','up','down','off','over','under','again','further','then','once','here','there','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','than','that','then','these','those','through','until','unto','very','just','but','do','does','doing','did','done','be','being','been','am','are','is','was','were','has','have','having','can','could','will','would','should','may','might','must'}
    words = re.findall(r'\b[a-z]{3,}\b', prompt)
    keywords = [w for w in words if w not in stop and len(w) > 2]
    # Remove duplicates
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:5] if unique else ['nature']

def rank_videos(videos, keywords):
    """Rank videos: base score from keyword matches, extra points for priority keywords."""
    for video in videos:
        score = 0
        tags = video.get('tags', '')
        for kw in keywords:
            if kw in tags:
                score += 10
        # Bonus for priority words (sunset, golden, etc.)
        for pk in PRIORITY_KEYWORDS:
            if pk in tags:
                score += 30
        # Prefer longer duration (>=5s)
        if video['duration'] >= 5:
            score += 5
        video['relevance'] = score
    videos.sort(key=lambda x: x['relevance'], reverse=True)
    return videos

def create_video(topic, duration=5):
    print(f"\n🎬 Creating video for: {topic}")
    base_keywords = extract_keywords(topic)
    print(f"Base keywords: {base_keywords}")

    # Separate lighting keywords from scene keywords
    lighting_terms = [w for w in base_keywords if w in PRIORITY_KEYWORDS]
    scene_terms = [w for w in base_keywords if w not in PRIORITY_KEYWORDS]

    # Build ordered search list: first try full prompt, then "scene + lighting", then just scene
    searches = []
    full = ' '.join(base_keywords)
    if full:
        searches.append(full)
    if scene_terms and lighting_terms:
        searches.append(' '.join(scene_terms + lighting_terms))
    if scene_terms:
        searches.append(' '.join(scene_terms))
    if scene_terms and 'mountain' in scene_terms:
        searches.append('mountain')  # fallback broad term

    all_videos = []
    for q in searches:
        print(f"Searching: '{q}'")
        vids = search_pixabay_videos(q, per_page=5)
        all_videos.extend(vids)
        if len(all_videos) >= 8:
            break

    if not all_videos:
        print("No videos found.")
        return None

    # Deduplicate
    seen = set()
    unique = []
    for v in all_videos:
        if v['url'] not in seen:
            seen.add(v['url'])
            unique.append(v)

    ranked = rank_videos(unique, base_keywords)
    best = ranked[0]
    print(f"Best match: relevance={best['relevance']}, tags={best['tags'][:100]}, duration={best['duration']}s")

    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, 'video.mp4')
    print("Downloading...")
    r = requests.get(best['url'], stream=True)
    with open(video_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    clip = VideoFileClip(video_path)
    clip_duration = min(duration, clip.duration)
    clip = clip.subclipped(0, clip_duration)
    output_path = os.path.join(temp_dir, f"{topic.replace(' ', '_')}.mp4")
    clip.write_videofile(output_path, fps=24, logger=None)
    clip.close()

    print(f"✅ Video created: {output_path}")
    return output_path

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "nature"
    result = create_video(topic)
    if result:
        print(f"SUCCESS: {result}")
    else:
        print("FAILED")
        sys.exit(1)