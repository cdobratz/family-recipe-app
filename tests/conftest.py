import os
import tempfile
import pytest
from app import app, db

@pytest.fixture(scope='session')
def test_app():
    """Create a Flask application configured for testing."""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key',
        'RATELIMIT_ENABLED': False,
        'RATELIMIT_STORAGE_URL': 'memory://',
    })

    # Create application context
    ctx = app.app_context()
    ctx.push()

    # Create all tables
    db.create_all()

    yield app

    # Clean up
    db.session.remove()
    db.drop_all()
    ctx.pop()

@pytest.fixture
def client(test_app):
    """Create a test client."""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Create a test CLI runner."""
    return test_app.test_cli_runner()
