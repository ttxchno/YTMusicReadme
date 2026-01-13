import os
import base64
import requests
from flask import Flask, send_file
from ytmusicapi2 import YTMusic
from PIL import Image, ImageDraw, ImageFont
import io

from constants import YT_CLIENT_CONFIG

app = Flask(__name__)
ytmusic = YTMusic(YT_CLIENT_CONFIG)

@app.route('/')
def now_playing_png():
    track = ytmusic.get_history()[0]
    title = track['title']
    artist = track.get("artists", [{"name": "Unknown"}])[0]['name']
    thumbnail_url = track['thumbnails'][0]['url']

    # Force high-res thumbnail
    if "=s" in thumbnail_url:
        thumbnail_url = thumbnail_url.split('=')[0] + "=s800"

    response = requests.get(thumbnail_url)
    if response.status_code != 200:
        return "Image fetch failed", 500

    album_art = Image.open(io.BytesIO(response.content)).convert("RGB")
    album_art = album_art.resize((100, 100))

    # Create card
    card = Image.new("RGB", (400, 120), color=(30, 30, 30))
    card.paste(album_art, (10, 10))

    draw = ImageDraw.Draw(card)
    font_title = ImageFont.truetype("arial.ttf", 18)
    font_artist = ImageFont.truetype("arial.ttf", 14)

    draw.text((120, 30), title, font=font_title, fill=(255, 255, 255))
    draw.text((120, 60), artist, font=font_artist, fill=(180, 180, 180))

    buf = io.BytesIO()
    card.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
