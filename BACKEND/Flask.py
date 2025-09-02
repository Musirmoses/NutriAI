from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
import os
import json
from typing import List, Dict, Any

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/nutriai_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    dietary_preferences = db.Column(db.Text)
    location = db.Column(db.String(100))
    
    # Relationships
    recipes = db.relationship('SavedRecipe', backref='user', lazy=True)
    analytics = db.relationship('UserAnalytics', backref='user', lazy=True)

class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)  # JSON string of ingredients
    instructions = db.Column(db.Text)
    nutrition_benefits = db.Column(db.Text)
    servings = db.Column(db.Integer)
    prep_time = db.Column(db.String(50))
    dietary_tags = db.Column(db.Text)  # JSON string of dietary tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    popularity_score = db.Column(db.Float, default=0.0)

class SavedRecipe(db.Model):
    __tablename__ = 'saved_recipes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.String(50), db.ForeignKey('recipes.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipe = db.relationship('Recipe', backref='saved_by_users')

class UserAnalytics(db.Model):
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Text)  # JSON string of additional data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def generate_recipe_id():
    import time
    import random
    return f"recipe_{int(time.time())}_{random.randint(1000, 9999)}"

def get_or_create_user(user_id: str) -> User:
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)
        db.session.commit()
    else:
        user.last_active = datetime.utcnow()
        db.session.commit()
    return user

