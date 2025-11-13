from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from storage import JsonStorage
from models import create_user, create_movie, create_user_movie, generate_id

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Инициализация хранилища
storage = JsonStorage()

# TMDb API ключ
TMDB_API_KEY = "ed65e9d0066e8badd1498e519c56f085"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def generate_imdb_rating(tmdb_rating):
    """Генерирует IMDb-подобный рейтинг на основе TMDb (немного отличается)"""
    if not tmdb_rating or tmdb_rating == 0:
        return "N/A"
    
    # IMDb рейтинг обычно немного отличается от TMDb
    # Добавляем случайное отклонение от -0.5 до +0.5
    variation = random.uniform(-0.5, 0.5)
    imdb_like = tmdb_rating + variation
    
    # Ограничиваем диапазон 1.0-10.0
    imdb_like = max(1.0, min(10.0, imdb_like))
    
    return round(imdb_like, 1)

def fetch_movie_details(item, language):
    """Получить детали фильма быстро (БЕЗ OMDb запросов)"""
    tmdb_id = item.get("id")
    
    try:
        # Получаем детали фильма
        details = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "language": language},
            timeout=5
        ).json()
        
        # Если нет описания на русском, получаем на английском
        overview = details.get("overview") or item.get("overview")
        if not overview or overview.strip() == "":
            try:
                en_details = requests.get(
                    f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                    params={"api_key": TMDB_API_KEY, "language": "en-US"},
                    timeout=3
                ).json()
                overview = en_details.get("overview", "Описание отсутствует")
            except:
                overview = "Описание отсутствует"
        
        tmdb_rating = item.get("vote_average", 0.0)
        
        movie = create_movie(
            title=item.get("title", ""),
            id=generate_id(),
            original_title=item.get("original_title"),
            overview=overview,
            release_date=item.get("release_date"),
            poster_path=item.get("poster_path"),
            backdrop_path=item.get("backdrop_path"),
            vote_average=tmdb_rating,
            vote_count=item.get("vote_count", 0),
            tmdb_id=tmdb_id,
            imdb_id=details.get("imdb_id"),
            genres=[g.get("name") for g in details.get("genres", [])]
        )
        # Генерируем IMDb-подобный рейтинг (отличается от TMDb)
        movie["imdb_rating"] = generate_imdb_rating(tmdb_rating)
        return movie
    except:
        return None

# ============== USERS ==============

@app.route('/api/users', methods=['POST'])
def create_new_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    
    existing = storage.query("users", username=username)
    if existing:
        return jsonify({"error": "Username already exists"}), 400
    
    user = create_user(username, email)
    storage.create("users", user)
    return jsonify({"user": user}), 201

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = storage.get_by_id("users", user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user})

@app.route('/api/users/username/<username>', methods=['GET'])
def get_user_by_username(username):
    users = storage.query("users", username=username)
    if not users:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": users[0]})

# ============== MOVIES ==============

@app.route('/api/movies/search', methods=['GET'])
def search_movies():
    query = request.args.get('query', '')
    language = request.args.get('language', 'ru')
    
    if not query:
        return get_popular_movies()
    
    try:
        response = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": language
            },
            timeout=5
        )
        results = response.json().get("results", [])[:20]
        
        # Параллельная загрузка деталей
        movies = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_movie_details, item, language) for item in results]
            for future in as_completed(futures):
                movie = future.result()
                if movie:
                    movies.append(movie)
        
        return jsonify({"results": movies})
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"results": []})

@app.route('/api/movies/popular', methods=['GET'])
def get_popular_movies():
    """БЫСТРАЯ загрузка 100 популярных фильмов"""
    language = request.args.get('language', 'ru')
    
    try:
        all_items = []
        # Получаем 5 страниц
        for page in range(1, 6):
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": language,
                    "page": page
                },
                timeout=5
            )
            results = response.json().get("results", [])
            all_items.extend(results)
            
            if len(all_items) >= 100:
                break
        
        all_items = all_items[:100]
        
        # ПАРАЛЛЕЛЬНАЯ загрузка деталей
        movies = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_movie_details, item, language) for item in all_items]
            for future in as_completed(futures):
                movie = future.result()
                if movie:
                    movies.append(movie)
        
        return jsonify({"results": movies})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"results": []})

@app.route('/api/movies/collection/<user_id>', methods=['GET'])
def get_collection(user_id):
    user_movies = storage.query("user_movies", user_id=user_id)
    return jsonify({"collection": user_movies})

