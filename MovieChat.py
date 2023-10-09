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
            {"role": "system", "content": "You are a helpful assistant with a ton of movie knowledge. Please place any movie titles in single quotes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message['content'].strip()


# Use the OpenAI API to get a text response
prompt = "Show me a short sentence that contains movie titles, but use the titles in the sentence as if they are not movie titles. Use one of the movie titles twice in two different ways in the sentence."
sample_text = get_openai_response(prompt)
print(f"OpenAI API response: {sample_text}")


def check_for_movie_title_in_string(text):
    found_movies = []  # List to store found movie titles and their tmdbIds

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
                and vote_average >= 5
                and vote_count >= 500
                and popularity > 8
            ):
                # Modified to store tmdbId as well
                found_movies.append({'title': movie_title, 'tmdbId': tmdbId})

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
        max_tokens=150
    ).choices[0].message['content'].strip()

    # Add the OpenAI's response to the conversation history
    conversations[channel_id].append(
        {"role": "assistant", "content": response})

    found_movie_titles = check_for_movie_title_in_string(response)

    if found_movie_titles:
        emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
        emoji_movie_map = {emoji: movie for emoji,
                           movie in zip(emojis, found_movie_titles)}

        # Edit the OpenAI response to add emojis next to movie titles
        for emoji, movie in emoji_movie_map.items():
            # Using regex to replace movie titles with title + emoji
            pattern = re.compile(
                re.escape(f"'{movie['title']}'"), re.IGNORECASE)
            response = pattern.sub(f"'{movie['title']}' {emoji}", response)

        # Print the OpenAI response with emojis to the Discord chat
        msg = await ctx.send(f"OpenAI: {response}")

        for emoji in emoji_movie_map.keys():
            await msg.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in emoji_movie_map and reaction.message.id == msg.id

        while True:
            reaction, user = await client.wait_for('reaction_add', check=check)
            movie = emoji_movie_map[str(reaction.emoji)]

            # Here, using arrapi to add movie to Radarr
            try:
                search = radarr.search_movies(movie['title'])
                if search:
                    # Modify path and quality as needed
                    search[0].add("/data/media/movies", "this")
                    await ctx.send(f"Added '{movie['title']}' to Radarr.")
                else:
                    await ctx.send(f"Failed to find '{movie['title']}' in Radarr database.")
            except Exception as e:
                await ctx.send(f"An error occurred while adding '{movie['title']}' to Radarr: {str(e)}")


# Run the Discord client
client.run(DISCORD_TOKEN)
