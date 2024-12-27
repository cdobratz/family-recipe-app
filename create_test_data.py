from flask import Flask
from models import db, User, Recipe
from config import Config
import os

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

def create_test_data():
    with app.app_context():
        # Create test users
        test_users = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'password123',
                'recipes': [
                    {
                        'title': 'Grandma\'s Apple Pie',
                        'description': 'A classic family recipe passed down through generations',
                        'ingredients': '2 pie crusts\n6 cups sliced apples\n1 cup sugar\n2 tbsp cinnamon\n1/4 cup butter',
                        'instructions': '1. Preheat oven to 375°F\n2. Mix apples with sugar and cinnamon\n3. Fill pie crust\n4. Bake for 45 minutes',
                        'prep_time': '30 minutes',
                        'cook_time': '45 minutes',
                        'servings': 8
                    },
                    {
                        'title': 'Sunday Pot Roast',
                        'description': 'Perfect for family gatherings',
                        'ingredients': '3 lb chuck roast\nPotatoes\nCarrots\nOnions\nGarlic\nBeef broth',
                        'instructions': '1. Season roast\n2. Sear all sides\n3. Add vegetables\n4. Cook for 6 hours',
                        'prep_time': '20 minutes',
                        'cook_time': '6 hours',
                        'servings': 6
                    }
                ]
            },
            {
                'username': 'mary_smith',
                'email': 'mary@example.com',
                'password': 'password123',
                'recipes': [
                    {
                        'title': 'Holiday Sugar Cookies',
                        'description': 'Decorated cookies perfect for any holiday',
                        'ingredients': '3 cups flour\n1 cup butter\n1.5 cups sugar\n2 eggs\n1 tsp vanilla',
                        'instructions': '1. Cream butter and sugar\n2. Add eggs and vanilla\n3. Mix in flour\n4. Chill, roll, cut, and bake',
                        'prep_time': '1 hour',
                        'cook_time': '10 minutes',
                        'servings': 24
                    }
                ]
            }
        ]

        for user_data in test_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"User {user_data['email']} already exists")
                continue

            # Create new user
            user = User(username=user_data['username'], email=user_data['email'])
            user.set_password(user_data['password'])
            db.session.add(user)
            
            # Create recipes for this user
            for recipe_data in user_data['recipes']:
                recipe = Recipe(
                    title=recipe_data['title'],
                    description=recipe_data['description'],
                    ingredients=recipe_data['ingredients'],
                    instructions=recipe_data['instructions'],
                    prep_time=recipe_data['prep_time'],
                    cook_time=recipe_data['cook_time'],
                    servings=recipe_data['servings'],
                    user_id=user.id
                )
                db.session.add(recipe)
            
            try:
                db.session.commit()
                print(f"Created user {user_data['email']} with {len(user_data['recipes'])} recipes")
            except Exception as e:
                print(f"Error creating user {user_data['email']}: {e}")
                db.session.rollback()

if __name__ == '__main__':
    create_test_data()
    print("Test data creation complete!")
