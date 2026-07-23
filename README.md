# Chann-YouTube-Agent

# YouTube Story Agent

Fully automated pipeline: writes a relatable "did you know" story script,
generates story-specific, character-consistent images for free via
Pollinations.ai, narrates it with free TTS, assembles the final 16:9
video, and uploads it to YouTube.

## One-time setup

1. **Make the repo Public**: Settings → General → Danger Zone → Change
   visibility → Public. (This is required so Pollinations can fetch your
   reference character image by URL. Your secrets stay encrypted and
   hidden regardless of repo visibility.)

2. **Upload your reference character image**: add it to the repo at
   exactly this path: `assets/character/reference.png`

3. **Secrets** (Settings → Secrets and variables → Actions):
   - `GEMINI_API_KEY` — from aistudio.google.com
   - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_TOKEN_JSON` —
     from the OAuth setup steps
   - `POLLINATIONS_TOKEN` (optional) — free token from auth.pollinations.ai,
     removes the watermark and raises rate limits. Works without it too.

4. **Edit the character description** (recommended): open
   `scripts/fetch_images.py` and adjust `CHARACTER_DESCRIPTION` to
   precisely match your reference character (hair, clothes, style) —
   also update the same constant in `scripts/generate_script.py` area if
   you added one there.

5. **Add the Anton font**: create `assets/fonts/Anton-Regular.ttf` — a
   free Google Font, download it from:
   `https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf`
   (open that link, save the file, upload it to the repo at that exact path)

## Weekly workflow

1. **Fully automatic**: 3x/week, "1 - Generate Script & Images" runs on
   its own — writes a new script, generates every scene image and the
   thumbnail via Pollinations, commits them, and opens a GitHub Issue
   with a thumbnail preview.

2. **You (quick review, ~1 minute)**: Open the Issue, glance at the
   thumbnail and a few slides in `data/slides/` to make sure they look
   right (Pollinations quality can vary since it's a free community
   project, not a guaranteed enterprise service).

3. **You tap one button**: Actions tab → "2 - Assemble & Publish Video"
   → **Run workflow**. This narrates, assembles, and uploads
   automatically.

If any images look off, just re-run step 1 for a fresh attempt, or
manually swap in a replacement image before running step 2.

## Repo structure

```
assets/
  character/reference.png   # your character reference (you upload once)
  fonts/Anton-Regular.ttf   # bold title font
scripts/
  generate_script.py        # Gemini writes the story
  fetch_images.py           # Pollinations generates story-specific images
  compose_thumbnail.py      # overlays crisp title text on the thumbnail
  check_slides_present.py   # safety check before assembling
  generate_audio.py         # free TTS narration (edge-tts)
  build_video.py            # combines images + audio into final_video.mp4
  upload_youtube.py         # publishes to your channel
data/
  script.json                # current script (auto-generated)
  slides/                    # auto-generated images
```

## Upgrading later

If Pollinations quality/consistency isn't cutting it, swap
`fetch_images.py`'s API call for a paid model (Gemini's Nano Banana 2,
~$0.05-0.07/image) — everything else in the pipeline stays the same.