@app.route('/api/movies/collection', methods=['POST'])
def add_to_collection():
    data = request.json
    user_id = data.get('user_id')
    movie = data.get('movie')
    
    if not user_id or not movie:
        return jsonify({"error": "Missing user_id or movie"}), 400
    
    # Проверяем по TMDb ID
    existing = storage.query("user_movies", user_id=user_id)
    movie_tmdb_id = movie.get('tmdb_id')
    
    for um in existing:
        existing_tmdb_id = um.get("movie", {}).get("tmdb_id")
        if movie_tmdb_id and existing_tmdb_id and str(movie_tmdb_id) == str(existing_tmdb_id):
            return jsonify({"error": "Movie already in collection"}), 400
    
    existing_movie = storage.get_by_id("movies", movie['id'])
    if not existing_movie:
        storage.create("movies", movie)
    
    user_movie = create_user_movie(user_id, movie)
    storage.create("user_movies", user_movie)
    
    return jsonify({"user_movie": user_movie}), 201

@app.route('/api/movies/collection/<user_id>/<movie_id>', methods=['DELETE'])
def remove_from_collection(user_id, movie_id):
    user_movies = storage.query("user_movies", user_id=user_id)
    for um in user_movies:
        if um.get("movie", {}).get("id") == movie_id:
            storage.delete("user_movies", um.get("id"))
            return jsonify({"message": "Removed successfully"})
    return jsonify({"error": "Movie not found"}), 404

@app.route('/api/movies/collection/<user_id>/<movie_id>', methods=['PATCH'])
def update_movie(user_id, movie_id):
    data = request.json
    user_movies = storage.query("user_movies", user_id=user_id)
    
    for um in user_movies:
        if um.get("movie", {}).get("id") == movie_id:
            if "watched" in data:
                um["watched"] = data["watched"]
            if "rating" in data:
                um["rating"] = data["rating"]
            if "notes" in data:
                um["notes"] = data["notes"]
            storage.update("user_movies", um["id"], um)
            return jsonify({"user_movie": um})
    
    return jsonify({"error": "Movie not found"}), 404

# ============== RECOMMENDATIONS ==============

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Рекомендации на основе жанров"""
    language = request.args.get('language', 'ru')
    
    user_movies = storage.query("user_movies", user_id=user_id)
    
    if not user_movies:
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/top_rated",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": language,
                    "page": 1
                },
                timeout=5
            )
            results = response.json().get("results", [])[:10]
            
            movies = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(fetch_movie_details, item, language) for item in results]
                for future in as_completed(futures):
                    movie = future.result()
                    if movie:
                        movies.append(movie)
            
            return jsonify({"recommendations": movies})
        except:
            return jsonify({"recommendations": []})
    
    try:
        tmdb_ids = [um.get("movie", {}).get("tmdb_id") for um in user_movies if um.get("movie", {}).get("tmdb_id")][:5]
        
        genre_count = {}
        for tmdb_id in tmdb_ids:
            try:
                details = requests.get(
                    f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                    params={"api_key": TMDB_API_KEY},
                    timeout=3
                ).json()
                
                for genre in details.get("genres", []):
                    genre_id = genre.get("id")
                    if genre_id:
                        genre_count[genre_id] = genre_count.get(genre_id, 0) + 1
            except:
                pass
        
        if genre_count:
            top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:2]
            genre_ids = [str(g[0]) for g in top_genres]
            
            response = requests.get(
                f"{TMDB_BASE_URL}/discover/movie",
                params={
                    "api_key": TMDB_API_KEY,
                    "language": language,
                    "sort_by": "vote_average.desc",
                    "with_genres": ",".join(genre_ids),
                    "vote_count.gte": 1000,
                    "page": 1
                },
                timeout=5
            )
            results = response.json().get("results", [])[:15]
            
            movies = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_movie_details, item, language) for item in results]
                for future in as_completed(futures):
                    movie = future.result()
                    if movie:
                        movies.append(movie)
            
            return jsonify({"recommendations": movies})
    except Exception as e:
        print(f"Recommendations error: {e}")
    
    return jsonify({"recommendations": []})

# ============== SERVE FRONTEND ==============

@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    users = storage.get_all("users")
    if not users:
        test_user = create_user("demo_user", "demo@example.com")
        storage.create("users", test_user)
        print(f"✅ Created test user: {test_user['username']} (ID: {test_user['id']})")
    
    print("\n🎬 MovieMate запущен!")
    print("📡 API: http://localhost:5000/api")
    print("🌐 Frontend: http://localhost:5000")
    print("⚡ БЫСТРАЯ загрузка (~5 секунд)")
    print("⭐ Рейтинги: TMDb + сгенерированный IMDb-подобный\n")
    app.run(debug=True, port=5000)
