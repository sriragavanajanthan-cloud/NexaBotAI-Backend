def add_music_simple(video_path, music_url, output_path):
    if not music_url or music_url in ["null", "None", ""]:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    music_path = tempfile.mktemp(suffix='.mp3')
    try:
        download_file(music_url, music_path)
        
        # Check if video has audio stream
        probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        has_audio = subprocess.run(probe_cmd, capture_output=True, text=True).stdout.strip()
        
        if has_audio:
            # Video has audio - mix with music
            cmd = ["ffmpeg", "-y",
                   "-i", video_path,
                   "-i", music_path,
                   "-filter_complex", "[1:a]volume=0.25[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
                   "-map", "0:v",
                   "-map", "[aout]",
                   "-c:v", "copy",
                   "-c:a", "aac",
                   output_path]
        else:
            # Video has no audio - just add music
            cmd = ["ffmpeg", "-y",
                   "-i", video_path,
                   "-i", music_path,
                   "-map", "0:v",
                   "-map", "1:a",
                   "-c:v", "copy",
                   "-c:a", "aac",
                   "-shortest",
                   output_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            import shutil
            shutil.copy2(video_path, output_path)
    finally:
        if os.path.exists(music_path):
            os.unlink(music_path)
    return output_path
