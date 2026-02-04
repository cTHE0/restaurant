// ============================================
// GESTION DES CATÉGORIES
// ============================================

async function loadCategories() {
    try {
        const response = await fetch('/restaurant/api/admin/categories', {
            credentials: 'include'
        });
        
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/restaurant/admin/login';
            return;
        }
        
        const categories = await response.json();
        
        // Mettre à jour le select des items
        const select = document.getElementById('item-category');
        if (select) {
            select.innerHTML = '<option value="">-- Sélectionner une catégorie --</option>';
            categories.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat.id;
                opt.textContent = cat.name;
                select.appendChild(opt);
            });
        }
        
        renderCategoriesList(categories);
        return categories;
    } catch (error) {
        console.error('Erreur chargement catégories:', error);
    }
}

function renderCategoriesList(categories) {
    const container = document.getElementById('categories-list');
    if (!container) return;
    
    if (categories.length === 0) {
        container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px">Aucune catégorie. Ajoutez-en une !</p>';
        return;
    }
    
    container.innerHTML = categories.map(cat => `
        <div class="category-item">
            <div>
                <div class="category-name">${escapeHtml(cat.name)}</div>
                ${cat.description ? `<div style="color:#64748b;font-size:0.9rem;margin-top:5px">${escapeHtml(cat.description)}</div>` : ''}
                <div style="color:#94a3b8;font-size:0.8rem;margin-top:3px">Ordre: ${cat.order}</div>
            </div>
            <div class="item-actions">
                <button class="btn btn-secondary btn-sm" onclick="editCategory(${cat.id}, '${escapeHtml(cat.name)}', '${escapeHtml(cat.description || '')}', ${cat.order})">✏️</button>
                <button class="btn btn-danger btn-sm" onclick="deleteCategory(${cat.id})">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Échapper le HTML pour éviter les injections XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Soumission du formulaire de catégorie
document.getElementById('category-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('category-name').value.trim(),
        description: document.getElementById('category-description').value.trim(),
        order: parseInt(document.getElementById('category-order').value) || 0
    };
    
    if (!data.name) {
        alert('Le nom est requis');
        return;
    }
    
    try {
        const editId = document.getElementById('category-form').dataset.editId;
        const url = editId 
            ? `/restaurant/api/admin/categories/${editId}`
            : '/restaurant/api/admin/categories';
        const method = editId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(editId ? 'Catégorie modifiée !' : 'Catégorie ajoutée !');
            resetCategoryForm();
            loadCategories();
        } else {
            const result = await response.json();
            alert('Erreur: ' + (result.error || 'Inconnue'));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur serveur');
    }
});

function editCategory(id, name, description, order) {
    document.getElementById('category-name').value = name;
    document.getElementById('category-description').value = description;
    document.getElementById('category-order').value = order;
    document.getElementById('category-form').dataset.editId = id;
    
    const submitBtn = document.querySelector('#category-form button[type="submit"]');
    if (submitBtn) submitBtn.textContent = '✏️ Modifier';
}

async function deleteCategory(id) {
    if (!confirm('Supprimer cette catégorie et tous ses items ?')) return;
    
    try {
        const response = await fetch(`/restaurant/api/admin/categories/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadCategories();
            loadItems();
        } else {
            alert('Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur serveur');
    }
}

function resetCategoryForm() {
    const form = document.getElementById('category-form');
    if (form) {
        form.reset();
        delete form.dataset.editId;
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.textContent = '➕ Ajouter';
    }
}

// ============================================
// GESTION DES ITEMS
// ============================================

let categoriesCache = [];

async function loadItems() {
    try {
        const response = await fetch('/restaurant/api/admin/items', {
            credentials: 'include'
        });
        
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/restaurant/admin/login';
            return;
        }
        
        const items = await response.json();
        renderItemsList(items);
    } catch (error) {
        console.error('Erreur chargement items:', error);
    }
}

function renderItemsList(items) {
    const container = document.getElementById('items-list');
    if (!container) return;
    
    if (items.length === 0) {
        container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px">Aucun item. Ajoutez-en un !</p>';
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="menu-item-row">
            <div style="flex:1">
                <div class="item-name">${escapeHtml(item.name)}</div>
                ${item.description ? `<div style="color:#64748b;font-size:0.85rem;margin-top:3px">${escapeHtml(item.description)}</div>` : ''}
                <div style="margin-top:5px">
                    <span class="item-price">${item.price.toFixed(2)}€</span>
                    <span style="margin-left:10px;padding:2px 8px;background:${item.available ? '#dcfce7' : '#fee2e2'};color:${item.available ? '#15803d' : '#b91c1c'};border-radius:10px;font-size:0.8rem">
                        ${item.available ? '✓ Disponible' : '✗ Indisponible'}
                    </span>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn btn-secondary btn-sm" onclick='editItem(${JSON.stringify(item)})'>✏️</button>
                <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Soumission du formulaire d'item
document.getElementById('item-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('item-name').value.trim(),
        description: document.getElementById('item-description').value.trim(),
        price: parseFloat(document.getElementById('item-price').value),
        category_id: parseInt(document.getElementById('item-category').value),
        available: document.getElementById('item-available').checked,
        order: parseInt(document.getElementById('item-order').value) || 0
    };
    
    if (!data.name || !data.price || !data.category_id) {
        alert('Nom, prix et catégorie sont requis');
        return;
    }
    
    try {
        const editId = document.getElementById('item-form').dataset.editId;
        const url = editId 
            ? `/restaurant/api/admin/items/${editId}`
            : '/restaurant/api/admin/items';
        const method = editId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert(editId ? 'Item modifié !' : 'Item ajouté !');
            resetItemForm();
            loadItems();
        } else {
            const result = await response.json();
            alert('Erreur: ' + (result.error || 'Inconnue'));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur serveur');
    }
});

function editItem(item) {
    document.getElementById('item-name').value = item.name;
    document.getElementById('item-description').value = item.description || '';
    document.getElementById('item-price').value = item.price;
    document.getElementById('item-category').value = item.category_id;
    document.getElementById('item-available').checked = item.available;
    document.getElementById('item-order').value = item.order;
    document.getElementById('item-form').dataset.editId = item.id;
    
    const submitBtn = document.querySelector('#item-form button[type="submit"]');
    if (submitBtn) submitBtn.textContent = '✏️ Modifier';
}

async function deleteItem(id) {
    if (!confirm('Supprimer cet item ?')) return;
    
    try {
        const response = await fetch(`/restaurant/api/admin/items/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadItems();
        } else {
            alert('Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur serveur');
    }
}

function resetItemForm() {
    const form = document.getElementById('item-form');
    if (form) {
        form.reset();
        document.getElementById('item-available').checked = true;
        delete form.dataset.editId;
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.textContent = '➕ Ajouter';
    }
}

// ============================================
// GESTION DES ONGLETS
// ============================================

function switchTab(tabName) {
    // Retirer la classe active de tous les onglets
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    // Activer l'onglet sélectionné
    document.getElementById(`${tabName}-tab`)?.classList.add('active');
    event.target.classList.add('active');
    
    // Charger les données selon l'onglet
    if (tabName === 'categories') {
        loadCategories();
    } else if (tabName === 'items') {
        loadCategories(); // Pour le select
        loadItems();
    }
}

// ============================================
// INITIALISATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Charger les catégories au démarrage
    loadCategories();
});