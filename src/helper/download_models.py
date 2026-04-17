import os
import time
from huggingface_hub import snapshot_download
from huggingface_hub.errors import HfHubHTTPError

# --- Configuration ---
MODELS = {
    "hubert": "facebook/hubert-large-ls960-ft",
}
MODEL_PATH_BASE = "/models"
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 15

def download():
    """
    Downloads all specified models from Hugging Face, using an API token
    to avoid rate limits and a retry mechanism for transient errors.
    """
    # Get the token from the environment variable provided by the Modal Secret.
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("Warning: Hugging Face token not found. Downloads may be rate-limited.")

    for model_name, repo_id in MODELS.items():
        for attempt in range(MAX_RETRIES):
            try:
                print(f"--- Attempt {attempt + 1}/{MAX_RETRIES} to download model: {repo_id} ---")
                
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=f"{MODEL_PATH_BASE}/{repo_id}",
                    token=hf_token,  # Pass the token to authenticate the request
                    local_dir_use_symlinks=False,
                    resume_download=True,
                    etag_timeout=100,
                )
                
                print(f"--- Successfully downloaded {repo_id} ---")
                break  # Exit the retry loop on success

            except HfHubHTTPError as e:
                print(f"Download failed with HTTP error: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print("--- Max retries reached. Failing the build. ---")
                    raise
            
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print("--- Max retries reached due to an unexpected error. Failing the build. ---")
                    raise

if __name__ == "__main__":
    download()
