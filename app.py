import os
from flask import Flask, request, redirect, jsonify, render_template, send_from_directory
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import secure_filename
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from flask_cors import CORS

# Setup Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Allow cross-origin requests

# Spotify credentials
CLIENT_ID = '49d17535644b47db9bc3b5dd8e54ff71'
CLIENT_SECRET = '2da36fcfb6f744eb8af3d54581d2399d'
REDIRECT_URI = 'http://localhost:5000/callback'
SCOPE = "user-library-read playlist-modify-public"
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# CLIP Model and Processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Define mood labels
moods = ["happy", "sad", "energetic", "calm", "relaxing", "neutral", "excited", "chill", "romantic", "angry", "playful", "melancholy"]

# Analyze image to predict mood
def analyze_image(image_path):
    image = Image.open(image_path)
    inputs = processor(text=moods, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    mood_index = logits_per_image.argmax()
    return moods[mood_index]

# Home route for form submission
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle image upload and playlist creation
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if file and file.filename.endswith(('jpg', 'jpeg', 'png')):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, filename)
            file.save(image_path)

            genre = request.form.get('genre', 'pop')
            num_songs = int(request.form.get('num_songs', 10))

            mood = analyze_image(image_path)
            
            # Now create the playlist
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                return jsonify({"error": "Spotify authentication required"}), 401

            sp = spotipy.Spotify(auth=token_info['access_token'])

            # Search for tracks based on mood and genre
            query = f"{mood} {genre}"
            results = sp.search(q=query, type='track', limit=int(num_songs))
            track_uris = [track['uri'] for track in results['tracks']['items']]

            # Create playlist
            user_id = sp.current_user()['id']
            playlist_name = f"{mood.capitalize()} Mood Playlist - {genre.capitalize()}"
            playlist = sp.user_playlist_create(user_id, playlist_name, public=True)
            sp.playlist_add_items(playlist['id'], track_uris)

            playlist_url = playlist['external_urls']['spotify']

            # Return the form and show playlist URL
            return render_template('home.html', playlist_url=playlist_url, mood=mood, genre=genre, num_songs=num_songs, image_url=f'/static/uploads/{filename}')

    return render_template('home.html')

# Serve uploaded images
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'uploads'), filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
