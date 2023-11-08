import os
import discord
from discord.ext import commands
import openai
from tmdbv3api import TMDb, Movie
from dotenv import load_dotenv
import re
import asyncio
from arrapi import RadarrAPI
import arrapi.exceptions

import time



# Load environment variables from .env file
load_dotenv()

# Get the TMDb and OpenAI API keys from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Radarr settings
RADARR_URL = os.getenv("RADARR_URL")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")

# Configure TMDb with the API key
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY

# Create a Movie object to search for movies
movie = Movie()

# Setup RadarrAPI instance
radarr = RadarrAPI(RADARR_URL, RADARR_API_KEY)

# Configure OpenAI API key
openai.api_key = OPENAI_API_KEY

message_movie_map = {}

def get_openai_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "First off, never list more than 20 movies in your response. It's very important that you never name or list more than 20 movies in your response. You are a helpful assistant with a ton of movie knowledge. Whenever you count things or list them go 1 through 9 then go to A then B then C and so on until K. Whenever you send a new message with a new list, even if it's a continuation of another list, always start over at 1 then count up to 9 then start at A and go to K. That is always how you will count lists. Whenever you use a movie title, use the title the exact way it is used on the TMDB website including capitalization, spelling, punctuation and spacing. It is imperative that the movie titles you give me match the titles on TMBDB perfectly. Whenever you use a movie title, please signify it by surrounding it with asterisks like *Movie Title* (Year). Never list or name more than 20 movies in a response even if I ask you to."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message['content'].strip()

def check_for_movie_title_in_string(text):
    movie_titles_map = {}
    phrases_in_stars = re.findall(r"\*([^*]+)\* \(\d{4}\)", text)  # Adjusted regex

    for phrase in phrases_in_stars:
        search_phrase = phrase  # No need to escape apostrophes
        results = movie.search(search_phrase)
        print(f"\nSearch phrase: '{search_phrase}'")
        print("Results:")

        time.sleep(0.1)  # Introduce a delay

        for idx, result in enumerate(results):
            if isinstance(result, dict) and 'title' in result and 'id' in result:
                print(f"  Result {idx + 1}: {result}")
                tmdb_title = result['title']
            elif hasattr(result, 'title') and hasattr(result, 'id'):
                print(f"  Result {idx + 1}: Title - {result.title}, ID - {result.id}")
                tmdb_title = result.title
            else:
                print(f"  Result {idx + 1}: Invalid format")
                continue

            if tmdb_title:
                movie_titles_map[phrase] = tmdb_title
                break  # Stop after finding the first valid result

    return movie_titles_map





intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

conversations = {}
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

@client.command(name='!')
async def ask(ctx, *, question):
    emojis = [
        '\u0031\uFE0F\u20E3', '\u0032\uFE0F\u20E3', '\u0033\uFE0F\u20E3', '\u0034\uFE0F\u20E3',
        '\u0035\uFE0F\u20E3', '\u0036\uFE0F\u20E3', '\u0037\uFE0F\u20E3', '\u0038\uFE0F\u20E3', '\u0039\uFE0F\u20E3',
        '\U0001F1E6', '\U0001F1E7', '\U0001F1E8', '\U0001F1E9', '\U0001F1EA', '\U0001F1EB', '\U0001F1EC', '\U0001F1ED',
        '\U0001F1EE', '\U0001F1EF', '\U0001F1F0'
    ]

    channel_id = str(ctx.channel.id)
    if channel_id not in conversations:
        conversations[channel_id] = [
            {"role": "system", "content": "First off, never list more than 20 movies in your response. It's very important that you never name or list more than 20 movies in your response. You are a helpful assistant with a ton of movie knowledge. Whenever you count things or list them go 1 through 9 then go to A then B then C and so on until K. Whenever you send a new message with a new list, even if it's a continuation of another list, always start over at 1 then count up to 9 then start at A and go to K. That is always how you will count lists. Whenever you use a movie title, use the title the exact way it is used on the TMDB website including capitalization, spelling, punctuation and spacing. It is imperative that the movie titles you give me match the titles on TMBDB perfectly. Whenever you use a movie title, please signify it by surrounding it with asterisks like *Movie Title* (Year). Never list or name more than 20 movies in a response even if I ask you to."}
        ]

    conversations[channel_id].append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversations[channel_id],
        temperature=0.8,
        max_tokens=750
    ).choices[0].message['content'].strip()

    print(f"GPT Response: {response}")

    conversations[channel_id].append({"role": "assistant", "content": response})

    movie_titles_map = check_for_movie_title_in_string(response)

    number_of_movies_found = len(movie_titles_map)
    print(f"Number of movies found in GPT response: {number_of_movies_found}")
    

    response_chunk = response.replace("*", "'")
    for index, (original_title, tmdb_title) in enumerate(movie_titles_map.items()):
        emoji = emojis[index % len(emojis)]  # Loop over emojis if more movies than emojis
        escaped_original_title = re.escape(original_title)
        pattern = re.compile(f"'{escaped_original_title}'", re.IGNORECASE)
        response_chunk = pattern.sub(f"'{tmdb_title}' {emoji}", response_chunk)

    max_length = 2000
    response_segments = [response_chunk[i:i+max_length] for i in range(0, len(response_chunk), max_length)]

    for response_segment in response_segments:
        msg = await ctx.send(f"OpenAI:\n {response_segment}")
        for emoji in emojis[:number_of_movies_found]:
            await msg.add_reaction(emoji)

        message_movie_map[msg.id] = movie_titles_map

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in emojis[:number_of_movies_found] and reaction.message.id == msg.id

        last_reaction_time = time.time()
        while True:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)  # Shorter timeout for each reaction
                selected_emoji = str(reaction.emoji)
                selected_movie = next((tmdb_title for original_title, tmdb_title in movie_titles_map.items() if f"'{tmdb_title}' {selected_emoji}" in response_segment), None)

                if selected_movie:
                    try:
                        search = radarr.search_movies(selected_movie)
                        if search:
                            search[0].add("/data/media/movies", "this")
                            await ctx.send(f"Added '{selected_movie}' to Radarr.")
                        else:
                            await ctx.send(f"Failed to find '{selected_movie}' in Radarr database.")
                    except Exception as e:
                        await ctx.send(f"You already have '{selected_movie}'!")
                last_reaction_time = time.time()
            except asyncio.TimeoutError:
                if time.time() - last_reaction_time > 60:  # If no reactions for 60 seconds
                    break  # Exit the loop if no reactions for a while

@client.event
async def on_reaction_add(reaction, user):
    if user != client.user and reaction.message.id in message_movie_map:
        selected_movie = None
        for title, tmdb_title in message_movie_map[reaction.message.id].items():
            if f"'{tmdb_title}' {reaction.emoji}" in reaction.message.content:
                selected_movie = tmdb_title
                break

        if selected_movie:
            try:
                search = radarr.search_movies(selected_movie)
                if search:
                    search[0].add("/data/media/movies", "this")
                    # Movie added to Radarr, no message needed
                else:
                    # Movie not found in Radarr, but no message needed
                    pass
            except arrapi.exceptions.Exists:
                # Movie already in Radarr, no message needed
                pass

            except Exception:
                # General error, but no message needed
                pass



client.run(DISCORD_TOKEN)
