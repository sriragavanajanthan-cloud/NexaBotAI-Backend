import subprocess
import os
import tempfile
import uuid
import requests
from supabase import create_client

# Supabase configuration (from environment variables)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def download_video(url, output_path):
    """Download video from URL"""
    r = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return output_path

def trim_video_ffmpeg(input_path, output_path, duration):
    """Trim video using FFmpeg - memory efficient"""
    cmd = ["ffmpeg", "-y", "-i", input_path, "-t", str(duration), "-c", "copy", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def create_video_from_option(video_url, topic, duration=5):
    """Download, trim, upload to Supabase, return URL, delete local files"""
    if not supabase:
        raise RuntimeError("Supabase client not initialized")
    
    # Download
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
        input_path = tmp_in.name
    download_video(video_url, input_path)
    
    # Trim
    with tempfile.NamedTemporaryFile(suffix='_trimmed.mp4', delete=False) as tmp_out:
        output_path = tmp_out.name
    trim_video_ffmpeg(input_path, output_path, duration)
    
    # Upload to Supabase
    bucket = "video-outputs"
    unique_name = f"{uuid.uuid4()}.mp4"
    with open(output_path, 'rb') as f:
        supabase.storage.from_(bucket).upload(unique_name, f)
    
    # Get public URL
    public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
    
    # Cleanup local files
    os.unlink(input_path)
    os.unlink(output_path)
    
    return public_url

def search_pixabay_videos(keyword, per_page=6):
    import requests
    PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    response = requests.get(url)
    data = response.json()
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

def get_video_options(topic, max_options=6):
    import re
    keywords = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should'}
    keywords = [w for w in keywords if w not in stop_words]
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
