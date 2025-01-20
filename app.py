import logging
from urllib.parse import (
    urlparse, urlunparse, urlsplit, urlunsplit, quote, quote_plus,
    unquote, unquote_plus, urlencode, parse_qs, parse_qsl, urljoin
)
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
from config import Config
from extensions import db, migrate, bcrypt, login_manager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Talisman for security headers - disable in testing
if not app.config.get('TESTING', False):
    talisman = Talisman(
        app,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
        content_security_policy={
            'default-src': "'self'",
            'img-src': "'self' data:",
            'script-src': "'self'",
            'style-src': "'self' 'unsafe-inline'",
        }
    )

# Initialize rate limiter with appropriate storage
if app.config.get('TESTING'):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["1000 per second"],  # High limits for testing
        storage_uri="memory://"
    )
else:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # In production, use redis or memcached
    )

# Register error handler for rate limit exceeded
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f'Rate limit exceeded for IP: {request.remote_addr}')
    return 'Rate limit exceeded. Please try again later.', 429

# URL path validation
VALID_PATHS = re.compile(r'^[a-zA-Z0-9/_-]*$')

@app.before_request
def validate_request():
    # Block requests to WordPress paths and other common exploit targets
    blocked_paths = [
        'wp-', '.git', 'admin', 'setup', 'install', 'config',
        'phpmy', 'mysql', '.env', '.htaccess', 'composer'
    ]
    
    path = request.path.lstrip('/')
    
    # Check for blocked paths
    if any(blocked in path.lower() for blocked in blocked_paths):
        logger.warning(f"Blocked attempt to access restricted path: {path} from IP: {request.remote_addr}")
        abort(404)
    
    # Validate path format
    if not VALID_PATHS.match(path):
        logger.warning(f"Invalid path format attempted: {path} from IP: {request.remote_addr}")
        abort(404)


# Initialize all extensions with the app

db.init_app(app)

migrate.init_app(app, db)

bcrypt.init_app(app)

login_manager.init_app(app)

# Import models and forms
from models import User, Recipe, RecipeIngredient, Ingredient, Tag, TagType  # noqa: E402
from forms import RegistrationForm, LoginForm, RecipeForm, IngredientForm  # noqa: E402

# Add custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    if not text:
        return ""
    return text.replace('\n', '<br>')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def landing():
    logger.debug('Rendering landing page')
    return render_template('landing.html')

@app.route('/home')
@login_required
def home():
    recipes = Recipe.query.all()
    return render_template('home.html', recipes=recipes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    logger.debug('Login route accessed')
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            logger.warning(f'Failed login attempt for email: {form.email.data}')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        logger.info(f'User logged in: {user.email}')
        return redirect(url_for('home'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        
        # Check if email already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email or login.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f'New user registered: {user.email}')
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f'Error during user registration: {str(e)}')
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))

