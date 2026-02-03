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
            const response = await fetch('/api/client/menu');
            if (!response.ok) throw new Error('Erreur chargement menu');
            
            this.menu = await response.json();
            this.renderMenu();
            
            document.getElementById('menu-loading').classList.add('hidden');
            document.getElementById('menu-content').classList.remove('hidden');
        } catch (error) {
            console.error('Erreur:', error);
            document.getElementById('menu-loading').classList.add('hidden');
            document.getElementById('menu-error').textContent = 'Impossible de charger le menu. Réessayez plus tard.';
            document.getElementById('menu-error').classList.remove('hidden');
        }
    }

    renderMenu() {
        const container = document.getElementById('categories');
        container.innerHTML = '';

        this.menu.forEach(category => {
            const categoryEl = document.createElement('div');
            categoryEl.className = 'category';
            
            categoryEl.innerHTML = `
                <h2 class="category-title">${category.name}</h2>
                ${category.description ? `<p class="category-description">${category.description}</p>` : ''}
                <div class="menu-items">
                    ${category.items.map(item => this.renderMenuItem(item)).join('')}
                </div>
            `;
            
            container.appendChild(categoryEl);
        });
    }

    renderMenuItem(item) {
        const unavailableClass = !item.available ? 'menu-item-unavailable' : '';
        const imageUrl = item.image_url || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" font-family="Arial" font-size="12" fill="%23999" text-anchor="middle" dominant-baseline="middle"%3EImage%3C/text%3E%3C/svg%3E';
        
        return `
            <div class="menu-item ${unavailableClass}" onclick="${item.available ? `addToCart(${item.id})` : ''}">
                <img src="${imageUrl}" alt="${item.name}" class="menu-item-image">
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
        
        if (existing) {
            existing.quantity++;
        } else {
            this.cart.push({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: 1
            });
        }

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
        // Update count
        document.getElementById('cart-count').textContent = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        // Update total
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        document.getElementById('cart-total').textContent = `${total.toFixed(2)}€`;
        
        // Update button
        document.getElementById('checkout-btn').disabled = this.cart.length === 0;
        document.getElementById('checkout-btn').innerHTML = `Commander (${total.toFixed(2)}€)`;
        
        // Update cart items display
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
            if (item.quantity > 1) {
                item.quantity--;
            } else {
                this.cart = this.cart.filter(i => i.id !== itemId);
            }
            this.updateCart();
        }
    }

    increaseQuantity(itemId) {
        const item = this.cart.find(i => i.id === itemId);
        if (item) {
            item.quantity++;
            this.updateCart();
        }
    }

    removeFromCart(itemId) {
        this.cart = this.cart.filter(i => i.id !== itemId);
        this.updateCart();
    }

    async checkout() {
        if (!this.tableNumber.trim()) {
            alert('Veuillez entrer un numéro de table.');
            return;
        }

        if (this.cart.length === 0) {
            alert('Votre panier est vide.');
            return;
        }

        const orderData = {
            table_number: this.tableNumber,
            total: this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
            items: this.cart.map(item => ({
                id: item.id,
                quantity: item.quantity
            }))
        };

        try {
            const response = await fetch('/api/client/order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            });

            const result = await response.json();

            if (result.success) {
                // Show order confirmation
                document.getElementById('order-number').textContent = result.order_id;
                document.getElementById('order-table').textContent = this.tableNumber;
                document.getElementById('order-total').textContent = `${orderData.total.toFixed(2)}€`;
                document.getElementById('order-modal').classList.remove('hidden');
                
                // Clear cart
                this.cart = [];
                this.updateCart();
            } else {
                alert('Erreur lors de la commande: ' + (result.error || 'Inconnue'));
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la commande. Réessayez plus tard.');
        }
    }

    closeOrderModal() {
        document.getElementById('order-modal').classList.add('hidden');
    }
}

// Global functions for onclick handlers
let app;

function addToCart(itemId) {
    app.addToCart(itemId);
}

function decreaseQuantity(itemId) {
    app.decreaseQuantity(itemId);
}

function increaseQuantity(itemId) {
    app.increaseQuantity(itemId);
}

function removeFromCart(itemId) {
    app.removeFromCart(itemId);
}

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

function checkout() {
    app.checkout();
}

function closeOrderModal() {
    app.closeOrderModal();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app = new RestaurantClient();
});