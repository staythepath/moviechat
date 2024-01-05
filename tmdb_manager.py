from tmdbv3api import TMDb, Movie, Person
import random


class TMDbManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tmdb = TMDb()
        self.tmdb.api_key = self.config_manager.get_config_value("tmdb_api_key")
        self.movie_api = Movie()

    def update_tmdb_api_key(self):
        self.tmdb.api_key = self.config_manager.get_config_value("tmdb_api_key")

    def search_movie(self, title):
        return self.movie_api.search(title)

    def get_movie_details(self, tmdb_id):
        return self.movie_api.details(tmdb_id)

    def get_movie_card_details(self, tmdb_id):
        movie = self.movie_api.details(tmdb_id)
        credits = self.movie_api.credits(tmdb_id)

        # Debugging: Print the structure of the 'credits' object
        # print("Credits Object:", credits)

        director = self.get_crew_member(credits, "Director")
        dop = self.get_crew_member(credits, "Director of Photography")
        writers = self.get_top_writers(credits)  # Get top 5 writers
        stars = self.get_main_actors(credits)  # Get top 5 actors

        return {
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
        }

    def get_person_details(self, name):
        person_api = Person()
        search_results = person_api.search(name)
        if search_results:
            # Fetch the person details
            person_id = search_results[0].id
            person_details = person_api.details(person_id)

            # Fetch the movie credits for the person
            movie_credits = person_api.movie_credits(person_id)
            # print("Here are the movie credits: ", movie_credits)

            # Process the movie credits to extract the required information
            credits_info = self.process_movie_credits(movie_credits)

            # Combine the details and credits to return a single response
            return {
                "name": person_details.name,
                "biography": person_details.biography,
                "birthday": person_details.birthday,
                "deathday": person_details.deathday,
                "place_of_birth": person_details.place_of_birth,
                "profile_path": person_details.profile_path,
                "movie_credits": credits_info,
                # Include movie credits in the response
            }
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
