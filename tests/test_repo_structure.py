from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_core_directories_exist():
    expected = [
        "src",
        "docs/images",
        "data/input",
        "data/processed",
        "output",
        "tests",
    ]
    for rel in expected:
        assert (ROOT / rel).exists(), f"Missing directory: {rel}"

def test_core_scripts_exist():
    expected = [
        "src/preprocess_data.py",
        "src/run_modal.py",
        "src/add_subtitles_modal.py",
        "src/generate_content.py",
    ]
    for rel in expected:
        assert (ROOT / rel).is_file(), f"Missing script: {rel}"
