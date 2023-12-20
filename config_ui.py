from flask import Flask, request, render_template
import yaml
import os
import threading

app = Flask(__name__)

def start_bot():
    # Function to start the bot
    os.system('python RunThis.py')  # Replace with the path to your bot file if needed

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get data from form
        tmdb_api_key = request.form.get('tmdb_api_key')
        radarr_url = request.form.get('radarr_url')
        radarr_api_key = request.form.get('radarr_api_key')
        openai_api_key = request.form.get('openai_api_key')
        discord_token = request.form.get('discord_token')
        

        # Write to config file
        with open('config.yaml', 'w') as file:
            yaml.dump({
                'tmdb_api_key': tmdb_api_key,
                'radarr_url': radarr_url,
                'radarr_api_key': radarr_api_key,
                'openai_api_key': openai_api_key,
                'discord_token': discord_token  # Add this line
            }, file)

        # Start bot in a new thread
        threading.Thread(target=start_bot).start()
        return "Bot is starting..."

    return render_template('index.html')  # Render a simple form for input

if __name__ == '__main__':
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            if config and all(key in config for key in ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key']):
                # If config exists and is valid, start bot
                threading.Thread(target=start_bot).start()
            else:
                app.run(host='0.0.0.0', port=1138)  # Start Flask server
    else:
        app.run(host='0.0.0.0', port=1138)  # Start Flask server
