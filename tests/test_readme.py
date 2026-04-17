from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_readme_exists():
    assert (ROOT / "README.md").is_file()

def test_readme_mentions_pipeline():
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    keywords = ["modal", "pipeline", "subtitle", "real3d"]
    for kw in keywords:
        assert kw in text, f"README missing keyword: {kw}"
