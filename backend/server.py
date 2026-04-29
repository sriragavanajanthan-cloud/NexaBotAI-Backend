from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PIXABAY_API_KEY = os.environ.get('PIXABAY_API_KEY', '55575290-329752efa37512543a3df3950')

@app.route('/search', methods=['GET'])
def search_videos():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page=12&video_type=film"
    response = requests.get(url)
    data = response.json()
    
    videos = []
    for hit in data.get("hits", []):
        video_url = hit["videos"].get("medium", {}).get("url") or hit["videos"].get("small", {}).get("url")
        if video_url:
            videos.append({
                "url": video_url,
                "duration": hit.get("duration", 0),
                "width": hit["videos"]["medium"].get("width", 0),
                "height": hit["videos"]["medium"].get("height", 0)
            })
    
    return jsonify({"videos": videos})

@app.route('/assemble', methods=['POST'])
def assemble_video():
    try:
        data = request.json
        topic = data.get('topic', '')
        
        url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={topic}&per_page=3&video_type=film"
        response = requests.get(url)
        result = response.json()
        
        if result.get("hits") and len(result["hits"]) > 0:
            video = result["hits"][0]
            video_url = video["videos"].get("medium", {}).get("url") or video["videos"].get("small", {}).get("url")
            return jsonify({
                "video_url": video_url,
                "duration": video.get("duration", 0),
                "message": f"Found video for: {topic}"
            })
        else:
            return jsonify({"error": "No videos found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
