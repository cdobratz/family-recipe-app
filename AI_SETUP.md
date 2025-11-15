# AI Service Integration Guide

This guide provides step-by-step instructions for integrating the AI-powered microservice from the [RecipeApp_AI repository](https://github.com/cdobratz/RecipeApp_AI) into the Family Recipe App.

> **Note:** This application already includes AI client integration code (`ai_client.py`), API routes, and frontend templates. This guide focuses on setting up and deploying the **external AI microservice** that these features connect to.

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

**Existing Integration Components (Already in this repo):**
- ✅ `ai_client.py` - Python client for communicating with AI service
- ✅ `/api/recipes/suggest` - Flask route for recipe suggestions
- ✅ `/api/recipes/parse` - Flask route for recipe parsing
- ✅ `recipe_suggestions.html` - Frontend for AI recipe suggestions
- ✅ `recipe_parsing.html` - Frontend for AI recipe parsing
- ✅ Database caching models - `RecipeSuggestionCache`, `RecipeParsingCache`

**What You Need to Set Up (This Guide):**
- ❌ External RecipeApp_AI microservice
- ❌ OpenRouter API configuration
- ❌ Environment variables for AI service

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

## Step 4: Configure Flask App Environment Variables

Update your Flask app's `.env` file (in `family-recipe-app/`) to connect to the AI service:

```env
# Add these lines to your existing .env
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=your_secure_api_key_here
```

**Note**: The `AI_SERVICE_API_KEY` should match the `API_KEY` you set in the AI agent's `.env` file.

## Step 5: Run the AI Agent Service

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

## Step 6: Test the Integration

With both services running:

### Terminal 1: AI Agent
```bash
cd RecipeApp_AI
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Terminal 2: Flask App
```bash
cd family-recipe-app
source venv/bin/activate
python app.py
```

### Access the AI Features

1. Navigate to `http://localhost:5001` and login
2. Go to **Recipe Suggestions** from the navigation menu
3. Enter ingredients and get AI-generated recipe suggestions
4. Go to **Recipe Parsing** to convert unstructured recipe text into structured data

### Test the AI Service Endpoints Directly

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

## Step 7: Production Deployment

### Deploy AI Agent to DigitalOcean

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

## Understanding the Existing Integration

### The `ai_client.py` Module

The Flask app includes a comprehensive AI client module with:

- **Caching**: Results are cached in the database to reduce API costs
  - Suggestions cached for 24 hours
  - Parsed recipes cached for 7 days
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Handling**: Comprehensive error handling and logging
- **Health Checks**: Verify AI service availability before requests

### Key Functions

```python
# Get recipe suggestions based on ingredients
get_recipe_suggestions(user_id, ingredients, dietary_preferences, excluded_ingredients)

# Parse unstructured recipe text
parse_recipe_text(recipe_text)

# Create recipe from parsed data
create_recipe_from_parsed_data(user_id, parsed_data)

# Check if AI service is available
check_ai_service_health()
```

### API Routes

The Flask app provides these endpoints:

- `POST /api/recipes/suggest` - Get recipe suggestions
- `POST /api/recipes/parse` - Parse recipe text
- `POST /api/recipes/create-from-parsed` - Create recipe from parsed data
- `GET /recipe-suggestions` - Frontend page for suggestions
- `GET /recipe-parsing` - Frontend page for parsing

### Database Models

The app includes caching models:

```python
class RecipeSuggestionCache(db.Model):
    """Cache for AI-generated recipe suggestions."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ingredients_hash = db.Column(db.String(32), index=True)
    suggestions_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecipeParsingCache(db.Model):
    """Cache for AI-parsed recipes."""
    id = db.Column(db.Integer, primary_key=True)
    recipe_text_hash = db.Column(db.String(32), unique=True, index=True)
    parsed_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Troubleshooting

### Common Issues

**1. Connection Refused Error**
- Ensure the AI service is running on port 8000
- Check firewall settings
- Verify `AI_SERVICE_URL` is correct in Flask app's .env

**2. Authentication Failed (401)**
- Verify API keys match between Flask app and AI service
- Check the `X-API-Key` header is being sent correctly
- Both `AI_SERVICE_API_KEY` (Flask) and `API_KEY` (AI service) must match

**3. OpenRouter API Errors**
- Verify your OpenRouter API key is valid
- Check your OpenRouter account has sufficient credits
- Review the AI service logs for detailed error messages

**4. CORS Errors**
- Update `ALLOWED_ORIGINS` in the AI service `.env` file
- Include all domains that will access the API

**5. "AI service is currently unavailable" Message**
- Check if the AI service is running: `curl http://localhost:8000/health`
- Verify the Flask app can reach the AI service URL
- Check logs in both services for connection errors

### Viewing Logs

```bash
# AI Service logs (if running with uvicorn)
# Logs appear in the terminal where you ran uvicorn

# AI Service logs (if running with Docker)
docker compose logs -f

# Flask app logs
# Check your Flask app's logging configuration
```

### Testing AI Service Independently

Before testing through the Flask app, verify the AI service works:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Test suggestions endpoint
curl -X POST http://localhost:8000/api/ai/recipe-suggestions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"ingredients": ["chicken", "rice"], "dietary_restrictions": [], "excluded_ingredients": []}'

# 3. Check the interactive docs
# Open http://localhost:8000/docs in your browser
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
   - Add `.env` to `.gitignore`
   - Use different keys for development and production

2. **HTTPS**: Use HTTPS in production for all API communication
   - Set up SSL certificates for both services
   - Update URLs to use `https://`

3. **Rate Limiting**: The Flask app includes rate limiting on AI endpoints
   - 5 requests per minute, 20 per hour, 50 per day for suggestions
   - 3 requests per minute, 10 per hour, 20 per day for parsing

4. **Input Validation**: Both services validate all inputs
   - Ingredient lists must be non-empty arrays
   - Recipe text must be at least 10 characters

5. **Environment Files**: Protect your .env files
   ```bash
   # Set proper permissions
   chmod 600 .env
   ```

## Cost Management

OpenRouter charges based on usage. To manage costs:

1. **Monitor Usage**: Check your OpenRouter dashboard regularly
2. **Set Billing Alerts**: Configure alerts in your OpenRouter account
3. **Use Caching**: The app caches results to minimize API calls
4. **Choose Cost-Effective Models**:
   - Claude 3 Haiku: Fastest, cheapest for simple tasks
   - Claude 3.5 Sonnet: Balanced quality and cost (recommended)
   - GPT-4 Turbo: Most capable but more expensive

5. **Review Cache Settings**: Adjust cache TTL in `ai_client.py`:
   ```python
   SUGGESTION_CACHE_TTL = timedelta(hours=24)  # Suggestions cache
   PARSING_CACHE_TTL = timedelta(days=7)       # Parsing cache
   ```

## Performance Optimization

### Caching Strategy

The app implements multi-level caching:

1. **Database Cache**: Stores AI responses in SQLite
2. **Hash-based Lookup**: Uses MD5 hashes for fast cache lookups
3. **Automatic Expiration**: Old cache entries are automatically ignored

### Retry Logic

The AI client includes smart retry logic:
- Retries connection errors and timeouts
- Exponential backoff (1s, 2s, 4s, 8s)
- Maximum 3 retry attempts
- Only retries transient errors

### Request Timeout

Default timeout is 10 seconds. Adjust in `ai_client.py` if needed:
```python
REQUEST_TIMEOUT = 10  # seconds
```

## Next Steps

1. **Test All Features**: Try both recipe suggestions and parsing
2. **Monitor Costs**: Keep an eye on OpenRouter usage
3. **Customize Models**: Experiment with different AI models
4. **Enhance Caching**: Adjust cache TTL based on your usage patterns
5. **Deploy to Production**: Follow the production deployment steps
6. **Add Analytics**: Track which AI features are most used

## Additional Resources

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
5. Check both services are running and can communicate

---

*Document created: 2025-11-15*
*This guide covers the setup of the external AI microservice. The Flask app integration code is already implemented.*
