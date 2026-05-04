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

CORS(app, resources={
    r"/*": {
        "origins": [
            "https://nexa-bot-ai.vercel.app",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Cleanup-Secret"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

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
    response.headers.add('Access-Control-Allow-Origin', 'https://nexa-bot-ai.vercel.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Cleanup-Secret')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/search-music', methods=['POST', 'OPTIONS'])
def search_music():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    query = data.get('query', '')
    mood = data.get('mood', 'upbeat')
    
    PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"
    
    mood_terms = {
        'upbeat': 'upbeat energetic',
        'cinematic': 'cinematic orchestral',
        'calm': 'calm relaxing meditation',
        'inspiring': 'inspiring motivational',
        'corporate': 'corporate business'
    }
    
    search_term = mood_terms.get(mood, query) if not query else query
    url = f"https://pixabay.com/api/music/?key={PIXABAY_API_KEY}&q={search_term}&per_page=8"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        music_tracks = []
        for hit in data.get('hits', []):
            music_tracks.append({
                'id': hit.get('id'),
                'title': hit.get('title'),
                'url': hit.get('audio'),
                'duration': hit.get('duration'),
                'tags': hit.get('tags', ''),
                'artist': hit.get('user', 'Pixabay')
            })
        
        return jsonify({"tracks": music_tracks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            "message": "Video created"
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/assemble-multi', methods=['POST', 'OPTIONS'])
def assemble_multi():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    video_urls = data.get('video_urls', [])
    duration_per_clip = data.get('duration_per_clip', 5)
    quality = data.get('quality', 'standard')
    
    if not video_urls or len(video_urls) < 2:
        return jsonify({"error": "Need at least 2 video URLs"}), 400
    
    quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["standard"])
    
    try:
        from video_assembler import create_multi_clip_video
        video_path = create_multi_clip_video(
            video_urls=video_urls,
            topic="multi_clip_video",
            duration_per_clip=duration_per_clip,
            quality_settings=quality_settings
        )
        return jsonify({"video_url": video_path, "message": "Multi-clip video created"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add-effect', methods=['POST', 'OPTIONS'])
def add_effect():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    video_url = data.get('video_url', '')
    effect = data.get('effect', 'ken_burns')
    speed = data.get('speed', 0.5)
    
    if not video_url:
        return jsonify({"error": "Missing video_url"}), 400
    
    import tempfile
    from video_assembler import download_file, add_ken_burns_effect, adjust_speed
    import uuid
    
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, 'input.mp4')
    download_file(video_url, input_path)
    
    output_path = os.path.join(temp_dir, 'output.mp4')
    
    if effect == 'ken_burns':
        add_ken_burns_effect(input_path, output_path, zoom=0.1)
    elif effect == 'slow_motion':
        adjust_speed(input_path, output_path, speed_factor=speed)
    elif effect == 'time_lapse':
        adjust_speed(input_path, output_path, speed_factor=speed)
    else:
        return jsonify({"error": f"Unknown effect: {effect}"}), 400
    
    bucket = "video-outputs"
    unique_name = f"{uuid.uuid4()}.mp4"
    with open(output_path, 'rb') as f:
        supabase.storage.from_(bucket).upload(unique_name, f)
    
    public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
    
    os.unlink(input_path)
    os.unlink(output_path)
    os.rmdir(temp_dir)
    
    return jsonify({"video_url": public_url, "effect": effect})

@app.route('/cleanup', methods=['POST', 'OPTIONS'])
def cleanup():
    if request.method == 'OPTIONS':
        return '', 200
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
            if age > 86400:
                supabase.storage.from_(bucket).remove([file['name']])
                deleted += 1
        except Exception:
            continue
    
    return str(deleted), 200, {'Content-Type': 'text/plain'}

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({"status": "ok", "message": "Video API is running"})

if __name__ == '__main__':
    app.run(port=5001, debug=False, threaded=False)
