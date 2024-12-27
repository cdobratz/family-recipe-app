from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, IntegerField, SubmitField, FieldList, FormField, DecimalField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class IngredientForm(FlaskForm):
    ingredient_quantity = DecimalField('Quantity', validators=[DataRequired(), NumberRange(min=0)], places=2)
    ingredient_unit = SelectField('Unit', choices=[
        ('cup', 'Cup(s)'),
        ('tbsp', 'Tablespoon(s)'),
        ('tsp', 'Teaspoon(s)'),
        ('oz', 'Ounce(s)'),
        ('lb', 'Pound(s)'),
        ('g', 'Gram(s)'),
        ('ml', 'Milliliter(s)'),
        ('piece', 'Piece(s)'),
        ('pinch', 'Pinch'),
        ('whole', 'Whole')
    ])
    ingredient_name = StringField('Ingredient', validators=[DataRequired(), Length(max=100)])

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    prep_time_minutes = IntegerField('Preparation Time (minutes)', validators=[DataRequired()])
    cook_time_minutes = IntegerField('Cooking Time (minutes)', validators=[DataRequired()])
    servings = IntegerField('Number of Servings', validators=[DataRequired()])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    submit = SubmitField('Save Recipe')
