# Adding AI Agent Integration to Family Recipe App

This guide provides step-by-step instructions for integrating the AI-powered microservice from the [RecipeApp_AI repository](https://github.com/cdobratz/RecipeApp_AI) into the Family Recipe App.

## What is the AI Agent?

The AI Agent is a FastAPI-based microservice that enhances the recipe app with intelligent features:
- **Recipe Suggestions**: Generate recipe ideas based on available ingredients and dietary preferences
- **Recipe Parsing**: Convert unstructured recipe text into structured JSON format with ingredients, instructions, and timing

The service runs independently from the main Flask application and communicates via HTTP API calls.

## Architecture Overview

```
Family Recipe App (Flask) <--HTTP--> AI Agent Service (FastAPI) <--API--> OpenRouter (AI Models)
       Port 5001                            Port 8000
```

## Prerequisites

Before starting, ensure you have:

1. **Python 3.11+** installed
2. **Git** installed
3. **OpenRouter API Key** - Sign up at [OpenRouter](https://openrouter.ai/) to get your API key
4. **Docker & Docker Compose** (optional, for containerized deployment)

## Step 1: Clone the AI Agent Repository

Navigate to your project directory and clone the AI agent repository alongside your main app:

```bash
# If you're in the family-recipe-app directory, go up one level
cd ..

# Clone the AI agent repository
git clone https://github.com/cdobratz/RecipeApp_AI.git

# Your directory structure should now look like:
# ├── family-recipe-app/
# └── RecipeApp_AI/
```

## Step 2: Set Up the AI Agent Environment

### Create Virtual Environment

```bash
cd RecipeApp_AI

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

The key dependencies include:
- FastAPI & Uvicorn (web framework and server)
- OpenAI client library (for OpenRouter API)
- Pydantic (data validation)
- python-dotenv (environment configuration)

## Step 3: Configure Environment Variables

Create a `.env` file in the `RecipeApp_AI` directory:

```bash
# Create .env file
touch .env
```

Add the following configuration to `.env`:

```env
# Required: OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_SITE_URL=http://localhost:5001
OPENROUTER_APP_NAME=FamilyRecipeApp

# Required: API Security
API_KEY=your_secure_api_key_here

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:5001,http://127.0.0.1:5001

# Optional: Logging
LOG_LEVEL=INFO
```

**Important Configuration Notes:**

1. **OPENROUTER_API_KEY**: Get this from your OpenRouter account dashboard
2. **OPENROUTER_MODEL**: Recommended models:
   - `anthropic/claude-3.5-sonnet` (high quality, balanced cost)
   - `anthropic/claude-3-haiku` (faster, lower cost)
   - `openai/gpt-4-turbo` (alternative option)
3. **API_KEY**: Generate a secure random string for authentication:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. **ALLOWED_ORIGINS**: Update with your production domain when deploying

## Step 4: Run the AI Agent Locally

### Option A: Run with Uvicorn (Development)

```bash
# Make sure you're in the RecipeApp_AI directory with venv activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will start on `http://localhost:8000`

### Option B: Run with Docker Compose (Production-like)

```bash
# Build and start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

### Verify the Service is Running

Open your browser or use curl to test the health endpoint:

```bash
curl http://localhost:8000/health
```

You should see a response like:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-15T12:00:00.000000"
}
```

View interactive API documentation at: `http://localhost:8000/docs`

## Step 5: Integrate with the Flask Application

### Add AI Client Helper Module

Create a new file `ai_client.py` in your Flask app directory (`family-recipe-app/`):

```python
import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AIServiceClient:
    """Client for communicating with the AI microservice."""

    def __init__(self):
        self.base_url = os.getenv('AI_SERVICE_URL', 'http://localhost:8000')
        self.api_key = os.getenv('AI_SERVICE_API_KEY', '')
        self.timeout = 30  # seconds

    def _make_request(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make a POST request to the AI service."""
        try:
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Service request failed: {e}")
            return None

    def get_recipe_suggestions(
        self,
        ingredients: List[str],
        dietary_restrictions: Optional[List[str]] = None,
        excluded_ingredients: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """Get AI-generated recipe suggestions based on ingredients."""
        data = {
            'ingredients': ingredients,
            'dietary_restrictions': dietary_restrictions or [],
            'excluded_ingredients': excluded_ingredients or []
        }
        result = self._make_request('/api/ai/recipe-suggestions', data)
        return result.get('suggestions') if result else None

    def parse_recipe_text(self, recipe_text: str) -> Optional[Dict]:
        """Parse unstructured recipe text into structured data."""
        data = {'recipe_text': recipe_text}
        result = self._make_request('/api/ai/recipe-parsing', data)
        return result.get('parsed_recipe') if result else None

# Create a singleton instance
ai_client = AIServiceClient()
```

### Update Flask App Configuration

Add to `config.py`:

```python
# AI Service Configuration
AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://localhost:8000')
AI_SERVICE_API_KEY = os.environ.get('AI_SERVICE_API_KEY', '')
```

Update your Flask app's `.env` file (or create one in `family-recipe-app/`):

```env
# Add these lines to your existing .env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=your_secure_api_key_here
```

**Note**: The `AI_SERVICE_API_KEY` should match the `API_KEY` you set in the AI agent's `.env` file.

### Add AI-Powered Routes to Flask App

Add these routes to `app.py`:

```python
from ai_client import ai_client

@app.route('/ai/suggest-recipes', methods=['POST'])
@login_required
def ai_suggest_recipes():
    """Get AI recipe suggestions based on ingredients."""
    data = request.get_json()
    ingredients = data.get('ingredients', [])
    dietary_restrictions = data.get('dietary_restrictions', [])

    suggestions = ai_client.get_recipe_suggestions(
        ingredients=ingredients,
        dietary_restrictions=dietary_restrictions
    )

    if suggestions:
        return {'success': True, 'suggestions': suggestions}
    else:
        return {'success': False, 'error': 'AI service unavailable'}, 503

@app.route('/ai/parse-recipe', methods=['POST'])
@login_required
def ai_parse_recipe():
    """Parse recipe text using AI."""
    data = request.get_json()
    recipe_text = data.get('recipe_text', '')

    parsed = ai_client.parse_recipe_text(recipe_text)

    if parsed:
        return {'success': True, 'parsed_recipe': parsed}
    else:
        return {'success': False, 'error': 'AI service unavailable'}, 503
```

### Add Requests Library Dependency

Update `requirements.txt` in the Flask app:

```bash
# Add this line if not already present
requests>=2.31.0
```

Then install:
```bash
pip install requests
```

## Step 6: Create Frontend Integration (Optional)

### Example: Recipe Suggestion Form

Create a new template `templates/ai_suggestions.html`:

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <h2>AI Recipe Suggestions</h2>
    <form id="suggestionForm">
        <div class="mb-3">
            <label class="form-label">Available Ingredients (one per line)</label>
            <textarea class="form-control" id="ingredients" rows="5"
                      placeholder="chicken breast&#10;garlic&#10;olive oil&#10;tomatoes"></textarea>
        </div>
        <div class="mb-3">
            <label class="form-label">Dietary Restrictions (optional)</label>
            <input type="text" class="form-control" id="dietary"
                   placeholder="e.g., vegetarian, gluten-free">
        </div>
        <button type="submit" class="btn btn-primary">Get Suggestions</button>
    </form>

    <div id="results" class="mt-4"></div>
</div>

<script>
document.getElementById('suggestionForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const ingredients = document.getElementById('ingredients').value
        .split('\n')
        .filter(i => i.trim());
    const dietary = document.getElementById('dietary').value
        .split(',')
        .map(d => d.trim())
        .filter(d => d);

    const response = await fetch('/ai/suggest-recipes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            ingredients: ingredients,
            dietary_restrictions: dietary
        })
    });

    const data = await response.json();

    if (data.success) {
        displayResults(data.suggestions);
    } else {
        alert('Error: ' + data.error);
    }
});

