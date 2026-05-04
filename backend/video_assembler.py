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

def download_file(url, output_path):
    """Download file in chunks"""
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    return output_path

def trim_video_simple(input_path, output_path, duration):
    """Simple trim using FFmpeg copy mode (fast, low memory)"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        raise Exception(f"Trim failed: {result.stderr}")
    return output_path

def add_music_simple(video_path, music_url, output_path):
    """Add music overlay using FFmpeg"""
    if not music_url or music_url == "null" or music_url == "None":
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Download music
    music_path = tempfile.mktemp(suffix='.mp3')
    download_file(music_url, music_path)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", "[1:a]volume=0.25[a1];[0:a][a1]amix=inputs=2:duration=first",
        "-c:v", "copy",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(music_path)
    
    if result.returncode != 0:
        print(f"Music error: {result.stderr}")
        # Fallback: return video without music
        import shutil
        shutil.copy2(video_path, output_path)
    
    return output_path

def add_text_simple(video_path, text, output_path):
    """Add text overlay - simple version"""
    if not text:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Escape text
    text_escaped = text.replace("'", "'\\\\''")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20",
        "-codec:a", "copy",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Text error: {result.stderr}")
        import shutil
        shutil.copy2(video_path, output_path)
    
    return output_path

def create_video_from_option(video_url, topic, duration=5, music_url=None, text_overlay=None, quality_settings=None):
    """Create video step by step (more reliable)"""
    if not supabase:
        raise RuntimeError("Supabase client not initialized")
    
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        # Step 1: Download original video
        input_path = os.path.join(temp_dir, 'input.mp4')
        temp_files.append(input_path)
        print(f"Downloading video...")
        download_file(video_url, input_path)
        
        # Step 2: Trim
        trimmed_path = os.path.join(temp_dir, 'trimmed.mp4')
        temp_files.append(trimmed_path)
        print(f"Trimming to {duration} seconds...")
        trim_video_simple(input_path, trimmed_path, duration)
        
        # Step 3: Add music (if provided)
        with_music_path = os.path.join(temp_dir, 'with_music.mp4')
        temp_files.append(with_music_path)
        print(f"Adding music...")
        add_music_simple(trimmed_path, music_url, with_music_path)
        
        # Step 4: Add text overlay (if provided)
        final_path = os.path.join(temp_dir, 'final.mp4')
        temp_files.append(final_path)
        print(f"Adding text overlay...")
        add_text_simple(with_music_path, text_overlay, final_path)
        
        # Step 5: Upload to Supabase
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        print(f"Uploading to Supabase...")
        with open(final_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f)
        
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        print(f"✅ Done: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        # Cleanup
        for file_path in temp_files:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass
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
