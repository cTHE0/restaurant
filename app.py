from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'restaurant-secret-key-change-in-production'  # ⚠️ Changer en prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/tt665/mysite/restaurant/restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/home/tt665/mysite/restaurant/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['APPLICATION_ROOT'] = '/restaurant'
app.config['SESSION_COOKIE_PATH'] = '/restaurant'

# Créer le dossier uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ===== MODELS =====
class MenuCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('menu_category.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, default=0)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float)

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Créer les tables et données initiales
with app.app_context():
    db.create_all()
    
    # Créer admin par défaut (une seule fois)
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin')
        admin.set_password('admin123')  # ⚠️ CHANGER APRÈS PREMIÈRE CONNEXION
        db.session.add(admin)
        
        # Menu par défaut
        cat1 = MenuCategory(name='Plats Principaux', order=1)
        cat2 = MenuCategory(name='Desserts', order=2)
        db.session.add_all([cat1, cat2])
        db.session.flush()
        
        items = [
            MenuItem(name='Pizza Margherita', description='Tomate, mozzarella, basilic', price=12.50, category_id=cat1.id, order=1),
            MenuItem(name='Pâtes Carbonara', description='Spaghetti, œufs, lardons, parmesan', price=14.00, category_id=cat1.id, order=2),
            MenuItem(name='Tiramisu', description='Dessert italien classique', price=7.50, category_id=cat2.id, order=1)
        ]
        db.session.add_all(items)
        db.session.commit()

# ===== DECORATEUR AUTH =====
def admin_required(f):
    def wrapper(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/restaurant/admin/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ===== ROUTES =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client/')
def client():
    return render_template('client.html')

@app.route('/admin/login', methods=['GET', 'POST'])
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

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/restaurant/admin/login')

@app.route('/admin/')
@admin_required
def admin_dashboard():
    total = Order.query.count()
    pending = Order.query.filter_by(status='pending').count()
    today = Order.query.filter(db.func.date(Order.created_at) == datetime.utcnow().date()).count()
    return render_template('admin/dashboard.html', total_orders=total, pending_orders=pending, today_orders=today)

@app.route('/admin/menus')
@admin_required
def admin_menus():
    return render_template('admin/menus.html')

@app.route('/admin/orders')
@admin_required
def admin_orders():
    return render_template('admin/orders.html')

# ===== API CLIENT =====
@app.route('/api/client/menu')
def api_menu():
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

@app.route('/api/client/order', methods=['POST'])
def api_order():
    data = request.get_json()
    order = Order(table_number=data['table_number'], total=data['total'])
    db.session.add(order)
    db.session.flush()
    
    for item in data['items']:
        oi = OrderItem(order_id=order.id, menu_item_id=item['id'], quantity=item['quantity'], unit_price=item['price'])
        db.session.add(oi)
    
    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id})

# ===== API ADMIN =====
@app.route('/api/admin/categories', methods=['GET', 'POST'])
@admin_required
def api_categories():
    if request.method == 'POST':
        data = request.get_json()
        cat = MenuCategory(name=data['name'], description=data.get('description', ''), order=data.get('order', 0))
        db.session.add(cat)
        db.session.commit()
        return jsonify({'success': True, 'id': cat.id})
    return jsonify([{'id': c.id, 'name': c.name, 'description': c.description, 'order': c.order} for c in MenuCategory.query.order_by(MenuCategory.order).all()])

@app.route('/api/admin/items', methods=['GET', 'POST'])
@admin_required
def api_items():
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

@app.route('/api/admin/orders')
@admin_required
def api_orders():
    status = request.args.get('status')
    query = Order.query
    if status and status != 'all':
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    
    result = []
    for o in orders:
        items = []
        for oi in o.order_items:
            mi = MenuItem.query.get(oi.menu_item_id)
            if mi:
                items.append({'name': mi.name, 'quantity': oi.quantity, 'unit_price': oi.unit_price})
        result.append({
            'id': o.id,
            'table_number': o.table_number,
            'status': o.status,
            'created_at': o.created_at.isoformat(),
            'total': o.total,
            'items': items
        })
    return jsonify(result)

@app.route('/api/admin/orders/<int:oid>/status', methods=['PUT'])
@admin_required
def api_order_status(oid):
    order = Order.query.get(oid)
    if not order:
        return jsonify({'error': 'Commande non trouvée'}), 404
    data = request.get_json()
    order.status = data['status']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)