function displayResults(suggestions) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h3>Suggested Recipes</h3>';

    suggestions.forEach(recipe => {
        resultsDiv.innerHTML += `
            <div class="card mb-3">
                <div class="card-body">
                    <h5>${recipe.title}</h5>
                    <p>${recipe.description}</p>
                    <p><strong>Time:</strong> ${recipe.prep_time + recipe.cook_time} minutes</p>
                </div>
            </div>
        `;
    });
}
</script>
{% endblock %}
```

Add a route in `app.py`:

```python
@app.route('/ai-suggestions')
@login_required
def ai_suggestions_page():
    return render_template('ai_suggestions.html')
```

## Step 7: Testing the Integration

### Test the AI Service Endpoints

```bash
# Test recipe suggestions
curl -X POST http://localhost:8000/api/ai/recipe-suggestions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "ingredients": ["chicken", "garlic", "olive oil"],
    "dietary_restrictions": ["gluten-free"],
    "excluded_ingredients": []
  }'

# Test recipe parsing
curl -X POST http://localhost:8000/api/ai/recipe-parsing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "recipe_text": "Mix 2 cups flour with 1 cup water. Bake at 350F for 30 minutes."
  }'
```

### Test the Flask Integration

1. Start both services:
   ```bash
   # Terminal 1: AI Agent
   cd RecipeApp_AI
   source venv/bin/activate
   uvicorn main:app --reload --port 8000

   # Terminal 2: Flask App
   cd family-recipe-app
   source venv/bin/activate
   python app.py
   ```

2. Test via Flask routes (use the interactive docs or your frontend)

## Step 8: Production Deployment

### Deploy AI Agent to DigitalOcean (Recommended)

The RecipeApp_AI repository includes a deployment script for DigitalOcean:

```bash
# Set your droplet IP
export DROPLET_IP=your.droplet.ip.address

# Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

Or use DigitalOcean App Platform:
1. Connect your GitHub repository
2. Set environment variables in the App Platform dashboard
3. Deploy directly from git

### Update Flask App Configuration for Production

Update your production environment variables:

```env
AI_SERVICE_URL=https://your-ai-service-domain.com
AI_SERVICE_API_KEY=your_production_api_key
```

## Troubleshooting

### Common Issues

**1. Connection Refused Error**
- Ensure the AI service is running on port 8000
- Check firewall settings
- Verify `AI_SERVICE_URL` is correct

**2. Authentication Failed (401)**
- Verify API keys match between Flask app and AI service
- Check the `X-API-Key` header is being sent correctly

**3. OpenRouter API Errors**
- Verify your OpenRouter API key is valid
- Check your OpenRouter account has sufficient credits
- Review the AI service logs for detailed error messages

**4. CORS Errors**
- Update `ALLOWED_ORIGINS` in the AI service `.env` file
- Include all domains that will access the API

### Viewing Logs

```bash
# AI Service logs (if running with uvicorn)
# Logs appear in the terminal

# AI Service logs (if running with Docker)
docker compose logs -f

# Flask app logs
# Check your Flask app's logging configuration
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **HTTPS**: Use HTTPS in production for all API communication
3. **Rate Limiting**: Consider adding rate limiting to AI endpoints
4. **Input Validation**: Validate all user inputs before sending to AI service
5. **Environment Files**: Add `.env` to `.gitignore`

## Cost Management

OpenRouter charges based on usage:
- Monitor your usage on the OpenRouter dashboard
- Set up billing alerts
- Consider caching frequent requests
- Choose cost-effective models (e.g., Claude 3 Haiku for simple tasks)

## Next Steps

1. **Enhance UI**: Add more polished frontend components for AI features
2. **Caching**: Implement caching for common ingredient combinations
3. **Background Jobs**: Use Celery for long-running AI requests
4. **Analytics**: Track which AI features are most used
5. **Error Handling**: Add more robust error handling and user feedback

## Resources

- [RecipeApp_AI GitHub Repository](https://github.com/cdobratz/RecipeApp_AI)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Support

If you encounter issues:
1. Check the AI service logs for errors
2. Verify all environment variables are set correctly
3. Test the AI service endpoints independently before integrating
4. Review the OpenRouter dashboard for API usage and errors
