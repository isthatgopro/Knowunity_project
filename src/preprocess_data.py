# preprocess_data.py
import argparse
import os
import subprocess
import shutil

def check_ffmpeg_installed():
    """Checks if ffmpeg is available in the system's PATH."""
    if not shutil.which("ffmpeg"):
        print("--------------------------------------------------")
        print("ERROR: ffmpeg is not installed or not in your PATH.")
        print("Please install it to continue.")
        print("On macOS with Homebrew: brew install ffmpeg")
        print("On Debian/Ubuntu: sudo apt-get install ffmpeg")
        print("--------------------------------------------------")
        return False
    return True

def process_audio(input_path, output_path):
    """Converts any audio file to the required 16kHz WAV format."""
    print(f"--- Processing Audio: {input_path} ---")
    if not os.path.exists(input_path):
        print(f"Error: Input audio file not found at '{input_path}'")
        return None

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Converting to 16kHz WAV format...")
    convert_cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-acodec', 'pcm_s16le', '-ar', '16000', output_path
    ]
    try:
        subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
        print(f"✅ Audio successfully converted to: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error during audio conversion: {e.stderr}")
        return None

def process_video(input_path, output_path):
    """Converts any video file to the required 512x512 square format."""
    print(f"--- Processing Video: {input_path} ---")
    if not os.path.exists(input_path):
        print(f"Error: Input video file not found at '{input_path}'")
        return None
        
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Converting to 512x512 square format...")
    convert_cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', 'scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2',
        output_path
    ]
    try:
        subprocess.run(convert_cmd, check=True, capture_output=True, text=True)
        print(f"✅ Video successfully converted to: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error during video conversion: {e.stderr}")
        return None

if __name__ == "__main__":
    if not check_ffmpeg_installed():
        exit(1)

    # New command-line arguments for directories
    parser = argparse.ArgumentParser(description="Pre-process audio and video files for Real3DPortrait.")
    parser.add_argument("--input-dir", required=True, help="Directory containing the raw input files.")
    parser.add_argument("--output-dir", required=True, help="Directory where processed files will be saved.")
    parser.add_argument("--audio-file", required=True, help="Filename of the audio file inside the input directory.")
    parser.add_argument("--video-file", required=True, help="Filename of the video file inside the input directory.")
    args = parser.parse_args()

    # Construct full input paths
    audio_input_path = os.path.join(args.input_dir, args.audio_file)
    video_input_path = os.path.join(args.input_dir, args.video_file)

    # Construct intelligent output paths
    audio_basename, _ = os.path.splitext(args.audio_file)
    audio_output_path = os.path.join(args.output_dir, f"{audio_basename}_16khz.wav")
    
    video_basename, _ = os.path.splitext(args.video_file)
    video_output_path = os.path.join(args.output_dir, f"{video_basename}_512x512.mp4")

    # Process the files
    processed_audio = process_audio(audio_input_path, audio_output_path)
    processed_video = process_video(video_input_path, video_output_path)

    print("\n--- Pre-processing Summary ---")
    if processed_audio and processed_video:
        print("✅ All files processed successfully.")
        print(f"   Audio: {processed_audio}")
        print(f"   Video: {processed_video}")
        print("\nYou can now use the processed files with 'run_modal.py'.")
    else:
        print("❌ Pre-processing failed for one or more files. Please check the errors above.")
