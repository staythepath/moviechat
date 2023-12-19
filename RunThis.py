import os
import discord
from discord.ext import commands
import openai
from openai import OpenAI
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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

message_movie_map = {}
segment_emoji_map = {}

def get_openai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "First off, never list more than 20 movies in your response. It's very important that you never name or list more than 20 movies in your response. You are a helpful assistant with a ton of movie knowledge. Whenever you count things or list them go 1 through 9 then go to A then B then C and so on until K. Whenever you send a new message with a new list, even if it's a continuation of another list, always start over at 1 then count up to 9 then start at A and go to K. Never leave a line space( an empty line) between 9 and A. That is always how you will count lists. Whenever you use a movie title, use the title the exact way it is used on the TMDB website including capitalization, spelling, punctuation and spacing. It is imperative that the movie titles you give me match the titles on TMBDB perfectly. Whenever you use a movie title, please signify it by surrounding it with asterisks like *Movie Title* (Year). Every single time you list a movie title make sure you surround the titles with * like this *Movie Title*. Do it every single time you put a movie in a list. Never list or name more than 20 movies in a response even if I ask you to. You don't have to list 20 movies every time. If a more accurate response would be to name less movies do so. There is no need to try to list exactly 20 movies on all your responses. Only list as many movies that will answer the question accurately."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        # Extracting the message content from the response
        if response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "No response received."
    except Exception as e:
        print(f"An error occurred: {e}")
        return "No response received."



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
client1 = commands.Bot(command_prefix='!', intents=intents)

conversations = {}
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

@client1.event
async def on_ready():
    print(f'Logged in as {client1.user.name}')

@client1.command(name='!')
async def ask(ctx, *, question):
    emojis = [
        '\u0031\uFE0F\u20E3', '\u0032\uFE0F\u20E3', '\u0033\uFE0F\u20E3', '\u0034\uFE0F\u20E3',
        '\u0035\uFE0F\u20E3', '\u0036\uFE0F\u20E3', '\u0037\uFE0F\u20E3', '\u0038\uFE0F\u20E3', '\u0039\uFE0F\u20E3',
        '\U0001F1E6', '\U0001F1E7', '\U0001F1E8', '\U0001F1E9', '\U0001F1EA', '\U0001F1EB', '\U0001F1EC', '\U0001F1ED',
        '\U0001F1EE', '\U0001F1EF', '\U0001F1F0'
    ]

    # Get the response from the OpenAI API
    openai_response = get_openai_response(question)

    # Process the movie list
    movie_titles_map = check_for_movie_title_in_string(openai_response)

    # Initialize an empty list to hold the new response
    new_response_lines = []

    global_emoji_index = 0  # Global index to keep track of emoji assignment across all segments

    # Split the OpenAI response into lines
    openai_response_lines = openai_response.split('\n')

    # Process each line
    for line in openai_response_lines:
        match = re.search(r"\*([^*]+)\* \((\d{4})\)", line)
        if match and global_emoji_index < len(emojis):
            original_title = match.group(1)
            year = match.group(2)
            tmdb_title = movie_titles_map.get(original_title, original_title)
            emoji = emojis[global_emoji_index]
            new_line = f"{emoji} *{tmdb_title}* ({year})" + line[match.end():]
            new_response_lines.append(new_line)
            global_emoji_index += 1
        else:
            new_response_lines.append(line)

    # Join the new lines to form the updated response
    response_chunk = "\n".join(new_response_lines)

    # Splitting response into chunks
    max_length = 1900
    response_segments = [response_chunk[i:i+max_length] for i in range(0, len(response_chunk), max_length)]

    # Variables to track the start and end of emojis for each segment
    segment_start_index = 0

    for response_segment in response_segments:
        msg = await ctx.send(f"\n{response_segment}")

        segment_end_index = segment_start_index + response_segment.count('*') // 2  # Count the pairs of asterisks

        # Add reactions for the current segment
        for i in range(segment_start_index, min(segment_end_index, len(emojis))):
            await msg.add_reaction(emojis[i])

        # Update the emoji map for the segment
        segment_emoji_map[msg.id] = emojis[segment_start_index:segment_end_index]

        # Update the start index for the next segment
        segment_start_index = segment_end_index

        message_movie_map[msg.id] = movie_titles_map




@client1.event
async def on_reaction_add(reaction, user):
    if user != client1.user and reaction.message.id in message_movie_map:
        if reaction.message.id in segment_emoji_map:
            message_emojis = segment_emoji_map[reaction.message.id]
            emoji_index = message_emojis.index(str(reaction.emoji)) if str(reaction.emoji) in message_emojis else -1

            if emoji_index != -1:
                selected_movie = list(message_movie_map[reaction.message.id].values())[emoji_index]

                if selected_movie:
                    try:
                        # Search for the movie in Radarr
                        search = radarr.search_movies(selected_movie)
                        if search:
                            # Add the movie to Radarr if found
                            search[0].add("/data/media/movies", "OK")
                            await reaction.message.channel.send(f"'{selected_movie}' has been added to Radarr.")
                        else:
                            # No message needed if the movie is not found in Radarr
                            pass
                    except arrapi.exceptions.Exists:
                        # If the movie already exists in Radarr
                        await reaction.message.channel.send(f"You already have '{selected_movie}' in Radarr.")
                    except Exception as e:
                        # Handle other exceptions if necessary
                        await reaction.message.channel.send(f"Error: {e}")




client1.run(DISCORD_TOKEN)
