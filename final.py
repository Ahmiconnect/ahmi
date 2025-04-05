import os
import subprocess
from shutil import which
from typing import List, Dict
from ahmi import AnimeVideoNamer  # Import your custom namer

SEGMENTS_DIR = "segments"
AUDIO_DIR = "audio"
MUSIC_PATH = "music/music.mp3"
OUTPUT_DIR = "final_videos"

def validate_environment():
    """Check required directories and files exist"""
    if not os.path.exists(SEGMENTS_DIR):
        raise FileNotFoundError(f"Segments directory '{SEGMENTS_DIR}' not found")
    if not os.path.exists(AUDIO_DIR):
        raise FileNotFoundError(f"Audio directory '{AUDIO_DIR}' not found")
    if not os.path.exists(MUSIC_PATH):
        raise FileNotFoundError(f"Music file '{MUSIC_PATH}' not found")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_audio_file(segment_base: str) -> str:
    """Find matching audio file for segment"""
    audio_base = segment_base.split('_segment_')[0]
    
    for f in os.listdir(AUDIO_DIR):
        if f.startswith(audio_base) and f.endswith('.mp4'):
            return os.path.join(AUDIO_DIR, f)
    
    raise FileNotFoundError(f"No matching audio found for segment {segment_base}")

def get_segment_entries(segment_group: List[str]) -> List[Dict]:
    """Extract metadata entries from segment filenames"""
    entries = []
    for seg in segment_group:
        parts = seg.split('_')
        if len(parts) >= 4:  # format: {base}_segment_{num}_{keyword}.mp4
            entries.append({
                "Folder": parts[3].replace('.mp4', ''),
                "starttime": 0,  # Not used in naming
                "endtime": 0     # Not used in naming
            })
    return entries

def process_video_group(segment_group: List[str]):
    """Process one group of segments into final video"""
    base_name = segment_group[0].split('_segment_')[0]
    
    # Generate custom title using your AnimeVideoNamer
    namer = AnimeVideoNamer()
    entries = get_segment_entries(segment_group)
    title = namer.create_title(entries, for_filename=True)
    
    # Create filesystem-safe name
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_', '#') else '_' for c in title)
    output_file = os.path.join(OUTPUT_DIR, f"{safe_title}.mp4")
    
    # Get all segments in order
    segments = sorted(segment_group, key=lambda x: int(x.split('_')[2]))
    segment_files = [os.path.join(SEGMENTS_DIR, s) for s in segments]
    
    # Get matching audio
    audio_file = get_audio_file(base_name)
    
    # Temporary files
    concat_list = "temp_concat.txt"
    video_no_audio = "temp_video_no_audio.mp4"
    
    # Create concatenation list
    with open(concat_list, 'w') as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
    
    # 1. Concatenate all segments
    concat_cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list,
        '-c:v', 'libx264',
        '-r', '30',  # Force 30 FPS
        '-preset', 'fast',
        '-crf', '23',
        '-an',  # No audio yet
        video_no_audio
    ]
    subprocess.run(concat_cmd, check=True)
    
    # 2. Process audio
    original_audio = "temp_original_audio.wav"
    audio_cmd = [
        'ffmpeg',
        '-y',
        '-i', audio_file,
        '-vn',
        '-acodec', 'pcm_s16le',
        original_audio
    ]
    subprocess.run(audio_cmd, check=True)
    
    # Process background music (10% volume)
    bg_music = "temp_bg_music.wav"
    music_cmd = [
        'ffmpeg',
        '-y',
        '-i', MUSIC_PATH,
        '-vn',
        '-filter:a', 'volume=0.1',
        '-acodec', 'pcm_s16le',
        bg_music
    ]
    subprocess.run(music_cmd, check=True)
    
    # 3. Combine audio tracks
    mixed_audio = "temp_mixed_audio.wav"
    mix_cmd = [
        'ffmpeg',
        '-y',
        '-i', original_audio,
        '-i', bg_music,
        '-filter_complex', '[0:a][1:a]amerge=inputs=2[aout]',
        '-map', '[aout]',
        '-ac', '2',
        '-c:a', 'pcm_s16le',
        mixed_audio
    ]
    subprocess.run(mix_cmd, check=True)
    
    # 4. Combine video and audio
    final_cmd = [
        'ffmpeg',
        '-y',
        '-i', video_no_audio,
        '-i', mixed_audio,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-r', '30',  # Ensure output is 30 FPS
        '-metadata', f'title={title}',
        output_file
    ]
    subprocess.run(final_cmd, check=True)
    
    # Cleanup temporary files
    for f in [concat_list, video_no_audio, original_audio, bg_music, mixed_audio]:
        if os.path.exists(f):
            os.remove(f)
    
    print(f"Created final video: {output_file}")
    print(f"Title: {title}")

def group_segments() -> Dict[str, List[str]]:
    """Group segments by their base audio name"""
    groups = {}
    for f in os.listdir(SEGMENTS_DIR):
        if f.endswith('.mp4'):
            base = f.split('_segment_')[0]
            if base not in groups:
                groups[base] = []
            groups[base].append(f)
    return groups

def main():
    """Main processing pipeline"""
    try:
        validate_environment()
        
        if which("ffmpeg") is None:
            raise Exception("ffmpeg is not installed")
        
        segment_groups = group_segments()
        if not segment_groups:
            print("No segments found to process")
            return
        
        for base_name, segments in segment_groups.items():
            print(f"\nProcessing {base_name} with {len(segments)} segments")
            process_video_group(segments)
        
        print("\nAll videos processed successfully")
    
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()