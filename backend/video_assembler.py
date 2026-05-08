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
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
    return output_path

def trim_video_simple(input_path, output_path, duration):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-t", str(duration), "-c", "copy", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def add_music_simple(video_path, music_url, output_path):
    if not music_url or music_url in ["null", "None", ""]:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    music_path = tempfile.mktemp(suffix='.mp3')
    download_file(music_url, music_path)
    
    cmd = ["ffmpeg", "-y", "-i", video_path, "-i", music_path,
           "-filter_complex", "[1:a]volume=0.25[a1];[0:a][a1]amix=inputs=2:duration=first",
           "-c:v", "copy", output_path]
    subprocess.run(cmd, check=False, capture_output=True)
    
    try:
        os.unlink(music_path)
    except:
        pass
    return output_path

def add_text_simple(video_path, text, output_path):
    if not text:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    text_escaped = text.replace("'", "'\\\\''")
    cmd = ["ffmpeg", "-y", "-i", video_path,
           "-vf", f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20",
           "-codec:a", "copy", output_path]
    subprocess.run(cmd, check=False, capture_output=True)
    return output_path

def create_video_from_option(video_url, topic, duration=5, music_url=None, text_overlay=None, quality_settings=None):
    if not supabase:
        raise RuntimeError("Supabase client not initialized")
    
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        input_path = os.path.join(temp_dir, 'input.mp4')
        temp_files.append(input_path)
        download_file(video_url, input_path)
        
        trimmed_path = os.path.join(temp_dir, 'trimmed.mp4')
        temp_files.append(trimmed_path)
        trim_video_simple(input_path, trimmed_path, duration)
        
        with_music_path = os.path.join(temp_dir, 'with_music.mp4')
        temp_files.append(with_music_path)
        add_music_simple(trimmed_path, music_url, with_music_path)
        
        final_path = os.path.join(temp_dir, 'final.mp4')
        temp_files.append(final_path)
        add_text_simple(with_music_path, text_overlay, final_path)
        
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        
        with open(final_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f, file_options={"content-type": "video/mp4"})
        
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        
        return public_url
    finally:
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass
        try:
            os.rmdir(temp_dir)
        except:
            pass
        gc.collect()

def get_video_options(topic, max_options=6):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should'}
    keywords = [w for w in words if w not in stop_words]
    search_term = ' '.join(keywords[:3]) if keywords else topic
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page={max_options}&video_type=film"
    try:
        data = requests.get(url, timeout=10).json()
        videos = []
        for hit in data.get('hits', []):
            vid = hit.get('videos', {})
            video_url = vid.get('medium', {}).get('url') or vid.get('small', {}).get('url')
            if video_url:
                videos.append({'url': video_url, 'duration': hit.get('duration', 0), 'tags': hit.get('tags', '')[:150]})
        return videos
    except Exception as e:
        return []

def create_multi_clip_video(video_urls, topic, duration_per_clip=3, quality_settings=None):
    temp_dir = tempfile.mkdtemp()
    clip_paths = []
    try:
        for i, url in enumerate(video_urls[:2]):
            clip_input = os.path.join(temp_dir, f'clip_{i}_input.mp4')
            clip_output = os.path.join(temp_dir, f'clip_{i}_trimmed.mp4')
            download_file(url, clip_input)
            trim_video_simple(clip_input, clip_output, duration_per_clip)
            clip_paths.append(clip_output)
        
        list_file = os.path.join(temp_dir, 'concat_list.txt')
        with open(list_file, 'w') as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")
        
        output_path = os.path.join(temp_dir, 'merged.mp4')
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
        subprocess.run(cmd, check=True, capture_output=True)
        
        bucket = "video-outputs"
        unique_name = f"multi_{uuid.uuid4()}.mp4"
        with open(output_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f, file_options={"content-type": "video/mp4"})
        return supabase.storage.from_(bucket).get_public_url(unique_name)
    finally:
        for f in clip_paths:
            if os.path.exists(f):
                os.unlink(f)
        os.rmdir(temp_dir)
        gc.collect()
