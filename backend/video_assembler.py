import requests
import json
import sys
import os
import re
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
import tempfile

PIXABAY_API_KEY = "55575290-329752efa37512543a3df3950"

def download_video(url, output_path):
    """Download a video from URL"""
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path

def trim_video(input_path, output_path, duration):
    """Trim video to exact duration"""
    clip = VideoFileClip(input_path)
    trimmed = clip.subclipped(0, min(duration, clip.duration))
    trimmed.write_videofile(output_path, logger=None)
    clip.close()
    trimmed.close()
    return output_path

def add_voiceover(video_path, text, output_path):
    """Add text-to-speech voiceover to video"""
    # Generate voiceover
    tts = gTTS(text, lang='en')
    audio_path = tempfile.mktemp(suffix='.mp3')
    tts.save(audio_path)
    
    # Load video and audio
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    # Trim audio to match video length if needed
    if audio.duration > video.duration:
        audio = audio.subclipped(0, video.duration)
    
    # Set audio and save
    final = video.with_audio(audio)
    final.write_videofile(output_path, logger=None)
    
    # Cleanup
    video.close()
    audio.close()
    final.close()
    os.remove(audio_path)
    
    return output_path

def add_text_overlay(video_path, text, output_path):
    """Add text overlay to video"""
    video = VideoFileClip(video_path)
    
    # Create text clip
    txt_clip = TextClip(
        text=text,
        font_size=24,
        color='white',
        bg_color='black',
        duration=video.duration,
        font='Arial'
    )
    txt_clip = txt_clip.with_position(('center', 'bottom')).with_duration(video.duration)
    
    # Overlay text
    final = CompositeVideoClip([video, txt_clip])
    final.write_videofile(output_path, logger=None)
    
    video.close()
    txt_clip.close()
    final.close()
    
    return output_path

def concatenate_clips(clip_paths, output_path):
    """Stitch multiple videos together"""
    clips = [VideoFileClip(path) for path in clip_paths]
    final = concatenate_videoclips(clips)
    final.write_videofile(output_path, logger=None)
    
    for clip in clips:
        clip.close()
    final.close()
    
    return output_path

def search_pixabay_videos(keyword, per_page=5):
    """Search for videos on Pixabay"""
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={keyword}&per_page={per_page}&video_type=film"
    response = requests.get(url)
    data = response.json()
    
    videos = []
    for hit in data.get('hits', []):
        video_url = hit['videos'].get('medium', {}).get('url') or hit['videos'].get('small', {}).get('url')
        if video_url:
            videos.append({
                'url': video_url,
                'duration': hit.get('duration', 0),
                'tags': hit.get('tags', '')
            })
    return videos

def extract_keywords(prompt):
    """Extract meaningful keywords from prompt"""
    stop_words = {'a', 'an', 'the', 'of', 'and', 'or', 'but', 'so', 'for', 'nor', 'yet',
                  'with', 'without', 'by', 'in', 'on', 'at', 'to', 'for', 'from', 'up',
                  'down', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
                  'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
                  'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                  'than', 'that', 'then', 'these', 'those', 'through', 'until', 'unto',
                  'very', 'just', 'but', 'do', 'does', 'doing', 'did', 'done'}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', prompt.lower())
    keywords = [w for w in words if w not in stop_words]
    
    return keywords[:3] if keywords else ['nature']

def create_edited_video(topic, scenes=None):
    """Create an edited video from a topic"""
    print(f"Creating edited video for: {topic}")
    
    # Extract keywords
    keywords = extract_keywords(topic)
    search_term = keywords[0] if keywords else topic
    print(f"Search term: {search_term}")
    
    # Search for videos
    videos = search_pixabay_videos(search_term, per_page=3)
    
    if not videos:
        print("No videos found")
        return None
    
    # Download and process videos
    temp_dir = tempfile.mkdtemp()
    processed_clips = []
    
    for i, video in enumerate(videos[:2]):  # Use up to 2 clips
        print(f"Processing clip {i+1}...")
        
        # Download
        raw_path = os.path.join(temp_dir, f'raw_{i}.mp4')
        download_video(video['url'], raw_path)
        
        # Trim to 4-5 seconds
        trimmed_path = os.path.join(temp_dir, f'trimmed_{i}.mp4')
        target_duration = min(5, video['duration'])
        trim_video(raw_path, trimmed_path, target_duration)
        
        processed_clips.append(trimmed_path)
    
    # Concatenate clips
    if len(processed_clips) > 1:
        concat_path = os.path.join(temp_dir, 'concatenated.mp4')
        concatenate_clips(processed_clips, concat_path)
        final_video_path = concat_path
    else:
        final_video_path = processed_clips[0]
    
    # Add voiceover
    voiced_path = os.path.join(temp_dir, 'with_voice.mp4')
    add_voiceover(final_video_path, topic, voiced_path)
    
    # Add text overlay
    final_path = os.path.join(temp_dir, 'final_edited.mp4')
    add_text_overlay(voiced_path, f"✨ {topic}", final_path)
    
    print(f"✅ Video created: {final_path}")
    return final_path

if __name__ == "__main__":
    # For command line testing
    topic = sys.argv[1] if len(sys.argv) > 1 else "nature"
    output = create_edited_video(topic)
    
    if output:
        print(f"SUCCESS: {output}")
    else:
        print("FAILED: Could not create video")
        sys.exit(1)
