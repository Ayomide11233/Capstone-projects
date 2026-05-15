from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import io
import base64
import os

app = Flask(__name__, static_folder='static')

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2])).upper()

def get_color_name_hint(r, g, b):
    """Very rough color family label"""
    h_max = max(r, g, b)
    h_min = min(r, g, b)
    brightness = (r * 299 + g * 587 + b * 114) / 1000

    if h_max - h_min < 30:
        if brightness < 50:
            return "Black"
        elif brightness > 200:
            return "White"
        else:
            return "Gray"

    if r > g and r > b:
        if g > b * 1.5:
            return "Yellow" if g > 150 else "Orange"
        return "Red"
    elif g > r and g > b:
        return "Green"
    elif b > r and b > g:
        if r > 150:
            return "Violet"
        return "Blue"
    elif r > 150 and g > 150 and b < 100:
        return "Yellow"
    elif r > 150 and b > 150 and g < 100:
        return "Magenta"
    elif g > 150 and b > 150 and r < 100:
        return "Cyan"
    return "Mixed"

def extract_colors(image_bytes, n_colors=10):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    # Resize for speed but keep proportions
    img.thumbnail((200, 200), Image.LANCZOS)
    pixels = np.array(img).reshape(-1, 3).astype(float)

    # KMeans clustering to find dominant colors
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10, max_iter=200)
    kmeans.fit(pixels)

    centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)
    total = len(pixels)

    # Sort by frequency
    sorted_indices = np.argsort(counts)[::-1]

    colors = []
    for idx in sorted_indices:
        r, g, b = centers[idx]
        percentage = (counts[idx] / total) * 100
        hex_code = rgb_to_hex([r, g, b])
        label = get_color_name_hint(r, g, b)
        colors.append({
            'hex': hex_code,
            'rgb': {'r': int(r), 'g': int(g), 'b': int(b)},
            'percentage': round(percentage, 1),
            'label': label
        })

    return colors

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/extract', methods=['POST'])
def extract():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    image_bytes = file.read()
    colors = extract_colors(image_bytes, n_colors=10)
    return jsonify({'colors': colors})

if __name__ == '__main__':
    app.run(debug=True, port=5000)