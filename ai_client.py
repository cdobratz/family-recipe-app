import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

import requests
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from extensions import db
from models import Recipe, RecipeIngredient, Ingredient, Tag, RecipeSuggestionCache, RecipeParsingCache

# Setup logging
logger = logging.getLogger(__name__)

# Configuration
AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://localhost:8000')
AI_SERVICE_API_KEY = os.environ.get('AI_SERVICE_API_KEY')
SUGGESTION_CACHE_TTL = timedelta(hours=24)  # Cache suggestions for 24 hours
PARSING_CACHE_TTL = timedelta(days=7)  # Cache parsed recipes for 7 days
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10  # seconds

# Custom exceptions
class AIServiceError(Exception):
    """Base exception for AI service errors."""
    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class AIServiceConnectionError(AIServiceError):
    """Raised when connection to AI service fails."""
    pass

class AIServiceTimeoutError(AIServiceError):
    """Raised when AI service request times out."""
    pass

class AIServiceResponseError(AIServiceError):
    """Raised when AI service returns an error response."""
    pass

def _calculate_hash(data: Union[List[str], str]) -> str:
    """Calculate a unique hash for data."""
    if isinstance(data, list):
        # Sort list items to ensure consistent hashing
        sorted_items = sorted([str(item) for item in data])
        data_str = ','.join(sorted_items)
    else:
        data_str = str(data)
    
    return hashlib.md5(data_str.encode()).hexdigest()

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
    reraise=True
)
def _make_api_request(
    endpoint: str, 
    data: Dict[str, Any], 
    method: str = 'POST'
) -> Tuple[Dict[str, Any], int]:
    """Make a request to the AI service with retry logic."""
    if not AI_SERVICE_URL or not AI_SERVICE_API_KEY:
        logger.error("AI service not properly configured")
        raise AIServiceError("AI service not properly configured", 500)
    
    url = f"{AI_SERVICE_URL}{endpoint}"
    headers = {
        "X-API-Key": AI_SERVICE_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.get(url, headers=headers, params=data, timeout=REQUEST_TIMEOUT)
            
        if response.status_code == 200:
            return response.json(), 200
        
        # Handle specific error codes
        error_message = f"AI service error: {response.status_code}"
        try:
            error_data = response.json()
            if 'detail' in error_data:
                error_message = f"AI service error: {error_data['detail']}"
        except ValueError:
            pass  # Use default error message if JSON parsing fails
        
        logger.error(f"{error_message} - Response: {response.text}")
        raise AIServiceResponseError(error_message, response.status_code, response.text)
        
    except requests.exceptions.Timeout:
        logger.error("AI service request timed out")
        raise AIServiceTimeoutError("AI service request timed out", 504)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"AI service connection error: {str(e)}")
        raise AIServiceConnectionError(f"Unable to connect to AI service: {str(e)}", 503)
    except Exception as e:
        logger.exception(f"Unexpected error in AI service request: {str(e)}")
        raise AIServiceError(f"An error occurred while processing your request: {str(e)}", 500)

def get_recipe_suggestions(
    user_id: int,
    ingredients: List[str],
    dietary_preferences: Optional[List[str]] = None,
    excluded_ingredients: Optional[List[str]] = None,
    force_refresh: bool = False
) -> Tuple[Dict[str, Any], int]:
    """
    Get recipe suggestions based on user ingredients and preferences.
    Can use cached results if available and not expired.
    
    Args:
        user_id: The ID of the user requesting suggestions
        ingredients: List of ingredient names
        dietary_preferences: Optional list of dietary preferences
        excluded_ingredients: Optional list of ingredients to exclude
        force_refresh: Whether to force a refresh from the AI service
        
    Returns:
        Tuple of (response_data, status_code)
    """
    # Calculate unique hash for this ingredients list and preferences
    ingredients_hash = _calculate_hash(ingredients)
    dietary_preferences_hash = _calculate_hash(dietary_preferences) if dietary_preferences else None
    
    # Check cache if not forcing refresh
    if not force_refresh:
        try:
            cache_query = RecipeSuggestionCache.query.filter_by(
                user_id=user_id,
                ingredients_hash=ingredients_hash
            )
            
            if dietary_preferences_hash:
                cache_query = cache_query.filter_by(dietary_preferences_hash=dietary_preferences_hash)
                
            cache_entry = cache_query.first()
            
            # Return cached result if valid and not expired
            if cache_entry and (datetime.utcnow() - cache_entry.created_at) < SUGGESTION_CACHE_TTL:
                logger.info(f"Using cached recipe suggestions for user {user_id}")
                return cache_entry.suggestions, 200
        except SQLAlchemyError as e:
            logger.error(f"Database error when retrieving cache: {str(e)}")
            # Continue with API request if cache retrieval fails
    
    # Prepare request data
    request_data = {
        "ingredients": ingredients
    }
    
    if dietary_preferences:
        request_data["dietary_preferences"] = dietary_preferences
        
    if excluded_ingredients:
        request_data["excluded_ingredients"] = excluded_ingredients
    
    # Make API request to get suggestions
    try:
        response, status_code = _make_api_request(
            "/api/ai/recipe-suggestions",
            request_data
        )
        
        # If successful, cache the result
        if status_code == 200:
            try:
                # Delete any existing cache entry
                RecipeSuggestionCache.query.filter_by(
                    user_id=user_id,
                    ingredients_hash=ingredients_hash,
                    dietary_preferences_hash=dietary_preferences_hash
                ).delete()
                
                # Create new cache entry
                cache_entry = RecipeSuggestionCache(
                    user_id=user_id,
                    ingredients_hash=ingredients_hash,
                    dietary_preferences_hash=dietary_preferences_hash,
                    suggestions=response
                )
                
                db.session.add(cache_entry)
                db.session.commit()
                logger.info(f"Cached new recipe suggestions for user {user_id}")
                
            except SQLAlchemyError as e:
                logger.error(f"Database error when caching suggestions: {str(e)}")
                db.session.rollback()
        
        return response, status_code
        
    except (AIServiceConnectionError, AIServiceTimeoutError, AIServiceResponseError) as e:
        logger.error(f"AI service error: {str(e)}")
        return {"error": str(e)}, getattr(e, 'status_code', 500)
    except Exception as e:
        logger.exception(f"Unexpected error getting recipe suggestions: {str(e)}")
        return {"error": "An unexpected error occurred"}, 500

