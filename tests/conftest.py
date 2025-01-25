import os
import tempfile
import pytest
from app import app, db
from models import User

@pytest.fixture(scope='session')
def test_app():
    """Create a Flask application configured for testing."""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'RATELIMIT_ENABLED': False
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    """Create a test CLI runner."""
    return test_app.test_cli_runner()

@pytest.fixture
def test_user(test_app):
    """Create test user fixture."""
    with test_app.app_context():
        user = User(
            username='testuser',
            email='test@test.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user