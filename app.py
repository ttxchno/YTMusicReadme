import os
import requests
from io import BytesIO
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
from ytmusicapi2 import YTMusic

from constants import (
    YT_CLIENT_CONFIG,
    SVG_WIDTH, SVG_HEIGHT,
    IMG_SIZE, IMG_Y_POSITION, IMG_THRESHOLD,
    TITLE_FONT_SIZE, TITLE_MAX_CHARS, TITLE_MAX_LINES, TITLE_LINE_SPACING,
    ARTIST_Y_OFFSET
)

app = Flask(__name__)
ytmusic = YTMusic(YT_CLIENT_CONFIG)

def wrap_text(text, max_chars_per_line=TITLE_MAX_CHARS, max_lines=TITLE_MAX_LINES):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        candidate = (current_line + " " + word).strip()
        if len(candidate) <= max_chars_per_line:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word
            if len(lines) >= max_lines:
                break

    if current_line and len(lines) < max_lines:
        lines.append(current_line)

    if len(words) > sum(len(l.split()) for l in lines):
        lines[-1] = lines[-1].rstrip('.') + "..."

    return lines

@app.route('/')
def get_latest_watch():
    last_watched = ytmusic.get_history()[0]
    title = last_watched['title']
    artist = (last_watched.get("artists") or [{"name": "Desconocido"}])[0]['name'].split(", ")[0]

    # Force high-res thumbnail
    thumbnail_url = last_watched['thumbnails'][0]['url']
    if '=' in thumbnail_url:
        thumbnail_url = thumbnail_url.split('=')[0] + "=s800"
    else:
        thumbnail_url += "=s800"

    try:
        response = requests.get(thumbnail_url, timeout=5)
        response.raise_for_status()
        thumbnail = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"Image fetch failed: {e}")
        return "Error fetching image", 500

    # Create card
    card = Image.new("RGB", (SVG_WIDTH, SVG_HEIGHT), color=(20, 20, 20))
    draw = ImageDraw.Draw(card)

    # Paste thumbnail
    thumb_resized = thumbnail.resize((IMG_SIZE, IMG_SIZE))
    card.paste(thumb_resized, (int(SVG_WIDTH / 2 - IMG_SIZE / 2), IMG_Y_POSITION))

    # Draw title
    font = ImageFont.load_default()
    y = IMG_Y_POSITION + IMG_SIZE + IMG_THRESHOLD
    for line in wrap_text(title):
        w, _ = draw.textsize(line, font=font)
        draw.text(((SVG_WIDTH - w) / 2, y), line, font=font, fill=(255, 255, 255))
        y += TITLE_LINE_SPACING

    # Draw artist
    w, _ = draw.textsize(artist, font=font)
    draw.text(((SVG_WIDTH - w) / 2, y + ARTIST_Y_OFFSET), artist, font=font, fill=(180, 180, 180))

    # Return PNG from memory
    buffer = BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')
