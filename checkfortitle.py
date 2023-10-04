from tmdbv3api import TMDb, Movie
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the TMDb API key from environment variable
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# Configure TMDb with the API key
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY

# Create a Movie object to search for movies
movie = Movie()

# Sample text to check for movie titles
sample_text = "Here is a list of movie I hope it pulls out some of them: Inception, 101 Dalmatians, The Sting."


def check_for_movie_title_in_string(text):
    words = text.split()
    found_movies = []  # List to store found movie titles

    for i in range(len(words)):
        for j in range(i + 1, len(words) + 1):
            phrase = ' '.join(words[i:j])
            if len(phrase) < 500:  # To ensure the query does not exceed TMDb's limit
                # Print the phrase being searched
                print(f"Searching TMDb for: {phrase}")
                results = movie.search(phrase)
                for result in results:
                    if isinstance(result, str):
                        print(f"Unexpected result format: {result}")
                        continue

                    movie_title = result.title
                    popularity = result.popularity

                    # Print the title and popularity
                    print(
                        f"Received from TMDb: {movie_title} with popularity {popularity}")

                    # Adjust the popularity threshold as needed
                    if movie_title.lower() in text.lower() and popularity > 10:
                        found_movies.append(movie_title)

    # Remove duplicates by converting the list to a set and back to a list
    found_movies = list(set(found_movies))
    return found_movies


# Test the function with the sample text
found_movie_titles = check_for_movie_title_in_string(sample_text)
if found_movie_titles:
    print(f"Found movie titles in the string: {', '.join(found_movie_titles)}")
else:
    print("No movie title found in the string.")
