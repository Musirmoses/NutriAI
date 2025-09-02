#!/usr/bin/env python3
"""
NutriAI Live Demo Script
Perfect for hackathon presentations - demonstrates all features step by step
"""

import time
import requests
import json
from app import app, db, User, Recipe, SavedRecipe, UserAnalytics

class DemoRunner:
    def __init__(self):
        self.base_url = 'http://localhost:5000/api'
        self.demo_user_id = 'hackathon_demo_user'
        
    def print_demo_step(self, step, description):
        print(f"\n🎭 DEMO STEP {step}: {description}")
        print("-" * 60)
        
    def wait_for_effect(self, seconds=2):
        """Add dramatic pause for demo effect"""
        time.sleep(seconds)
        
    def demo_step_1_environment(self):
        """Demonstrate environment setup"""
        self.print_demo_step(1, "Environment & Configuration")
        
        print("📋 Checking environment variables...")
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        checks = {
            'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
            'SECRET_KEY': bool(os.getenv('SECRET_KEY')),
            'DATABASE_URL': bool(os.getenv('DEV_DATABASE_URL'))
        }
        
        for key, status in checks.items():
            print(f"  {key}: {'✅ Configured' if status else '❌ Missing'}")
        
        self.wait_for_effect()
        
    def demo_step_2_database(self):
        """Demonstrate database connectivity"""
        self.print_demo_step(2, "Database Connection & Models")
        
        with app.app_context():
            try:
                # Test database connection
                db.create_all()
                print("✅ Database tables created/verified")
                
                # Show table counts
                user_count = User.query.count()
                recipe_count = Recipe.query.count()
                
                print(f"📊 Current data: {user_count} users, {recipe_count} recipes")
                
                # Create demo user if not exists
                demo_user = User.query.get(self.demo_user_id)
                if not demo_user:
                    demo_user = User(id=self.demo_user_id, location='Nairobi, Kenya')
                    db.session.add(demo_user)
                    db.session.commit()
                    print(f"👤 Demo user created: {self.demo_user_id}")
                
            except Exception as e:
                print(f"❌ Database error: {e}")
        
        self.wait_for_effect()
        
    def demo_step_3_api_endpoints(self):
        """Demonstrate API endpoints"""
        self.print_demo_step(3, "API Endpoints Testing")
        
        endpoints = [
            ('GET', '/health', None),
            ('GET', '/ingredients/suggest', None),
            ('POST', '/recipes/generate', {
                'ingredients': ['chicken', 'tomatoes', 'kale'],
                'dietary_needs': 'children',
                'user_id': self.demo_user_id
            })
        ]
        
        for method, endpoint, data in endpoints:
            try:
                print(f"🔗 Testing {method} {endpoint}")
                
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}")
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ Status: {response.status_code}")
                    if 'recipes' in result:
                        print(f"  📋 Generated {len(result['recipes'])} recipes")
                    elif 'ingredients' in result:
                        print(f"  🥬 Found {len(result['ingredients'])} ingredient categories")
                    else:
                        print(f"  📄 Response: {result.get('status', 'OK')}")
                else:
                    print(f"  ❌ Status: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            self.wait_for_effect(1)
    
    def demo_step_4_ai_integration(self):
        """Demonstrate AI integration"""
        self.print_demo_step(4, "AI Recipe Generation")
        
        print("🤖 Testing OpenAI integration...")
        
        try:
            import openai
            import os
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key or api_key == 'your-openai-api-key-here':