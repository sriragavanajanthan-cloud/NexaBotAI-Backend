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
    """Download a file from URL with chunking to save memory"""
    r = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=16384):  # 16KB chunks
            f.write(chunk)
    return output_path

def trim_video_ffmpeg(input_path, output_path, duration, quality_settings=None):
    """Trim video using FFmpeg - memory efficient"""
    if quality_settings:
        crf = quality_settings.get("crf", 28)
        preset = quality_settings.get("preset", "fast")
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
    else:
        # Fast copy mode for draft quality (no re-encoding)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-t", str(duration), "-c", "copy", output_path]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def add_music_to_video(video_path, music_url, output_path):
    """Add background music to video with memory optimization"""
    if not music_url or music_url == "null" or music_url == "None":
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Download music file
    music_path = tempfile.mktemp(suffix='.mp3')
    try:
        download_file(music_url, music_path)
        
        # Mix audio: video original audio + background music (volume reduced)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", "[1:a]volume=0.25[a1];[0:a][a1]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-max_muxing_queue_size", "1024",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        # Cleanup music file
        if os.path.exists(music_path):
            os.unlink(music_path)
    
    return output_path

def add_text_overlay(video_path, text, output_path):
    """Add text overlay to video using FFmpeg"""
    if not text:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Escape text for FFmpeg
    text_escaped = text.replace("'", "'\\''").replace('"', '\\"')
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-text_h-20",
        "-c:a", "copy",
        "-max_muxing_queue_size", "1024",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def create_video_from_option(video_url, topic, duration=5, music_url=None, text_overlay=None, quality_settings=None):
    """Download, trim, add music, add text, upload to Supabase, return URL"""
    if not supabase:
        raise RuntimeError("Supabase client not initialized")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        # Step 1: Download original video
        input_path = os.path.join(temp_dir, 'downloaded.mp4')
        temp_files.append(input_path)
        print(f"Downloading video...")
        download_file(video_url, input_path)
        
        # Step 2: Trim video (with or without re-encoding)
        trimmed_path = os.path.join(temp_dir, 'trimmed.mp4')
        temp_files.append(trimmed_path)
        print(f"Trimming to {duration} seconds...")
        trim_video_ffmpeg(input_path, trimmed_path, duration, quality_settings)
        
        # Force garbage collection after trim
        gc.collect()
        
        # Step 3: Add music (if provided)
        with_music_path = os.path.join(temp_dir, 'with_music.mp4')
        temp_files.append(with_music_path)
        print(f"Adding music...")
        add_music_to_video(trimmed_path, music_url, with_music_path)
        
        # Force garbage collection
        gc.collect()
        
        # Step 4: Add text overlay (if provided)
        final_path = os.path.join(temp_dir, 'final.mp4')
        temp_files.append(final_path)
        print(f"Adding text overlay...")
        add_text_overlay(with_music_path, text_overlay, final_path)
        
        # Step 5: Upload to Supabase
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        with open(final_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f)
        
        # Step 6: Get public URL
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        
        print(f"✅ Video uploaded: {public_url}")
        return public_url
        
    finally:
        # Cleanup temp files
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
        # Force garbage collection
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

def download_multiple_videos(video_urls, temp_dir):
    """Download multiple videos for assembly"""
    downloaded_paths = []
    for i, url in enumerate(video_urls):
        path = os.path.join(temp_dir, f'clip_{i}.mp4')
        download_file(url, path)
        downloaded_paths.append(path)
    return downloaded_paths

def concatenate_videos(video_paths, output_path):
    """Concatenate multiple videos into one"""
    if len(video_paths) == 1:
        import shutil
        shutil.copy2(video_paths[0], output_path)
        return output_path
    
    # Create concat file list
    concat_file = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
    with open(concat_file, 'w') as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    # Run FFmpeg concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Cleanup
    os.unlink(concat_file)
    return output_path

