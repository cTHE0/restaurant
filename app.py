from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from database import db, MenuCategory, MenuItem, Order, OrderItem, AdminUser
from config import Config
import os
from datetime import datetime
import json

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialiser la base de données
db.init_app(app)

# Créer les tables
with app.app_context():
    db.create_all()
    
    # Créer un utilisateur admin par défaut (à changer en production)
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin')
        admin.set_password('admin123')  # ⚠️ Changer ce mot de passe !
        db.session.add(admin)
        db.session.commit()

# ============================================
# ROUTES CLIENT
# ============================================

@app.route('/restaurant/client/')
def client_index():
    """Page d'accueil client"""
    return render_template('client/index.html')

@app.route('/api/client/menu')
def get_menu():
    """API: Obtenir le menu complet"""
    categories = MenuCategory.query.order_by(MenuCategory.order).all()
    
    menu_data = []
    for category in categories:
        items = MenuItem.query.filter_by(
            category_id=category.id, 
            available=True
        ).order_by(MenuItem.order).all()
        
        if items:
            menu_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'items': [{
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'price': item.price,
                    'image_url': item.image_url,
                    'available': item.available
                } for item in items]
            })
    
    return jsonify(menu_data)

@app.route('/api/client/order', methods=['POST'])
def create_order():
    """API: Créer une nouvelle commande"""
    try:
        data = request.get_json()
        
        # Créer la commande
        order = Order(
            table_number=data.get('table_number', 'Table inconnue'),
            total=data.get('total', 0)
        )
        db.session.add(order)
        db.session.flush()  # Obtenir l'ID de la commande
        
        # Ajouter les items
        for item_data in data.get('items', []):
            menu_item = MenuItem.query.get(item_data['id'])
            if menu_item:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=item_data['quantity'],
                    unit_price=menu_item.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Commande passée avec succès !'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/client/order/<int:order_id>')
def get_order_status(order_id):
    """API: Obtenir le statut d'une commande"""
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Commande non trouvée'}), 404
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'total': order.total
    })

# ============================================
# ROUTES ADMIN (AUTHENTIFICATION REQUISE)
# ============================================

def admin_required(f):
    """Décorateur pour routes admin protégées"""
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/restaurant/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de login admin"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            
            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('admin_dashboard'))
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401
        return render_template('admin/login.html', error='Identifiants invalides')
    
    return render_template('admin/login.html')

@app.route('/restaurant/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/restaurant/admin/')
@admin_required
def admin_dashboard():
    """Dashboard admin"""
    # Statistiques
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == datetime.utcnow().date()
    ).count()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         today_orders=today_orders)

# ============================================
# API ADMIN - GESTION MENUS
# ============================================

@app.route('/api/admin/categories', methods=['GET'])
@admin_required
def get_categories():
    """Obtenir toutes les catégories"""
    categories = MenuCategory.query.order_by(MenuCategory.order).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'order': c.order
    } for c in categories])

@app.route('/api/admin/categories', methods=['POST'])
@admin_required
def create_category():
    """Créer une catégorie"""
    data = request.get_json()
    category = MenuCategory(
        name=data['name'],
        description=data.get('description', ''),
        order=data.get('order', 0)
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'success': True, 'id': category.id})

@app.route('/api/admin/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    """Modifier une catégorie"""
    category = MenuCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Catégorie non trouvée'}), 404
    
    data = request.get_json()
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.order = data.get('order', category.order)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """Supprimer une catégorie"""
    category = MenuCategory.query.get(category_id)
    if category:
        db.session.delete(category)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/items', methods=['GET'])
@admin_required
def get_items():
    """Obtenir tous les items de menu"""
    items = MenuItem.query.order_by(MenuItem.order).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'description': i.description,
        'price': i.price,
        'image_url': i.image_url,
        'category_id': i.category_id,
        'available': i.available,
        'order': i.order
    } for i in items])

@app.route('/api/admin/items', methods=['POST'])
@admin_required
def create_item():
    """Créer un item de menu"""
    data = request.get_json()
    item = MenuItem(
        name=data['name'],
        description=data.get('description', ''),
        price=float(data['price']),
        category_id=data['category_id'],
        available=data.get('available', True),
        order=data.get('order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})

@app.route('/api/admin/items/<int:item_id>', methods=['PUT'])
@admin_required
def update_item(item_id):
    """Modifier un item de menu"""
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item non trouvé'}), 404
    
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    item.price = float(data.get('price', item.price))
    item.category_id = data.get('category_id', item.category_id)
    item.available = data.get('available', item.available)
    item.order = data.get('order', item.order)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    """Supprimer un item de menu"""
    item = MenuItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'success': True})

# ============================================
# API ADMIN - GESTION COMMANDES
# ============================================

@app.route('/api/admin/orders', methods=['GET'])
@admin_required
def get_orders():
    """Obtenir toutes les commandes (avec pagination)"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    query = Order.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    orders_data = []
    for order in orders.items:
        items = []
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                items.append({
                    'name': menu_item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total': item.quantity * item.unit_price
                })
        
        orders_data.append({
            'id': order.id,
            'table_number': order.table_number,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'total': order.total,
            'items': items
        })
    
    return jsonify({
        'orders': orders_data,
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page
    })

@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    """Modifier le statut d'une commande"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Commande non trouvée'}), 404
    
    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/admin/orders/stats')
@admin_required
def get_order_stats():
    """Obtenir des statistiques sur les commandes"""
    total = Order.query.count()
    by_status = {}
    for status in ['pending', 'preparing', 'ready', 'delivered', 'cancelled']:
        by_status[status] = Order.query.filter_by(status=status).count()
    
    return jsonify({
        'total': total,
        'by_status': by_status
    })

# ============================================
# UPLOAD D'IMAGES
# ============================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/api/admin/upload', methods=['POST'])
@admin_required
def upload_image():
    """Uploader une image pour un menu item"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if file and allowed_file(file.filename):
        # Créer un nom de fichier unique
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # URL relative pour le frontend
        image_url = f"/restaurant/static/uploads/{filename}"
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': filename
        })
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

@app.route('/restaurant/static/uploads/<filename>')
def uploaded_file(filename):
    """Servir les fichiers uploadés"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================
# TEMPLATES
# ============================================

@app.route('/restaurant/admin/menus')
@admin_required
def admin_menus():
    return render_template('admin/menus.html')

@app.route('/restaurant/admin/orders')
@admin_required
def admin_orders():
    return render_template('admin/orders.html')

# ============================================
# GÉNÉRATEUR DE QR CODE
# ============================================

@app.route('/api/admin/generate-qr')
@admin_required
def generate_qr_code():
    """Générer un QR code pour l'interface client"""
    from urllib.parse import urljoin
    from flask import request
    
    # URL de l'interface client
    base_url = request.host_url.rstrip('/')
    client_url = f"{base_url}/restaurant/client/"
    
    # Générer le QR code (simple version textuelle)
    qr_data = {
        'url': client_url,
        'restaurant': 'Restaurant theocouerbe.com',
        'type': 'menu_ordering'
    }
    
    return jsonify({
        'success': True,
        'url': client_url,
        'qr_data': qr_data
    })

if __name__ == '__main__':
    app.run(debug=True)