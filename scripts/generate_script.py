"""
generate_script.py
-------------------
Calls the Gemini API (free tier) to write a ~10-15 minute narrated script
about a relatable discovery/story, broken into scenes for the video.

Output: data/script.json
{
  "title": "...",
  "thumbnail_text_top": "...",
  "thumbnail_text_bottom": "...",
  "scenes": [
    {"narration": "...", "visual_description": "...", "pose": "shocked"},
    ...
  ]
}

Requires env var: GEMINI_API_KEY
"""

import os
import json
import re
import urllib.request
import urllib.error

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-flash-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI_API_KEY}"

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "script.json")

ALLOWED_POSES = ["explaining", "shocked", "thinking", "pointing", "happy", "confused"]

PROMPT = """
You are writing a script for a YouTube video in the style of relatable
"did you know" / "this happens to everyone" discovery videos. The tone is
warm, conversational, a little humorous, and easy to follow — like a
friend explaining something surprising about everyday life, the human
body, psychology, or the world, NOT dry academic narration.

Pick ONE specific, highly relatable topic (something most people have
personally experienced or wondered about — e.g. why a song gives you
chills, why you feel embarrassed remembering something from years ago,
why time feels faster as you age, why you can't tickle yourself, etc).
Do not repeat topics that are extremely overused (avoid "why yawning is
contagious" unless you have a fresh angle).

Write a script meant to be narrated aloud for 10-15 minutes (roughly
1400-2000 spoken words total across all scenes).

Break it into 30-40 scenes so the visuals change frequently and the
video doesn't feel static — each scene is a SHORT narration chunk
(1-3 sentences, natural spoken pacing) paired with a detailed visual
description.

For each visual description: describe whatever the story actually
calls for at that exact moment — this might be the narrator character
alone reacting, but it might just as easily be two friends talking,
a crowd of people, a doctor and patient, a classroom, an object or
diagram, a historical scene, etc. Depict the content of that specific
sentence, not a default "narrator reacting to camera" pose repeated
every time. Only include the recurring narrator character when the
narration is him personally speaking/reacting directly (roughly a
third to half of scenes) — the rest should illustrate the actual
subject matter, people, and situations being described, with as many
people/characters in frame as the story naturally calls for. Also
include a "pose" tag from this exact list purely as a fallback label,
only meaningful for scenes where the narrator character appears:
explaining, shocked, thinking, pointing, happy, confused.

Respond with ONLY valid JSON, no markdown fences, no commentary, in
exactly this shape:

{
  "title": "short catchy video title",
  "thumbnail_text_top": "SHORT PUNCHY HOOK IN CAPS (under 6 words)",
  "thumbnail_text_bottom": "SHORT SUBTITLE IN CAPS (under 5 words)",
  "scenes": [
    {"narration": "...", "visual_description": "detailed scene-specific description of exactly who/what should be shown", "pose": "explaining", "narrator_present": true}
  ]
}
"""


def list_available_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        names = [
            m["name"] for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        print("Models available to this API key that support generateContent:")
        for n in names:
            print(f"  - {n}")
    except Exception as e:
        print(f"Could not list models: {e}")


def call_gemini(prompt: str) -> str:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"Gemini API returned HTTP {e.code}:\n{error_body}")
        list_available_models()
        raise

    return data["candidates"][0]["content"]["parts"][0]["text"]


def extract_json(text: str) -> dict:
    # Strip markdown fences if the model added them anyway
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(text)


def validate(script: dict) -> dict:
    assert "title" in script and script["title"], "Missing title"
    assert "scenes" in script and len(script["scenes"]) >= 10, "Too few scenes"
    for scene in script["scenes"]:
        assert scene.get("narration"), "Scene missing narration"
        assert scene.get("visual_description"), "Scene missing visual_description"
        if scene.get("pose") not in ALLOWED_POSES:
            scene["pose"] = "explaining"  # safe fallback
        scene.setdefault("narrator_present", True)
    script.setdefault("thumbnail_text_top", script["title"].upper()[:40])
    script.setdefault("thumbnail_text_bottom", "")
    return script


def main():
    last_error = None
    for attempt in range(1, 4):
        try:
            raw = call_gemini(PROMPT)
            script = extract_json(raw)
            script = validate(script)
            break
        except (json.JSONDecodeError, AssertionError) as e:
            last_error = e
            print(f"Attempt {attempt} produced invalid script ({e}), retrying...")
    else:
        raise RuntimeError(f"Failed to get a valid script after 3 attempts: {last_error}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"Script generated: '{script['title']}' with {len(script['scenes'])} scenes")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
