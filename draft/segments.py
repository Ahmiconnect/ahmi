import os
import json
import subprocess
from typing import List, Dict
from shutil import which

CLIPS_DIR = "clips"
SEGMENTS_DIR = "segments"
TRANSCRIPTIONS_DIR = "temp_transcriptions"

def validate_environment():
    """Check required directories exist"""
    if not os.path.exists(CLIPS_DIR):
        raise FileNotFoundError(f"Clips directory '{CLIPS_DIR}' not found")
    if not os.path.exists(TRANSCRIPTIONS_DIR):
        raise FileNotFoundError(f"Transcriptions directory '{TRANSCRIPTIONS_DIR}' not found")
    os.makedirs(SEGMENTS_DIR, exist_ok=True)

def get_clips_for_keyword(keyword: str) -> List[str]:
    """Get all MP4 clips from a keyword folder"""
    keyword_dir = os.path.join(CLIPS_DIR, keyword)
    if not os.path.exists(keyword_dir):
        raise FileNotFoundError(f"No clips found for keyword '{keyword}'")
    
    clips = [os.path.join(keyword_dir, f) 
             for f in os.listdir(keyword_dir) 
             if f.lower().endswith('.mp4')]
    
    if not clips:
        raise ValueError(f"No MP4 clips found in {keyword_dir}")
    
    return clips

def create_segment(clips: List[str], duration: float, output_path: str):
    """Concatenate clips to create a segment of exact duration"""
    # Create temporary list file for ffmpeg concat
    list_file = "temp_clips.txt"
    with open(list_file, 'w') as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")
    
    # First concatenate all clips
    temp_output = "temp_concat.mp4"
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        temp_output
    ]
    subprocess.run(cmd, check=True)
    
    # Then trim to exact duration
    cmd = [
        'ffmpeg',
        '-y',
        '-i', temp_output,
        '-t', str(duration),
        '-c', 'copy',
        output_path
    ]
    subprocess.run(cmd, check=True)
    
    # Cleanup
    os.remove(list_file)
    os.remove(temp_output)

def process_segments(json_path: str):
    """Process a single JSON file into video segments"""
    base_name = os.path.splitext(os.path.basename(json_path))[0].replace('_segments', '')
    
    with open(json_path) as f:
        segments_data = json.load(f)
    
    for i, segment in enumerate(segments_data):
        keyword = segment['Folder']
        duration = segment['endtime'] - segment['starttime']
        
        # Get all clips for this keyword
        try:
            clips = get_clips_for_keyword(keyword)
        except Exception as e:
            print(f"Skipping segment {i} for {base_name}: {str(e)}")
            continue
        
        # Create output filename
        output_file = os.path.join(SEGMENTS_DIR, f"{base_name}_segment_{i}_{keyword}.mp4")
        
        # Create the segment
        print(f"Creating segment {i} for {base_name} ({duration:.2f}s from {keyword} clips)")
        create_segment(clips, duration, output_file)

def main():
    """Main processing pipeline"""
    try:
        validate_environment()
        
        # Process all JSON files in transcriptions directory
        json_files = [os.path.join(TRANSCRIPTIONS_DIR, f) 
                     for f in os.listdir(TRANSCRIPTIONS_DIR) 
                     if f.endswith('.json')]
        
        if not json_files:
            print("No JSON files found in transcriptions directory")
            return
        
        for json_file in json_files:
            print(f"\nProcessing {json_file}")
            process_segments(json_file)
        
        print("\nAll segments created successfully")
        
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    # Check ffmpeg is available
    if which("ffmpeg") is None:
        raise Exception("ffmpeg is not installed. Please install ffmpeg first.")
    
    main()