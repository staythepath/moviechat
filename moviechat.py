import os
from dotenv import load_dotenv
import openai
from openai import OpenAI

client = OpenAI()
from tmdbv3api import TMDb, Movie

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# Set up the OpenAI and TMDb API clients with the loaded API keys
raise Exception("The 'openai.api_key' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_key=OPENAI_API_KEY)'")
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
movie = Movie()

# Function to check if a string is a movie title


def is_movie(title):
    # Added this print statement
    print(f"Checking if '{title}' is a movie title...")
    if len(title) > 500:  # Skip if the title exceeds the maximum length for TMDb query
        print(
            f"Skipping '{title}' as it exceeds the maximum length for TMDb query.")
        return None
    results = movie.search(title)
    # Changed this line to use dictionary-like access
    return results[0]['title'] if len(results) > 0 else None

# Function to extract movie titles from OpenAI API response


def extract_movie_titles_from_openai_response(prompt):
    print("Making a request to the GPT-3 API...")  # Added this print statement
    # Make a request to the GPT-3 API
    response = client.completions.create(engine="davinci",
    prompt=prompt,
    temperature=0.7,
    max_tokens=40,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop=None)

    # Extract the text from the API response
    text = response.choices[0].text.strip()
    # Added this print statement
    print(f"Received response from GPT-3: {text}")

    # Check each word/phrase to see if it's a movie
    words = text.split()
    movie_titles = set()  # Using a set to store unique movie titles
    for i in range(len(words)):
        # Limit the number of words in each phrase to avoid long queries
        for j in range(i+1, min(i+10, len(words)+1)):
            phrase = ' '.join(words[i:j])
            movie_title = is_movie(phrase)
            if movie_title:
                movie_titles.add(movie_title)

    return list(movie_titles)


# Example usage with a prompt
prompt = "Here is a list of the titles of 4 movies:\n"
# Added this print statement
print("Extracting movie titles from OpenAI API response...")
movie_titles = extract_movie_titles_from_openai_response(prompt)

if movie_titles:
    print("Movie titles found in the OpenAI API response:")
    for title in movie_titles:
        print(title)
else:
    print("No movie titles found in the OpenAI API response.")
