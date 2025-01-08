import os
import sys
from app import app as application

# Add your project directory to the sys.path
project_home = '/home/yourusername/family-site'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PRODUCTION'] = 'true'
os.environ['FLASK_DEBUG'] = 'false'
os.environ['SECRET_KEY'] = 'your-production-secret-key'  # Change this to a secure value```
