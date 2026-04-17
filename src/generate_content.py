import os
import logging
import openai
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# --- Configuration ---
LYRICS_OUTPUT_FILE = "lyrics.txt"
AUDIO_OUTPUT_FILE = "rap_audio.wav"
LOG_FILE = "generator.log"
ENV_FILE = ".env"

def setup_logging():
    """Configures the logging system to output to console and a dedicated file."""
    # Get the root logger
    logger = logging.getLogger()
    # Clear existing handlers to prevent duplicate logs on re-runs
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO) # Set the lowest level to capture

    # Create a formatter to define the log message structure
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')

    # Create a handler to write log records to the generator.log file
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Create a handler to write log records to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add both handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def generate_rap_lyrics(prompt: str, api_key: str) -> str:
    """Generates rap lyrics using OpenAI."""
    openai.api_key = api_key
    try:
        logging.info("Sending prompt to OpenAI to generate lyrics...")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a hilarious and creative math rapper like Kendrick Lamar."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=400
        )
        lyrics = response.choices[0].message.content.strip()
        logging.info("Lyrics generated successfully from OpenAI.")
        return lyrics
    except Exception:
        logging.exception("Failed to generate lyrics from OpenAI.")
        return None

def generate_audio_from_lyrics(text: str, api_key: str, output_path: str):
    """Generates a WAV file from text using ElevenLabs."""
    try:
        logging.info(f"Sending text to ElevenLabs to generate audio for voice ID 'pNInz6obpgDQGcFmaJgB'...")
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            model_id="eleven_multilingual_v2",
            text=text,
        )
        with open(output_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        logging.info(f"Audio stream successfully saved to: {output_path}")
    except Exception:
        logging.exception("Failed to generate audio from ElevenLabs.")

def main():
    """Main function to run the content generation pipeline."""
    load_dotenv(dotenv_path=ENV_FILE)
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

    if not all([openai_key, elevenlabs_key]):
        logging.error("Missing OPENAI_API_KEY or ELEVENLABS_API_KEY in .env file. Halting execution.")
        return

    # --- Step 1: Generate Lyrics ---
    lyrics_prompt = """
    Write creative, hilarious, and rhythmic rap lyrics about the math concept of logarithms,
    in the style of Kendrick Lamar's "Not Like Us".
    Structure it with two verses and a chorus.
    """
    raw_lyrics = generate_rap_lyrics(lyrics_prompt, openai_key)

    if raw_lyrics:
        # --- Step 2: Save Lyrics to File ---
        with open(LYRICS_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(raw_lyrics)
        logging.info(f"Lyrics saved to local file: {LYRICS_OUTPUT_FILE}")

        # --- Step 3: Generate Audio from Lyrics ---
        generate_audio_from_lyrics(raw_lyrics, elevenlabs_key, AUDIO_OUTPUT_FILE)
        
        logging.info("Content generation pipeline complete.")

if __name__ == "__main__":
    setup_logging()
    main()
