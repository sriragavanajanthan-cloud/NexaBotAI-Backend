import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import time
from supabase import create_client
from video_assembler import get_video_options, create_video_from_option

app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
CLEANUP_SECRET = os.environ.get("CLEANUP_SECRET", "default-secret-change-me")

QUALITY_SETTINGS = {
    "draft": {"label": "540p", "crf": 32, "preset": "fast"},
    "standard": {"label": "720p", "crf": 28, "preset": "fast"},
    "hd": {"label": "1080p", "crf": 23, "preset": "medium"},
    "cinematic": {"label": "1080p", "crf": 23, "preset": "medium"}
}

# Rate limiting - only allow 1 request at a time
processing_lock = False

@app.route('/options', methods=['POST', 'OPTIONS'])
def get_options():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    topic = data.get('topic', '')
    max_options = data.get('max_options', 6)
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    opts = get_video_options(topic, max_options=max_options)
    return jsonify({"options": opts})

@app.route('/assemble', methods=['POST', 'OPTIONS'])
def assemble():
    global processing_lock
    
    if request.method == 'OPTIONS':
        return '', 200
    
    # Prevent concurrent processing (memory protection)
    if processing_lock:
        return jsonify({"error": "Server busy, please try again in a few seconds"}), 429
    
    data = request.json
    topic = data.get('topic', '')
    video_url = data.get('video_url', '')
    duration = data.get('duration', 5)
    quality = data.get('quality', 'standard')
    music_url = data.get('music', None)
    text_overlay = data.get('text_overlay', None)
    
    if not topic or not video_url:
        return jsonify({"error": "Missing topic or video_url"}), 400
    
    if duration < 2 or duration > 30:
        return jsonify({"error": "Duration must be between 2 and 30 seconds"}), 400
    
    # Set lock
    processing_lock = True
    
    try:
        quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["standard"])
        
        print(f"Processing: {duration}s, quality: {quality}")
        
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
            "resolution": quality_settings["label"],
            "message": "Video created"
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        processing_lock = False
        import gc
        gc.collect()

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({"status": "ok", "message": "Video API is running"})

if __name__ == '__main__':
    app.run(port=5001, debug=False, threaded=False)
