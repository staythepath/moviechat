import openai
import re
from openai import OpenAI
import time


class OpenAIChatManager:
    def __init__(self, config_manager, tmdb_manager):
        self.config_manager = config_manager
        self.tmdb_manager = tmdb_manager
        self.initialize_openai_client()

    def initialize_openai_client(self):
        self.openai_api_key = self.config_manager.get_config_value("openai_api_key")
        self.max_chars = self.config_manager.get_config_value("max_chars")
        self.selected_model = self.config_manager.get_config_value("selected_model")
        self.client = OpenAI(api_key=self.openai_api_key)

    def trim_conversation_history(self, conversation_history, new_message):
        conversation_history.append(new_message)
        total_chars = sum(len(msg["content"]) for msg in conversation_history)
        while total_chars > self.max_chars and len(conversation_history) > 1:
            removed_message = conversation_history.pop(0)
            total_chars -= len(removed_message["content"])
        return conversation_history

    def get_openai_response(self, conversation_history, message):
        # Prepare new message and conversation history
        new_message = {"role": "user", "content": message}
        conversation_history = self.trim_conversation_history(
            conversation_history, new_message
        )

        messages = [
            {
                "role": "system",
                "content": "You are a fun and informative conversational bot focused on movies. Never put quotes around movie titles. Always leave movie title unquoted. You never under any circumstances number any list. When you do list movies put each movie on it's own line. When mentioning movies in any capacity, always enclose the movies title in asterisks with the year in parentheses and always include the year after the title, like ' *Movie Title* (Year)', e.g., '*Jurassic Park* (1994)' . Every single time you say a movie title it needs to be wrapped in asteriks and it needs to have the year after the title. Ensure movie titles exactly match those on the TMDB website, including capitalization, spelling, punctuation, and spacing. For lists, use a dash (-) instead of numbering, and never list more than 20 movies. Be conversational and engage with the user's preferences, including interesting movie facts. Only create lists when it's relevant or requested by the user. Avoid creating a list in every message. You're here to discuss movies, not just list them.",  # System message
            }
        ] + conversation_history

        # Generate response from OpenAI
        response = self.client.chat.completions.create(
            model=self.selected_model, messages=messages, temperature=0
        )
        response_content = (
            response.choices[0].message.content.strip()
            if response.choices
            else "No response received."
        )

        print("OpenAI response: ", response_content)

        # Process movie titles
        movie_titles_map = self.check_for_movie_title_in_string(response_content)
        for title, tmdb_id in movie_titles_map.items():
            response_content = response_content.replace(
                f"*{title}*",
                f"<span class='movie-link' data-toggle='popover' data-tmdb-id='{tmdb_id}' data-title='{title}' onclick='addMovieToRadarr({tmdb_id})'>{title}</span>",
            )
        return response_content

    def check_for_movie_title_in_string(self, text):
        movie_titles_map = {}
        phrases_in_stars = re.findall(r"\*\"?([^*]+)\"?\*(?: \(\d{4}\))?", text)

        for phrase in phrases_in_stars:
            # Use the tmdb_manager's search_movie method
            results = self.tmdb_manager.search_movie(phrase)
            print(f"\nSearch phrase: '{phrase}'")
            print("Results:")

            # Introduce a delay to prevent hitting API rate limits
            time.sleep(0.3)

            for idx, result in enumerate(results):
                if isinstance(result, dict) and "title" in result and "id" in result:
                    print(f"  Result {idx + 1}: {result}")
                    tmdb_id = result["id"]
                elif hasattr(result, "title") and hasattr(result, "id"):
                    print(
                        f"  Result {idx + 1}: Title - {result.title}, ID - {result.id}"
                    )
                    tmdb_id = result.id
                else:
                    print(f"  Result {idx + 1}: Invalid format")
                    continue

                if tmdb_id:
                    movie_titles_map[phrase] = tmdb_id
                    break  # Stop after finding the first valid result

        return movie_titles_map
