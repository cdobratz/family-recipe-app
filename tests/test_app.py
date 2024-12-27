import pytest
from app import app, db
from models import User, Recipe

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
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
    assert b'Welcome' in response.data

def test_recipes_page(client):
    """Test that recipes page loads successfully"""
    response = client.get('/recipes')
    assert response.status_code == 200

def test_user_registration(client):
    """Test user registration"""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'password123',
        'password2': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(username='testuser').first() is not None
