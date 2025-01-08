from flask import Flask, render_template, url_for, flash, redirect, request
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from config import Config
import logging
from urllib.parse import (
    urlparse, urlunparse, urlsplit, urlunsplit, quote, quote_plus,
    unquote, unquote_plus, urlencode, parse_qs, parse_qsl, urljoin
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'

# Initialize all extensions with the app
db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
login_manager.init_app(app)

# Import models after db initialization to avoid circular imports
from models import User, Recipe, RecipeIngredient, Ingredient, Tag, TagType
from forms import RegistrationForm, LoginForm, RecipeForm, IngredientForm

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
def login():
    logger.debug('Login route accessed')
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))

@app.route('/new_recipe', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            instructions=form.instructions.data,
            prep_time_minutes=form.prep_time_minutes.data,
            cook_time_minutes=form.cook_time_minutes.data,
            servings=form.servings.data,
            user_id=current_user.user_id
        )
        db.session.add(recipe)
        db.session.commit()

        # Add ingredients
        for ingredient_form in form.ingredients.entries:
            # Get or create ingredient
            ingredient = Ingredient.query.filter_by(name=ingredient_form.ingredient_name.data).first()
            if not ingredient:
                ingredient = Ingredient(name=ingredient_form.ingredient_name.data)
                db.session.add(ingredient)
                db.session.commit()

            # Create recipe ingredient relationship
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.recipe_id,
                ingredient_id=ingredient.ingredient_id,
                quantity=ingredient_form.ingredient_quantity.data,
                unit=ingredient_form.ingredient_unit.data
            )
            db.session.add(recipe_ingredient)

        db.session.commit()
        flash('Your recipe has been created!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe.recipe_id))

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

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        flash('You can only delete your own recipes.', 'danger')
        return redirect(url_for('recipe', recipe_id=recipe_id))
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe has been deleted.', 'success')
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

if __name__ == '__main__':
    # Add debug mode and use port 5001 instead
    app.run(debug=True, host='0.0.0.0', port=5001)
