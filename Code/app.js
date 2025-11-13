// Translations
const translations = {
    en: {
        search: 'Search',
        collection: 'My Collection',
        recommendations: 'Recommendations',
        addToCollection: 'Add to Collection',
        removeFromCollection: 'Remove',
        searchPlaceholder: 'Search movies...',
        loading: 'Loading...',
        noResults: 'No movies found',
        added: 'Added to collection!',
        removed: 'Removed from collection!',
        alreadyAdded: 'Already in collection'
    },
    ru: {
        search: 'Поиск',
        collection: 'Моя коллекция',
        recommendations: 'Рекомендации',
        addToCollection: 'Добавить в коллекцию',
        removeFromCollection: 'Удалить',
        searchPlaceholder: 'Поиск фильмов...',
        loading: 'Загрузка...',
        noResults: 'Ничего не найдено',
        added: 'Добавлено в коллекцию!',
        removed: 'Удалено из коллекции!',
        alreadyAdded: 'Уже в коллекции'
    }
};

// State
let currentUser = null;
let currentLang = localStorage.getItem('language') || 'ru';
let currentTheme = localStorage.getItem('theme') || 'dark';
let searchResults = [];
let collectionMovies = [];
let popularMovies = [];
let searchHistory = []; // История поиска
let lastSearchQuery = ''; // Последний поисковый запрос

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize
async function init() {
    // Load or create user
    const username = localStorage.getItem('username');
    if (!username) {
        const newUsername = 'user_' + Date.now();
        const result = await api.createUser(newUsername);
        currentUser = result.user;
        localStorage.setItem('username', newUsername);
        localStorage.setItem('userId', currentUser.id);
    } else {
        const userId = localStorage.getItem('userId');
        const result = await api.getUser(userId);
        currentUser = result.user;
    }
    
    // Apply theme
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        document.getElementById('themeToggle').textContent = '☀️';
    }
    
    // Apply language
    updateTranslations();
    
    // ВАЖНО: Сначала загружаем коллекцию, потом популярные фильмы
    await loadCollection();
    await loadPopularMovies();
    
    // Event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Search
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    const searchInput = document.getElementById('searchInput');
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    
    // НОВОЕ: Отслеживание изменений в строке поиска
    searchInput.addEventListener('input', (e) => {
        const currentValue = e.target.value.trim();
        
        // Если поле очищено, возвращаемся к предыдущим результатам или главной
        if (currentValue === '') {
            if (searchHistory.length > 0) {
                // Возвращаемся к последним результатам из истории
                const lastSearch = searchHistory[searchHistory.length - 1];
                searchResults = lastSearch.results;
                lastSearchQuery = lastSearch.query;
                const container = document.getElementById('searchResults');
                renderMovies(searchResults, container, false);
                searchHistory.pop(); // Убираем из истории
            } else {
                // Возвращаемся на главную (популярные фильмы)
                loadPopularMovies();
                lastSearchQuery = '';
            }
        }
    });
    
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            switchView(e.target.closest('.nav-btn').dataset.view);
        });
    });
    
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    
    // Language toggle
    document.getElementById('langToggle').addEventListener('click', toggleLanguage);
    
    // НОВОЕ: Клик по логотипу возвращает на главную
    document.querySelector('.logo').addEventListener('click', (e) => {
        e.preventDefault();
        returnToHome();
    });
}

// НОВАЯ функция: Возврат на главную
function returnToHome() {
    // Очищаем историю поиска
    searchHistory = [];
    lastSearchQuery = '';
    
    // Очищаем поле поиска
    document.getElementById('searchInput').value = '';
    
    // Переключаемся на вкладку "Поиск"
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector('[data-view="search"]').classList.add('active');
    
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById('searchView').classList.add('active');
    
    // Загружаем популярные фильмы
    loadPopularMovies();
}

async function handleSearch() {
    const query = document.getElementById('searchInput').value.trim();
    
    if (!query) {
        await loadPopularMovies();
        return;
    }
    
    // Сохраняем предыдущие результаты в историю
    if (lastSearchQuery && searchResults.length > 0) {
        searchHistory.push({
            query: lastSearchQuery,
            results: [...searchResults]
        });
    }
    
    lastSearchQuery = query;
    
    const container = document.getElementById('searchResults');
    container.innerHTML = '<p style="text-align: center; padding: 40px; grid-column: 1/-1;">⏳ Загрузка...</p>';
    
    const result = await api.searchMovies(query, currentLang);
    searchResults = result.results || [];
    
    renderMovies(searchResults, container, false);
}

