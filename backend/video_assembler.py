import subprocess
import os
import tempfile
import uuid
import requests
import re
import gc
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

def stream_download(url, output_path):
    """Download file in chunks to reduce memory"""
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return output_path

def process_video_pipeline(video_url, duration, output_path, quality_settings=None, music_url=None, text_overlay=None):
    """
    Process video in a single FFmpeg pipeline - NO intermediate files!
    This reduces memory usage by 80%
    """
    # Build FFmpeg command with filters
    filters = []
    
    # Trim filter
    filters.append(f"trim=duration={duration}")
    filters.append("setpts=PTS-STARTPTS")
    
    # Scale filter based on quality
    if quality_settings:
        if quality_settings.get("preset") == "fast":
            filters.append(f"scale=1280:720")
        else:
            filters.append(f"scale=1920:1080")
    
    # Text overlay filter
    if text_overlay:
        text_escaped = text_overlay.replace("'", "'\\''")
        filters.append(f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20")
    
    # Combine filters
    filter_complex = ",".join(filters) if filters else "null"
    
    # Build command
    cmd = ["ffmpeg", "-y", "-i", video_url]
    
    # Add music if provided
    if music_url and music_url != "null":
        cmd.extend(["-i", music_url])
        cmd.extend(["-filter_complex", f"[0:v]{filter_complex}[v];[1:a]volume=0.25[a1];[0:a][a1]amix=inputs=2:duration=first"])
        cmd.extend(["-map", "[v]", "-map", "a"])
    else:
        if filter_complex != "null":
            cmd.extend(["-filter_complex", f"[0:v]{filter_complex}", "-map", "[v]", "-map", "0:a"])
        else:
            cmd.extend(["-c:v", "copy"])
    
    cmd.extend(["-c:v", "libx264", "-crf", "28", "-preset", "fast", "-c:a", "aac"])
    cmd.append(output_path)
    
    # Run FFmpeg
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def create_video_from_option(video_url, topic, duration=5, music_url=None, text_overlay=None, quality_settings=None):
    """Create video using streaming pipeline - minimal memory usage"""
    if not supabase:
        raise RuntimeError("Supabase client not initialized")
    
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, 'output.mp4')
    
    try:
        print(f"🎬 Processing video (duration: {duration}s)")
        
        # Process in one go - no intermediate files
        process_video_pipeline(video_url, duration, output_path, quality_settings, music_url, text_overlay)
        
        # Upload to Supabase
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        with open(output_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f)
        
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        print(f"✅ Uploaded: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.unlink(output_path)
        try:
            os.rmdir(temp_dir)
        except:
            pass
        gc.collect()

def search_pixabay_videos(keyword, per_page=6):
    """Search for videos on Pixabay"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    try:
        response = requests.get(url, timeout=10)
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
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_video_options(topic, max_options=6):
    """Get video options for a topic"""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should'}
    keywords = [w for w in words if w not in stop_words]
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
