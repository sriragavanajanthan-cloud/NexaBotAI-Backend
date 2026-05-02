import requests
import sys
import os
import re
import tempfile

# MoviePy 2.x imports
from moviepy import VideoFileClip, concatenate_videoclips

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"  # Replace with your actual key

def search_pixabay_videos(keyword, per_page=3):
    """Search for videos on Pixabay"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    response = requests.get(url)
    data = response.json()
    
    videos = []
    for hit in data.get('hits', []):
        video_url = hit['videos'].get('medium', {}).get('url') or hit['videos'].get('small', {}).get('url')
        if video_url:
            videos.append({
                'url': video_url,
                'duration': hit.get('duration', 0)
            })
    return videos

def download_video(url, output_path):
    """Download video from URL"""
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path

def extract_keywords(prompt):
    """Extract simple keywords from prompt"""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt.lower())
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should'}
    keywords = [w for w in words if w not in stop_words]
    return keywords[:2] if keywords else ['nature']

def create_video(topic, duration=5):
    """Create a simple video from a topic"""
    print(f"🎬 Creating video for: {topic}")
    
    # Extract keywords
    keywords = extract_keywords(topic)
    search_term = ' '.join(keywords)
    print(f"Search term: {search_term}")
    
    # Search for videos
    videos = search_pixabay_videos(search_term, per_page=3)
    
    if not videos:
        print("No videos found")
        return None
    
    print(f"Found {len(videos)} videos")
    
    # Download videos
    temp_dir = tempfile.mkdtemp()
    clips = []
    
    for i, video in enumerate(videos):
        print(f"Downloading video {i+1}...")
        video_path = os.path.join(temp_dir, f'video_{i}.mp4')
        download_video(video['url'], video_path)
        
        clip = VideoFileClip(video_path)
        # Trim to duration
        clip_duration = min(duration // len(videos), clip.duration)
        clip = clip.subclipped(0, clip_duration)
        clips.append(clip)
    
    # Combine clips
    if len(clips) == 1:
        final = clips[0]
    else:
        final = concatenate_videoclips(clips)
    
    # Output
    output_path = os.path.join(temp_dir, f"{topic.replace(' ', '_')}.mp4")
    final.write_videofile(output_path, fps=24, logger=None)
    
    # Cleanup
    for clip in clips:
        clip.close()
    if len(clips) > 1:
        final.close()
    
    print(f"✅ Video created: {output_path}")
    return output_path

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "nature"
    output = create_video(topic)
    
    if output:
        print(f"SUCCESS: {output}")
    else:
        print("FAILED")
        sys.exit(1)
