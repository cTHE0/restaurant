// API base URL
const API_BASE = '/restaurant/api';

// Check admin authentication via session (server-side)
function checkAdminAuth() {
    // La vérification de session se fait côté serveur
    // Cette fonction retourne true pour permettre le chargement initial
    // Le serveur redirigera vers login si non authentifié
    return true;
}

// Handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    if (error.status === 401 || error.status === 403) {
        window.location.href = '/restaurant/admin/login';
        return;
    }
    alert('Erreur serveur. Veuillez réessayer.');
}

// Fetch wrapper with error handling
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/restaurant/admin/login';
            return null;
        }
        
        return response;
    } catch (error) {
        handleApiError(error);
        throw error;
    }
}