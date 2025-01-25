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
        'SECRET_KEY': 'test-key',
        'RATELIMIT_ENABLED': False
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


@pytest.fixture(scope='function')
def test_user(test_app, test_db):
    """Create a test user"""
    with test_app.app_context():
        user = User(
            username='testuser',
            email='test@test.com'
        )
        user.set_password('password123')
        test_db.session.add(user)
        test_db.session.commit()
        
        # Get a fresh instance from the session
        user = User.query.filter_by(username='testuser').first()
        return user


@pytest.fixture(scope='function')
def test_recipe(test_app, test_db, test_user):
    """Create a test recipe"""
    with test_app.app_context():
        # Get a fresh user instance
        user = User.query.filter_by(username='testuser').first()
        
        recipe = Recipe(
            title='Test Recipe',
            description='Test Description',
            instructions='Test Instructions',
            prep_time_minutes=30,
            cook_time_minutes=60,
            servings=4,
            user_id=user.id
        )
        test_db.session.add(recipe)
        
        # Add ingredients
        ingredient = Ingredient(name='Test Ingredient')
        test_db.session.add(ingredient)
        test_db.session.commit()
        
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=1.0,
            unit='cup'
        )
        test_db.session.add(recipe_ingredient)
        test_db.session.commit()
        
        # Get a fresh instance from the session
        recipe = Recipe.query.filter_by(title='Test Recipe').first()
        return recipe


def test_landing_page(client):
    """Test that landing page loads successfully"""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Recipe' in response.data


def test_recipes_page(client, test_recipe, test_app):
    """Test that recipes page loads successfully"""
    with test_app.app_context():
        # First test without login - should redirect to login page
        response = client.get('/recipes', follow_redirects=True)
        assert response.status_code == 200
        assert b'Please log in to access this page' in response.data
        
        # Login and test again
        client.post('/login',
            data={
                'email': 'test@test.com',
                'password': 'password123'
            }
        )
        
        response = client.get('/recipes', follow_redirects=True)
        assert response.status_code == 200
        assert b'Recipes' in response.data
        assert b'Test Recipe' in response.data


def test_recipes_search(client, test_recipe, test_app):
    """Test recipe search functionality"""
    with test_app.app_context():
        # Login first
        client.post('/login',
            data={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        # Test successful search
        response = client.get('/recipes?q=Test', follow_redirects=True)
        assert response.status_code == 200
        assert b'Test Recipe' in response.data
        
        # Test empty search
        response = client.get('/recipes?q=NonExistent', follow_redirects=True)
        assert response.status_code == 200
        assert b'Test Recipe' not in response.data


def test_login_page(client):
    """Test that login page loads successfully"""
    response = client.get('/login', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_page(client):
    """Test that register page loads successfully"""
    response = client.get('/register', follow_redirects=True)
    assert response.status_code == 200
    assert b'Register' in response.data


def test_user_registration(client, test_app, test_db):
    """Test user registration process"""
    with test_app.app_context():
        # Test successful registration
        response = client.post('/register', 
            data={
                'username': 'newuser',
                'email': 'new@test.com',
                'password': 'password123',
                'password2': 'password123',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Congratulations, you are now a registered user!' in response.data
        
        # Verify user was created
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
                'password2': 'password123',
                'submit': 'Register'
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
                'password2': 'password123',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        assert b'Email already registered' in response.data
        
        # Test password mismatch
        response = client.post('/register',
            data={
                'username': 'testuser3',
                'email': 'test3@test.com',
                'password': 'password123',
                'password2': 'password456',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        assert b'Field must be equal to password' in response.data


def test_login_logout(client, test_user, test_app):
   """Test login/logout functionality"""
   with test_app.app_context():
       # Test invalid credentials
       response = client.post('/login',
           data={
               'email': test_user.email, 
               'password': 'password123',
               'submit': 'Sign In'
           }, follow_redirects=True)
       assert response.status_code == 200
       assert b'Invalid email or password' in response.data

       # Test successful login
       response = client.post('/login',
           data={
               'email': test_user.email,
               'password': 'password123', 
               'submit': 'Sign In'
           },
           follow_redirects=True
       )
       assert response.status_code == 200
       assert b'Invalid email or password' not in response.data

       # Verify protected access
       response = client.get('/home')
       assert response.status_code == 200

       # Test logout
       client.get('/logout')
       response = client.get('/home', follow_redirects=True) 
       assert b'Please log in to access this page' in response.data


def test_new_recipe(client, test_user, test_app):
    """Test recipe creation"""
    with test_app.app_context():
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
        
        recipe = Recipe.query.filter_by(title='New Test Recipe').first()
        assert recipe is not None
        assert recipe.description == 'New Description'
        assert recipe.user_id == test_user.id


def test_edit_recipe(client, test_recipe, test_user, test_app):
    """Test recipe editing"""
    with test_app.app_context():
        # Login first
        client.post('/login',
            data={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        # Get fresh recipe instance
        recipe = db.session.get(Recipe, test_recipe.id)
        
        # Test edit
        response = client.post(f'/recipe/{recipe.id}/edit',
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
    with test_app.app_context():
        # Login first
        response = client.post('/login',
            data={
                'email': test_user.email,
                'password': 'password123',
                'submit': 'Sign In'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Get fresh recipe instance
        recipe = db.session.get(Recipe, test_recipe.id)
        assert recipe is not None
        
        # Test GET request (confirmation page)
        response = client.get(f'/recipe/{recipe.id}/delete')
        assert response.status_code == 200
        assert b'Are you sure you want to delete' in response.data
        
        # Test deletion
        response = client.post(f'/recipe/{recipe.id}/delete',
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b'Recipe has been deleted' in response.data
        
        # Verify recipe is deleted
        deleted_recipe = db.session.get(Recipe, recipe.id)
        assert deleted_recipe is None
        
        # Verify ingredients are deleted
        recipe_ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        assert len(recipe_ingredients) == 0


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
    # Test nonexistent route
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data
    
    # Test blocked paths
    blocked_paths = [
        '/wp-admin',
        '/.git/config',
        '/admin',
        '/phpMyAdmin',
        '/wp-login.php',
        '/administrator',
        '/backup',
        '/.env'
    ]
    
    for path in blocked_paths:
        response = client.get(path)
        assert response.status_code == 404
        assert b'Page Not Found' in response.data


@pytest.fixture
def rate_limit_config(test_app):
    """Configure rate limits for testing"""
    original_config = test_app.config.copy()
    
    # Set strict rate limits for testing
    test_app.config['RATELIMIT_DEFAULT'] = "1 per hour"  # Strict default
    test_app.config['RATELIMIT_STORAGE_URL'] = "memory://"
    
    yield test_app
    
    # Restore original config
    test_app.config.update(original_config)


def test_rate_limiting(client, rate_limit_config):
    """Test rate limiting functionality"""
    with rate_limit_config.app_context():
        rate_limit_config.config['RATELIMIT_ENABLED'] = True  # Add at start of context
        
        # First request should succeed
        response = client.post('/login',
            data={
                'email': 'test@test.com',
                'password': 'wrongpassword',
                'submit': 'Sign In'
            },
            follow_redirects=False
        )
        assert response.status_code == 302
        
        # Second request should be rate limited
        response = client.post('/login',
            data={
                'email': 'test@test.com',
                'password': 'wrongpassword',
                'submit': 'Sign In'
            },
            follow_redirects=False
        )
        assert response.status_code == 429
        assert b'Rate limit exceeded. Please try again later.' in response.data
