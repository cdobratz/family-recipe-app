# Family Recipe App

A Flask web application for preserving and sharing family recipes. This platform is dedicated to keeping old recipes alive and accessible while creating and sharing new ones.

## Features

- User Registration and Authentication
- Recipe Creation and Management
- Recipe Viewing and Sharing
- Responsive Design
- Secure Password Management

## Tech Stack

- Backend: Flask 3.0.0
- Database: SQLAlchemy 2.0.23
- Authentication: Flask-Login
- Forms: Flask-WTF
- Password Security: Flask-Bcrypt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cdobratz/family-recipe-app.git
cd family-recipe-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Register a new account or login with existing credentials
2. Browse recipes on the home page
3. Create new recipes using the "Add Recipe" button
4. View detailed recipe information by clicking on a recipe
5. Edit or delete your own recipes

## Contributing

Feel free to fork the repository and submit pull requests for any improvements.
