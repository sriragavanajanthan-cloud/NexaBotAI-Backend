def add_text_simple(video_path, text, output_path):
    # Skip text overlay - just copy original
    import shutil
    shutil.copy2(video_path, output_path)
    return output_path