def parse_recipe_text(
    recipe_text: str,
    force_refresh: bool = False
) -> Tuple[Dict[str, Any], int]:
    """
    Parse unstructured recipe text using the AI service.
    
    Args:
        recipe_text: The raw recipe text to parse
        force_refresh: Whether to force a refresh from the AI service
        
    Returns:
        Tuple of (response_data, status_code)
    """
    # Calculate hash for recipe text
    recipe_text_hash = _calculate_hash(recipe_text)
    
    # Check cache if not forcing refresh
    if not force_refresh:
        try:
            cache_entry = RecipeParsingCache.query.filter_by(
                recipe_text_hash=recipe_text_hash
            ).first()
            
            # Return cached result if valid and not expired
            if cache_entry and (datetime.utcnow() - cache_entry.created_at) < PARSING_CACHE_TTL:
                logger.info(f"Using cached recipe parsing result")
                return cache_entry.parsed_recipe, 200
        except SQLAlchemyError as e:
            logger.error(f"Database error when retrieving parsing cache: {str(e)}")
            # Continue with API request if cache retrieval fails
    
    # Make API request to parse recipe
    try:
        response, status_code = _make_api_request(
            "/api/ai/recipe-parsing",
            {"recipe_text": recipe_text}
        )
        
        # If successful, cache the result
        if status_code == 200:
            try:
                # Delete any existing cache entry
                RecipeParsingCache.query.filter_by(
                    recipe_text_hash=recipe_text_hash
                ).delete()
                
                # Create new cache entry
                cache_entry = RecipeParsingCache(
                    recipe_text_hash=recipe_text_hash,
                    parsed_recipe=response
                )
                
                db.session.add(cache_entry)
                db.session.commit()
                logger.info(f"Cached new recipe parsing result")
                
            except SQLAlchemyError as e:
                logger.error(f"Database error when caching parsed recipe: {str(e)}")
                db.session.rollback()
        
        return response, status_code
        
    except (AIServiceConnectionError, AIServiceTimeoutError, AIServiceResponseError) as e:
        logger.error(f"AI service error during recipe parsing: {str(e)}")
        return {"error": str(e)}, getattr(e, 'status_code', 500)
    except Exception as e:
        logger.exception(f"Unexpected error parsing recipe: {str(e)}")
        return {"error": "An unexpected error occurred"}, 500

def create_recipe_from_parsed_data(
    user_id: int,
    parsed_recipe: Dict[str, Any]
) -> Tuple[Optional[Recipe], str]:
    """
    Create a new Recipe object from parsed recipe data.
    
    Args:
        user_id: The ID of the user creating the recipe
        parsed_recipe: The parsed recipe data from the AI service
        
    Returns:
        Tuple of (created_recipe, message)
    """
    try:
        # Extract data from parsed recipe
        recipe_data = parsed_recipe.get("parsed_recipe", {})
        if not recipe_data:
            return None, "Invalid parsed recipe data"
        
        # Create new recipe
        recipe = Recipe(
            user_id=user_id,
            title=recipe_data.get("title", "Untitled Recipe"),
            description=recipe_data.get("description", ""),
            instructions="\n".join(recipe_data.get("instructions", [])),
            prep_time_minutes=recipe_data.get("preparation_time_minutes"),
            cook_time_minutes=recipe_data.get("cooking_time_minutes"),
            servings=recipe_data.get("servings")
        )
        
        db.session.add(recipe)
        db.session.flush()  # Get recipe ID without committing
        
        # Add ingredients
        for ing_data in recipe_data.get("ingredients", []):
            # Get or create ingredient
            ingredient_name = ing_data.get("name", "").strip()
            if not ingredient_name:
                continue
                
            ingredient = Ingredient.query.filter(Ingredient.name.ilike(ingredient_name)).first()
            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                db.session.add(ingredient)
                db.session.flush()
            
            # Create recipe ingredient relationship
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=float(ing_data.get("quantity", 1)),
                unit=ing_data.get("unit", "")
            )
            db.session.add(recipe_ingredient)
        
        db.session.commit()
        return recipe, "Recipe created successfully"
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating recipe from parsed data: {str(e)}")
        return None, f"Database error: {str(e)}"
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error creating recipe from parsed data: {str(e)}")
        return None, f"Error: {str(e)}"

def check_ai_service_health() -> bool:
    """
    Check if the AI service is healthy.
    
    Returns:
        Boolean indicating if the service is healthy
    """
    try:
        response = requests.get(
            f"{AI_SERVICE_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

