import os
import tempfile
import pytest
from app import app, db

@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        yield

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key'
    })

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    os.close(db_fd)
    os.unlink(db_path)
