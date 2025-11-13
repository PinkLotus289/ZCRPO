const API_BASE = 'http://localhost:5000/api';

const api = {
    // Users
    async createUser(username, email) {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email })
        });
        return response.json();
    },

    async getUser(userId) {
        const response = await fetch(`${API_BASE}/users/${userId}`);
        return response.json();
    },

    async getUserByUsername(username) {
        const response = await fetch(`${API_BASE}/users/username/${username}`);
        return response.json();
    },

    // Movies
    async searchMovies(query, language = 'ru') {
        const response = await fetch(`${API_BASE}/movies/search?query=${encodeURIComponent(query)}&language=${language}`);
        return response.json();
    },

    async getPopularMovies(language = 'ru') {
        const response = await fetch(`${API_BASE}/movies/popular?language=${language}`);
        return response.json();
    },

    async getCollection(userId) {
        const response = await fetch(`${API_BASE}/movies/collection/${userId}`);
        return response.json();
    },

    async addToCollection(userId, movie) {
        const response = await fetch(`${API_BASE}/movies/collection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, movie })
        });
        if (!response.ok) {
            throw new Error('Failed to add movie');
        }
        return response.json();
    },

    async removeFromCollection(userId, movieId) {
        const response = await fetch(`${API_BASE}/movies/collection/${userId}/${movieId}`, {
            method: 'DELETE'
        });
        return response.json();
    },

    async updateMovie(userId, movieId, updates) {
        const response = await fetch(`${API_BASE}/movies/collection/${userId}/${movieId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        return response.json();
    },

    // Recommendations
    async getRecommendations(userId, language = 'ru') {
        const response = await fetch(`${API_BASE}/recommendations/${userId}?language=${language}`);
        return response.json();
    }
};

function getImageUrl(path, size = 'w500') {
    if (!path) return 'https://via.placeholder.com/250x350?text=No+Image';
    return `https://image.tmdb.org/t/p/${size}${path}`;
}
