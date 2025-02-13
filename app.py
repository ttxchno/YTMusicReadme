import os
import base64
import requests
import svgwrite
from flask import Flask, send_file
from ytmusicapi import YTMusic, OAuthCredentials
from src import constants

app = Flask(__name__)

client_id = constants.client_id
client_secret = constants.client_secret

ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret))

# Ruta de la carpeta donde se guardarán las imágenes SVG generadas
image_folder = 'static/images'

# Creo la carpeta
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# Convierte la imagen a binario
def image_to_base64(url):
    response = requests.get(url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    return None

# Convierte un archivo GIF a base64
def gif_to_base64(file_path):
    with open(file_path, "rb") as gif_file:
        return base64.b64encode(gif_file.read()).decode('utf-8')

# Función para dividir el texto en múltiples líneas si es necesario
def wrap_text(text, max_width, font_size):
    lines = []
    words = text.split()
    current_line = words[0]
    
    for word in words[1:]:
        if len(current_line + ' ' + word) * font_size <= max_width:
            current_line += ' ' + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

@app.route('/')
def get_latest_watch():
    history = ytmusic.get_history()  # Consigo el historial entero
    last_watched = history[0]
    title = last_watched['title']
    thumbnail_url = last_watched['thumbnails'][0]['url']
    artist = last_watched['artists'][0]['name']

    # Descargo la imagen y la convierto a base64
    base64_image = image_to_base64(thumbnail_url)
    if base64_image is None:
        return "Error al obtener la imagen", 500
    base64_gif = gif_to_base64(constants.gif_path)

    if base64_gif is None:
        return "Error al obtener el GIF", 500

    # Creo el archivo
    svg_filename = "image.svg"
    svg_path = os.path.join(image_folder, svg_filename)

    # Cálculo del tamaño del texto
    wrapped_title = wrap_text(title, constants.max_width, constants.font_size)
    y_position = 30
    for line in wrapped_title:
        y_position += constants.font_size + 5 # Espacio entre líneas

    y_position += constants.font_size + 5 # El texto del artista

    svg_height = y_position + 30
    dwg = svgwrite.Drawing(svg_path, profile='tiny', size=(constants.svg_width, svg_height))
    dwg.add(dwg.rect(insert=(0, 0), size=(constants.svg_width, svg_height), fill="white"))

    # Agrego la pesca de los textos (diría que estas medidas van bien)
    y_position = 30
    for line in wrapped_title:
        dwg.add(dwg.text(line, insert=(150, y_position), font_size=constants.font_size, fill='black', font_weight="bold", text_anchor="start"))
        y_position += constants.font_size + 5
    dwg.add(dwg.text(artist, insert=(150, y_position), font_size=constants.font_size, fill='black', text_anchor="start"))

    # Altura total del bloque de texto (título + artista)
    total_text_height = y_position - 30  # Altura total del texto (sin incluir el margen superior)
    center_y = (total_text_height - constants.image_height) / 2 + 30  # Centrado en el eje Y respecto al bloque de texto

    # Imagen a la izquierda, centrada con respecto al texto
    dwg.add(dwg.image(f"data:image/png;base64,{base64_image}", insert=(constants.image_x, center_y), size=(100, 100)))
    dwg.add(dwg.image(f"data:image/gif;base64,{base64_gif}", insert=(constants.gif_x, center_y), size=(100, 100)))

    # Guardo el fichero y lo devuelvo
    dwg.save()
    return send_file(svg_path, mimetype='image/svg+xml')
