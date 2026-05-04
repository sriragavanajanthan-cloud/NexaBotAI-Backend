import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
from supabase import create_client
from video_assembler import get_video_options, create_video_from_option

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
CLEANUP_SECRET = os.environ.get("CLEANUP_SECRET", "default-secret-change-me")

# Quality to resolution mapping
QUALITY_SETTINGS = {
    "draft": {"min_width": 640, "min_height": 360, "label": "540p", "crf": 32, "preset": "fast"},
    "standard": {"min_width": 1280, "min_height": 720, "label": "720p", "crf": 28, "preset": "fast"},
    "hd": {"min_width": 1920, "min_height": 1080, "label": "1080p", "crf": 23, "preset": "medium"},
    "cinematic": {"min_width": 1920, "min_height": 1080, "label": "1080p", "crf": 23, "preset": "medium"}
}

@app.route('/options', methods=['POST'])
def options():
    data = request.json
    topic = data.get('topic', '')
    max_options = data.get('max_options', 6)
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    opts = get_video_options(topic, max_options=max_options)
    return jsonify({"options": opts})

@app.route('/assemble', methods=['POST'])
def assemble():
    data = request.json
    topic = data.get('topic', '')
    video_url = data.get('video_url', '')
    duration = data.get('duration', 5)
    quality = data.get('quality', 'standard')
    aspect_ratio = data.get('aspectRatio', '16:9')
    style = data.get('style', 'cinematic')
    music_url = data.get('music', None)
    text_overlay = data.get('text_overlay', None)
    
    if not topic or not video_url:
        return jsonify({"error": "Missing topic or video_url"}), 400
    
    # Enforce memory-safe duration limit (30 seconds max for Render)
    if duration < 2:
        return jsonify({"error": "Duration must be at least 2 seconds"}), 400
    if duration > 30:
        return jsonify({"error": "Duration cannot exceed 30 seconds due to server memory limits"}), 400
    
    try:
        # Get quality settings
        quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["standard"])
        resolution = quality_settings["label"]
        
        print(f"Processing video: {duration}s, quality: {quality}, style: {style}")
        
        # Create the video with memory optimizations
        video_path = create_video_from_option(
            video_url=video_url,
            topic=topic,
            duration=duration,
            music_url=music_url,
            text_overlay=text_overlay,
            quality_settings=quality_settings
        )
        
        return jsonify({
            "video_url": video_path,
            "duration": duration,
            "resolution": resolution,
            "style": style,
            "message": "Video created successfully"
        })
    except Exception as e:
        print(f"Assembly error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    auth = request.headers.get('X-Cleanup-Secret')
    if auth != CLEANUP_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
    
    bucket = "video-outputs"
    try:
        files = supabase.storage.from_(bucket).list()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    now = datetime.datetime.utcnow()
    deleted = 0
    for file in files:
        try:
            created = datetime.datetime.fromisoformat(file['created_at'].replace('Z', '+00:00'))
            age = (now - created).total_seconds()
            if age > 86400:  # 24 hours
                supabase.storage.from_(bucket).remove([file['name']])
                deleted += 1
        except Exception:
            continue
    
    return str(deleted), 200, {'Content-Type': 'text/plain'}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Video API is running"})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
