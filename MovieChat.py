import os
import discord
from discord.ext import commands
import openai
from tmdbv3api import TMDb, Movie
from dotenv import load_dotenv
import re
import requests
import asyncio
from arrapi import RadarrAPI
import more_itertools

# Load environment variables from .env file
load_dotenv()

# Get the TMDb and OpenAI API keys from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Radarr settings
RADARR_URL = os.getenv("RADARR_URL")  # Replace with your Radarr URL
# Replace with your Radarr API key
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

# Function to get response from OpenAI API
def get_openai_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant with a ton of movie knowledge. Whenever you count things or list them go 1 through 9 then go to A then B then C and so on until K.  Please place any movie titles in single quotes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message['content'].strip()

# Use the OpenAI API to get a text response
prompt = "Hey there. Do you like movies?"
sample_text = get_openai_response(prompt)
print(f"{sample_text}")

def check_for_movie_title_in_string(text):
    found_movies_dict = {}  # Dictionary to store found movie titles and their tmdbIds

    # Use regular expressions to find all phrases enclosed in single quotes
    phrases_in_quotes = re.findall(r"'(.*?)'", text)

    for phrase in phrases_in_quotes:
        # Skip the check if the phrase is too long
        if len(phrase.split()) > 10:
            continue

        print(f"Searching TMDb for: {phrase}")
        results = movie.search(phrase)
        for result in results:
            movie_title = result.title
            tmdbId = result.id  # Added line to capture tmdbId
            popularity = result.popularity
            vote_average = result.vote_average
            vote_count = result.vote_count

            print(
                f"Received from TMDb: {movie_title} with popularity {popularity}")

            if (
                movie_title.lower() in text.lower()
                and vote_average >= 0
                and vote_count >= 0
                and popularity > 0
            ):
                # Only add the movie if it's not already in the dictionary
                if movie_title not in found_movies_dict:
                    found_movies_dict[movie_title] = {'title': movie_title, 'tmdbId': tmdbId}
                    print(f"Added: {movie_title}")

    # Convert the dictionary back to a list of movies before returning it
    found_movies = list(found_movies_dict.values())
    print(found_movies)
    return found_movies

# Create a new Discord client
# Create a new Discord client with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

conversations = {}

# Get the Discord token from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

@client.command(name='!')
async def ask(ctx, *, question):
    # Get the conversation history for this channel
    channel_id = str(ctx.channel.id)
    if channel_id not in conversations:
        conversations[channel_id] = [
            {"role": "system", "content": "You are a helpful assistant with a ton of movie knowledge. Every time you name a movie put it in single quotes."}
        ]

    # Add the user's message to the conversation history
    conversations[channel_id].append({"role": "user", "content": question})

    # Get the response from OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversations[channel_id],
        temperature=0.8,
        max_tokens=750
    ).choices[0].message['content'].strip()

    # Add the OpenAI's response to the conversation history
    conversations[channel_id].append(
        {"role": "assistant", "content": response})

    found_movie_titles = check_for_movie_title_in_string(response)

    if found_movie_titles:
        emojis = [
    '\u0031\uFE0F\u20E3', '\u0032\uFE0F\u20E3', '\u0033\uFE0F\u20E3', '\u0034\uFE0F\u20E3',
    '\u0035\uFE0F\u20E3', '\u0036\uFE0F\u20E3', '\u0037\uFE0F\u20E3', '\u0038\uFE0F\u20E3', '\u0039\uFE0F\u20E3',
    '\U0001F1E6', '\U0001F1E7', '\U0001F1E8', '\U0001F1E9', '\U0001F1EA', '\U0001F1EB', '\U0001F1EC', '\U0001F1ED',
    '\U0001F1EE', '\U0001F1EF', '\U0001F1F0'
]

        emoji_movie_map = dict(zip(emojis, found_movie_titles))  # Create map for this chunk
        response_chunk = response
        for emoji, movie in emoji_movie_map.items():
            # Using regex to replace movie titles with title + emoji
            pattern = re.compile(
                re.escape(f"'{movie['title']}'"), re.IGNORECASE)
            response_chunk = pattern.sub(f"'{movie['title']}' {emoji}", response_chunk)

        # Split the response_chunk into smaller chunks if it's too long
        max_length = 2000
        response_segments = [response_chunk[i:i+max_length] for i in range(0, len(response_chunk), max_length)]

        for response_segment in response_segments:
            # Print the OpenAI response with emojis to the Discord chat
            msg = await ctx.send(f"OpenAI: {response_segment}")

            for emoji in emoji_movie_map.keys():  # Updated line
                await msg.add_reaction(emoji)

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in emoji_movie_map and reaction.message.id == msg.id

            while True:
                reaction, user = await client.wait_for('reaction_add', check=check)
                movie = emoji_movie_map[str(reaction.emoji)]

# Run the Discord client
client.run(DISCORD_TOKEN)
