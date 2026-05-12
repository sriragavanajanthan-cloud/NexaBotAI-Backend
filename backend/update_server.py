# Add to server.py imports
import sys
with open('server.py', 'r') as f:
    content = f.read()

if 'from video_search import' not in content:
    content = content.replace(
        'from video_assembler import get_video_options, create_video_from_option, create_multi_clip_video',
        'from video_assembler import get_video_options, create_video_from_option, create_multi_clip_video\nfrom video_search import search_by_mood, search_with_smart_query'
    )
    
    # Add new endpoint for smart search
    smart_endpoint = '''

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
'''
    
    # Insert before if __name__
    content = content.replace('if __name__ ==', smart_endpoint + '\n\nif __name__ ==')
    
    with open('server.py', 'w') as f:
        f.write(content)
    print("✅ Added smart search endpoint")
