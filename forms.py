from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField, IntegerField,
    SubmitField, FieldList, FormField, DecimalField, SelectField, SelectMultipleField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
from models import User, Tag, TagType

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
    prep_time_minutes = IntegerField('Preparation Time (minutes)', validators=[DataRequired(), NumberRange(min=0)])
    cook_time_minutes = IntegerField('Cooking Time (minutes)', validators=[NumberRange(min=0)])
    servings = IntegerField('Number of Servings', validators=[DataRequired(), NumberRange(min=1)])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    meal_tags = SelectMultipleField('Meal Type', coerce=int)
    diet_tags = SelectMultipleField('Diet Type', coerce=int)
    submit = SubmitField('Save Recipe')

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)
        # Populate the tag choices
        meal_tags = Tag.query.join(TagType).filter(TagType.name == 'meal').all()
        diet_tags = Tag.query.join(TagType).filter(TagType.name == 'diet').all()
        self.meal_tags.choices = [(tag.id, tag.name) for tag in meal_tags]
        self.diet_tags.choices = [(tag.id, tag.name) for tag in diet_tags]
