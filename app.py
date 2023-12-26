from flask import Flask, request, render_template, jsonify, session
import yaml
import os
import threading
import discord
import asyncio
import WebChat
from arrapi import RadarrAPI
import arrapi.exceptions
import requests
from tmdbv3api import TMDb, Movie
import subprocess
import multiprocessing


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

channels_data = []

def start_discord_bot_process():
    subprocess.Popen(['python', 'RunThis.py'])

def load_config():
    config_path = 'config.yaml'
    if not os.path.exists(config_path):
        create_default_config(config_path)
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
    
def create_default_config(config_path):
    default_config = {
        'tmdb_api_key': '',
        'radarr_url': '',
        'radarr_api_key': '',
        'openai_api_key': '',
        'discord_token': '',
        'radarr_quality': '',
        'selected_model': '',
        'max_chars': 65540,
        'discord_channel': '',
        'radarr_root_folder': ''
    }
    with open(config_path, 'w') as file:
        yaml.dump(default_config, file)
    
def initialize_radarr(config):
    try:
        if config['radarr_url'] and config['radarr_api_key']:
            return RadarrAPI(config['radarr_url'], config['radarr_api_key'])
    except Exception as e:
        print(f"Error initializing Radarr API: {e}")
        return None

config = load_config()
# Set the root folder during initialization

DISCORD_TOKEN = config['discord_token']
TMDB_API_KEY = config['tmdb_api_key']
RADARR_API_KEY = config['radarr_api_key']
RADARR_URL = config['radarr_url']
OPENAI_API_KEY = config['openai_api_key']
RADARR_QUALITY = config["radarr_quality"]
MAX_CHARS = config['max_chars']
SELECTED_MODEL = config['selected_model']
RADARR_ROOT_FOLDER = config['radarr_root_folder']




if RADARR_URL and RADARR_API_KEY:
    try:
        radarr = RadarrAPI(RADARR_URL, RADARR_API_KEY)
        # ... [rest of your RadarrAPI related code]
    except Exception as e:
        print(f"Error initializing Radarr API: {e}")
        radarr = None  # Handle the error gracefully
else:
    print("Radarr URL or API Key is not configured.")
    radarr = None  # Skip RadarrAPI initialization


# Function to load or create configuration
def load_or_create_config():
    config_path = 'config.yaml'
    default_config = {
        'tmdb_api_key': '',
        'radarr_url': '',
        'radarr_api_key': '',
        'openai_api_key': '',
        'discord_token': '',
        'radarr_quality': '',
        'selected_model': '',
        'max_chars': 65540,  # Default value for gpt-3.5-turbo-1106
        'discord_channel': '',
        'radarr_root_folder': ''
    }

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file) or default_config
    else:
        config = default_config
        with open(config_path, 'w') as file:
            yaml.dump(config, file)

    # Update MAX_CHARS based on the selected model
    model = config.get('selected_model')
    if model == 'gpt-4-1106-preview':
        config['max_chars'] = 512000

    return config

def start_bot(config):
    # Function to start the bot
    os.system('python RunThis.py') 

def check_and_start_bot():
    config = load_or_create_config()
    # Check if the start_discord_bot_on_launch key is true
    if config.get('start_discord_bot_on_launch', True):
        required_keys = ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model', 'max_chars', 'discord_channel']
        if all(key in config and config[key] for key in required_keys): 
            threading.Thread(target=start_bot, args=(config,)).start()
    else:
        print("Discord bot startup is disabled in the configuration.")


async def get_channels(token):
    global channels_data
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channels_data.clear()
        for guild in client.guilds:
            for channel in guild.text_channels:
                channels_data.append({'id': str(channel.id), 'name': channel.name})

        await client.close()

    await client.login(token)
    await client.start(token)

