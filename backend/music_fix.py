def add_music_simple(video_path, music_url, output_path):
    if not music_url or music_url in ["null", "None", ""]:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Download music to same directory as video
    music_path = video_path.replace('.mp4', '_music.mp3')
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
