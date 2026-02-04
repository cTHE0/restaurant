import os

# Détecter l'environnement (PythonAnywhere ou local)
IS_PYTHONANYWHERE = os.path.exists('/home/tt665')
BASE_DIR = '/home/tt665/cv' if IS_PYTHONANYWHERE else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'restaurant-secret-key-change-in-production-2026')
    
    # Base de données SQLite
    if IS_PYTHONANYWHERE:
        SQLALCHEMY_DATABASE_URI = 'sqlite:////home/tt665/cv/restaurant.db'
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "restaurant.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}