def create_multi_clip_video(video_urls, topic, duration_per_clip=5, quality_settings=None):
    """Create a video from multiple clips"""
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        # Download all clips
        print(f"Downloading {len(video_urls)} clips...")
        clip_paths = download_multiple_videos(video_urls, temp_dir)
        temp_files.extend(clip_paths)
        
        # Trim each clip
        trimmed_paths = []
        for i, clip_path in enumerate(clip_paths):
            trimmed_path = os.path.join(temp_dir, f'trimmed_{i}.mp4')
            temp_files.append(trimmed_path)
            trim_video_ffmpeg(clip_path, trimmed_path, duration_per_clip, quality_settings)
            trimmed_paths.append(trimmed_path)
        
        # Concatenate all clips
        concat_path = os.path.join(temp_dir, 'concatenated.mp4')
        temp_files.append(concat_path)
        concatenate_videos(trimmed_paths, concat_path)
        
        # Upload to Supabase
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        with open(concat_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f)
        
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        return public_url
        
    finally:
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

def download_multiple_videos(video_urls, temp_dir):
    """Download multiple videos for assembly"""
    downloaded_paths = []
    for i, url in enumerate(video_urls):
        path = os.path.join(temp_dir, f'clip_{i}.mp4')
        download_file(url, path)
        downloaded_paths.append(path)
    return downloaded_paths

def concatenate_videos(video_paths, output_path):
    """Concatenate multiple videos into one"""
    if len(video_paths) == 1:
        import shutil
        shutil.copy2(video_paths[0], output_path)
        return output_path
    
    # Create concat file list
    concat_file = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
    with open(concat_file, 'w') as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    # Run FFmpeg concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Cleanup
    os.unlink(concat_file)
    return output_path

def create_multi_clip_video(video_urls, topic, duration_per_clip=5, quality_settings=None):
    """Create a video from multiple clips"""
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    
    try:
        # Download all clips
        print(f"Downloading {len(video_urls)} clips...")
        clip_paths = download_multiple_videos(video_urls, temp_dir)
        temp_files.extend(clip_paths)
        
        # Trim each clip
        trimmed_paths = []
        for i, clip_path in enumerate(clip_paths):
            trimmed_path = os.path.join(temp_dir, f'trimmed_{i}.mp4')
            temp_files.append(trimmed_path)
            trim_video_ffmpeg(clip_path, trimmed_path, duration_per_clip, quality_settings)
            trimmed_paths.append(trimmed_path)
        
        # Concatenate all clips
        concat_path = os.path.join(temp_dir, 'concatenated.mp4')
        temp_files.append(concat_path)
        concatenate_videos(trimmed_paths, concat_path)
        
        # Upload to Supabase
        bucket = "video-outputs"
        unique_name = f"{uuid.uuid4()}.mp4"
        with open(concat_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f)
        
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        return public_url
        
    finally:
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

