import requests
import re
from collections import defaultdict

PIXABAY_KEY = "55575290-329752efa37512543a3df3950"

# Video quality preferences
QUALITY_PREFERENCES = {
    'best': 'large',
    'hd': 'medium',
    'mobile': 'small'
}

def search_pixabay(topic, max_results=10, min_duration=3, max_duration=30):
    """Search Pixabay with duration filters"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={topic}&per_page={max_results}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        videos = []
        
        for hit in data.get('hits', []):
            duration = hit.get('duration', 0)
            
            # Filter by duration
            if duration < min_duration or duration > max_duration:
                continue
            
            vid = hit.get('videos', {})
            
            # Get best available quality
            for quality in ['large', 'medium', 'small']:
                if quality in vid:
                    video_url = vid[quality].get('url')
                    if video_url:
                        break
            
            if video_url:
                videos.append({
                    'url': video_url,
                    'duration': duration,
                    'tags': hit.get('tags', ''),
                    'views': hit.get('views', 0),
                    'likes': hit.get('likes', 0),
                    'downloads': hit.get('downloads', 0),
                    'user': hit.get('user', ''),
                    'source': 'Pixabay'
                })
        
        # Sort by popularity (views + likes)
        videos.sort(key=lambda x: x['views'] + x['likes'] * 10, reverse=True)
        
        return videos
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

def search_multiple_topics(topics, max_per_topic=3):
    """Search multiple related topics"""
    all_videos = []
    
    for topic in topics:
        videos = search_pixabay(topic, max_per_topic)
        all_videos.extend(videos)
    
    # Remove duplicates by URL
    seen = set()
    unique_videos = []
    for video in all_videos:
        if video['url'] not in seen:
            seen.add(video['url'])
            unique_videos.append(video)
    
    return unique_videos[:10]

def search_by_mood(mood, max_results=8):
    """Map mood to search terms"""
    mood_terms = {
        'cinematic': ['epic', 'dramatic', 'cinematic', 'movie'],
        'upbeat': ['happy', 'energetic', 'upbeat', 'positive'],
        'calm': ['peaceful', 'relaxing', 'calm', 'nature'],
        'inspiring': ['motivational', 'inspiring', 'success', 'hope'],
        'corporate': ['business', 'corporate', 'office', 'technology']
    }
    
    terms = mood_terms.get(mood, [mood])
    return search_multiple_topics(terms, max_per_topic=max_results)

def search_with_smart_query(topic, max_results=8):
    """Extract keywords and search smarter"""
    # Remove common words
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could', 'should', 'a', 'an', 'of', 'to', 'in', 'on', 'at', 'by'}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', topic.lower())
    keywords = [w for w in words if w not in stop_words]
    
    # Try different combinations
    search_terms = []
    
    # Original topic
    search_terms.append(topic)
    
    # Top 2 keywords
    if len(keywords) >= 2:
        search_terms.append(' '.join(keywords[:2]))
    
    # First keyword only
    if keywords:
        search_terms.append(keywords[0])
    
    # Search with multiple terms
    all_videos = []
    for term in search_terms[:3]:
        videos = search_pixabay(term, max_results=3)
        all_videos.extend(videos)
    
    # Remove duplicates
    seen = set()
    unique = []
    for v in all_videos:
        if v['url'] not in seen:
            seen.add(v['url'])
            unique.append(v)
    
    return unique[:max_results]
