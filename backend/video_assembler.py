import requests
import sys
import os
import re
import tempfile
from moviepy import VideoFileClip, concatenate_videoclips

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

def search_pixabay_videos(keyword, per_page=6):
    """Search for videos on Pixabay"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
        
        data = response.json()
        if 'error' in data:
            return []
        
        videos = []
        for hit in data.get('hits', []):
            vid = hit.get('videos', {})
            video_url = vid.get('medium', {}).get('url') or vid.get('small', {}).get('url')
            if video_url:
                videos.append({
                    'url': video_url,
                    'duration': hit.get('duration', 0),
                    'tags': hit.get('tags', ''),
                    'width': vid.get('medium', {}).get('width', 0),
                    'height': vid.get('medium', {}).get('height', 0)
                })
        return videos
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_video_options(topic, max_options=6):
    """Get video options for a topic"""
    # Extract keywords
    keywords = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    keywords = [w for w in keywords if w not in ['the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should']]
    search_term = ' '.join(keywords[:3]) if keywords else topic
    
    videos = search_pixabay_videos(search_term, per_page=max_options + 2)
    
    options = []
    for i, video in enumerate(videos[:max_options]):
        options.append({
            'id': i + 1,
            'url': video['url'],
            'duration': video['duration'],
            'tags': video['tags'][:150],
            'resolution': f"{video['width']}x{video['height']}"
        })
    
    return options

def download_video(url, output_path):
    """Download video from URL"""
    r = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return output_path

def trim_video(input_path, output_path, duration):
    """Trim video to duration"""
    clip = VideoFileClip(input_path)
    clip_duration = min(duration, clip.duration)
    clip = clip.subclipped(0, clip_duration)
    clip.write_videofile(output_path, fps=24, logger=None)
    clip.close()
    return output_path

def create_video_from_option(video_url, topic, duration=5):
    """Create video from selected option"""
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, 'downloaded.mp4')
    output_path = os.path.join(temp_dir, f"{topic.replace(' ', '_')}.mp4")
    
    print(f"Downloading video...")
    download_video(video_url, video_path)
    
    print(f"Trimming to {duration} seconds...")
    trim_video(video_path, output_path, duration)
    
    return output_path

# CLI with interactive selection
if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "nature"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"\n🎬 Searching videos for: {topic}")
    options = get_video_options(topic, max_options=4)
    
    if not options:
        print("No videos found")
        sys.exit(1)
    
    print("\n📹 Available videos:\n")
    for opt in options:
        print(f"  {opt['id']}. Duration: {opt['duration']}s | Resolution: {opt['resolution']}")
        print(f"     Tags: {opt['tags']}\n")
    
    while True:
        try:
            choice = input(f"Select video (1-{len(options)}): ")
            selected = int(choice)
            if 1 <= selected <= len(options):
                break
            print(f"Invalid choice. Enter 1-{len(options)}")
        except ValueError:
            print("Enter a number")
    
    selected_video = options[selected - 1]
    print(f"\n✅ Selected video {selected}")
    
    output = create_video_from_option(selected_video['url'], topic, duration)
    print(f"\n✅ Video created: {output}")
