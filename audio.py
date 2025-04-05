import os
import json
import whisper
import string
from typing import List, Dict

MAX_AUDIO_FILES = 5
AUDIO_DIR = "audio"
OUTPUT_DIR = "temp_transcriptions"

def normalize_word(word: str) -> str:
    """Normalize words for consistent matching"""
    return word.strip().rstrip(string.punctuation).lower()

def process_audio_file(audio_path: str, keywords: List[str], audio_duration: float) -> List[Dict]:
    """Process single audio file and return keyword segments"""
    model = whisper.load_model("base")
    
    print(f"Transcribing {audio_path}...")
    transcription = model.transcribe(audio_path, word_timestamps=True)
    
    # First pass - find all keyword occurrences
    raw_timestamps = []
    for segment in transcription['segments']:
        for word in segment['words']:
            normalized_word = normalize_word(word['word'])
            if normalized_word in keywords:
                raw_timestamps.append({
                    'Folder': normalized_word,
                    'starttime': word['start']
                })
    
    # Process timestamps to create segments
    if not raw_timestamps:
        return []
    
    # Force first keyword to start at 0
    raw_timestamps[0]['starttime'] = 0.0
    
    # Calculate end times
    processed_timestamps = []
    for i in range(len(raw_timestamps)):
        current = raw_timestamps[i]
        next_start = raw_timestamps[i+1]['starttime'] if i+1 < len(raw_timestamps) else audio_duration
        processed_timestamps.append({
            'Folder': current['Folder'],
            'starttime': current['starttime'],
            'endtime': next_start
        })
    
    return processed_timestamps

def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file using whisper"""
    model = whisper.load_model("tiny")  # Lightweight just for duration
    result = model.transcribe(audio_path)
    return result['segments'][-1]['end']

def validate_audio_files() -> List[str]:
    """Check audio directory and return valid MP4 files"""
    if not os.path.exists(AUDIO_DIR):
        raise FileNotFoundError(f"Audio directory '{AUDIO_DIR}' not found")
    
    audio_files = [
        os.path.join(AUDIO_DIR, f) 
        for f in os.listdir(AUDIO_DIR) 
        if f.lower().endswith('.mp4')
    ]
    
    if len(audio_files) > MAX_AUDIO_FILES:
        raise ValueError(f"Maximum {MAX_AUDIO_FILES} audio files allowed. Found {len(audio_files)}")
        
    if not audio_files:
        raise ValueError("No MP4 audio files found in audio directory")
        
    return audio_files

def save_segments(output_path: str, segments: List[Dict]):
    """Save segments data to JSON file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(segments, f, indent=2)

def main(keywords: List[str]):
    """Main processing pipeline"""
    try:
        audio_files = validate_audio_files()
        print(f"Found {len(audio_files)} audio files to process")
        
        for audio_file in audio_files:
            duration = get_audio_duration(audio_file)
            segments = process_audio_file(audio_file, keywords, duration)
            
            # Create output filename
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            output_file = os.path.join(OUTPUT_DIR, f"{base_name}_segments.json")
            
            save_segments(output_file, segments)  # Fixed variable name here
            print(f"Saved segments to {output_file}")
            
        print("Audio processing completed successfully")
        return True
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return False




if __name__ == "__main__":
    # Example keywords - will be passed from run.py in final version
    EXAMPLE_KEYWORDS = ["luffy", "naruto", "saitama", "goku", "ichigo", "gojo", "madara", "sukuna", "kakashi", "vegeta"]
    main(EXAMPLE_KEYWORDS)