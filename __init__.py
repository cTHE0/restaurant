"""
Blueprint principal pour le système de restaurant
Gère les routes client et admin avec API REST
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session, send_from_directory, url_for
from functools import wraps
from datetime import datetime
import os

from .database import db
from .models import MenuCategory, MenuItem, Order, OrderItem, AdminUser

# Créer le Blueprint avec chemins relatifs corrects
restaurant_bp = Blueprint(
    'restaurant', 
    __name__, 
    url_prefix='/restaurant',
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

# ============================================
# DECORATEUR ADMIN AVEC FUNCTOOLS.WRAPS
# ============================================

def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('restaurant.admin_login'))
        return f(*args, **kwargs)
    return wrapper

# ============================================
# ROUTES PUBLIQUES
# ============================================

@restaurant_bp.route('/')
def index():
    """Page d'accueil du restaurant"""
    return render_template('index.html')

@restaurant_bp.route('/client/')
@restaurant_bp.route('/client')
def client():
    """Interface client pour commander"""
    return render_template('client.html')

# ============================================
# ROUTES ADMIN - AUTHENTIFICATION
# ============================================

@restaurant_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Connexion admin"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('admin/login.html', error='Veuillez remplir tous les champs')
        
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session.permanent = True
            return redirect(url_for('restaurant.admin_dashboard'))
        
        return render_template('admin/login.html', error='Identifiants invalides')
    
    return render_template('admin/login.html')

