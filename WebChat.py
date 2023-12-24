import os
import discord
from discord.ext import commands
import openai
from openai import OpenAI
from tmdbv3api import TMDb, Movie
import re
import asyncio
from arrapi import RadarrAPI
import arrapi.exceptions
import yaml
import time
from flask import request

# Read the YAML config file
import yaml

def load_config():
    config_path = 'config.yaml'
    default_config = {
        'discord_token': '',
        'tmdb_api_key': '',
        'radarr_api_key': '',
        'radarr_url': '',
        'openai_api_key': '',
        'radarr_quality': '',
        'selected_model': '',
        'max_chars': 65540,  # Default value, can be adjusted
        'discord_channel': '',
        'radarr_root_folder': ''
    }

    if not os.path.exists(config_path):
        # File doesn't exist, create it with default configuration
        with open(config_path, 'w') as file:
            yaml.dump(default_config, file)
        return default_config

    # File exists, load and return its content
    with open(config_path, 'r') as file:
        return yaml.safe_load(file) or default_config

# Rest of the WebChat.py code...


# Load configuration
config = load_config()

# Using variables from config
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
if config['radarr_url'] and config['radarr_api_key']:
    radarr = RadarrAPI(config['radarr_url'], config['radarr_api_key'])
else:
    radarr = None

# Configure TMDb, Movie, RadarrAPI, and OpenAI with the settings from config
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
movie = Movie()


message_movie_map = {}
segment_emoji_map = {}




def trim_conversation_history(conversation_history, new_message):
    conversation_history.append(new_message)
    total_chars = sum(len(msg['content']) for msg in conversation_history)
    while total_chars > MAX_CHARS and len(conversation_history) > 1:
        removed_message = conversation_history.pop(0)
        total_chars -= len(removed_message['content'])
    return conversation_history


def get_openai_response(conversation_history, prompt):
    config = load_config()

    # Update variables with new config values
    OPENAI_API_KEY = config['openai_api_key']
    SELECTED_MODEL = config['selected_model']

    # Initialize OpenAI client with the new API key
    client = OpenAI(api_key=OPENAI_API_KEY)
    

    new_message = {"role": "user", "content": prompt}
    conversation_history.append(new_message)

    messages = [
        {"role": "system", "content": "You are a fun and informative conversational bot focused on movies. Never put quotes around movie titles. Always leave movie title unquoted. You never under any circumstances number any list. When you do list movies put each movie on it's own line. When mentioning movies in any capacity, always enclose the movies title in asterisks with the year in parentheses and always include the year after the title, like ' *Movie Title* (Year)', e.g., '*Jurassic Park* (1994)' . Every single time you say a movie title it needs to be wrapped in asteriks and it needs to have the year after the title. Ensure movie titles exactly match those on the TMDB website, including capitalization, spelling, punctuation, and spacing. For lists, use a dash (-) instead of numbering, and never list more than 20 movies. Be conversational and engage with the user's preferences, including interesting movie facts. Only create lists when it's relevant or requested by the user. Avoid creating a list in every message. You're here to discuss movies, not just list them."}  # System message
    ] + conversation_history

    print("This is convo history:  ", conversation_history)

    response = client.chat.completions.create(model=SELECTED_MODEL, messages=messages, temperature=0)
    response_content = response.choices[0].message.content.strip() if response.choices else "No response received."
    print("This is the response content: ", response_content)

    # Process movie titles
    movie_titles_map = check_for_movie_title_in_string(response_content)
    print("Movie titles map: ", movie_titles_map)
    for title, tmdb_id in movie_titles_map.items():
        link = f"{RADARR_URL}/add_movie_to_radarr/{tmdb_id}"
        response_content = response_content.replace(f"*{title}*", f"<span onclick='addMovieToRadarr({tmdb_id})' class='movie-link'>{title}</span>")

    return response_content
    


def check_for_movie_title_in_string(text):
    movie_titles_map = {}
    phrases_in_stars = re.findall(r"\*\"?([^*]+)\"?\*(?: \(\d{4}\))?", text)  # Adjusted regex

    for phrase in phrases_in_stars:
        search_phrase = phrase  # No need to escape apostrophes
        results = movie.search(search_phrase)
        print(f"\nSearch phrase: '{search_phrase}'")
        print("Results:")

        time.sleep(0.3)  # Introduce a delay

        for idx, result in enumerate(results):
            if isinstance(result, dict) and 'title' in result and 'id' in result:
                print(f"  Result {idx + 1}: {result}")
                tmdb_id = result['id']  # Use the ID instead of the title
            elif hasattr(result, 'title') and hasattr(result, 'id'):
                print(f"  Result {idx + 1}: Title - {result.title}, ID - {result.id}")
                tmdb_id = result.id  # Use the ID instead of the title
            else:
                print(f"  Result {idx + 1}: Invalid format")
                continue

            if tmdb_id:  # Check if the ID is present
                movie_titles_map[phrase] = tmdb_id  # Store the ID as the value
                break  # Stop after finding the first valid result

    return movie_titles_map




conversations = {}





