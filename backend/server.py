from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import tempfile
from video_assembler import get_video_options, create_video_from_option

app = Flask(__name__)
CORS(app)

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page=12&video_type=film"
    response = requests.get(url)
    data = response.json()
    
    videos = []
    for hit in data.get('hits', []):
        video_url = hit['videos'].get('medium', {}).get('url') or hit['videos'].get('small', {}).get('url')
        if video_url:
            videos.append({
                "url": video_url,
                "duration": hit.get('duration', 0),
                "width": hit['videos']['medium'].get('width', 0),
                "height": hit['videos']['medium'].get('height', 0),
                "tags": hit.get('tags', '')
            })
    
    return jsonify({"videos": videos})

@app.route('/options', methods=['POST'])
def options():
    """Get video options for a topic"""
    data = request.json
    topic = data.get('topic', '')
    max_options = data.get('max_options', 6)
    
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    
    options = get_video_options(topic, max_options=max_options)
    return jsonify({"options": options})

@app.route('/assemble', methods=['POST'])
def assemble():
    """Create video from selected option"""
    data = request.json
    topic = data.get('topic', '')
    video_url = data.get('video_url', '')
    duration = data.get('duration', 5)
    
    if not topic or not video_url:
        return jsonify({"error": "Missing topic or video_url"}), 400
    
    try:
        output_path = create_video_from_option(video_url, topic, duration)
        
        # In production, you'd upload to cloud storage and return a public URL
        # For now, return a local path (or use a temporary public URL)
        return jsonify({
            "video_url": f"/download/{os.path.basename(output_path)}",
            "duration": duration,
            "message": "Video created successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Video API is running"})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
