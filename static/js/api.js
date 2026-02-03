// API base URL
const API_BASE = '/restaurant/api';

// Check admin authentication
function checkAdminAuth() {
    return localStorage.getItem('admin_logged_in') === 'true';
}

// Handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    alert('Erreur serveur. Veuillez réessayer.');
}