from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/api/now-playing')
def now_playing():
    image_path = os.path.join(os.getcwd(), 'static', 'images', 'now-playing.png')
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    return 'No image found', 404
