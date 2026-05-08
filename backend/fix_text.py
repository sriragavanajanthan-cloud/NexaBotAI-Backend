def add_text_simple(video_path, text, output_path):
    if not text:
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    text_escaped = text.replace("'", "'\\\\''")
    
    # Use a system font that exists on macOS
    # Common fonts: /System/Library/Fonts/Helvetica.ttc or use default
    cmd = [FFMPEG_PATH, "-y", "-i", video_path,
           "-vf", f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20:fontfile=/System/Library/Fonts/Helvetica.ttc",
           "-codec:a", "copy", output_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: try without fontfile
        cmd2 = [FFMPEG_PATH, "-y", "-i", video_path,
                "-vf", f"drawtext=text='{text_escaped}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:x=(w-text_w)/2:y=h-text_h-20",
                "-codec:a", "copy", output_path]
        subprocess.run(cmd2, capture_output=True)
    
    return output_path
