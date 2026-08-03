"""
generate_audio.py
-------------------
Generates narration audio for each scene using edge-tts (free, no API key,
uses Microsoft's neural voices). Produces one mp3 per scene so we know
exactly how long each scene should be shown on screen.

Output: data/audio/scene_000.mp3, scene_001.mp3, ...
        data/audio/durations.json  (seconds per scene, used by build_video.py)

Requires: pip install edge-tts
"""

import os
import json
import asyncio
from mutagen.mp3 import MP3
import edge_tts

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio")
DURATIONS_PATH = os.path.join(AUDIO_DIR, "durations.json")

# A newer, more conversational/expressive free neural voice (less flat
# than the older Guy voice). Browse more with: edge-tts --list-voices
VOICE = "en-US-AndrewNeural"


async def synthesize(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+0%", pitch="+0Hz")
    await communicate.save(out_path)


async def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    os.makedirs(AUDIO_DIR, exist_ok=True)
    durations = {}

    for i, scene in enumerate(script["scenes"]):
        out_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.mp3")
        await synthesize(scene["narration"], out_path)

        audio = MP3(out_path)
        durations[f"scene_{i:03d}"] = round(audio.info.length, 2)
        print(f"Narrated scene_{i:03d} ({durations[f'scene_{i:03d}']}s)")

    with open(DURATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(durations, f, indent=2)

    total = sum(durations.values())
    print(f"\nTotal narration length: {total/60:.1f} minutes")
    if total < 8 * 60:
        print("WARNING: video will be under 10 minutes. Consider a longer script.")


if __name__ == "__main__":
    asyncio.run(main())
