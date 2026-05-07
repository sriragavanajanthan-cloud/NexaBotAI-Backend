import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import time
import requests
from supabase import create_client
from video_assembler import get_video_options, create_video_from_option
from music_library import get_tracks_by_mood, get_track_info, LIBRARY_STATS

app = Flask(__name__)

# Enable CORS for all routes with proper configuration
CORS(app, 
     resources={r"/*": {"origins": "*"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Cleanup-Secret"],
     expose_headers=["Content-Type"],
     supports_credentials=True)

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

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Cleanup-Secret'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/search-music', methods=['GET', 'POST', 'OPTIONS'])
def search_music():
    if request.method == 'OPTIONS':
        return '', 200
    
    if request.method == 'GET':
        mood = request.args.get('mood', 'upbeat')
    else:
        data = request.json or {}
        mood = data.get('mood', 'upbeat')
    
    track_urls = get_tracks_by_mood(mood, limit=10)
    
    tracks = []
    for i, url in enumerate(track_urls):
        tracks.append({
            'id': i,
            'title': get_track_info(url),
            'url': url,
            'duration': 120,
            'artist': 'Mixkit/SoundHelix',
            'license': 'Royalty-Free for Commercial Use'
        })
    
    return jsonify({
        "tracks": tracks,
        "count": len(tracks),
        "source": "Mixkit + SoundHelix Library",
        "total_available": LIBRARY_STATS['total_tracks'],
        "moods_available": LIBRARY_STATS['moods']
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        "status": "ok",
        "message": "Video API is running with local music library",
        "endpoints": ["/search-music", "/options", "/assemble", "/health"],
        "music_source": "Mixkit + SoundHelix",
        "total_tracks": LIBRARY_STATS['total_tracks'],
        "moods_available": LIBRARY_STATS['moods'],
        "supabase_configured": bool(supabase)
    })

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
    if request.method == 'OPTIONS':
        return '', 200
    
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
    
    if music_url and music_url.startswith('/'):
        music_url = None
    
    # Check Supabase configuration
    if not supabase:
        return jsonify({
            "error": "Supabase not configured",
            "note": "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables"
        }), 500
    
    try:
        quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["standard"])
        
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
            "message": "Video created successfully"
        })
    except Exception as e:
        print(f"Assembly error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=False, threaded=False)
