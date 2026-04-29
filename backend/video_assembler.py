import requests
import sys

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

def fetch_pixabay_clip(keyword):
    # per_page must be between 3 and 200
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page=3&video_type=film"
    print(f"Requesting: {url}")
    
    try:
        response = requests.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
            
        data = response.json()
        
        if data.get("hits") and len(data["hits"]) > 0:
            # Take the first video from results
            video = data["hits"][0]
            # Try to get medium quality, fallback to small
            video_url = video["videos"].get("medium", {}).get("url")
            if not video_url:
                video_url = video["videos"].get("small", {}).get("url")
            return video_url
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "nature"
    print(f"Searching for: {topic}")
    
    video_url = fetch_pixabay_clip(topic)
    
    if video_url:
        print(f"SUCCESS: {video_url}")
    else:
        print("FAILED: No video found")
        sys.exit(1)
