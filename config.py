import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Basic Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'recipe_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_SECURE = os.environ.get('PRODUCTION', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    
    # Security Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Static File Configuration
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    TEMPLATES_AUTO_RELOAD = True
