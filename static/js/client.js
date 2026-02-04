class RestaurantClient {
    constructor() {
        this.cart = [];
        this.menu = [];
        this.tableNumber = localStorage.getItem('table_number') || '';
        this.init();
    }

    init() {
        document.getElementById('table-number').value = this.tableNumber;
        document.getElementById('table-number').addEventListener('change', (e) => {
            this.tableNumber = e.target.value;
            localStorage.setItem('table_number', this.tableNumber);
        });
        this.loadMenu();
    }

    async loadMenu() {
        try {
            const response = await fetch('/restaurant/api/client/menu');
            if (!response.ok) throw new Error('Erreur chargement menu');
            this.menu = await response.json();
            this.renderMenu();
            document.getElementById('menu-loading').classList.add('hidden');
            document.getElementById('menu-content').classList.remove('hidden');
        } catch (error) {
            console.error('Erreur:', error);
            document.getElementById('menu-loading').classList.add('hidden');
            document.getElementById('menu-error').textContent = 'Impossible de charger le menu.';
            document.getElementById('menu-error').classList.remove('hidden');
        }
    }

    renderMenu() {
        const container = document.getElementById('categories');
        container.innerHTML = '';
        this.menu.forEach(category => {
            const el = document.createElement('div');
            el.className = 'category';
            el.innerHTML = `
                <h2 class="category-title">${category.name}</h2>
                ${category.description ? `<p class="category-description">${category.description}</p>` : ''}
                <div class="menu-items">
                    ${category.items.map(item => this.renderMenuItem(item)).join('')}
                </div>
            `;
            container.appendChild(el);
        });
    }

    renderMenuItem(item) {
        const unavailableClass = !item.available ? 'menu-item-unavailable' : '';
        return `
            <div class="menu-item ${unavailableClass}" onclick="${item.available ? `addToCart(${item.id})` : ''}">
                <div class="menu-item-info">
                    <div class="menu-item-name">${item.name}</div>
                    <div class="menu-item-description">${item.description || ''}</div>
                    <div class="menu-item-price">${item.price.toFixed(2)}€</div>
                </div>
            </div>
        `;
    }

    addToCart(itemId) {
        const item = this.findItemById(itemId);
        if (!item) return;
        const existing = this.cart.find(i => i.id === itemId);
        if (existing) existing.quantity++;
        else this.cart.push({...item, quantity: 1});
        this.updateCart();
    }

    findItemById(id) {
        for (const category of this.menu) {
            const item = category.items.find(i => i.id === id);
            if (item) return item;
        }
        return null;
    }

    updateCart() {
        document.getElementById('cart-count').textContent = this.cart.reduce((s, i) => s + i.quantity, 0);
        const total = this.cart.reduce((s, i) => s + (i.price * i.quantity), 0);
        document.getElementById('cart-total').textContent = `${total.toFixed(2)}€`;
        document.getElementById('checkout-btn').disabled = this.cart.length === 0;
        document.getElementById('checkout-btn').innerHTML = `Commander (${total.toFixed(2)}€)`;
        this.renderCartItems();
    }

    renderCartItems() {
        const container = document.getElementById('cart-items');
        if (this.cart.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#666;padding:20px">Panier vide</p>';
            container.classList.add('hidden');
            return;
        }
        container.classList.remove('hidden');
        container.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">${item.price.toFixed(2)}€</div>
                </div>
                <div class="cart-item-quantity">
                    <button class="quantity-btn" onclick="decreaseQuantity(${item.id})">-</button>
                    <span class="quantity-display">${item.quantity}</span>
                    <button class="quantity-btn" onclick="increaseQuantity(${item.id})">+</button>
                </div>
                <button class="remove-item" onclick="removeFromCart(${item.id})">×</button>
            </div>
        `).join('');
    }

    decreaseQuantity(itemId) {
        const item = this.cart.find(i => i.id === itemId);
        if (item) {
            if (item.quantity > 1) item.quantity--;
            else this.cart = this.cart.filter(i => i.id !== itemId);
            this.updateCart();
        }
    }

    increaseQuantity(itemId) {
        const item = this.cart.find(i => i.id === itemId);
        if (item) { item.quantity++; this.updateCart(); }
    }

    removeFromCart(itemId) {
        this.cart = this.cart.filter(i => i.id !== itemId);
        this.updateCart();
    }

    async checkout() {
        if (!this.tableNumber.trim()) { alert('Numéro de table requis.'); return; }
        if (this.cart.length === 0) { alert('Panier vide.'); return; }

        const data = {
            table_number: this.tableNumber,
            total: this.cart.reduce((s, i) => s + (i.price * i.quantity), 0),
            items: this.cart.map(i => ({ id: i.id, quantity: i.quantity, price: i.price }))
        };

        try {
            const response = await fetch('/restaurant/api/client/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (result.success) {
                document.getElementById('order-number').textContent = result.order_id;
                document.getElementById('order-table').textContent = this.tableNumber;
                document.getElementById('order-total').textContent = `${data.total.toFixed(2)}€`;
                document.getElementById('order-modal').classList.add('visible');
                this.cart = [];
                this.updateCart();
            } else {
                alert('Erreur: ' + (result.error || 'Inconnue'));
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la commande.');
        }
    }

    closeOrderModal() {
        document.getElementById('order-modal').classList.remove('visible');
    }
}

let app;
function addToCart(id) { app.addToCart(id); }
function decreaseQuantity(id) { app.decreaseQuantity(id); }
function increaseQuantity(id) { app.increaseQuantity(id); }
function removeFromCart(id) { app.removeFromCart(id); }
function toggleCart() {
    const items = document.getElementById('cart-items');
    const arrow = document.getElementById('cart-arrow');
    if (items.classList.contains('hidden')) {
        items.classList.remove('hidden');
        arrow.textContent = '▲';
    } else {
        items.classList.add('hidden');
        arrow.textContent = '▼';
    }
}
function checkout() { app.checkout(); }
function closeOrderModal() { app.closeOrderModal(); }

document.addEventListener('DOMContentLoaded', () => { app = new RestaurantClient(); });