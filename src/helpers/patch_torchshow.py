import inspect
import pathlib

print("Attempting to patch torchshow to fix FigureCanvasAgg title error...")

try:
    # Dynamically import the module to be patched
    import torchshow.visualization as vz

    # Find the source file location
    source_file = inspect.getsourcefile(vz)
    if not source_file:
        raise FileNotFoundError("Could not locate the source file for torchshow.visualization.")

    path = pathlib.Path(source_file)
    print(f"Found torchshow visualization module at: {path}")

    # Read the file's content
    text = path.read_text()

    # Define the code to be replaced and its replacement
    original_string = 'fig.canvas.set_window_title'
    replacement_string = 'fig.canvas.manager.set_window_title'

    # Apply the patch only if the problematic code exists
    if original_string in text:
        patched_text = text.replace(original_string, replacement_string)
        path.write_text(patched_text)
        print("Successfully patched torchshow.")
    else:
        print("Patch not needed. The target string was not found (perhaps the library is already updated).")

except ImportError:
    print("Error: 'torchshow' is not installed. Skipping patch.")
except Exception as e:
    print(f"An unexpected error occurred while patching torchshow: {e}")
    # If this patch is critical, you might want to exit with an error
    # import sys
    # sys.exit(1)
