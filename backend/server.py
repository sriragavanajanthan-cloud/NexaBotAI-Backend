import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import time
import requests
import uuid
from supabase import create_client
from video_assembler import get_video_options, create_video_from_option, create_multi_clip_video
from video_search import search_by_mood, search_with_smart_query

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["*"], supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

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

@app.route('/search-music', methods=['GET', 'POST', 'OPTIONS'])
def search_music():
    if request.method == 'OPTIONS':
        return '', 200
    from music_library import get_tracks_by_mood, get_track_info, LIBRARY_STATS
    if request.method == 'GET':
        mood = request.args.get('mood', 'upbeat')
    else:
        data = request.json or {}
        mood = data.get('mood', 'upbeat')
    track_urls = get_tracks_by_mood(mood, limit=10)
    tracks = [{'id': i, 'title': get_track_info(url), 'url': url, 'duration': 120, 'artist': 'Mixkit/SoundHelix', 'license': 'Royalty-Free for Commercial Use'} for i, url in enumerate(track_urls)]
    return jsonify({"tracks": tracks, "count": len(tracks), "source": "Mixkit + SoundHelix Library", "total_available": LIBRARY_STATS['total_tracks'], "moods_available": LIBRARY_STATS['moods']})

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({"status": "ok", "message": "Video API running", "endpoints": ["/search-music", "/options", "/assemble", "/assemble-multi", "/add-effect", "/health"], "supabase_configured": bool(supabase)})

@app.route('/options', methods=['POST', 'OPTIONS'])
def get_options_route():
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
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
    try:
        quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["standard"])
        video_path = create_video_from_option(video_url=video_url, topic=topic, duration=duration, music_url=music_url, text_overlay=text_overlay, quality_settings=quality_settings)
        return jsonify({"video_url": video_path, "duration": duration, "resolution": quality_settings["label"], "message": "Video created successfully"})
    except Exception as e:
        print(f"Assembly error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/assemble-multi', methods=['POST', 'OPTIONS'])
def assemble_multi():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    video_urls = data.get('video_urls', [])
    duration_per_clip = data.get('duration_per_clip', 3)
    if not video_urls or len(video_urls) < 2:
        return jsonify({"error": "Need at least 2 video URLs"}), 400
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
    try:
        # Clean up temp dirs first
        import tempfile
        tempfile.tempdir = None
        video_path = create_multi_clip_video(video_urls=video_urls, topic="multi_clip", duration_per_clip=duration_per_clip)
        return jsonify({"video_url": video_path, "message": f"Multi-clip video created with {len(video_urls)} clips"})
    except Exception as e:
        import time
        time.sleep(1)
        try:
            video_path = create_multi_clip_video(video_urls=video_urls, topic="multi_clip", duration_per_clip=duration_per_clip)
            return jsonify({"video_url": video_path, "message": f"Multi-clip video created with {len(video_urls)} clips"})
        except Exception as e2:
            return jsonify({"error": str(e2)}), 500

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
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500
    import tempfile
    from video_assembler import download_file
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, 'input.mp4')
    output_path = os.path.join(temp_dir, 'output.mp4')
    try:
        download_file(video_url, input_path)
        if effect == 'ken_burns':
            from video_assembler import add_ken_burns_effect
            add_ken_burns_effect(input_path, output_path, zoom=0.1)
        elif effect == 'slow_motion':
            from video_assembler import adjust_speed
            adjust_speed(input_path, output_path, speed_factor=speed)
        elif effect == 'time_lapse':
            from video_assembler import adjust_speed
            adjust_speed(input_path, output_path, speed_factor=speed)
        else:
            return jsonify({"error": "Effect must be ken_burns, slow_motion, or time_lapse"}), 400
        bucket = "video-outputs"
        unique_name = f"effect_{effect}_{uuid.uuid4()}.mp4"
        with open(output_path, 'rb') as f:
            supabase.storage.from_(bucket).upload(unique_name, f, file_options={"content-type": "video/mp4"})
        public_url = supabase.storage.from_(bucket).get_public_url(unique_name)
        return jsonify({"video_url": public_url, "effect": effect})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
        os.rmdir(temp_dir)

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



@app.route('/search', methods=['POST', 'OPTIONS'])
def smart_search():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    query = data.get('query', '')
    mood = data.get('mood', None)
    max_results = data.get('max_results', 8)
    
    if not query and not mood:
        return jsonify({"error": "Provide query or mood"}), 400
    
    if mood:
        videos = search_by_mood(mood, max_results)
    else:
        videos = search_with_smart_query(query, max_results)
    
    return jsonify({
        "videos": videos,
        "count": len(videos),
        "query": query or mood
    })


if __name__ == '__main__':
    app.run(port=5001, debug=False, threaded=False)
