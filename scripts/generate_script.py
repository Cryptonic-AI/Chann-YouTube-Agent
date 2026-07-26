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
MODEL = "gemini-2.5-flash"
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

Break it into 16-20 scenes. Each scene is a short narration chunk (3-6
sentences, natural spoken pacing) paired with a detailed visual
description of what should be illustrated: describe the specific
action/moment/scene the character should be depicted doing or reacting
to, matching that exact part of the story (not just a generic pose).
Also include a "pose" tag from this exact list purely as a fallback
label: explaining, shocked, thinking, pointing, happy, confused.

Respond with ONLY valid JSON, no markdown fences, no commentary, in
exactly this shape:

{
  "title": "short catchy video title",
  "thumbnail_text_top": "SHORT PUNCHY HOOK IN CAPS (under 6 words)",
  "thumbnail_text_bottom": "SHORT SUBTITLE IN CAPS (under 5 words)",
  "scenes": [
    {"narration": "...", "visual_description": "detailed scene-specific action description", "pose": "explaining"}
  ]
}
"""


def call_gemini(prompt: str) -> str:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 8192}
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
    script.setdefault("thumbnail_text_top", script["title"].upper()[:40])
    script.setdefault("thumbnail_text_bottom", "")
    return script


def main():
    raw = call_gemini(PROMPT)
    script = extract_json(raw)
    script = validate(script)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"Script generated: '{script['title']}' with {len(script['scenes'])} scenes")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
