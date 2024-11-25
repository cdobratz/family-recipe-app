from flask import Flask
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    users = User.query.all()
    print("\nUsers in database:")
    print("-----------------")
    if users:
        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Created at: {user.created_at}")
            print("-----------------")
    else:
        print("No users found in the database.")
