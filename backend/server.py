from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import datetime
from video_assembler import get_video_options, create_video_from_option
from supabase import create_client

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
CLEANUP_SECRET = os.environ.get("CLEANUP_SECRET", "default-secret-change-me")

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
    if not topic or not video_url:
        return jsonify({"error": "Missing topic or video_url"}), 400
    try:
        video_path = create_video_from_option(video_url, topic, duration)
        return jsonify({"video_url": video_path, "duration": duration, "message": "Video created"})
    except Exception as e:
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
        created = datetime.datetime.fromisoformat(file['created_at'].replace('Z', '+00:00'))
        age = (now - created).total_seconds()
        if age > 86400:  # 24 hours
            supabase.storage.from_(bucket).remove([file['name']])
            deleted += 1
    return jsonify({"deleted": deleted}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
