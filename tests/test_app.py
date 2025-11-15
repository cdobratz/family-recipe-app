import os
import sys
import pytest
from app import app, db
from models import User, Recipe, Ingredient, RecipeIngredient
from flask_login import current_user, login_user

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def test_app():
    """Configure Flask application for testing"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['RATELIMIT_ENABLED'] = False
    return app

@pytest.fixture
def test_db(test_app):
    """Set up and tear down test database"""
    with test_app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = User(username='testuser', email='testuser@example.com')
    user.set_password('password123')
    test_db.session.add(user)
    test_db.session.commit()
    return user

@pytest.fixture
def test_recipe(test_app, test_db, test_user):
    """Fixture to create a test recipe with ingredients for testing"""
    with test_app.app_context():
        recipe = Recipe(
            title='Test Recipe',
            description='Test Description',
            instructions='Test Instructions',
            prep_time_minutes=30,
            cook_time_minutes=45,
            servings=4,
            user_id=test_user.id
        )
        test_db.session.add(recipe)
        test_db.session.commit()
        return recipe

def login(client):
    response = client.post('/login', data=dict(
        email='testuser@example.com',
        password='password123'
    ), follow_redirects=True)
    print(response.data)  # Debugging information
    return response

def test_login_logout(client, test_user, test_app):
    """Test login/logout functionality"""
    with test_app.test_request_context():
        with test_app.test_client() as client:
            response = login(client)
            assert response.status_code == 200
            
            # Verify the user is logged in
            with client.session_transaction() as sess:
                assert sess.get('_user_id') is not None
            
            # Check flash message
            assert b'You have been logged in!' in response.data

def test_new_recipe(client, test_user, test_app):
    """Test recipe creation"""
    with test_app.app_context():
        login_response = login(client)
        assert login_response.status_code == 200
        print(login_response.data)  # Debugging information

        
        response = client.post('/new_recipe',
            data={
                'title': 'New Test Recipe',
                'description': 'New Description',
                'instructions': 'New Instructions',
                'prep_time_minutes': 15,
                'cook_time_minutes': 30,
                'servings': 2,
                'ingredients-0-ingredient_name': 'Flour',
                'ingredients-0-ingredient_quantity': '2',
                'ingredients-0-ingredient_unit': 'cup'  # Ensure this is a valid choice
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        print(response.data)  # Debugging information
        assert b'Recipe created successfully!' in response.data