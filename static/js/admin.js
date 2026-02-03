// Categories
async function loadCategories() {
    try {
        const response = await fetch('/restaurant/api/admin/categories');
        const categories = await response.json();
        const select = document.getElementById('item-category');
        select.innerHTML = '<option value="">-- Sélectionner --</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.id;
            opt.textContent = cat.name;
            select.appendChild(opt);
        });
        renderCategoriesList(categories);
    } catch (error) { console.error('Erreur:', error); }
}

function renderCategoriesList(categories) {
    const container = document.getElementById('categories-list');
    if (categories.length === 0) {
        container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px">Aucune catégorie</p>';
        return;
    }
    container.innerHTML = categories.map(cat => `
        <div class="category-item">
            <div>
                <div class="category-name">${cat.name}</div>
                ${cat.description ? `<div style="color:#64748b;font-size:0.9rem;margin-top:5px">${cat.description}</div>` : ''}
            </div>
            <div class="item-actions">
                <button class="btn btn-secondary btn-sm" onclick="alert('Modifier non implémenté')">✏️</button>
                <button class="btn btn-danger btn-sm" onclick="deleteCategory(${cat.id})">🗑️</button>
            </div>
        </div>
    `).join('');
}

document.getElementById('category-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('category-name').value,
        description: document.getElementById('category-description').value,
        order: parseInt(document.getElementById('category-order').value)
    };
    try {
        const response = await fetch('/restaurant/api/admin/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        if (response.ok) {
            alert('Catégorie ajoutée !');
            document.getElementById('category-form').reset();
            loadCategories();
        } else {
            alert('Erreur ajout');
        }
    } catch (error) { console.error('Erreur:', error); alert('Erreur serveur'); }
});

async function deleteCategory(id) {
    if (!confirm('Supprimer cette catégorie ?')) return;
    try {
        const response = await fetch(`/restaurant/api/admin/categories/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (response.ok) { loadCategories(); loadItems(); }
        else alert('Erreur suppression');
    } catch (error) { console.error('Erreur:', error); alert('Erreur serveur'); }
}

function resetCategoryForm() {
    document.getElementById('category-form').reset();
}

// Items
async function loadItems() {
    try {
        const response = await fetch('/restaurant/api/admin/items');
        const items = await response.json();
        renderItemsList(items);
    } catch (error) { console.error('Erreur:', error); }
}

function renderItemsList(items) {
    const container = document.getElementById('items-list');
    if (items.length === 0) {
        container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px">Aucun item</p>';
        return;
    }
    container.innerHTML = items.map(item => `
        <div class="menu-item-row">
            <div>
                <div class="item-name">${item.name}</div>
                <div style="color:#64748b;font-size:0.9rem;margin-top:3px">${item.category_id}</div>
                <div class="item-price">${item.price.toFixed(2)}€</div>
            </div>
            <div class="item-actions">
                <button class="btn btn-secondary btn-sm" onclick="alert('Modifier non implémenté')">✏️</button>
                <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">🗑️</button>
            </div>
        </div>
    `).join('');
}

document.getElementById('item-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('item-name').value,
        description: document.getElementById('item-description').value,
        price: parseFloat(document.getElementById('item-price').value),
        category_id: parseInt(document.getElementById('item-category').value),
        available: document.getElementById('item-available').checked,
        order: parseInt(document.getElementById('item-order').value)
    };
    try {
        const response = await fetch('/restaurant/api/admin/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        if (response.ok) {
            alert('Item ajouté !');
            document.getElementById('item-form').reset();
            loadItems();
        } else {
            alert('Erreur ajout');
        }
    } catch (error) { console.error('Erreur:', error); alert('Erreur serveur'); }
});

async function deleteItem(id) {
    if (!confirm('Supprimer cet item ?')) return;
    try {
        const response = await fetch(`/restaurant/api/admin/items/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (response.ok) loadItems();
        else alert('Erreur suppression');
    } catch (error) { console.error('Erreur:', error); alert('Erreur serveur'); }
}

function resetItemForm() {
    document.getElementById('item-form').reset();
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    if (tabName === 'categories') loadCategories();
    else if (tabName === 'items') { loadCategories(); loadItems(); }
}

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAdminAuth()) window.location.href = '/restaurant/admin/login';
    loadCategories();
});