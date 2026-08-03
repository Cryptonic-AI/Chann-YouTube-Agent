"""
fetch_images.py
-----------------
Generates every scene image (and the thumbnail background) using
Pollinations.ai's free `flux` text-to-image model.

No reference image / image-to-image editing is used here (that
capability, `kontext`, has moved on and off Pollinations' paid tier
multiple times in 2026 and isn't reliable to depend on for free).
Instead, character consistency comes from reusing an identical, highly
detailed character description in every single prompt — the outfit,
hair, and art style should stay consistent; exact facial likeness may
vary slightly frame to frame, same as any text-only AI art generator.

No API key required for basic use. Optional: set POLLINATIONS_TOKEN as
a repo secret (free, from enter.pollinations.ai) for higher rate limits.
"""

import os
import json
import time
import urllib.parse
import urllib.request
import urllib.error

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
SLIDES_DIR = os.path.join(BASE_DIR, "data", "slides")

W, H = 1920, 1080
MODEL = "flux"

ART_STYLE = (
    "Flat cartoon illustration style, bold clean black outlines, soft "
    "cel-shading, simple warm yellow solid background, no clutter."
)

# Be as specific as possible here — this exact text is repeated in every
# prompt where the narrator appears, so it's doing all the work of
# keeping his look consistent since there's no reference image to lock
# it in.
CHARACTER_DESCRIPTION = (
    "A young man character named Alex: short neat dark brown hair, "
    "black rectangular glasses, light skin tone, friendly expression. "
    "Wearing a maroon/burgundy button-up collared shirt with sleeves "
    "rolled to the elbow, dark navy blue trousers, brown leather shoes."
)

POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN")  # optional


def generate_image(prompt: str, out_path: str, retries: int = 3):
    params = {"model": MODEL, "width": W, "height": H, "nologo": "true", "safe": "true"}
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{urllib.parse.urlencode(params)}"

    headers = {"User-Agent": "youtube-story-agent"}
    if POLLINATIONS_TOKEN:
        headers["Authorization"] = f"Bearer {POLLINATIONS_TOKEN}"

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
            return
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")[:500]
            last_error = f"HTTP {e.code}: {error_body}"
            print(f"  attempt {attempt} failed: {last_error}")
            time.sleep(8)
        except Exception as e:
            last_error = e
            print(f"  attempt {attempt} failed: {e}")
            time.sleep(8)
    raise RuntimeError(f"Failed to generate image for prompt after {retries} attempts: {last_error}")


def build_scene_prompt(scene: dict) -> str:
    if scene.get("narrator_present", True):
        return (
            f"{ART_STYLE} The recurring narrator character, {CHARACTER_DESCRIPTION} "
            f"appears in this scene. Scene: {scene['visual_description']}. "
            f"16:9 landscape composition, no text overlay."
        )
    else:
        # No forced character — let the scene depict whoever/whatever the
        # story actually calls for (multiple people, objects, settings),
        # just keep it in the same illustration style.
        return (
            f"{ART_STYLE} Scene: {scene['visual_description']}. Depict "
            f"exactly the people/objects/setting described, however many "
            f"that requires. 16:9 landscape composition, no text overlay."
        )


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    os.makedirs(SLIDES_DIR, exist_ok=True)

    thumb_prompt = (
        f"{ART_STYLE} The recurring narrator character, {CHARACTER_DESCRIPTION} "
        f"reacts with excitement/surprise to: {script['scenes'][0]['visual_description']}. "
        f"Full body shot, character positioned in the lower two-thirds of the "
        f"frame and shifted slightly to one side, leaving the top third of the "
        f"image as plain empty yellow background with nothing in it — that "
        f"space is reserved for text and must stay completely clear. "
        f"16:9 landscape, eye-catching thumbnail composition, no text."
    )
    print("Generating thumbnail background...")
    generate_image(thumb_prompt, os.path.join(SLIDES_DIR, "thumbnail_bg.png"))

    for i, scene in enumerate(script["scenes"]):
        prompt = build_scene_prompt(scene)
        out_path = os.path.join(SLIDES_DIR, f"scene_{i:03d}.png")
        print(f"Generating scene_{i:03d}...")
        generate_image(prompt, out_path)

    print(f"\nAll {len(script['scenes']) + 1} images generated.")


if __name__ == "__main__":
    main()

