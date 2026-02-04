"""
Application Flask principale pour www.theocouerbe.com
Intègre le CV, le jeu NEON PULSE, le QR Scanner et le système Restaurant
Compatible PythonAnywhere (une seule web app)

USAGE:
- Sur PythonAnywhere: Copier ce fichier vers ~/cv/app.py
- En local: Exécuter depuis le dossier PARENT de restaurant/
  cd /chemin/vers/cv && python -m restaurant.app
  ou: PYTHONPATH=/chemin/vers/cv python /chemin/vers/cv/restaurant/app.py
"""

from flask import Flask, send_from_directory
import os
import sys

# === CONFIGURATION ===
# Détecter l'environnement (PythonAnywhere ou local)
IS_PYTHONANYWHERE = os.path.exists('/home/tt665')

if IS_PYTHONANYWHERE:
    BASE_DIR = '/home/tt665/cv'
else:
    # En local, BASE_DIR est le dossier parent de restaurant/
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # S'assurer que le dossier parent est dans le path pour les imports
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

app = Flask(__name__)

# Configuration Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'restaurant-secret-key-change-in-production-2026')

# Configuration SQLAlchemy pour le restaurant
if IS_PYTHONANYWHERE:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/tt665/cv/restaurant.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "restaurant.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# === INITIALISATION BASE DE DONNÉES ===
from restaurant.database import db
db.init_app(app)

# === ENREGISTREMENT DU BLUEPRINT RESTAURANT ===
from restaurant import restaurant_bp
app.register_blueprint(restaurant_bp)

# Créer les tables et données par défaut au premier démarrage
with app.app_context():
    from restaurant.models import init_db
    init_db()

# ============================================
# ROUTES PRINCIPALES (CV, Jeu, QR Scanner)
# ============================================

@app.route('/')
def serve_cv():
    """Page d'accueil - CV personnel"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/neon_pulse')
@app.route('/neon_pulse.html')
def serve_game():
    """Jeu NEON PULSE INFINITY"""
    return send_from_directory(BASE_DIR, 'neon_pulse.html')

@app.route('/qr_scanner_app/')
@app.route('/qr_scanner_app/index.html')
def serve_qr_scanner():
    """Application QR Scanner PWA"""
    return send_from_directory(os.path.join(BASE_DIR, 'qr_scanner_app'), 'index.html')

@app.route('/qr_scanner_app/<path:filename>')
def serve_qr_scanner_files(filename):
    """Fichiers statiques QR Scanner"""
    return send_from_directory(os.path.join(BASE_DIR, 'qr_scanner_app'), filename)

@app.route('/<path:filename>')
def serve_file(filename):
    """Servir les fichiers statiques restants (CSS, JS, images)"""
    if filename.startswith('restaurant/'):
        return "Not found", 404
    return send_from_directory(BASE_DIR, filename)

# ============================================
# GESTION DES ERREURS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>404 - Page non trouvée</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #f1f5f9; }}
        .container {{ background: white; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        h1 {{ color: #ef4444; }}
        a {{ color: #2563eb; text-decoration: none; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>404 - Page non trouvée</h1>
            <p>La page demandée n'existe pas.</p>
            <p><a href="/">← Retour au CV</a> | <a href="/restaurant/">Restaurant</a></p>
        </div>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(e):
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>500 - Erreur serveur</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #f1f5f9; }}
        .container {{ background: white; padding: 40px; border-radius: 20px; max-width: 500px; margin: 0 auto; }}
        h1 {{ color: #ef4444; }}
        a {{ color: #2563eb; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>500 - Erreur serveur</h1>
            <p>Une erreur interne s'est produite.</p>
            <p><a href="/">← Retour au CV</a></p>
        </div>
    </body>
    </html>
    """, 500

# ============================================
# POINT D'ENTRÉE
# ============================================

if __name__ == '__main__':
    print(f"🍽️ Restaurant App - Mode {'PythonAnywhere' if IS_PYTHONANYWHERE else 'Local'}")
    print(f"📁 BASE_DIR: {BASE_DIR}")
    print(f"🔗 http://localhost:5000/restaurant/")
    app.run(debug=True, host='0.0.0.0', port=5000)
