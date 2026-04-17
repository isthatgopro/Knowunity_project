import fileinput
import sys
import os

print("--- Applying runtime patch to use local HuBERT model and processor ---")

file_to_patch = "/workspace/Real3DPortrait/data_gen/utils/process_audio/extract_hubert.py"

if not os.path.exists(file_to_patch):
    print(f"Error: Could not find file to patch at {file_to_patch}", file=sys.stderr)
    sys.exit(1)

# Define the text to find and replace for BOTH model and processor
model_find = 'HubertModel.from_pretrained("facebook/hubert-large-ls960-ft")'
model_replace = 'HubertModel.from_pretrained("/models/facebook/hubert-large-ls960-ft")'

# Add a second find/replace for the Wav2Vec2Processor
processor_find = 'Wav2Vec2Processor.from_pretrained("facebook/hubert-large-ls960-ft")'
processor_replace = 'Wav2Vec2Processor.from_pretrained("/models/facebook/hubert-large-ls960-ft")'

try:
    with fileinput.FileInput(file_to_patch, inplace=True) as file:
        for line in file:
            modified_line = line.replace(model_find, model_replace).replace(processor_find, processor_replace)
            print(modified_line, end="")
    print("--- Patching complete for both model and processor. ---")

except Exception as e:
    print(f"An unexpected error occurred during patching: {e}", file=sys.stderr)
    sys.exit(1)
