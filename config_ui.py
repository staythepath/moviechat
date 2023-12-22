from flask import Flask, request, render_template
import yaml
import os
import threading

app = Flask(__name__)

# Function to load or create configuration
def load_or_create_config():
    config_path = 'config.yaml'
    config = {}

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        # Set MAX_CHARS based on the selected model
        if config.get('selected_model') == 'gpt-3.5-turbo-1106':
            config['max_chars'] = 65540
        elif config.get('selected_model') == 'gpt-4-1106-preview':
            config['max_chars'] = 512000

        # Save the config to a file
        with open(config_path, 'w') as file:
            yaml.dump(config, file)

    return config


def start_bot(config):
    # Function to start the bot
    os.system('python RunThis.py')

def check_and_start_bot():
    config = load_or_create_config()
    required_keys = ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model', 'max_chars']
    if all(key in config and config[key] for key in required_keys): 
        threading.Thread(target=start_bot, args=(config,)).start()




        
@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_or_create_config()
    if request.method == 'POST':
        # Update config from form data
        for key in ['tmdb_api_key', 'radarr_url', 'radarr_api_key', 'openai_api_key', 'discord_token', 'radarr_quality', 'selected_model']:
            config[key] = request.form.get(key, config.get(key))
        
        # Set MAX_CHARS based on the selected model
        selected_model = config.get('selected_model')
        if selected_model == 'gpt-3.5-turbo-1106':
            config['max_chars'] = 65540
        elif selected_model == 'gpt-4-1106-preview':
            config['max_chars'] = 512000

        # Write updated configuration to file
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file)
        
        # Restart the bot to apply new configuration
        threading.Thread(target=start_bot, args=(config,)).start()
        return "Bot is restarting with new configuration..."

    return render_template('index.html', config=config)

if __name__ == '__main__':
    check_and_start_bot()
    app.run(host='0.0.0.0', port=1138)
