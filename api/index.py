import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

# Import the Flask app
from app import app

# Export the app for Vercel
app = app