def add_transition(clip1_path, clip2_path, output_path, transition_type="fade", duration=0.5):
    """Add transition effect between two clips"""
    if transition_type == "fade":
        # Create fade transition using FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", clip1_path,
            "-i", clip2_path,
            "-filter_complex",
            f"[0:v]fade=out:st={duration}:d={duration}[v0];"
            f"[1:v]fade=in:st=0:d={duration}[v1];"
            f"[v0][v1]concat=n=2:v=1:a=1",
            output_path
        ]
    elif transition_type == "crossfade":
        cmd = [
            "ffmpeg", "-y",
            "-i", clip1_path,
            "-i", clip2_path,
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset={duration}",
            output_path
        ]
    else:
        import shutil
        shutil.copy2(clip1_path, output_path)
        return output_path
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def add_ken_burns_effect(input_path, output_path, zoom=0.1, pan="center"):
    """Apply Ken Burns zoom/pan effect to video"""
    # Calculate zoom scale
    scale = 1 + zoom
    
    if pan == "center":
        # Center zoom
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale=iw*{scale}:ih*{scale},crop=iw/{scale}:ih/{scale}",
            "-c:a", "copy",
            output_path
        ]
    elif pan == "left":
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale=iw*{scale}:ih*{scale},crop=iw/{scale}:ih/{scale}:(iw-iw/{scale})/2:0",
            "-c:a", "copy",
            output_path
        ]
    else:
        import shutil
        shutil.copy2(input_path, output_path)
        return output_path
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def adjust_speed(input_path, output_path, speed_factor=1.0):
    """Adjust video speed (slow-motion or time-lapse)"""
    if speed_factor == 1.0:
        import shutil
        shutil.copy2(input_path, output_path)
        return output_path
    
    # Calculate PTS value
    pts_value = 1.0 / speed_factor
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", f"[0:v]setpts={pts_value}*PTS[v];[0:a]atempo={speed_factor}[a]",
        "-map", "[v]",
        "-map", "[a]",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def add_outro(video_path, outro_text, duration=3, output_path=None):
    """Add an outro screen to the video"""
    if output_path is None:
        output_path = video_path.replace('.mp4', '_with_outro.mp4')
    
    # Create a black frame with text using FFmpeg
    temp_dir = tempfile.mkdtemp()
    outro_path = os.path.join(temp_dir, 'outro.mp4')
    
    # Generate outro video
    cmd_outro = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1920x1080:d={duration}",
        "-vf", f"drawtext=text='{outro_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:a", "aac",
        outro_path
    ]
    subprocess.run(cmd_outro, check=True, capture_output=True)
    
    # Concatenate original video with outro
    concat_file = os.path.join(temp_dir, 'concat.txt')
    with open(concat_file, 'w') as f:
        f.write(f"file '{video_path}'\n")
        f.write(f"file '{outro_path}'\n")
    
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd_concat, check=True, capture_output=True)
    
    # Cleanup
    os.unlink(outro_path)
    os.unlink(concat_file)
    os.rmdir(temp_dir)
    
    return output_path

def add_watermark(video_path, watermark_url, position="bottom-right", output_path=None):
    """Add watermark image to video"""
    if output_path is None:
        output_path = video_path.replace('.mp4', '_watermarked.mp4')
    
    # Download watermark
    watermark_path = tempfile.mktemp(suffix='.png')
    download_file(watermark_url, watermark_path)
    
    # Position mapping
    positions = {
        "top-left": "10:10",
        "top-right": "main_w-overlay_w-10:10",
        "bottom-left": "10:main_h-overlay_h-10",
        "bottom-right": "main_w-overlay_w-10:main_h-overlay_h-10",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
    }
    
    position = positions.get(position, positions["bottom-right"])
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", watermark_path,
        "-filter_complex", f"[1:v]scale=150:150[wm];[0:v][wm]overlay={position}",
        "-codec:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    os.unlink(watermark_path)
    return output_path

def add_audio_fade(video_path, fade_in_duration=1.0, fade_out_duration=1.0, output_path=None):
    """Add audio fade in and fade out effects"""
    if output_path is None:
        output_path = video_path.replace('.mp4', '_audio_fade.mp4')
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-af", f"afade=t=in:st=0:d={fade_in_duration},afade=t=out:st={fade_out_duration}:d={fade_out_duration}",
        "-c:v", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def normalize_audio(video_path, output_path=None):
    """Normalize audio volume to a standard level"""
    if output_path is None:
        output_path = video_path.replace('.mp4', '_audio_norm.mp4')
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:v", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def detect_scenes(video_path):
    """Detect scene changes in video"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "select='gt(scene,0.3)',showinfo",
        "-f", "null",
        "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse output for scene timestamps
    scenes = []
    for line in result.stderr.split('\n'):
        if 'pts_time' in line:
            import re
            match = re.search(r'pts_time:([0-9.]+)', line)
            if match:
                scenes.append(float(match.group(1)))
    
    return scenes
