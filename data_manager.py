from tmdbv3api import TMDb, Movie, Person
import requests
import imdb  # pip install imdbpy
import random
import time


class DataManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tmdb = TMDb()
        self.tmdb.api_key = self.config_manager.get_config_value("tmdb_api_key")
        self.movie_api = Movie()
        self.cache = {}  # Initialize the cache
        self.cache_duration = 3600  # Cache duration in seconds (e.g., 1 hour)

    def get_from_cache(self, key):
        """Retrieve an item from the cache if it exists and is not expired."""
        cached_item = self.cache.get(key)
        if cached_item and (
            time.time() - cached_item["timestamp"] < self.cache_duration
        ):
            return cached_item["data"]
        return None

    def add_to_cache(self, key, data):
        """Add an item to the cache with a timestamp."""
        self.cache[key] = {"data": data, "timestamp": time.time()}

    def update_tmdb_api_key(self):
        self.tmdb.api_key = self.config_manager.get_config_value("tmdb_api_key")

    def search_movie(self, title):
        return self.movie_api.search(title)

    def get_imdb_id(self, title):
        ia = imdb.IMDb()
        search_results = ia.search_movie(title)
        if search_results:
            # Assuming the first search result is the desired one
            return search_results[0].movieID
        return "Not Available"

    def get_wiki_url(self, title):
        """
        Retrieve the Wikipedia URL for a given movie title using Wikimedia API.
        """
        language_code = "en"  # Language code for English Wikipedia
        search_query = title.replace(" ", "%20")

        # Wikipedia API endpoint for search
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_query}&format=json"

        try:
            response = requests.get(search_url)
            if response.status_code == 200:
                search_results = response.json().get("query", {}).get("search", [])
                if search_results:
                    page_title = search_results[0]["title"]
                    wiki_url = f"https://{language_code}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                    return wiki_url
                else:
                    return "Wikipedia page not found"
            else:
                return "Error in fetching data from Wikipedia"
        except Exception as e:
            return f"Error: {e}"

    def get_movie_card_details(self, tmdb_id):
        cache_key = f"movie_card_{tmdb_id}"
        cached_data = self.get_from_cache(cache_key)

        if cached_data:
            time.sleep(0.250)  # Add a 350ms delay
            return cached_data

        # Fetch the movie details and credits if not in cache
        movie = self.movie_api.details(tmdb_id)
        credits = self.movie_api.credits(tmdb_id)
        imdb_id = self.get_imdb_id(movie.title)
        director = self.get_crew_member(credits, "Director")
        dop = self.get_crew_member(credits, "Director of Photography")
        writers = self.get_top_writers(credits)  # Get top 5 writers
        stars = self.get_main_actors(credits)  # Get top 5 actors
        wiki_url = self.get_wiki_url(movie.title)

        movie_card_data = {
            "title": movie.title,
            "director": director,
            "dop": dop,
            "writers": writers,
            "stars": stars,
            "description": movie.overview,
            "poster_path": f"https://image.tmdb.org/t/p/original{movie.poster_path}"
            if movie.poster_path
            else None,
            "release_date": movie.release_date,
            "vote_average": movie.vote_average,
            "imdb_id": imdb_id,
            "wiki_url": wiki_url,
        }

        # Add the fetched data to the cache
        self.add_to_cache(cache_key, movie_card_data)
        return movie_card_data

    def get_person_details(self, name):
        cache_key = f"person_{name}"
        cached_data = self.get_from_cache(cache_key)

        if cached_data:
            return cached_data

        person_api = Person()
        search_results = person_api.search(name)

        if search_results:
            # Fetch the person details
            person_id = search_results[0].id
            person_details = person_api.details(person_id)

            # Fetch the movie credits for the person
            movie_credits = person_api.movie_credits(person_id)

            # Process the movie credits to extract the required information
            credits_info = self.process_movie_credits(movie_credits)

            # Combine the details and credits to return a single response
            person_data = {
                "name": person_details.name,
                "biography": person_details.biography,
                "birthday": person_details.birthday,
                "deathday": person_details.deathday,
                "place_of_birth": person_details.place_of_birth,
                "profile_path": person_details.profile_path,
                "movie_credits": credits_info,
            }

            # Add the fetched data to the cache
            self.add_to_cache(cache_key, person_data)
            return person_data

        return {}

    def process_movie_credits(self, movie_credits, number_of_credits=7):
        cast_credits = movie_credits.get("cast", [])

        if not cast_credits:
            return []

        # Convert AsObj to list of dictionaries if needed
        if not isinstance(cast_credits, list):
            cast_credits = [credit.__dict__ for credit in cast_credits]

        # Filter out non-feature films (e.g., documentaries, TV movies)
        # This is just an example and might need adjustments based on actual data
        feature_film_credits = [
            credit for credit in cast_credits if 99 not in credit.get("genre_ids", [])
        ]

        # Sort credits by popularity and vote average
        sorted_credits = sorted(
            feature_film_credits,
            key=lambda x: (x.get("popularity", 0), x.get("vote_average", 0)),
            reverse=True,
        )

        # Select the top movies
        selected_credits = sorted_credits[:number_of_credits]

        # Format the selected credits
        formatted_credits = []
        for credit in selected_credits:
            release_year = (
                credit.get("release_date", "N/A").split("-")[0]
                if credit.get("release_date")
                else "N/A"
            )
            credit_info = {
                "title": credit.get("title", "N/A"),
                "release_year": release_year,
            }
            formatted_credits.append(credit_info)

        return formatted_credits

    def get_crew_member(self, credits, job_title):
        for crew_member in credits["crew"]:
            if crew_member["job"] == job_title:
                return crew_member["name"]
        return "Not Available"

    def get_crew_members(self, credits, job_title):
        return [
            member["name"] for member in credits["crew"] if member["job"] == job_title
        ]

    def get_main_actors(
        self, credits, count=1000
    ):  # Assuming 1000 is a large enough number to include all actors
        actors = [member["name"] for member in credits["cast"]][:count]
        return ", ".join(actors) if actors else "Not Available"

    def get_top_writers(self, credits, count=5):
        writers = [
            member["name"]
            for member in credits["crew"]
            if member["department"] == "Writing"
        ][:count]
        return ", ".join(writers) if writers else "Not Available"