def start_discord_client(token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(get_channels(token))

@app.route('/server_status')
def server_status():
    # Simple status check. You can add more complex logic if needed.
    return jsonify({'status': 'ready'})

@app.route('/channels', methods=['GET'])
def channels_endpoint():
    token = request.args.get('token')
    if token:
        thread = threading.Thread(target=start_discord_client, args=(token,))
        thread.start()
        thread.join()
        print("Here is the channel data from the api call", channels_data)
    return jsonify(channels_data)

@app.route('/load_config', methods=['GET'])
def load_config_endpoint():
    # Call the load_config() function here to reload the configuration
    loaded_config = load_config()
    
    # You can return a response or log a message if needed
    print('Configuration reloaded on the server')
    
    return jsonify({'message': 'Configuration reloaded on the server'})


@app.route('/fetch_root_folders')
def fetch_root_folders():
    config = load_config()
    radarr_url = config.get('radarr_url')
    radarr_api_key = config.get('radarr_api_key')

    if radarr_url and radarr_api_key:
        try:
            url = f"{radarr_url}/api/v3/rootfolder"
            headers = {'X-Api-Key': radarr_api_key}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                root_folders = response.json()
                return jsonify(root_folders)
            else:
                print(f"Error fetching Radarr root folders: HTTP {response.status_code}")
                return jsonify([])
        except Exception as e:
            print(f"Error fetching Radarr root folders: {e}")
            return jsonify([])

    return jsonify([])

        
@app.route('/', methods=['GET', 'POST'])
def index():
    global radarr 
    config = load_or_create_config()

    
    if request.method == 'POST':
        # Update config from form data only if the input is not empty
        for key in ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model', 'discord_channel']:
            form_value = request.form.get(key)
            if form_value:  # Only update if the form input is not empty
                config[key] = form_value
        
         # Update the discord_channel_id separately
        discord_channel_id = request.form.get('discord_channel')
        if discord_channel_id:
            print("Received discord_channel_id:", discord_channel_id) # Logging statement
            config['discord_channel_id'] = discord_channel_id

        # Handling the Radarr root folder
        radarr_root_folder = request.form.get('radarr_root_folder')
        if radarr_root_folder:
            config['radarr_root_folder'] = radarr_root_folder
        
        # Set MAX_CHARS based on the selected model
        selected_model = config.get('selected_model')
        if selected_model == 'gpt-3.5-turbo-1106':
            config['max_chars'] = 65540
        elif selected_model == 'gpt-4-1106-preview':
            config['max_chars'] = 512000

        global radarr
        radarr = initialize_radarr(config)

        

        
        # Restart the bot to apply new configuration
        threading.Thread(target=start_bot, args=(config,)).start()

        start_discord_bot = request.form.get('start_discord_bot_on_launch') == 'on'
        config['start_discord_bot_on_launch'] = start_discord_bot

        # Write updated configuration to file
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file)
          # Start the Discord bot in a separate process
            

    
    radarr = None
    if config.get('radarr_url') and config.get('radarr_api_key'):
        try:
            radarr = RadarrAPI(config['radarr_url'], config['radarr_api_key'])
        except Exception as e:
            print(f"Error initializing Radarr API: {e}")

    # Fetch root folders if RadarrAPI is initialized
    root_folders = []

        
    
    print("Root folders:", root_folders)
    return render_template('index.html', config=config, root_folders=root_folders)

if config.get('start_discord_bot_on_launch', True):
        required_keys = ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model', 'max_chars', 'discord_channel']
        if all(key in config and config[key] for key in required_keys):
            start_discord_bot_process()


@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.json['message']
    print(f"Received message from UI: {message}")

    if 'conversation_history' not in session:
        session['conversation_history'] = []

    conversation_history = session['conversation_history']

    # Removed the line that adds the new message to conversation_history
    response = WebChat.get_openai_response(conversation_history, message)

    session['conversation_history'] = conversation_history
    return jsonify({'response': response})





@app.route('/add_movie_to_radarr/<int:tmdb_id>', methods=['GET'])
def add_movie_to_radarr(tmdb_id):
    config = load_config()
    global radarr
    radarr = initialize_radarr(load_config())

    if radarr is None:
        return jsonify({"status": "error", "message": "Radarr is not configured."})

    tmdb = TMDb()
    tmdb.api_key = config['tmdb_api_key']
    movie = Movie()

    try:
        # Search for the movie in Radarr using its TMDb ID
        search_results = radarr.search_movies(tmdb_id)
        if search_results:
            # Movie already exists in Radarr
            movie_title = search_results[0]['title']
            message = f"*{movie_title}* already exists in Radarr."
            return jsonify({"status": "info", "message": message})
        
        # Fetch movie details from TMDB
        movie_details = movie.details(tmdb_id)
        movie_title = movie_details.title
        RADARR_QUALITY = config["radarr_quality"]
        # Add the movie to Radarr
        radarr.add_movie(root_folder=RADARR_ROOT_FOLDER, quality_profile=RADARR_QUALITY, tmdb_id=tmdb_id, search=True)
        message = f"*{movie_title}* added to Radarr"
        return jsonify({"status": "success", "message": message})
    except Exception as e:
        message = str(e)
        return jsonify({"status": "error", "message": message})






if __name__ == '__main__':
    print("RRRRRRRRRRRRRRRRUNNING")
    config = load_or_create_config()

    DISCORD_TOKEN = config['discord_token']
    TMDB_API_KEY = config['tmdb_api_key']
    RADARR_API_KEY = config['radarr_api_key']
    RADARR_URL = config['radarr_url']
    OPENAI_API_KEY = config['openai_api_key']
    RADARR_QUALITY = config["radarr_quality"]
    MAX_CHARS = config['max_chars']
    SELECTED_MODEL = config['selected_model']
    RADARR_ROOT_FOLDER = config['radarr_root_folder']

    # Conditional initialization of RadarrAPI
    if RADARR_URL and RADARR_API_KEY:
        radarr = RadarrAPI(RADARR_URL, RADARR_API_KEY)
    else:
        radarr = None

    
    # Start the Discord bot in a separate process
    if config.get('start_discord_bot_on_launch', True):
        required_keys = ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model', 'max_chars', 'discord_channel']
        if all(key in config and config[key] for key in required_keys):
            discord_process = multiprocessing.Process(target=start_discord_bot_process)
            start_discord_bot_process()
 
    else:
        print("Discord bot startup is disabled in the configuration.")

    app.run(host='0.0.0.0', port=1138)


    
