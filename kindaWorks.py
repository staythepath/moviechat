import openai
from tmdbv3api import TMDb, Movie
import os
from dotenv import load_dotenv

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
openai.api_key = OPENAI_API_KEY

# Function to get response from OpenAI API


def get_openai_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant with a ton of movie knowledge."},
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
    words = text.split()
    found_movies = []  # List to store found movie titles

    for i in range(len(words)):
        for j in range(i + 1, len(words) + 1):
            phrase = ' '.join(words[i:j])
            if len(phrase) < 500:  # To ensure the query does not exceed TMDb's limit
                # Print the phrase being searched
                if len(phrase.split()) > 10:
                    continue

                print(f"Searching TMDb for: {phrase}")
                results = movie.search(phrase)
                for result in results:
                    if isinstance(result, str):
                        print(f"Unexpected result format: {result}")
                        continue

                    movie_title = result.title
                    popularity = result.popularity
                    vote_average = result.vote_average  # Added this line
                    vote_count = result.vote_count  # Added this line

                    # Print the title and popularity
                    print(
                        f"Received from TMDb: {movie_title} with popularity {popularity}")

                    # Adjust the popularity threshold as needed
                    if (
                        movie_title.lower() in text.lower()
                        and vote_average >= 6  # Adjust the threshold for vote average
                        and vote_count >= 1000  # Adjust the threshold for vote count
                        and popularity > 10
                    ):
                        found_movies.append(movie_title)

    # Remove duplicates by converting the list to a set and back to a list
    found_movies = list(set(found_movies))
    return found_movies


# Show the OpenAi API response
print(f"OpenAI API response: {sample_text}")

# Test the function with the sample text
found_movie_titles = check_for_movie_title_in_string(sample_text)
if found_movie_titles:
    print(f"Found movie titles in the string: {', '.join(found_movie_titles)}")
else:
    print("No movie title found in the string.")
