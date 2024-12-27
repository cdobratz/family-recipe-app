# Family Recipe App

<img src="images/cd_octocat_med.png" width="60%">

A Flask web application for preserving and sharing family recipes. This platform is dedicated to keeping old recipes alive and accessible while creating and sharing new ones.

## Features

- User Registration and Authentication
- Recipe Management (Create, Read, Update, Delete)
- Dynamic Ingredient Management
- Recipe Search Functionality
- Latest Recipes Display
- Responsive Design with Bootstrap
- Secure Password Management

## Tech Stack

### Backend
- Flask 3.0.0
- SQLAlchemy 2.0.23
- Flask-Login for authentication
- Flask-WTF for forms
- Flask-Migrate for database migrations
- Flask-Bcrypt for password hashing

### Frontend
- Bootstrap 5 for responsive design
- Font Awesome for icons
- Custom JavaScript for dynamic forms

### Testing & CI/CD
- pytest for unit testing
- GitHub Actions for CI/CD pipeline
- Flake8 for code linting

## Project Structure

```
family-site/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── models.py           # Database models
├── forms.py            # Form definitions
├── templates/          # Jinja2 templates
├── static/            # Static files (CSS, JS)
├── tests/             # Test suite
└── instance/          # Instance-specific files
```

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
```bash
python init_db.py
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5001`

## Development

### Running Tests
```bash
python -m pytest
```

### Code Style
The project uses Flake8 for code linting. Run:
```bash
flake8 .
```

### Branch Strategy
- `main`: Production-ready code
- `development`: Active development
- `family`: Family-specific deployments

## Features in Detail

### Recipe Management
- Create new recipes with multiple ingredients
- Dynamic ingredient form with quantity and unit selection
- Edit existing recipes
- Delete recipes with confirmation
- View detailed recipe information

### Search Functionality
- Search recipes by title, description, or instructions
- View latest recipes on the main page
- Filter recipes by category

### User System
- User registration with email verification
- Secure password handling
- User-specific recipe management
- Profile management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
