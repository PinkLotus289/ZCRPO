function createMovieCard(movie, isInCollection = false) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    
    const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
    const tmdbRating = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
    const imdbRating = movie.imdb_rating || 'N/A';
    
    // ПРАВИЛЬНАЯ проверка: сравниваем по TMDb ID
    const movieTmdbId = movie.tmdb_id;
    const inCollection = collectionMovies.some(collectionMovie => {
        const collectionTmdbId = collectionMovie.tmdb_id;
        return movieTmdbId && collectionTmdbId && movieTmdbId.toString() === collectionTmdbId.toString();
    });
    
    card.innerHTML = `
        <img src="${getImageUrl(movie.poster_path)}" alt="${movie.title}" class="movie-poster" loading="lazy">
        <div class="movie-info">
            <h3 class="movie-title">${movie.title}</h3>
            <div class="movie-meta">
                <span>📅 ${year}</span>
            </div>
            <div class="movie-ratings">
                <div class="rating-item">
                    <span class="rating-label">TMDb:</span>
                    <span class="rating-value">⭐ ${tmdbRating}</span>
                </div>
                <div class="rating-item">
                    <span class="rating-label">Rating:</span>
                    <span class="rating-value">🎬 ${imdbRating}</span>
                </div>
            </div>
            ${movie.genres && movie.genres.length > 0 ? `
                <div class="movie-genres">
                    ${movie.genres.slice(0, 3).map(g => `<span class="genre-tag">${g}</span>`).join('')}
                </div>
            ` : ''}
            <p class="movie-overview">${movie.overview || 'Нет описания'}</p>
            <div class="movie-actions">
                ${inCollection || isInCollection ? 
                    `<button class="btn btn-danger" onclick="handleRemove('${movieTmdbId}')">
                        ${translations[currentLang].removeFromCollection}
                    </button>` :
                    `<button class="btn btn-primary" onclick="handleAdd('${movie.id}', '${movieTmdbId}')">
                        ${translations[currentLang].addToCollection}
                    </button>`
                }
            </div>
        </div>
    `;
    
    return card;
}

function renderMovies(movies, container, isInCollection = false) {
    container.innerHTML = '';
    
    if (movies.length === 0) {
        container.innerHTML = `<p style="text-align: center; padding: 40px; grid-column: 1/-1;">${translations[currentLang].noResults}</p>`;
        return;
    }
    
    movies.forEach(movie => {
        const card = createMovieCard(movie, isInCollection);
        container.appendChild(card);
    });
}
