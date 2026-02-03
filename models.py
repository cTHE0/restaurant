from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class MenuCategory(db.Model):
    __tablename__ = 'menu_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    items = db.relationship('MenuItem', backref='category', lazy=True, cascade='all, delete-orphan')

class MenuItem(db.Model):
    __tablename__ = 'menu_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('menu_category.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total = db.Column(db.Float, default=0)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float)
    menu_item = db.relationship('MenuItem')

class AdminUser(db.Model):
    __tablename__ = 'admin_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Initialiser les données par défaut
def init_db():
    """Créer les tables et données par défaut"""
    db.create_all()
    
    # Créer admin par défaut (une seule fois)
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Créer catégories par défaut
        category1 = MenuCategory(name='Plats Principaux', description='Nos plats principaux', order=1)
        category2 = MenuCategory(name='Desserts', description='Nos desserts maison', order=2)
        db.session.add(category1)
        db.session.add(category2)
        db.session.flush()
        
        # Créer items par défaut
        items = [
            MenuItem(name='Pizza Margherita', description='Tomate, mozzarella, basilic', price=12.50, category_id=category1.id, available=True, order=1),
            MenuItem(name='Pâtes Carbonara', description='Spaghetti, œufs, lardons, parmesan', price=14.00, category_id=category1.id, available=True, order=2),
            MenuItem(name='Tiramisu', description='Dessert italien classique', price=7.50, category_id=category2.id, available=True, order=1)
        ]
        db.session.add_all(items)
        db.session.commit()