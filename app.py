from flask import Flask, request, render_template, jsonify, session
import subprocess
import threading
import asyncio
import discord
from arrapi import RadarrAPI
from tmdbv3api import TMDb, Movie
import requests
import os
import yaml
import WebChat

from config_manager import ConfigManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

config_manager = ConfigManager()
global radarr
channels_data = []


def start_discord_bot_process():
    subprocess.Popen(["python", "RunThis.py"])


def initialize_radarr():
    try:
        radarr_url = config_manager.get_config_value("radarr_url")
        radarr_api_key = config_manager.get_config_value("radarr_api_key")
        if radarr_url and radarr_api_key:
            return RadarrAPI(radarr_url, radarr_api_key)
    except Exception as e:
        print(f"Error initializing Radarr API: {e}")
        return None


radarr = initialize_radarr()


def check_and_start_bot():
    if config_manager.get_config_value("start_discord_bot_on_launch"):
        required_keys = [
            "tmdb_api_key",
            "radarr_url",
            "radarr_api_key",
            "openai_api_key",
            "discord_token",
            "radarr_quality",
            "selected_model",
            "max_chars",
            "discord_channel",
        ]
        if all(config_manager.get_config_value(key) for key in required_keys):
            threading.Thread(target=start_discord_bot_process).start()
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
                channels_data.append({"id": str(channel.id), "name": channel.name})
        await client.close()

    await client.login(token)
    await client.start(token)


def start_discord_client(token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(get_channels(token))


@app.route("/server_status")
def server_status():
    return jsonify({"status": "ready"})


@app.route("/channels", methods=["GET"])
def channels_endpoint():
    token = request.args.get("token")
    if token:
        thread = threading.Thread(target=start_discord_client, args=(token,))
        thread.start()
        thread.join()
        print("Here is the channel data from the api call", channels_data)
    return jsonify(channels_data)


@app.route("/load_config", methods=["GET"])
def load_config_endpoint():
    config_manager.load_config()  # Reload the configuration
    print("Configuration reloaded on the server")
    return jsonify({"message": "Configuration reloaded on the server"})


@app.route("/fetch_root_folders")
def fetch_root_folders():
    radarr_url = config_manager.get_config_value("radarr_url")
    radarr_api_key = config_manager.get_config_value("radarr_api_key")

    if radarr_url and radarr_api_key:
        try:
            url = f"{radarr_url}/api/v3/rootfolder"
            headers = {"X-Api-Key": radarr_api_key}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                print(
                    f"Error fetching Radarr root folders: HTTP {response.status_code}"
                )
                return jsonify([])
        except Exception as e:
            print(f"Error fetching Radarr root folders: {e}")
            return jsonify([])

    return jsonify([])


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        for key in [
            "tmdb_api_key",
            "radarr_url",
            "radarr_api_key",
            "openai_api_key",
            "discord_token",
            "radarr_quality",
            "selected_model",
            "discord_channel",
        ]:
            form_value = request.form.get(key)
            if form_value:
                config_manager.config[key] = form_value

        discord_channel_id = request.form.get("discord_channel")
        if discord_channel_id:
            config_manager.config["discord_channel_id"] = discord_channel_id

        radarr_root_folder = request.form.get("radarr_root_folder")
        if radarr_root_folder:
            config_manager.config["radarr_root_folder"] = radarr_root_folder

        selected_model = config_manager.get_config_value("selected_model")
        if selected_model == "gpt-3.5-turbo-1106":
            config_manager.config["max_chars"] = 65540
        elif selected_model == "gpt-4-1106-preview":
            config_manager.config["max_chars"] = 512000

        start_discord_bot = request.form.get("start_discord_bot_on_launch") == "on"
        config_manager.config["start_discord_bot_on_launch"] = start_discord_bot

        with open(config_manager.config_path, "w") as file:
            yaml.dump(config_manager.config, file)

        radarr = initialize_radarr()

    root_folders = []
    return render_template(
        "index.html", config=config_manager.config, root_folders=root_folders
    )


if config_manager.get_config_value("start_discord_bot_on_launch"):
    required_keys = [
        "tmdb_api_key",
        "radarr_url",
        "radarr_api_key",
        "openai_api_key",
        "discord_token",
        "radarr_quality",
        "selected_model",
        "max_chars",
        "discord_channel",
    ]
    if all(config_manager.get_config_value(key) for key in required_keys):
        start_discord_bot_process()


@app.route("/send_message", methods=["POST"])
def send_message():
    message = request.json["message"]
    print(f"Received message from UI: {message}")

    if "conversation_history" not in session:
        session["conversation_history"] = []

    conversation_history = session["conversation_history"]
    response = WebChat.get_openai_response(conversation_history, message)
    session["conversation_history"] = conversation_history
    return jsonify({"response": response})


@app.route("/add_movie_to_radarr/<int:tmdb_id>", methods=["GET"])
def add_movie_to_radarr(tmdb_id):
    # Initialize Radarr inside the function
    local_radarr = initialize_radarr()

    if local_radarr is None:
        return jsonify({"status": "error", "message": "Radarr is not configured."})

    tmdb = TMDb()
    tmdb.api_key = config_manager.get_config_value("tmdb_api_key")
    movie_api = Movie()

    try:
        movie_details = movie_api.details(tmdb_id)
        movie_title = movie_details.title
        quality_profile_id = config_manager.get_config_value("radarr_quality")

        response = local_radarr.add_movie(
            tmdb_id=tmdb_id,
            quality_profile=quality_profile_id,
            root_folder=config_manager.get_config_value("radarr_root_folder"),
        )

        if response:
            return jsonify(
                {"status": "success", "message": f"*{movie_title}* added to Radarr"}
            )
        else:
            return jsonify(
                {"status": "error", "message": "Failed to add movie to Radarr"}
            )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