def call_openai_api(ingredients: List[str], dietary_needs: str = None) -> List[Dict]:
    """
    Call OpenAI API to generate recipe recommendations
    """
    try:
        # Construct prompt for OpenAI
        prompt = f"""
        Generate 3 healthy, simple recipes using these available ingredients: {', '.join(ingredients)}.
        
        Requirements:
        - Use only the provided ingredients plus basic seasonings (salt, oil, water)
        - Focus on nutritious, affordable meals for communities with limited resources
        - Include preparation instructions that are easy to follow
        - Provide nutrition benefits for each recipe
        {"- Make recipes suitable for " + dietary_needs if dietary_needs else ""}
        
        Return as JSON array with this structure:
        {{
            "name": "Recipe Name",
            "description": "Brief description",
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": "Step by step instructions",
            "nutrition_benefits": "Health benefits explanation",
            "servings": 4,
            "prep_time": "30 minutes"
        }}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a nutrition expert helping communities with limited resources create healthy, affordable meals."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        # Parse the response
        content = response.choices[0].message.content
        recipes = json.loads(content)
        
        # Add IDs and process
        for recipe in recipes:
            recipe['id'] = generate_recipe_id()
            recipe['usedIngredients'] = recipe.get('ingredients', ingredients)
        
        return recipes
        
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # Fallback to local generation
        return generate_fallback_recipes(ingredients, dietary_needs)

def generate_fallback_recipes(ingredients: List[str], dietary_needs: str = None) -> List[Dict]:
    """
    Fallback recipe generation when OpenAI API is unavailable
    """
    templates = [
        {
            "name": "Nutritious Protein Stew",
            "description": "A hearty, protein-rich stew perfect for building strength.",
            "instructions": "1. Heat oil and sauté onions. 2. Add protein and brown. 3. Add vegetables and water. 4. Simmer 30-45 minutes. 5. Season and serve.",
            "nutrition_benefits": "High in protein and vitamins for immune support.",
            "servings": 4,
            "prep_time": "45 minutes"
        },
        {
            "name": "Simple Grain Bowl",
            "description": "Complete protein combination that's filling and nutritious.",
            "instructions": "1. Cook grains in salted water. 2. Cook legumes separately. 3. Combine and add oil. 4. Serve with vegetables.",
            "nutrition_benefits": "Complete amino acids and high fiber content.",
            "servings": 3,
            "prep_time": "30 minutes"
        },
        {
            "name": "Fresh Vegetable Mix",
            "description": "Light, nutrient-dense meal perfect for any time.",
            "instructions": "1. Wash and chop vegetables. 2. Mix with available proteins. 3. Add lemon and oil. 4. Let marinate and serve.",
            "nutrition_benefits": "Rich in vitamins and antioxidants.",
            "servings": 2,
            "prep_time": "15 minutes"
        }
    ]
    
    recipes = []
    for i, template in enumerate(templates):
        recipe = template.copy()
        recipe['id'] = generate_recipe_id()
        recipe['usedIngredients'] = ingredients[:3] + ['salt', 'oil', 'water']
        
        # Modify based on dietary needs
        if dietary_needs == 'children':
            recipe['nutrition_benefits'] += " Specially formulated for growing children."
            recipe['instructions'] += " Cut into child-friendly pieces."
        
        recipes.append(recipe)
    
    return recipes

# API Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recipes/generate', methods=['POST'])
def generate_recipes():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        dietary_needs = data.get('dietary_needs', '')
        user_id = data.get('user_id')
        
        if not ingredients:
            return jsonify({'success': False, 'error': 'No ingredients provided'}), 400
        
        # Get or create user
        user = get_or_create_user(user_id)
        
        # Generate recipes using OpenAI or fallback
        recipes = call_openai_api(ingredients, dietary_needs)
        
        # Save recipes to database
        for recipe_data in recipes:
            recipe = Recipe(
                id=recipe_data['id'],
                name=recipe_data['name'],
                description=recipe_data['description'],
                ingredients=json.dumps(recipe_data.get('usedIngredients', ingredients)),
                instructions=recipe_data['instructions'],
                nutrition_benefits=recipe_data['nutrition_benefits'],
                servings=recipe_data.get('servings', 4),
                prep_time=recipe_data.get('prep_time', '30 minutes'),
                dietary_tags=json.dumps([dietary_needs] if dietary_needs else [])
            )
            
            # Check if recipe already exists
            existing = Recipe.query.get(recipe.id)
            if not existing:
                db.session.add(recipe)
        
        db.session.commit()
        
        # Track analytics
        track_user_action(user_id, 'recipes_generated', {
            'ingredients_count': len(ingredients),
            'dietary_needs': dietary_needs,
            'recipes_count': len(recipes)
        })
        
        return jsonify({
            'success': True,
            'recipes': recipes,
            'message': f'Generated {len(recipes)} recipes successfully'
        })
        
    except Exception as e:
        print(f"Error generating recipes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recipes/save', methods=['POST'])
def save_user_recipe():
    try:
        data = request.get_json()
        recipe_data = data.get('recipe')
        user_id = data.get('user_id')
        
        if not recipe_data or not user_id:
            return jsonify({'success': False, 'error': 'Missing recipe or user data'}), 400
        
        # Get or create user
        user = get_or_create_user(user_id)
        
        # Check if already saved
        existing = SavedRecipe.query.filter_by(
            user_id=user_id, 
            recipe_id=recipe_data['id']
        ).first()
        
        if not existing:
            saved_recipe = SavedRecipe(
                user_id=user_id,
                recipe_id=recipe_data['id']
            )
            db.session.add(saved_recipe)
            db.session.commit()
            
            # Track analytics
            track_user_action(user_id, 'recipe_saved', {'recipe_id': recipe_data['id']})
        
        return jsonify({'success': True, 'message': 'Recipe saved successfully'})
        
    except Exception as e:
        print(f"Error saving recipe: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recipes/user/<user_id>', methods=['GET'])
def get_user_recipes(user_id):
    try:
        # Get user's saved recipes
        saved_recipes = db.session.query(SavedRecipe, Recipe).join(
            Recipe, SavedRecipe.recipe_id == Recipe.id
        ).filter(SavedRecipe.user_id == user_id).all()
        
        recipes = []
        for saved_recipe, recipe in saved_recipes:
            recipe_dict = {
                'id': recipe.id,
                'name': recipe.name,
                'description': recipe.description,
                'ingredients': json.loads(recipe.ingredients),
                'instructions': recipe.instructions,
                'nutrition_benefits': recipe.nutrition_benefits,
                'servings': recipe.servings,
                'prep_time': recipe.prep_time,
                'saved_at': saved_recipe.saved_at.isoformat()
            }
            recipes.append(recipe_dict)
        
        return jsonify({'success': True, 'recipes': recipes})
        
    except Exception as e:
        print(f"Error fetching user recipes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/track', methods=['POST'])
def track_analytics():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        action = data.get('action')
        event_data = data.get('data', {})
        
        if not user_id or not action:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        track_user_action(user_id, action, event_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error tracking analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health/tips', methods=['GET'])
def get_health_tips():
    try:
        tips = [
            {
                "category": "nutrition",
                "tip": "Eat a variety of colorful vegetables daily for different vitamins and minerals.",
                "importance": "high"
            },
            {
                "category": "hydration",
                "tip": "Drink clean water regularly - aim for 6-8 glasses per day.",
                "importance": "critical"
            },
            {
                "category": "protein",
                "tip": "Include protein in every meal to support growth and healing.",
                "importance": "high"
            },
            {
                "category": "grains",
                "tip": "Choose whole grains over refined grains when possible.",
                "importance": "medium"
            },
            {
                "category": "calcium",
                "tip": "Include calcium-rich foods for bone health.",
                "importance": "high"
            }
        ]
        
        return jsonify({'success': True, 'tips': tips})
        
    except Exception as e:
        print(f"Error fetching health tips: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ingredients/suggest', methods=['GET'])
def suggest_ingredients():
    """Suggest common local ingredients"""
    try:
        common_ingredients = {
            "proteins": ["chicken", "fish", "beans", "lentils", "eggs", "groundnuts"],
            "vegetables": ["tomatoes", "kale", "cabbage", "carrots", "onions", "spinach"],
            "grains": ["rice", "maize", "millet", "sorghum", "wheat"],
            "fruits": ["bananas", "oranges", "mangoes", "avocados"],
            "staples": ["oil", "salt", "garlic", "ginger"]
        }
        
        return jsonify({'success': True, 'ingredients': common_ingredients})
        
    except Exception as e:
        print(f"Error fetching ingredient suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/nutrition/analyze', methods=['POST'])
def analyze_nutrition():
    """Analyze nutritional content of selected ingredients"""
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        
        # Simple nutrition analysis (can be enhanced with nutrition API)
        nutrition_analysis = {
            "total_ingredients": len(ingredients),
            "protein_sources": len([i for i in ingredients if i in ['chicken', 'fish', 'beans', 'lentils', 'eggs']]),
            "vegetable_count": len([i for i in ingredients if i in ['tomatoes', 'kale', 'cabbage', 'carrots', 'spinach']]),
            "grain_sources": len([i for i in ingredients if i in ['rice', 'maize', 'wheat', 'millet']]),
            "nutritional_score": 0
        }
        
        # Calculate basic nutritional score
        score = 0
        if nutrition_analysis["protein_sources"] > 0:
            score += 30
        if nutrition_analysis["vegetable_count"] >= 2:
            score += 40
        if nutrition_analysis["grain_sources"] > 0:
            score += 20
        if len(ingredients) >= 5:
            score += 10
            
        nutrition_analysis["nutritional_score"] = score
        
        # Provide recommendations
        recommendations = []
        if nutrition_analysis["protein_sources"] == 0:
            recommendations.append("Add a protein source like beans, lentils, or eggs")
        if nutrition_analysis["vegetable_count"] < 2:
            recommendations.append("Include more vegetables for vitamins and minerals")
        if nutrition_analysis["grain_sources"] == 0:
            recommendations.append("Add a grain like rice or maize for energy")
            
        nutrition_analysis["recommendations"] = recommendations
        
        return jsonify({'success': True, 'analysis': nutrition_analysis})
        
    except Exception as e:
        print(f"Error analyzing nutrition: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Utility Functions
def track_user_action(user_id: str, action: str, data: Dict[str, Any] = None):
    """Track user actions for analytics"""
    try:
        analytics = UserAnalytics(
            user_id=user_id,
            action=action,
            data=json.dumps(data) if data else None
        )
        db.session.add(analytics)
        db.session.commit()
    except Exception as e:
        print(f"Analytics tracking error: {e}")

# Admin Routes (for hackathon demo)
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get usage statistics for demonstration"""
    try:
        stats = {
            "total_users": User.query.count(),
            "total_recipes": Recipe.query.count(),
            "recipes_generated_today": UserAnalytics.query.filter(
                UserAnalytics.action == 'recipes_generated',
                UserAnalytics.timestamp >= datetime.utcnow().date()
            ).count(),
            "most_popular_ingredients": get_popular_ingredients(),
            "user_engagement": calculate_user_engagement()
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        print(f"Error fetching admin stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_popular_ingredients():
    """Get most commonly used ingredients"""
    # This would analyze saved recipes to find popular ingredients
    # For demo purposes, return sample data
    return [
        {"ingredient": "rice", "usage_count": 45},
        {"ingredient": "beans", "usage_count": 38},
        {"ingredient": "tomatoes", "usage_count": 35},
        {"ingredient": "onions", "usage_count": 32},
        {"ingredient": "kale", "usage_count": 28}
    ]

def calculate_user_engagement():
    """Calculate user engagement metrics"""
    total_users = User.query.count()
    active_users = User.query.filter(
        User.last_active >= datetime.utcnow().date()
    ).count()
    
    return {
        "total_users": total_users,
        "active_today": active_users,
        "engagement_rate": (active_users / total_users * 100) if total_users > 0 else 0
    }

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Database initialization
@app.before_first_request
def create_tables():
    """Create database tables"""
    db.create_all()
    print("Database tables created successfully!")

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)