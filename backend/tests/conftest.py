import sys
import os
import pytest

if os.environ.get("SKIP_FLASK_APP", "0") == "1":
    flask_app = None
else:
    from app import app as flask_app

# Set before any app import so validate_env_vars() is suppressed during tests
os.environ.setdefault("TESTING", "1")

# Make backend/legacy and backend importable from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'legacy'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def client():
    if flask_app is None:
        pytest.skip("Flask app not available for this test run.")
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client
