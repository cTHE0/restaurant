# 🍽️ Système de Commande Restaurant

Système de commande de restaurant complet avec interface client et administration.  
Conçu pour être intégré dans un portfolio Flask sur PythonAnywhere.

## 📋 Fonctionnalités

### Interface Client (`/restaurant/client/`)
- ✅ Affichage du menu catégorisé
- ✅ Panier avec gestion des quantités
- ✅ Checkout avec numéro de table
- ✅ Confirmation de commande

### Interface Admin (`/restaurant/admin/`)
- ✅ Login sécurisé (sessions Flask)
- ✅ Dashboard avec statistiques en temps réel
- ✅ CRUD complet des catégories
- ✅ CRUD complet des items de menu
- ✅ Gestion des commandes (statuts: pending → preparing → ready → delivered)
- ✅ Upload d'images pour les plats

### API REST
- `GET /restaurant/api/client/menu` - Menu pour les clients
- `POST /restaurant/api/client/order` - Créer une commande
- `GET/POST /restaurant/api/admin/categories` - Gestion catégories
- `GET/PUT/DELETE /restaurant/api/admin/categories/<id>` - CRUD catégorie
- `GET/POST /restaurant/api/admin/items` - Gestion items
- `GET/PUT/DELETE /restaurant/api/admin/items/<id>` - CRUD item
- `GET /restaurant/api/admin/orders` - Liste des commandes
- `PUT /restaurant/api/admin/orders/<id>/status` - Modifier statut

## 🚀 Installation

### Développement local

```bash
# Depuis le dossier restaurant/
pip install -r requirements.txt

# Lancer l'application
python app.py
```

Accéder à http://localhost:5000/restaurant/

### PythonAnywhere

1. Copier le dossier `restaurant/` dans `~/cv/`
2. Modifier le fichier `app.py` principal (`~/cv/app.py`) :

```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-unique'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/tt665/cv/restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser la base de données
from restaurant.database import db
db.init_app(app)

# Enregistrer le blueprint restaurant
from restaurant import restaurant_bp
app.register_blueprint(restaurant_bp)

# Créer les tables au démarrage
with app.app_context():
    from restaurant.models import init_db
    init_db()

# Route CV (racine)
@app.route('/')
def serve_cv():
    return send_from_directory('/home/tt665/cv', 'index.html')

# Route jeu NEON PULSE
@app.route('/neon_pulse')
@app.route('/neon_pulse.html')
def serve_game():
    return send_from_directory('/home/tt665/cv', 'neon_pulse.html')

# Route QR Scanner
@app.route('/qr_scanner_app/')
@app.route('/qr_scanner_app/index.html')
def serve_qr_scanner():
    return send_from_directory('/home/tt665/cv/qr_scanner_app', 'index.html')

@app.route('/qr_scanner_app/<path:filename>')
def serve_qr_scanner_files(filename):
    return send_from_directory('/home/tt665/cv/qr_scanner_app', filename)

# Fichiers statiques généraux
@app.route('/<path:filename>')
def serve_file(filename):
    if filename.startswith('restaurant/'):
        return "Not found", 404
    return send_from_directory('/home/tt665/cv', filename)

if __name__ == '__main__':
    app.run(debug=True)
```

3. Recharger l'application web dans PythonAnywhere

## 🔐 Authentification Admin

**Identifiants par défaut** (créés automatiquement) :
- Username: `admin`
- Password: `admin123`

⚠️ **Changez ces identifiants en production !**

## 📁 Structure du projet

```
restaurant/
├── __init__.py          # Blueprint Flask + routes
├── app.py               # Point d'entrée (dev local)
├── config.py            # Configuration
├── database.py          # Instance SQLAlchemy
├── models.py            # Modèles de données
├── requirements.txt     # Dépendances Python
├── README.md            # Documentation
├── static/
│   ├── css/
│   │   ├── style.css    # Styles communs
│   │   ├── client.css   # Styles interface client
│   │   └── admin.css    # Styles interface admin
│   ├── js/
│   │   ├── api.js       # Utilitaires API
│   │   ├── admin.js     # Logique admin
│   │   └── client.js    # Logique client
│   └── uploads/         # Images des plats
└── templates/
    ├── index.html       # Page d'accueil restaurant
    ├── client.html      # Interface client
    └── admin/
        ├── login.html   # Page de connexion
        ├── dashboard.html # Tableau de bord
        ├── menus.html   # Gestion des menus
        └── orders.html  # Gestion des commandes
```

## 🛠️ Technologies

- **Backend**: Flask 3.0, Flask-SQLAlchemy
- **Base de données**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Authentification**: Sessions Flask + Werkzeug

## 📱 URLs

| URL | Description |
|-----|-------------|
| `/restaurant/` | Page d'accueil |
| `/restaurant/client/` | Interface client |
| `/restaurant/admin/login` | Connexion admin |
| `/restaurant/admin/` | Dashboard admin |
| `/restaurant/admin/menus` | Gestion menus |
| `/restaurant/admin/orders` | Gestion commandes |

## 🔧 Modèles de données

### MenuCategory
- `id`: Integer (PK)
- `name`: String(100)
- `description`: Text
- `order`: Integer

### MenuItem
- `id`: Integer (PK)
- `name`: String(200)
- `description`: Text
- `price`: Float
- `image_url`: String(500)
- `category_id`: FK → MenuCategory
- `available`: Boolean
- `order`: Integer

### Order
- `id`: Integer (PK)
- `table_number`: String(50)
- `status`: String(50) ['pending', 'preparing', 'ready', 'delivered', 'cancelled']
- `created_at`: DateTime
- `updated_at`: DateTime
- `total`: Float

### OrderItem
- `id`: Integer (PK)
- `order_id`: FK → Order
- `menu_item_id`: FK → MenuItem
- `quantity`: Integer
- `unit_price`: Float

### AdminUser
- `id`: Integer (PK)
- `username`: String(80)
- `password_hash`: String(200)
- `is_active`: Boolean

## 📝 License

MIT - Théo Couerbe © 2026
