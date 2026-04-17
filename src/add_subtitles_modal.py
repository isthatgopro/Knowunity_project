import modal
import os
import logging
import argparse

# --- Basic Setup ---
app = modal.App("video-subtitler-word-by-word")
logger = logging.getLogger("subtitler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Define the Container Image ---
# Reuse Dockerfile and adds 'whisper-timestamped'.
image = (
    modal.Image.from_dockerfile("./Dockerfile")
    .run_commands(
        "apt-get update && apt-get install -y imagemagick",
        "sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml",
        "python3 -m pip install git+https://github.com/linto-ai/whisper-timestamped.git",
    )
)

# --- Define a Persistent Shared Volume and Mount Path ---
volume = modal.NetworkFileSystem.from_name("subtitling-volume", create_if_missing=True)
REMOTE_MOUNT_PATH = "/data"


# --- Define the "bare" logic as a global function ---
def _add_subtitles_remote(input_filename, output_filename, whisper_model_name):
    """This remote function creates a word-by-word subtitle animation."""
    import whisper_timestamped as whisper
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

    video_path_remote = os.path.join(REMOTE_MOUNT_PATH, input_filename)
    logger.info(f"--- Starting word-by-word subtitling for {video_path_remote} ---")

    logger.info(f"Loading whisper-timestamped model '{whisper_model_name}'...")
    model = whisper.load_model(whisper_model_name, device="cpu")
    logger.info(f"Starting word-level transcription...")
    result = whisper.transcribe(model, video_path_remote, language="en")

    logger.info("Transcription complete. Creating word-level TextClips...")
    all_word_clips = []
    for segment in result["segments"]:
        for word_info in segment["words"]:
            word_text = word_info["text"].upper().strip()
            start_time = word_info["start"]
            end_time = word_info["end"]
            duration = end_time - start_time

            # Create a styled TextClip for the current word
            word_clip = TextClip(
                word_text,
                fontsize=48,
                font='Arial-Bold',
                # Change the text color to yellow.
                color='yellow',
                stroke_color='black',
                stroke_width=2
            )
            
            word_clip = (
                word_clip.set_start(start_time)
                .set_duration(duration)
                .set_position(('center', 0.85), relative=True)
            )
            
            all_word_clips.append(word_clip)

    logger.info("Compositing all word clips onto the original video...")
    original_video_clip = VideoFileClip(video_path_remote)
    
    final_clip = CompositeVideoClip([original_video_clip] + all_word_clips)

    output_path_remote = os.path.join(REMOTE_MOUNT_PATH, output_filename)
    logger.info(f"Writing final video to {output_path_remote}...")
    os.makedirs(os.path.dirname(output_path_remote), exist_ok=True)
    
    final_clip.write_videofile(
        output_path_remote, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        fps=24
    )
    
    return output_filename


@app.local_entrypoint()
def main():
    """This local entrypoint handles file uploads, function calls, and downloads."""
    parser = argparse.ArgumentParser(description="Add word-by-word subtitles to a video using Whisper on Modal.")
    parser.add_argument("--input-video", required=True, help="Path to the local video file you want to subtitle.")
    parser.add_argument("--output-video", default="output_with_word_subs.mp4", help="Filename for the final subtitled video.")
    parser.add_argument("--gpu", default="T4", help="GPU type to use on Modal (e.g., T4, A10G, H100).")
    parser.add_argument("--model", default="base", help="Whisper model size (e.g., tiny, base, small, medium, large).")
    args = parser.parse_args()

    local_path = args.input_video
    if not os.path.exists(local_path):
        logger.error(f"Input file not found at: {local_path}")
        return

    input_filename = os.path.basename(local_path)
    remote_path = f"/{input_filename}"
    
    logger.info(f"Uploading '{local_path}' to the shared volume at path '{remote_path}'...")
    with open(local_path, "rb") as local_file_handle:
        volume.write_file(remote_path, local_file_handle)
    logger.info("Upload complete.")

    add_subtitles = app.function(
        image=image,
        gpu=args.gpu,
        network_file_systems={REMOTE_MOUNT_PATH: volume},
        timeout=1800,
    )(_add_subtitles_remote)

    with app.run():
        final_video_relative_path = add_subtitles.remote(
            input_filename=input_filename,
            output_filename=args.output_video,
            whisper_model_name=args.model
        )

    logger.info(f"Downloading final video from volume path '{final_video_relative_path}' to local path '{args.output_video}'...")
    remote_download_path = f"/{final_video_relative_path}"
    video_generator = volume.read_file(remote_download_path)
    video_bytes = b"".join(video_generator)
    
    output_dir = os.path.dirname(os.path.normpath(args.output_video))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(args.output_video, "wb") as local_f:
        local_f.write(video_bytes)
            
    logger.info(f"✅ Success! Your subtitled video is saved at '{args.output_video}'")

if __name__ == "__main__":
    main()