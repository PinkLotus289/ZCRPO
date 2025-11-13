import uuid
from datetime import datetime

def generate_id():
    return str(uuid.uuid4())

def create_user(username, email=None):
    return {
        "id": generate_id(),
        "username": username,
        "email": email,
        "preferences": {},
        "created_at": datetime.now().isoformat()
    }

def create_movie(title, **kwargs):
    return {
        "id": kwargs.get("id", generate_id()),
        "title": title,
        "original_title": kwargs.get("original_title"),
        "overview": kwargs.get("overview"),
        "release_date": kwargs.get("release_date"),
        "poster_path": kwargs.get("poster_path"),
        "backdrop_path": kwargs.get("backdrop_path"),
        "vote_average": kwargs.get("vote_average", 0.0),
        "vote_count": kwargs.get("vote_count", 0),
        "genres": kwargs.get("genres", []),
        "runtime": kwargs.get("runtime"),
        "tmdb_id": kwargs.get("tmdb_id"),
        "imdb_id": kwargs.get("imdb_id")
    }

def create_user_movie(user_id, movie):
    return {
        "id": generate_id(),
        "user_id": user_id,
        "movie": movie,
        "added_at": datetime.now().isoformat(),
        "rating": None,
        "watched": False,
        "notes": None
    }
