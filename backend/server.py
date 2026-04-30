from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import math

app = Flask(__name__)
CORS(app)

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

# Quality to resolution mapping
QUALITY_SETTINGS = {
    "draft": {"min_width": 640, "min_height": 360, "max_width": 1280, "max_height": 720},
    "standard": {"min_width": 1280, "min_height": 720, "max_width": 1920, "max_height": 1080},
    "hd": {"min_width": 1920, "min_height": 1080, "max_width": 2560, "max_height": 1440},
    "cinematic": {"min_width": 1920, "min_height": 1080, "max_width": 3840, "max_height": 2160}
}

# Style to tag mapping
STYLE_TAGS = {
    "cinematic": ["cinematic", "dramatic", "film", "movie"],
    "realistic": ["real", "natural", "authentic", "photorealistic"],
    "anime": ["anime", "animation", "cartoon", "illustration"],
    "cyberpunk": ["cyberpunk", "futuristic", "neon", "tech", "digital"],
    "vintage": ["vintage", "retro", "old", "classic", "nostalgic"],
    "fantasy": ["fantasy", "magical", "dreamy", "ethereal", "whimsical"]
}

def extract_keywords(prompt, style_id=None):
    """Extract relevant keywords from a prompt, optionally adding style tags"""
    filler_words = ['a', 'an', 'the', 'of', 'and', 'or', 'but', 'so', 'for', 'nor', 'yet',
                    'with', 'without', 'by', 'in', 'on', 'at', 'to', 'for', 'from', 'up',
                    'down', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
                    'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
                    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                    'than', 'that', 'then', 'these', 'those', 'through', 'until', 'unto',
                    'very', 'just', 'but', 'do', 'does', 'doing', 'did', 'done', 'be',
                    'being', 'been', 'am', 'are', 'is', 'was', 'were', 'has', 'have',
                    'having', 'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must']
    
    # Clean and split
    words = re.findall(r'\b[a-zA-Z]+\b', prompt.lower())
    keywords = [w for w in words if w not in filler_words and len(w) > 2]
    
    # Add style tags if provided
    if style_id and style_id in STYLE_TAGS:
        keywords.extend(STYLE_TAGS[style_id])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)
    
    return unique_keywords[:5]

def find_best_video(videos, target_duration, quality_id, style_id):
    """Find the best matching video based on duration, quality, and style"""
    quality = QUALITY_SETTINGS.get(quality_id, QUALITY_SETTINGS["standard"])
    style_tags = STYLE_TAGS.get(style_id, [])
    
    scored_videos = []
    for video in videos:
        score = 0
        duration = video.get("duration", 0)
        tags = video.get("tags", "").lower()
        
        # Duration score: prefer videos slightly longer than target
        if duration >= target_duration:
            # Perfect or longer video
            score += min(100, int((target_duration / duration) * 100))
        else:
            # Too short
            score += int((duration / target_duration) * 50)
        
        # Quality score based on resolution
        width = video.get("width", 0)
        height = video.get("height", 0)
        if width >= quality["min_width"] and height >= quality["min_height"]:
            score += 100
        elif width >= quality["min_width"]//2 and height >= quality["min_height"]//2:
            score += 50
        else:
            score += 20
        
        # Style score: check if tags match style keywords
        if style_tags:
            tag_score = 0
            for tag in style_tags:
                if tag in tags:
                    tag_score += 25
            score += min(tag_score, 100)
        
        scored_videos.append((score, video))
    
    # Sort by score descending and return best
    scored_videos.sort(reverse=True, key=lambda x: x[0])
    return scored_videos[0][1] if scored_videos else None

@app.route('/search', methods=['GET'])
def search_videos():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    # Extract keywords
    keywords = extract_keywords(query)
    search_term = ' '.join(keywords[:3]) if keywords else query
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page=20&video_type=film"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        videos = []
        for hit in data.get("hits", []):
            video_url = hit["videos"].get("medium", {}).get("url") or hit["videos"].get("small", {}).get("url")
            if video_url:
                videos.append({
                    "url": video_url,
                    "duration": hit.get("duration", 0),
                    "width": hit["videos"]["medium"].get("width", 1920),
                    "height": hit["videos"]["medium"].get("height", 1080),
                    "tags": hit.get("tags", "")
                })
        
        return jsonify({"videos": videos[:12], "search_term": search_term})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/assemble', methods=['POST'])
def assemble_video():
    try:
        data = request.json
        topic = data.get('topic', '')
        quality_id = data.get('quality', 'standard')
        fps = data.get('fps', 24)
        target_duration = data.get('duration', 5)
        style_id = data.get('style', 'cinematic')
        aspect_ratio = data.get('aspectRatio', '16:9')
        
        if not topic:
            return jsonify({"error": "No topic provided"}), 400
        
        # Extract keywords with style
        keywords = extract_keywords(topic, style_id)
        search_term = ' '.join(keywords[:4]) if keywords else topic
        
        # Get videos from Pixabay
        url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={search_term}&per_page=20&video_type=film"
        response = requests.get(url)
        result = response.json()
        
        if not result.get("hits"):
            # Fallback: try with fewer keywords
            fallback_term = keywords[0] if keywords else topic.split()[0]
            url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={fallback_term}&per_page=20&video_type=film"
            response = requests.get(url)
            result = response.json()
        
        hits = result.get("hits", [])
        
        if hits:
            # Find best matching video based on all criteria
            best_video = find_best_video(hits, target_duration, quality_id, style_id)
            
            if best_video:
                video_url = best_video["videos"].get("medium", {}).get("url") or best_video.get("url")
                if not video_url and "videos" in best_video:
                    video_url = best_video["videos"].get("small", {}).get("url")
                
                return jsonify({
                    "video_url": video_url,
                    "duration": best_video.get("duration", target_duration),
                    "fps": fps,
                    "quality": quality_id,
                    "style": style_id,
                    "aspect_ratio": aspect_ratio,
                    "search_term": search_term,
                    "keywords_used": keywords,
                    "message": f"Found matching video for: {topic}"
                })
        
        return jsonify({"error": f"No suitable video found for '{topic}'. Try different keywords."}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Video API is running"})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
