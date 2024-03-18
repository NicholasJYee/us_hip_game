import pydicom
import io
import csv
import time
import re
import os

from flask import Flask, render_template, jsonify, send_file, request, redirect, session, flash
from flask_session import Session
from game import Game
from PIL import Image

# Initialize applications
app = Flask(__name__, static_folder='../data')

# Configure the secret key for sessions
app.config['SECRET_KEY'] = 'super_duper_secret_key_that_no_one_can_guess' # can be anything
# Configure server-side session management
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def index():
    if 'game' in session:
        del session['game']
    game = Game()
    session['game'] = game
        
    # Render the main page
    return render_template('index.html')

@app.route('/game', methods=['POST'])
def game_path():
    game = session['game']
    
    # Get preferred name from the form
    name = request.form.get('name')
    
    # Sanitize the name by allowing only letters, numbers
    game.name = re.sub(r'[^a-zA-Z0-9]', '', name) if name else 'zUnknown'
    
    game.last_action_time = time.time()
    
    session['game'] = game
    image_path = game.get_current_image_path()
    return render_template('game.html', image_path=image_path)

@app.route('/keypress/<key>', methods=['GET'])
def keypress(key):
    game = session['game']

    # Return the image path based on the key pressed
    image_path = game.handle_keypress(key)
    session['game'] = game
    if image_path:
        return jsonify({'success': True, 'image_path': image_path})
    else:
        return jsonify({'success': False, 'redirect': '/endgame'})

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    print(image_path)
    dicom_path = image_path
    ds = pydicom.dcmread(dicom_path)
    
    # Convert DICOM to PIL Image
    img = Image.fromarray(ds.pixel_array)
    
    # Save PIL Image to a BytesIO object in PNG format
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)  # Go to the start of the BytesIO object
    
    # Serve the image directly
    return send_file(img_byte_arr, mimetype='image/png')

@app.route('/endgame', methods=['GET'])
def endgame_get():
    return render_template('endgame.html', game=session['game'])

@app.route('/endgame', methods=['POST'])
def endgame_post():
    game = session['game']
    
    is_fractured_guess = request.form.get('boneStatus')
    confidence_level = request.form.get('confidence')
    
    # Save csv in output/game folder
    output_folder = 'output/game/'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filename = f'{output_folder}{game.name}_{game.status}_{is_fractured_guess}_{confidence_level}_{game.pig}_{game.laterality}_{time.strftime("%Y%m%d-%H%M%S")}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Probe position','Action', 'Time'])
        writer.writerows(game.actions)

    print(f"Game ended. Actions and time taken saved to {filename}.")
    
    # Clean up session
    del session['game']
    
    flash('Submitted. Thank you for participating!')
    
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True,
            host='0.0.0.0',
            port=5001
    )   