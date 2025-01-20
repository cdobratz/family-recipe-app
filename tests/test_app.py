import os
import pytest
from flask_login import current_user
from app import app, db
from models import User, Recipe, Ingredient, RecipeIngredient, Tag, TagType


@pytest.fixture(scope='function')
def test_app():
    """Test app fixture with proper configuration"""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key'
    })
    return app


@pytest.fixture(scope='function')
def test_db():
    """Test database fixture"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(test_app, test_db):
    """Test client fixture"""
    return test_app.test_client()


@pytest.fixture
def test_user(test_app, test_db):
    """Create a test user"""
    with test_app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_recipe(test_app, test_db, test_user):
    """Create a test recipe"""
    with test_app.app_context():
        recipe = Recipe(
            title='Test Recipe',
            description='Test Description',
            instructions='Test Instructions',
            prep_time_minutes=30,
            cook_time_minutes=60,
            servings=4,
            user_id=test_user.id
        )
        db.session.add(recipe)
        
        # Add ingredients
        ingredient = Ingredient(name='Test Ingredient')
        db.session.add(ingredient)
        db.session.commit()
        
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=1.0,
            unit='cup'
        )
        db.session.add(recipe_ingredient)
        db.session.commit()
        
        return recipe


def test_landing_page(client):
    """Test that landing page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Recipe' in response.data


def test_recipes_page(client, test_recipe):
    """Test that recipes page loads successfully"""
    response = client.get('/recipes')
    assert response.status_code == 200
    assert b'Recipes' in response.data
    assert b'Test Recipe' in response.data


def test_recipes_search(client, test_recipe):
    """Test recipe search functionality"""
    # Test successful search
    response = client.get('/recipes?q=Test')
    assert response.status_code == 200
    assert b'Test Recipe' in response.data
    
    # Test empty search
    response = client.get('/recipes?q=NonExistent')
    assert response.status_code == 200
    assert b'Test Recipe' not in response.data


def test_login_page(client):
    """Test that login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_page(client):
    """Test that register page loads successfully"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data


def test_user_registration(client, test_app, test_db):
    """Test user registration process"""
    # Test successful registration
    response = client.post('/register', 
        data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'password2': 'password123'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    with test_app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@test.com'
        assert user.check_password('password123')
    
    # Test duplicate username
    response = client.post('/register',
        data={
            'username': 'newuser',
            'email': 'another@test.com',
            'password': 'password123',
            'password2': 'password123'
        },
        follow_redirects=True
    )
    assert b'Username already exists' in response.data
    
    # Test duplicate email
    response = client.post('/register',
        data={
            'username': 'anotheruser',
            'email': 'new@test.com',
            'password': 'password123',
            'password2': 'password123'
        },
        follow_redirects=True
    )
    assert b'Email already registered' in response.data


def test_login_logout(client, test_user):
    """Test login and logout functionality"""
    # Test successful login
    response = client.post('/login',
        data={
            'username': 'testuser',
            'password': 'password123'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid username or password' not in response.data
    
    # Test invalid password
    response = client.post('/login',
        data={
            'username': 'testuser',
            'password': 'wrongpassword'
        },
        follow_redirects=True
    )
    assert b'Invalid username or password' in response.data
    
    # Test logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


def test_new_recipe(client, test_user, test_app):
    """Test recipe creation"""
    # Login first
    client.post('/login',
        data={
            'username': 'testuser',
            'password': 'password123'
        }
    )
    
    # Test recipe creation
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
            'ingredients-0-ingredient_unit': 'cups'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    with test_app.app_context():
        recipe = Recipe.query.filter_by(title='New Test Recipe').first()
        assert recipe is not None
        assert recipe.description == 'New Description'
        assert recipe.user_id == test_user.id


def test_edit_recipe(client, test_recipe, test_user):
    """Test recipe editing"""
    # Login first
    client.post('/login',
        data={
            'username': 'testuser',
            'password': 'password123'
        }
    )
    
    # Test edit
    response = client.post(f'/recipe/{test_recipe.id}/edit',
        data={
            'title': 'Updated Recipe',
            'description': 'Updated Description',
            'instructions': 'Updated Instructions',
            'prep_time_minutes': 45,
            'cook_time_minutes': 90,
            'servings': 6
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Updated Recipe' in response.data


def test_delete_recipe(client, test_recipe, test_user, test_app):
    """Test recipe deletion"""
    # Login first
    client.post('/login',
        data={
            'username': 'testuser',
            'password': 'password123'
        }
    )
    
    # Test deletion
    response = client.post(f'/recipe/{test_recipe.id}/delete',
        follow_redirects=True
    )
    assert response.status_code == 200
    
    with test_app.app_context():
        recipe = Recipe.query.get(test_recipe.id)
        assert recipe is None


def test_protected_routes(client):
    """Test that protected routes require login"""
    routes = [
        '/new_recipe',
        '/home'
    ]
    
    for route in routes:
        response = client.get(route, follow_redirects=True)
        assert b'Please log in to access this page' in response.data


def test_invalid_routes(client):
    """Test handling of invalid routes"""
    response = client.get('/nonexistent', follow_redirects=True)
    assert response.status_code == 404
    
    # Test blocked paths
    blocked_paths = [
        '/wp-admin',
        '/.git/config',
        '/admin',
        '/phpMyAdmin'
    ]
    
    for path in blocked_paths:
        response = client.get(path)
        assert response.status_code == 404


def test_rate_limiting(client):
    """Test rate limiting functionality"""
    # Test login rate limit
    for _ in range(6):  # Limit is 5 per minute
        response = client.post('/login',
            data={
                'username': 'testuser',
                'password': 'wrongpassword'
            }
        )
    assert response.status_code == 429  # Too Many Requests
