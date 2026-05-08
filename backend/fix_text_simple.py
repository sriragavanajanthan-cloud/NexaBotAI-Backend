def add_text_simple(video_path, text, output_path):
    if not text:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # Simple text overlay without complex fonts
    cmd = ["ffmpeg", "-y", "-i", video_path,
           "-vf", f"drawtext=text='{text}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20",
           "-c:a", "copy", output_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0 or not os.path.exists(output_path):
        # If failed, just copy original
        import shutil
        shutil.copy2(video_path, output_path)
    
    return output_path