@restaurant_bp.route('/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.clear()
    return redirect(url_for('restaurant.admin_login'))

# ============================================
# ROUTES ADMIN - PAGES
# ============================================

@restaurant_bp.route('/admin/')
@restaurant_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Dashboard admin avec statistiques"""
    try:
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        preparing_orders = Order.query.filter_by(status='preparing').count()
        ready_orders = Order.query.filter_by(status='ready').count()
        
        today = datetime.utcnow().date()
        today_orders = Order.query.filter(
            db.func.date(Order.created_at) == today
        ).count()
        
        today_revenue = db.session.query(db.func.sum(Order.total)).filter(
            db.func.date(Order.created_at) == today,
            Order.status != 'cancelled'
        ).scalar() or 0
        
        return render_template('admin/dashboard.html', 
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             preparing_orders=preparing_orders,
                             ready_orders=ready_orders,
                             today_orders=today_orders,
                             today_revenue=round(today_revenue, 2))
    except Exception as e:
        return render_template('admin/dashboard.html',
                             total_orders=0,
                             pending_orders=0,
                             preparing_orders=0,
                             ready_orders=0,
                             today_orders=0,
                             today_revenue=0,
                             error=str(e))

@restaurant_bp.route('/admin/menus')
@admin_required
def admin_menus():
    """Page de gestion des menus"""
    return render_template('admin/menus.html')

@restaurant_bp.route('/admin/orders')
@admin_required
def admin_orders():
    """Page de gestion des commandes"""
    return render_template('admin/orders.html')

# ============================================
# API CLIENT - MENU
# ============================================

@restaurant_bp.route('/api/client/menu')
def api_client_menu():
    """Récupérer le menu pour les clients"""
    try:
        categories = MenuCategory.query.order_by(MenuCategory.order).all()
        result = []
        
        for cat in categories:
            items = MenuItem.query.filter_by(
                category_id=cat.id, 
                available=True
            ).order_by(MenuItem.order).all()
            
            if items:
                result.append({
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description or '',
                    'items': [{
                        'id': item.id,
                        'name': item.name,
                        'description': item.description or '',
                        'price': float(item.price),
                        'image_url': item.image_url or '',
                        'available': item.available
                    } for item in items]
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# API CLIENT - COMMANDES
# ============================================

@restaurant_bp.route('/api/client/order', methods=['POST'])
def api_client_order():
    """Créer une nouvelle commande"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
        
        table_number = data.get('table_number', '').strip()
        if not table_number:
            return jsonify({'error': 'Numéro de table requis'}), 400
        
        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'Panier vide'}), 400
        
        total = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)
        
        order = Order(
            table_number=table_number, 
            total=total,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        for item in items:
            order_item = OrderItem(
                order_id=order.id, 
                menu_item_id=int(item['id']), 
                quantity=int(item.get('quantity', 1)), 
                unit_price=float(item.get('price', 0))
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'order_id': order.id,
            'message': 'Commande enregistrée avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================
# API ADMIN - CATEGORIES
# ============================================

@restaurant_bp.route('/api/admin/categories', methods=['GET', 'POST'])
@admin_required
def api_admin_categories():
    """Lister ou créer des catégories"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({'error': 'Nom requis'}), 400
            
            category = MenuCategory(
                name=data['name'].strip(),
                description=data.get('description', '').strip(),
                order=int(data.get('order', 0))
            )
            db.session.add(category)
            db.session.commit()
            
            return jsonify({'success': True, 'id': category.id})
        
        categories = MenuCategory.query.order_by(MenuCategory.order).all()
        return jsonify([{
            'id': c.id, 
            'name': c.name, 
            'description': c.description or '', 
            'order': c.order
        } for c in categories])
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@restaurant_bp.route('/api/admin/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def api_admin_category(category_id):
    """Récupérer, modifier ou supprimer une catégorie"""
    try:
        category = MenuCategory.query.get(category_id)
        if not category:
            return jsonify({'error': 'Catégorie non trouvée'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'order': category.order
            })
        
        if request.method == 'PUT':
            data = request.get_json()
            if data.get('name'):
                category.name = data['name'].strip()
            if 'description' in data:
                category.description = data['description'].strip() if data['description'] else ''
            if 'order' in data:
                category.order = int(data['order'])
            db.session.commit()
            return jsonify({'success': True})
        
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================
# API ADMIN - ITEMS
# ============================================

@restaurant_bp.route('/api/admin/items', methods=['GET', 'POST'])
@admin_required
def api_admin_items():
    """Lister ou créer des items"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data or not data.get('name') or not data.get('price') or not data.get('category_id'):
                return jsonify({'error': 'Nom, prix et catégorie requis'}), 400
            
            item = MenuItem(
                name=data['name'].strip(),
                description=data.get('description', '').strip(),
                price=float(data['price']),
                category_id=int(data['category_id']),
                image_url=data.get('image_url', ''),
                available=bool(data.get('available', True)),
                order=int(data.get('order', 0))
            )
            db.session.add(item)
            db.session.commit()
            
            return jsonify({'success': True, 'id': item.id})
        
        items = MenuItem.query.order_by(MenuItem.category_id, MenuItem.order).all()
        return jsonify([{
            'id': i.id, 
            'name': i.name, 
            'description': i.description or '', 
            'price': float(i.price),
            'image_url': i.image_url or '', 
            'category_id': i.category_id, 
            'available': i.available, 
            'order': i.order
        } for i in items])
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@restaurant_bp.route('/api/admin/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def api_admin_item(item_id):
    """Récupérer, modifier ou supprimer un item"""
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item non trouvé'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'id': item.id,
                'name': item.name,
                'description': item.description or '',
                'price': float(item.price),
                'image_url': item.image_url or '',
                'category_id': item.category_id,
                'available': item.available,
                'order': item.order
            })
        
        if request.method == 'PUT':
            data = request.get_json()
            if 'name' in data:
                item.name = data['name'].strip()
            if 'description' in data:
                item.description = data['description'].strip() if data['description'] else ''
            if 'price' in data:
                item.price = float(data['price'])
            if 'category_id' in data:
                item.category_id = int(data['category_id'])
            if 'image_url' in data:
                item.image_url = data['image_url']
            if 'available' in data:
                item.available = bool(data['available'])
            if 'order' in data:
                item.order = int(data['order'])
            db.session.commit()
            return jsonify({'success': True})
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================
# API ADMIN - ORDERS
# ============================================

@restaurant_bp.route('/api/admin/orders')
@admin_required
def api_admin_orders():
    """Lister les commandes avec filtrage"""
    try:
        status = request.args.get('status', 'all')
        
        query = Order.query
        if status and status != 'all':
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        result = []
        for order in orders:
            items_list = []
            for order_item in order.items:
                menu_item = MenuItem.query.get(order_item.menu_item_id)
                items_list.append({
                    'name': menu_item.name if menu_item else 'Item supprimé',
                    'quantity': order_item.quantity,
                    'unit_price': float(order_item.unit_price) if order_item.unit_price else 0,
                    'total': order_item.quantity * (float(order_item.unit_price) if order_item.unit_price else 0)
                })
            
            result.append({
                'id': order.id,
                'table_number': order.table_number or 'N/A',
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else datetime.utcnow().isoformat(),
                'total': float(order.total) if order.total else 0,
                'items': items_list
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@restaurant_bp.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def api_admin_order_status(order_id):
    """Modifier le statut d'une commande"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'preparing', 'ready', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Statut invalide'}), 400
        
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'new_status': new_status})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@restaurant_bp.route('/api/admin/orders/stats')
@admin_required
def api_admin_order_stats():
    """Statistiques des commandes"""
    try:
        total = Order.query.count()
        by_status = {}
        for status in ['pending', 'preparing', 'ready', 'delivered', 'cancelled']:
            by_status[status] = Order.query.filter_by(status=status).count()
        
        total_revenue = db.session.query(db.func.sum(Order.total)).filter(
            Order.status != 'cancelled'
        ).scalar() or 0
        
        return jsonify({
            'total': total, 
            'by_status': by_status,
            'total_revenue': round(float(total_revenue), 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# UPLOAD D'IMAGES
# ============================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@restaurant_bp.route('/api/admin/upload', methods=['POST'])
@admin_required
def api_admin_upload():
    """Uploader une image pour un item"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Type de fichier non autorisé'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}.{ext}"
        
        upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        image_url = f"/restaurant/static/uploads/{filename}"
        
        return jsonify({
            'success': True, 
            'image_url': image_url, 
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@restaurant_bp.route('/static/uploads/<filename>')
def serve_uploaded_file(filename):
    """Servir les fichiers uploadés"""
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    return send_from_directory(upload_folder, filename)
