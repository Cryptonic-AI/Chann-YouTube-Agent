"""
build_video.py
---------------
Combines the manually-generated scene images (data/slides/scene_XXX.png)
with their matching narration audio (data/audio/scene_XXX.mp3) into the
final 16:9 video, with a gentle Ken Burns zoom on each slide so it doesn't
feel like a static slideshow.

Output: data/output/final_video.mp4

Requires: pip install moviepy
"""

import os
import json
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, vfx

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
SLIDES_DIR = os.path.join(BASE_DIR, "data", "slides")
AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "final_video.mp4")

W, H = 1920, 1080
ZOOM_AMOUNT = 1.08  # subtle zoom over the duration of each slide


def ken_burns_clip(image_path: str, duration: float) -> ImageClip:
    clip = ImageClip(image_path).with_duration(duration)
    # Slow zoom-in over the slide's duration (Ken Burns effect)
    clip = clip.resized(lambda t: 1 + (ZOOM_AMOUNT - 1) * (t / duration))
    clip = clip.resized(width=int(W * ZOOM_AMOUNT), height=int(H * ZOOM_AMOUNT))
    clip = clip.with_effects([vfx.Crop(width=W, height=H, x_center=W * ZOOM_AMOUNT / 2, y_center=H * ZOOM_AMOUNT / 2)])
    return clip


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    clips = []
    for i, scene in enumerate(script["scenes"]):
        img_path = os.path.join(SLIDES_DIR, f"scene_{i:03d}.png")
        audio_path = os.path.join(AUDIO_DIR, f"scene_{i:03d}.mp3")

        if not os.path.exists(img_path):
            raise FileNotFoundError(
                f"Missing {img_path} — generate and upload this scene's "
                f"image before running build_video.py"
            )
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Missing {audio_path} — run generate_audio.py first")

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration + 0.4  # small pad so narration doesn't feel cut off

        clip = ken_burns_clip(img_path, duration)
        clip = clip.with_audio(audio_clip)
        clips.append(clip)
        print(f"Prepared scene_{i:03d} ({duration:.1f}s)")

    final = concatenate_videoclips(clips, method="compose")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final.write_videofile(
        OUTPUT_PATH,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
    )

    print(f"\nFinal video saved to {OUTPUT_PATH}")
    print(f"Total duration: {final.duration/60:.1f} minutes")


if __name__ == "__main__":
    main()
