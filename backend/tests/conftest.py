import sys
import os

# Set before any app import so validate_env_vars() is suppressed during tests
os.environ.setdefault("TESTING", "1")

# Make backend/legacy and backend importable from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'legacy'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
