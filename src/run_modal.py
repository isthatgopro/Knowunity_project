# src/run_modal.py
import modal
import subprocess
import os
import glob
import zipfile
import logging
import argparse

# --- Basic Setup (Logger and App) ---
modal.enable_output()
logger = logging.getLogger("run_pipeline")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)

app = modal.App("real3d-portrait")

# --- Define the "bare" logic as a global function ---
def _run_pipeline_inner(src_img, drv_aud, drv_pose, bg_img, out_name):
    """This is the internal implementation of the pipeline."""
    # The body of this function is correct and does not need to change
    _logger = logging.getLogger("run_pipeline_remote")
    _logger.setLevel(logging.INFO)
    repo_url = "https://github.com/yerfor/Real3DPortrait.git"
    subprocess.run(["git", "clone", repo_url, "Real3DPortrait"], check=True)
    os.chdir("Real3DPortrait")
    _logger.info("Applying runtime patch to use local HuBERT model...")
    subprocess.run(["python", "/root/patch_hubert_runtime.py"], check=True)
    if os.path.exists("requirements.txt"):
        _logger.info("Installing requirements.txt from the repo")
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    bfm_folder = "deep_3drecon/BFM"
    os.makedirs(bfm_folder, exist_ok=True)
    _logger.info("Downloading BFM model files...")
    subprocess.run(["gdown", "--folder", "1o4t5YIw7w4cMUN4bgU9nPf6IyWVG1bEk", "-O", bfm_folder], check=True)
    ckpt_folder = "checkpoints"
    os.makedirs(ckpt_folder, exist_ok=True)
    _logger.info("Downloading pretrained checkpoints...")
    subprocess.run(["gdown", "--folder", "1MAveJf7RvJ-Opg1f5qhLdoRoC_Gc6nD9", "-O", ckpt_folder], check=True)
    for archive in glob.glob(os.path.join(ckpt_folder, "*.zip")):
        _logger.info(f"Unzipping {archive}...")
        with zipfile.ZipFile(archive, 'r') as z:
            z.extractall(ckpt_folder)
    infer_cmd = [
        "python", "inference/real3d_infer.py", "--src_img", src_img, "--drv_aud", drv_aud,
        "--drv_pose", drv_pose, "--bg_img", bg_img, "--out_name", out_name,
        "--out_mode", "concat_debug", "--low_memory_usage",
    ]
    _logger.info(f"Running inference: {' '.join(infer_cmd)}")
    subprocess.run(infer_cmd, check=True)
    output_path = out_name
    with open(output_path, "rb") as f:
        return f.read()

@app.local_entrypoint()
def main():
    """This local entrypoint now builds the full Modal function dynamically."""
    parser = argparse.ArgumentParser(description="Run Real3DPortrait inference on Modal with custom data.")
    parser.add_argument("--src-img", required=True, help="Path to the source image (e.g., data/raw/kendrick.png).")
    parser.add_argument("--drv-aud", required=True, help="Path to the driving audio (e.g., data/processed/audio.wav).")
    parser.add_argument("--drv-pose", required=True, help="Path to the driving pose video (e.g., data/processed/video.mp4).")
    parser.add_argument("--bg-img", required=True, help="Path to the background image (e.g., data/raw/bg.png).")
    parser.add_argument("--out-name", default="output.mp4", help="Name of the output video file.")
    args = parser.parse_args()

    image = (
        modal.Image.from_dockerfile("./Dockerfile")
        .add_local_file("src/helper/patch_hubert_runtime.py", remote_path="/root/patch_hubert_runtime.py")
        # Mount the entire project directory into the container.
        .add_local_dir(".", remote_path="/project")
    )

    run_pipeline = app.function(
        image=image,
        gpu="H100",
        timeout=15 * 60,
        secrets=[modal.Secret.from_name("huggingface-secret")],
    )(_run_pipeline_inner)

    with app.run():
        src_img_path = f"/project/{args.src_img}"
        drv_aud_path = f"/project/{args.drv_aud}"
        drv_pose_path = f"/project/{args.drv_pose}"
        bg_img_path = f"/project/{args.bg_img}"

        video_bytes = run_pipeline.remote(
            src_img=src_img_path,
            drv_aud=drv_aud_path,
            drv_pose=drv_pose_path,
            bg_img=bg_img_path,
            out_name=args.out_name
        )
    
    if video_bytes:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, args.out_name)
        with open(output_path, "wb") as out_file:
            out_file.write(video_bytes)
        logger.info(f"✅ Success! Saved output video to {output_path}")
    else:
        logger.error("❌ Pipeline did not return video bytes. Check logs for errors.")

if __name__ == "__main__":
    main()
