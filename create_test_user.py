from flask import Flask
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Create a test user
    test_user = User(
        username='testuser',
        email='test@example.com'
    )
    test_user.set_password('password123')
    
    # Add and commit to database
    db.session.add(test_user)
    db.session.commit()
    
    print("\nTest user created successfully:")
    print(f"Username: {test_user.username}")
    print(f"Email: {test_user.email}")
    print("Password: password123")
