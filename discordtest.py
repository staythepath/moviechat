import os
import discord
from discord.ext import commands
import openai
from openai import OpenAI

client = OpenAI()
from tmdbv3api import TMDb, Movie
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# Get the TMDb and OpenAI API keys from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure TMDb with the API key
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY

# Create a Movie object to search for movies
movie = Movie()

# Configure OpenAI API key
raise Exception("The 'openai.api_key' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_key=OPENAI_API_KEY)'")

# Function to get response from OpenAI API


def get_openai_response(prompt):
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with a ton of movie knowledge. Please place any movie titles in single quotes."},
        {"role": "user", "content": prompt},
    ],
    temperature=0)
    return response.choices[0].message['content'].strip()


# Use the OpenAI API to get a text response
prompt = "Show me a short sentence that contains movie titles, but use the titles in the sentence as if they are not movie titles. Use one of the movie titles twice in two different ways in the sentence."
sample_text = get_openai_response(prompt)
print(f"OpenAI API response: {sample_text}")


def check_for_movie_title_in_string(text):
    found_movies = []  # List to store found movie titles

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
            popularity = result.popularity
            vote_average = result.vote_average
            vote_count = result.vote_count

            print(
                f"Received from TMDb: {movie_title} with popularity {popularity}")

            if (
                movie_title.lower() in text.lower()
                and vote_average >= 5
                and vote_count >= 500
                and popularity > 18
            ):
                found_movies.append(movie_title)

    # Remove duplicates by converting the list to a set and back to a list
    found_movies = list(set(found_movies))
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
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=conversations[channel_id],
    temperature=0.8,
    max_tokens=150).choices[0].message['content'].strip()

    # Add the OpenAI's response to the conversation history
    conversations[channel_id].append(
        {"role": "assistant", "content": response})

    # Print the OpenAI response to the Discord chat
    await ctx.send(f"OpenAI: {response}")

    # Check if the OpenAI response contains movie titles
    found_movie_titles = check_for_movie_title_in_string(response)

    # If movie titles are found, print them to the Discord chat
    if found_movie_titles:
        await ctx.send(f"Movies mentioned: {', '.join(found_movie_titles)}")
    else:
        await ctx.send("No movies mentioned.")

# Run the Discord client
client.run(DISCORD_TOKEN)
