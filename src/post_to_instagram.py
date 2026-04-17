import os
import logging
import random
import string
import openai
from dotenv import load_dotenv, set_key
from instagrapi import Client
from instagrapi.exceptions import ClientError, ChallengeRequired
from instagrapi.mixins.challenge import ChallengeChoice

# --- Configuration ---
VIDEO_PATH = "kendrick_new_output3.mp4"
LYRICS_INPUT_FILE = "lyrics.txt"
SESSION_FILE = "session.json"
LOG_FILE = "poster.log"
ENV_FILE = ".env"

def setup_logging():
    """Configures the logging system to output to console and a dedicated file."""
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def generate_caption_with_openai(lyrics: str, api_key: str) -> str:
    """Generates a trendy Instagram caption using OpenAI."""
    logging.info("Generating caption with OpenAI...")
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""
        You are a chronically online Gen Z social media expert. Your task is to write a short, witty, "brainrot" style Instagram Reel caption for a math-themed rap song.

        Rules:
        1.  Short caption (under 25 words).
        2.  3-5 relevant, unhinged hashtags.
        3.  Include at least one popular emoji (e.g., 🤖, 🧠, 📈, 🔥, 💀).
        4.  Tone should be confident, nerdy, and funny.

        Song lyrics for context:
        ---
        {lyrics}
        ---
        Now, generate the caption.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        caption = response.choices[0].message.content.strip()
        logging.info(f"Successfully generated caption: '{caption}'")
        return caption
    except Exception:
        logging.exception("Failed to generate caption from OpenAI.")
        return None

def challenge_code_handler(username, choice):
    """Handles the 6-digit code challenge."""
    if choice == ChallengeChoice.EMAIL:
        code = input(f"Enter the 6-digit code for {username}: ").strip()
        return code
    return None

def change_password_handler(username):
    """Handles forced password resets."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    new_password = "".join(random.choice(chars) for i in range(12))
    set_key(ENV_FILE, "INSTAGRAM_PASSWORD", new_password)
    logging.warning(f"Password reset for {username}. New password: {new_password}. .env updated.")
    return new_password

def upload_reel():
    """Main function to log in, generate a caption, and upload a Reel."""
    load_dotenv(dotenv_path=ENV_FILE)
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([username, password, openai_api_key]):
        logging.error("Missing credentials. Check USERNAME, PASSWORD, and OPENAI_API_KEY in .env.")
        return

    # --- Step 1: Read Lyrics and Generate Caption ---
    try:
        with open(LYRICS_INPUT_FILE, "r", encoding="utf-8") as f:
            lyrics_for_caption = f.read()
        logging.info(f"Read lyrics from '{LYRICS_INPUT_FILE}' to generate caption.")
    except FileNotFoundError:
        logging.error(f"'{LYRICS_INPUT_FILE}' not found. Run 'generate_content.py' first.")
        return

    caption_text = generate_caption_with_openai(lyrics_for_caption, openai_api_key)
    if not caption_text:
        logging.error("Halting upload: caption generation failed.")
        return

    # --- Step 2: Login and Upload ---
    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    cl.change_password_handler = change_password_handler
    
    try:
        logging.info("Attempting to log in...")
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            logging.info("Login via session successful.")
        else:
            cl.login(username, password)
            logging.info("Fresh login successful.")
        
        cl.dump_settings(SESSION_FILE)
        logging.info(f"Session state saved to '{SESSION_FILE}'")

        if not os.path.exists(VIDEO_PATH):
            logging.error(f"Video file not found at '{VIDEO_PATH}'")
            return
            
        logging.info(f"Uploading Reel with generated caption...")
        cl.clip_upload(path=VIDEO_PATH, caption=caption_text)
        logging.info("Reel uploaded successfully!")

    except Exception:
        logging.exception("An unexpected, critical error occurred during the upload process.")

if __name__ == "__main__":
    setup_logging()
    upload_reel()
