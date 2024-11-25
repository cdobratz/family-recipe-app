from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db, User
from config import Config
import os

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

# Create the database and tables
with app.app_context():
    # Create the instance directory if it doesn't exist
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Create all database tables
    db.create_all()
    
    # Check if test user already exists
    existing_user = User.query.filter_by(email='test@example.com').first()
    
    if existing_user:
        print("Test user already exists!")
        print("Test user credentials:")
        print("Email: test@example.com")
        print("Password: password123")
    else:
        # Create a test user
        test_user = User(
            username='testuser',
            email='test@example.com'
        )
        test_user.set_password('password123')
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("Database initialized and test user created successfully!")
            print("Test user credentials:")
            print("Email: test@example.com")
            print("Password: password123")
        except Exception as e:
            print(f"Error creating test user: {e}")
            db.session.rollback()
