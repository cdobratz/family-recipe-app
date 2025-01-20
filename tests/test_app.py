import os
import pytest
from app import app, db
from models import User, Recipe


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


def test_landing_page(client):
    """Test that landing page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Recipe' in response.data


def test_recipes_page(client):
    """Test that recipes page loads successfully"""
    response = client.get('/recipes')
    assert response.status_code == 200
    assert b'Recipes' in response.data


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
    """Test user registration"""
    # Test registration
    response = client.post('/register', 
        data={
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'password123',
            'password2': 'password123'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Verify user was created
    with test_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@test.com'
        
        # Verify password was hashed
        assert user.check_password('password123')
        
    # Test login with created user
    response = client.post('/login',
        data={
            'username': 'testuser',
            'password': 'password123'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid username or password' not in response.data
