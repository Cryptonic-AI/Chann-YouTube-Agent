"""
check_slides_present.py
-------------------------
Fails fast with a clear message if any scene image (or the thumbnail)
hasn't been uploaded yet, so the workflow doesn't waste time generating
audio/video only to fail later.
"""

import os
import json
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
SLIDES_DIR = os.path.join(BASE_DIR, "data", "slides")


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    missing = []

    thumb_path = os.path.join(SLIDES_DIR, "thumbnail.png")
    if not os.path.exists(thumb_path):
        missing.append("thumbnail.png")

    for i in range(len(script["scenes"])):
        path = os.path.join(SLIDES_DIR, f"scene_{i:03d}.png")
        if not os.path.exists(path):
            missing.append(f"scene_{i:03d}.png")

    if missing:
        print("Missing images — upload these to data/slides/ before running this workflow:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)

    print(f"All {len(script['scenes']) + 1} images present. Proceeding.")


if __name__ == "__main__":
    main()