async function loadPopularMovies() {
    const container = document.getElementById('searchResults');
    container.innerHTML = '<p style="text-align: center; padding: 40px; grid-column: 1/-1;">⏳ Загрузка...</p>';
    
    const result = await api.getPopularMovies(currentLang);
    popularMovies = result.results || [];
    searchResults = popularMovies;
    lastSearchQuery = ''; // Сбрасываем запрос
    
    renderMovies(popularMovies, container, false);
}

async function loadCollection() {
    const result = await api.getCollection(currentUser.id);
    collectionMovies = result.collection.map(um => ({...um.movie, user_movie_data: um}));
    
    const container = document.getElementById('collectionMovies');
    renderMovies(collectionMovies, container, true);
}

async function loadRecommendations() {
    const container = document.getElementById('recommendationsMovies');
    container.innerHTML = '<p style="text-align: center; padding: 40px; grid-column: 1/-1;">⏳ Загрузка...</p>';
    
    const result = await api.getRecommendations(currentUser.id, currentLang);
    const recommendations = result.recommendations || [];
    
    renderMovies(recommendations, container, false);
}

window.handleAdd = async function(movieId, tmdbId) {
    // Проверяем, нет ли уже в коллекции по TMDb ID
    const alreadyInCollection = collectionMovies.some(m => 
        m.tmdb_id && tmdbId && m.tmdb_id.toString() === tmdbId.toString()
    );
    
    if (alreadyInCollection) {
        showNotification(translations[currentLang].alreadyAdded, 'error');
        return;
    }
    
    const movie = searchResults.find(m => m.id === movieId);
    if (!movie) return;
    
    try {
        await api.addToCollection(currentUser.id, movie);
        await loadCollection();
        showNotification(translations[currentLang].added, 'success');
        
        // Обновляем отображение
        if (document.getElementById('searchView').classList.contains('active')) {
            const container = document.getElementById('searchResults');
            renderMovies(searchResults, container, false);
        }
    } catch (error) {
        showNotification(translations[currentLang].alreadyAdded, 'error');
    }
}

window.handleRemove = async function(tmdbId) {
    // Находим фильм в коллекции по TMDb ID
    const userMovie = collectionMovies.find(m => 
        m.tmdb_id && tmdbId && m.tmdb_id.toString() === tmdbId.toString()
    );
    
    if (userMovie) {
        const actualMovieId = userMovie.id;
        await api.removeFromCollection(currentUser.id, actualMovieId);
        await loadCollection();
        showNotification(translations[currentLang].removed, 'success');
        
        // Обновляем текущий вид
        if (document.getElementById('searchView').classList.contains('active')) {
            const container = document.getElementById('searchResults');
            renderMovies(searchResults, container, false);
        }
    }
}

function switchView(viewName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
    
    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    if (viewName === 'search') {
        document.getElementById('searchView').classList.add('active');
        if (searchResults.length === 0) {
            loadPopularMovies();
        }
    } else if (viewName === 'collection') {
        document.getElementById('collectionView').classList.add('active');
        loadCollection();
    } else if (viewName === 'recommendations') {
        document.getElementById('recommendationsView').classList.add('active');
        loadRecommendations();
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    currentTheme = isDark ? 'dark' : 'light';
    localStorage.setItem('theme', currentTheme);
    document.getElementById('themeToggle').textContent = isDark ? '☀️' : '🌙';
}

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'ru' : 'en';
    localStorage.setItem('language', currentLang);
    document.getElementById('langToggle').textContent = currentLang === 'en' ? 'RU' : 'EN';
    updateTranslations();
    
    // Reload current view
    const activeView = document.querySelector('.nav-btn.active').dataset.view;
    switchView(activeView);
}

function updateTranslations() {
    document.querySelectorAll('.translate').forEach(el => {
        const key = el.dataset.key;
        el.textContent = translations[currentLang][key];
    });
    
    const searchInput = document.getElementById('searchInput');
    searchInput.placeholder = translations[currentLang].searchPlaceholder;
}

// Start app
init();
