"""
Blueprint principal pour le système de restaurant
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session, send_from_directory
from datetime import datetime
from .database import db
from .models import MenuCategory, MenuItem, Order, OrderItem, AdminUser
import os

# Créer le Blueprint
restaurant_bp = Blueprint('restaurant', __name__, 
                         url_prefix='/restaurant',
                         template_folder='templates',
                         static_folder='static')

# ============================================
# DECORATEUR ADMIN
# ============================================

def admin_required(f):
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/restaurant/admin/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ============================================
# ROUTES PUBLIQUES
# ============================================

@restaurant_bp.route('/')
def index():
    return render_template('index.html')

@restaurant_bp.route('/client/')
def client():
    return render_template('client.html')

# ============================================
# ROUTES ADMIN
# ============================================

@restaurant_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect('/restaurant/admin/')
        
        return render_template('admin/login.html', error='Identifiants invalides')
    
    return render_template('admin/login.html')

@restaurant_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/restaurant/admin/login')

@restaurant_bp.route('/admin/')
@admin_required
def admin_dashboard():
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(db.func.date(Order.created_at) == today).count()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         today_orders=today_orders)

@restaurant_bp.route('/admin/menus')
@admin_required
def admin_menus():
    return render_template('admin/menus.html')

@restaurant_bp.route('/admin/orders')
@admin_required
def admin_orders():
    return render_template('admin/orders.html')

# ============================================
# API CLIENT
# ============================================

@restaurant_bp.route('/api/client/menu')
def api_client_menu():
    categories = MenuCategory.query.order_by(MenuCategory.order).all()
    result = []
    for cat in categories:
        items = MenuItem.query.filter_by(category_id=cat.id, available=True).order_by(MenuItem.order).all()
        if items:
            result.append({
                'id': cat.id,
                'name': cat.name,
                'description': cat.description,
                'items': [{
                    'id': i.id,
                    'name': i.name,
                    'description': i.description,
                    'price': i.price,
                    'image_url': i.image_url,
                    'available': i.available
                } for i in items]
            })
    return jsonify(result)

@restaurant_bp.route('/api/client/order', methods=['POST'])
def api_client_order():
    data = request.get_json()
    order = Order(table_number=data['table_number'], total=data['total'])
    db.session.add(order)
    db.session.flush()
    
    for item in data['items']:
        oi = OrderItem(order_id=order.id, menu_item_id=item['id'], quantity=item['quantity'], unit_price=item['price'])
        db.session.add(oi)
    
    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id})

# ============================================
# API ADMIN - CATEGORIES
# ============================================

@restaurant_bp.route('/api/admin/categories', methods=['GET', 'POST'])
@admin_required
def api_admin_categories():
    if request.method == 'POST':
        data = request.get_json()
        cat = MenuCategory(name=data['name'], description=data.get('description', ''), order=data.get('order', 0))
        db.session.add(cat)
        db.session.commit()
        return jsonify({'success': True, 'id': cat.id})
    return jsonify([{'id': c.id, 'name': c.name, 'description': c.description, 'order': c.order} for c in MenuCategory.query.order_by(MenuCategory.order).all()])

@restaurant_bp.route('/api/admin/categories/<int:category_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_admin_category(category_id):
    category = MenuCategory.query.get(category_id)
    if not category:
        return jsonify({'error': 'Catégorie non trouvée'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        category.order = data.get('order', category.order)
        db.session.commit()
        return jsonify({'success': True})
    else:  # DELETE
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})

# ============================================
# API ADMIN - ITEMS
# ============================================

@restaurant_bp.route('/api/admin/items', methods=['GET', 'POST'])
@admin_required
def api_admin_items():
    if request.method == 'POST':
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
    return jsonify([{
        'id': i.id, 'name': i.name, 'description': i.description, 'price': i.price,
        'image_url': i.image_url, 'category_id': i.category_id, 'available': i.available, 'order': i.order
    } for i in MenuItem.query.order_by(MenuItem.order).all()])

@restaurant_bp.route('/api/admin/items/<int:item_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_admin_item(item_id):
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item non trouvé'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        item.name = data.get('name', item.name)
        item.description = data.get('description', item.description)
        item.price = float(data.get('price', item.price))
        item.category_id = data.get('category_id', item.category_id)
        item.available = data.get('available', item.available)
        item.order = data.get('order', item.order)
        db.session.commit()
        return jsonify({'success': True})
    else:  # DELETE
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})

# ============================================
# API ADMIN - ORDERS
# ============================================

@restaurant_bp.route('/api/admin/orders')
@admin_required
def api_admin_orders():
    status = request.args.get('status')
    query = Order.query
    if status and status != 'all':
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    
    result = []
    for o in orders:
        items = []
        # CORRECTION ICI : o.items au lieu de o.order_items
        for oi in o.items:  # <-- CHANGÉ ICI
            mi = MenuItem.query.get(oi.menu_item_id)
            if mi:
                items.append({
                    'name': mi.name,
                    'quantity': oi.quantity,
                    'unit_price': oi.unit_price,
                    'total': oi.quantity * oi.unit_price
                })
        result.append({
            'id': o.id,
            'table_number': o.table_number,
            'status': o.status,
            'created_at': o.created_at.isoformat() if o.created_at else datetime.utcnow().isoformat(),
            'updated_at': o.updated_at.isoformat() if o.updated_at else datetime.utcnow().isoformat(),
            'total': o.total,
            'items': items
        })
    return jsonify(result)

@restaurant_bp.route('/api/admin/orders/<int:oid>/status', methods=['PUT'])
@admin_required
def api_admin_order_status(oid):
    order = Order.query.get(oid)
    if not order:
        return jsonify({'error': 'Commande non trouvée'}), 404
    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    return jsonify({'success': True})

@restaurant_bp.route('/api/admin/orders/stats')
@admin_required
def api_admin_order_stats():
    total = Order.query.count()
    by_status = {}
    for status in ['pending', 'preparing', 'ready', 'delivered', 'cancelled']:
        by_status[status] = Order.query.filter_by(status=status).count()
    return jsonify({'total': total, 'by_status': by_status})

# ============================================
# UPLOAD D'IMAGES
# ============================================

@restaurant_bp.route('/api/admin/upload', methods=['POST'])
@admin_required
def api_admin_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(os.path.dirname(__file__), 'static', 'uploads', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        image_url = f"/restaurant/static/uploads/{filename}"
        
        return jsonify({'success': True, 'image_url': image_url, 'filename': filename})
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

@restaurant_bp.route('/static/uploads/<filename>')
def restaurant_uploaded_file(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static', 'uploads'), filename)