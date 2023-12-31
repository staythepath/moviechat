from tmdbv3api import TMDb, Movie


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
        # Format the details as needed for the movie card
        return {
            "title": movie.title,
            "director": self.get_director(movie.credits),
            "main_actors": self.get_main_actors(movie.credits, 3),  # Get top 3 actors
            "description": movie.overview,
            "poster_path": f"https://image.tmdb.org/t/p/original{movie.poster_path}"
            if movie.poster_path
            else None,
            "release_date": movie.release_date,
            "vote_average": movie.vote_average
            # Add any other details needed for the card
        }

    def get_director(self, credits):
        for crew_member in credits.crew:
            if crew_member.job.lower() == "director":
                return crew_member.name
        return "Not Available"

    def get_main_actors(self, credits, count=3):
        actors = [
            member.name for member in credits.cast[:count]
        ]  # Get top 'count' actors
        return actors if actors else ["Not Available"]
