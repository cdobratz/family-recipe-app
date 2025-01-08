from flask import Flask
from models import db, User, Recipe, Ingredient, RecipeIngredient
from config import Config
import os

# Create the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db.init_app(app)

def create_ingredients_for_recipe(recipe, ingredients_text):
    # Split ingredients text into lines
    ingredient_lines = ingredients_text.split('\n')
    for line in ingredient_lines:
        # Create ingredient if it doesn't exist
        ingredient_name = line.split(' ', 1)[1] if ' ' in line else line
        ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
        if not ingredient:
            ingredient = Ingredient(name=ingredient_name)
            db.session.add(ingredient)
            db.session.commit()
        
        # Create recipe ingredient relationship
        quantity = line.split(' ')[0] if ' ' in line else "1"
        unit = "unit"  # Default unit
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.recipe_id,
            ingredient_id=ingredient.ingredient_id,
            quantity=float(quantity),
            unit=unit
        )
        db.session.add(recipe_ingredient)

def create_test_data():
    with app.app_context():
        try:
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
                            'instructions': (
                                '1. Preheat oven to 375°F\n'
                                '2. Mix apples with sugar and cinnamon\n'
                                '3. Fill pie crust\n'
                                '4. Bake for 45 minutes'
                            ),
                            'prep_time': '30',
                            'cook_time': '45 minutes',
                            'servings': 8
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
                db.session.commit()
                print(f"Created user: {user.username}")

                # Create recipes for this user
                for recipe_data in user_data['recipes']:
                    try:
                        recipe = Recipe(
                            title=recipe_data['title'],
                            description=recipe_data['description'],
                            instructions=recipe_data['instructions'],
                            prep_time_minutes=30,
                            cook_time_minutes=45,
                            servings=recipe_data['servings'],
                            user_id=user.user_id
                        )
                        db.session.add(recipe)
                        db.session.commit()
                        print(f"Created recipe: {recipe.title}")
                    except Exception as e:
                        print(f"Error creating recipe {recipe_data['title']}: {e}")
                        db.session.rollback()

        except Exception as e:
            print(f"Error in create_test_data: {e}")
            db.session.rollback()


if __name__ == '__main__':
    create_test_data()
    print("Test data creation complete!")
