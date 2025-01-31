from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Configure the SQLite database path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "test.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Define a simple test model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

with app.app_context():
    # Create the database and tables
    db.create_all()
    
    try:
        # Create a test user
        test_user = User(name='Test User', email='test@example.com')
        db.session.add(test_user)
        db.session.commit()
        
        # Query the user to verify
        user = User.query.first()
        print("Database connection successful!")
        print(f"Retrieved user: {user.name} ({user.email})")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        db.session.close()


