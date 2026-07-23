"""
fetch_images.py
-----------------
Automatically generates every scene image (and the thumbnail background)
using Pollinations.ai's free `kontext` image-to-image model, which takes
a reference image URL + a text prompt and produces a new image keeping
the subject consistent.

This replaces the manual "generate in the Gemini app" step — everything
here runs unattended in GitHub Actions.

Reference character image must be publicly reachable (repo set to
Public), at: assets/character/reference.png

No API key required for basic use. Optional: set POLLINATIONS_TOKEN as
a repo secret (free, from auth.pollinations.ai) to remove the watermark
and raise rate limits.
"""

import os
import json
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
SLIDES_DIR = os.path.join(BASE_DIR, "data", "slides")

W, H = 1920, 1080

CHARACTER_DESCRIPTION = (
    "A young man with short dark hair, glasses, a maroon button-up shirt, "
    "dark navy trousers, and brown shoes. Flat cartoon illustration style "
    "with bold black outlines, soft cel-shading, on a solid warm yellow "
    "background. Keep the character's face, hair, and outfit identical to "
    "the reference image in every generation."
)

POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN")  # optional


def reference_image_url() -> str:
    """Builds the raw GitHub URL for the reference character image.
    Requires the repo to be Public and GITHUB_REPOSITORY env var (set
    automatically by GitHub Actions)."""
    repo = os.environ.get("GITHUB_REPOSITORY")  # e.g. "yourname/youtube-story-agent"
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        raise RuntimeError(
            "GITHUB_REPOSITORY env var not set — run this inside GitHub "
            "Actions, or set it manually for local testing."
        )
    return f"https://raw.githubusercontent.com/{repo}/{branch}/assets/character/reference.png"


def generate_image(prompt: str, reference_url: str, out_path: str, retries: int = 3):
    params = {
        "model": "kontext",
        "image": reference_url,
        "width": W,
        "height": H,
        "nologo": "true" if POLLINATIONS_TOKEN else "false",
        "safe": "true",
    }
    if POLLINATIONS_TOKEN:
        params["token"] = POLLINATIONS_TOKEN

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{urllib.parse.urlencode(params)}"

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "youtube-story-agent"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
            return
        except Exception as e:
            last_error = e
            print(f"  attempt {attempt} failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"Failed to generate image for prompt after {retries} attempts: {last_error}")


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    ref_url = reference_image_url()
    os.makedirs(SLIDES_DIR, exist_ok=True)

    # Thumbnail background (text gets overlaid separately for crisp readability)
    thumb_prompt = (
        f"{CHARACTER_DESCRIPTION} The character reacts with excitement/surprise "
        f"to: {script['scenes'][0]['visual_description']}. "
        f"16:9 landscape, eye-catching thumbnail composition, no text."
    )
    print("Generating thumbnail background...")
    generate_image(thumb_prompt, ref_url, os.path.join(SLIDES_DIR, "thumbnail_bg.png"))

    for i, scene in enumerate(script["scenes"]):
        prompt = (
            f"{CHARACTER_DESCRIPTION} Scene: {scene['visual_description']}. "
            f"16:9 landscape composition, no text overlay."
        )
        out_path = os.path.join(SLIDES_DIR, f"scene_{i:03d}.png")
        print(f"Generating scene_{i:03d}...")
        generate_image(prompt, ref_url, out_path)

    print(f"\nAll {len(script['scenes']) + 1} images generated.")


if __name__ == "__main__":
    main()
