import requests

PIXABAY_KEY = "55575290-329752efa37512543a3df3950"

def search_videos(topic, max_options=6):
    """Search videos from Pixabay (working)"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={topic}&per_page={max_options}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        videos = []
        
        for hit in data.get('hits', []):
            vid = hit.get('videos', {})
            video_url = vid.get('medium', {}).get('url') or vid.get('small', {}).get('url')
            
            if video_url:
                videos.append({
                    'url': video_url,
                    'duration': hit.get('duration', 0),
                    'tags': hit.get('tags', ''),
                    'source': 'Pixabay'
                })
        
        return videos
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

# For backward compatibility
def search_pixabay(topic, max_options=6):
    return search_videos(topic, max_options)
