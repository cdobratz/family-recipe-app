import os
import pytest
from app import app, db
from models import User, Recipe

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_landing_page(client):
    """Test that landing page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    # Check for any common text that should be on the page
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

def test_user_registration(client):
    """Test user registration"""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'password123',
        'password2': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.email == 'test@test.com'