@app.route('/new_recipe', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        try:
            logger.info(f'Creating new recipe: {form.title.data}')
            
            # Create recipe
            recipe = Recipe(
                title=form.title.data,
                description=form.description.data,
                instructions=form.instructions.data,
                prep_time_minutes=form.prep_time_minutes.data,
                cook_time_minutes=form.cook_time_minutes.data,
                servings=form.servings.data,
                user_id=current_user.id
            )
            db.session.add(recipe)
            db.session.flush()  # Get recipe.id without committing
            
            logger.debug(f'Recipe object created with ID {recipe.id}')

            # Add ingredients
            for ingredient_form in form.ingredients.entries:
                if ingredient_form.ingredient_name.data:  # Only process if ingredient name is provided
                    try:
                        # Get or create ingredient
                        ingredient = Ingredient.query.filter_by(name=ingredient_form.ingredient_name.data).first()
                        if not ingredient:
                            ingredient = Ingredient(name=ingredient_form.ingredient_name.data)
                            db.session.add(ingredient)
                            db.session.flush()  # Get ingredient.id without committing
                            logger.debug(f'Created new ingredient: {ingredient.name}')

                        # Create recipe ingredient relationship
                        recipe_ingredient = RecipeIngredient(
                            recipe_id=recipe.id,
                            ingredient_id=ingredient.id,
                            quantity=float(ingredient_form.ingredient_quantity.data),
                            unit=ingredient_form.ingredient_unit.data
                        )
                        db.session.add(recipe_ingredient)
                        logger.debug(f'Added ingredient {ingredient.name} to recipe {recipe.id}')
                    except ValueError as e:
                        logger.error(f'Error processing ingredient {ingredient_form.ingredient_name.data}: {str(e)}')
                        db.session.rollback()
                        flash('Error processing ingredients. Please check the quantities.', 'error')
                        return render_template('new_recipe.html', title='New Recipe', form=form)

            # Commit all changes
            db.session.commit()
            logger.info(f'Successfully created recipe {recipe.id}: {recipe.title}')
            flash('Your recipe has been created!', 'success')
            return redirect(url_for('recipe', recipe_id=recipe.id))

        except Exception as e:
            logger.error(f'Error creating recipe: {str(e)}')
            db.session.rollback()
            flash('An error occurred while creating your recipe. Please try again.', 'error')
            return render_template('new_recipe.html', title='New Recipe', form=form)

    if form.errors:
        logger.warning(f'Form validation errors: {form.errors}')
        
    return render_template('new_recipe.html', title='New Recipe', form=form)

@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe.html', recipe=recipe)

@app.route('/recipes')
def recipes():
    search_query = request.args.get('q', '')
    if search_query:
        # Search in title, description, and instructions
        search = f"%{search_query}%"
        recipes = Recipe.query.filter(
            (Recipe.title.ilike(search)) |
            (Recipe.description.ilike(search)) |
            (Recipe.instructions.ilike(search))
        ).order_by(Recipe.created_at.desc()).all()
    else:
        # Get the latest 5 recipes if no search query
        recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(5).all()
    
    return render_template('recipes.html', recipes=recipes, search_query=search_query)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        flash('You can only edit your own recipes.', 'danger')
        return redirect(url_for('recipe', recipe_id=recipe_id))
    
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.instructions = form.instructions.data
        recipe.prep_time_minutes = form.prep_time_minutes.data
        recipe.cook_time_minutes = form.cook_time_minutes.data
        recipe.servings = form.servings.data
        
        db.session.commit()
        flash('Recipe has been updated!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe_id))
    
    return render_template('edit_recipe.html', title='Edit Recipe', form=form, recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        flash('You can only delete your own recipes.', 'error')
        return redirect(url_for('recipe', recipe_id=recipe_id))
    
    if request.method == 'GET':
        return render_template('delete_recipe.html', recipe=recipe)
    
    try:
        # Delete related recipe ingredients first
        RecipeIngredient.query.filter_by(recipe_id=recipe_id).delete()
        
        # Delete recipe tags
        recipe.tags = []
        
        # Delete the recipe
        db.session.delete(recipe)
        db.session.commit()
        logger.info(f'Recipe {recipe_id} deleted by user {current_user.id}')
        flash('Recipe has been deleted.', 'success')
    except Exception as e:
        logger.error(f'Error deleting recipe {recipe_id}: {str(e)}')
        db.session.rollback()
        flash('An error occurred while deleting the recipe.', 'error')
    
    return redirect(url_for('recipes'))

@app.cli.command("init-tags")
def init_tags():
    """Initialize tag types and tags."""
    # Create tag types if they don't exist
    meal_type = TagType.query.filter_by(name='meal').first()
    if not meal_type:
        meal_type = TagType(name='meal')
        db.session.add(meal_type)
    
    diet_type = TagType.query.filter_by(name='diet').first()
    if not diet_type:
        diet_type = TagType(name='diet')
        db.session.add(diet_type)


    # Create meal tags if they don't exist
    meal_tags = ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Dessert']
    for tag_name in meal_tags:
        tag = Tag.query.filter_by(name=tag_name, tag_type_id=meal_type.id).first()
        if not tag:
            tag = Tag(name=tag_name, tag_type=meal_type)
            db.session.add(tag)
    

    # Create diet tags if they don't exist
    diet_tags = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Keto', 'Low-Carb']
    for tag_name in diet_tags:
        tag = Tag.query.filter_by(name=tag_name, tag_type_id=diet_type.id).first()
        if not tag:
            tag = Tag(name=tag_name, tag_type=diet_type)
            db.session.add(tag)
    
    db.session.commit()
    print("Tags initialized successfully!")


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # Use configuration for debug mode
    app.run(host='0.0.0.0', port=5001)
