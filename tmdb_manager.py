from tmdbv3api import TMDb, Movie, Person


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
        writers = self.get_top_writers(credits, 5)  # Get top 5 writers
        stars = self.get_main_actors(credits, 5)  # Get top 5 actors

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
            person_id = search_results[0].id  # Directly access the id
            person_details = person_api.details(person_id)
            return {
                "name": person_details.name,
                "biography": person_details.biography,
                "birthday": person_details.birthday,
                "deathday": person_details.deathday,
                "place_of_birth": person_details.place_of_birth,
                "profile_path": person_details.profile_path,
            }
        return {}

    def get_crew_member(self, credits, job_title):
        for crew_member in credits["crew"]:
            if crew_member["job"] == job_title:
                return crew_member["name"]
        return "Not Available"

    def get_crew_members(self, credits, job_title):
        writers = [
            member["name"] for member in credits["crew"] if member["job"] == job_title
        ]
        return ", ".join(writers) if writers else "Not Available"

    def get_main_actors(self, credits, count=3):
        actors = [
            member["name"] for member in credits["cast"] if "name" in member
        ]  # Filter out crew members without a "name" attribute
        return ", ".join(actors[:count]) if actors else "Not Available"

    def get_top_writers(self, credits, count=5):
        writers = [
            member["name"]
            for member in credits["crew"]
            if member["department"] == "Writing"
        ][:count]
        return ", ".join(writers) if writers else "Not Available"
