from tmdbv3api import TMDb, Movie


class TMDbManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tmdb = TMDb()
        self.tmdb.api_key = self.config_manager.get_config_value("tmdb_api_key")
        self.movie_api = Movie()

    def search_movie(self, title):
        return self.movie_api.search(title)

    def get_movie_details(self, tmdb_id):
        return self.movie_api.details(tmdb_id)
