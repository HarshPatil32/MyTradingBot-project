import sys
import os

# Make backend/legacy and backend importable from tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'legacy'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
