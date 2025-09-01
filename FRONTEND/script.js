// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let selectedIngredients = [];
let recipeDatabase = []; // Will be replaced with backend calls

// DOM elements
const ingredientsInput = document.getElementById('ingredients');
const ingredientTags = document.getElementById('ingredientTags');
const dietarySelect = document.getElementById('dietary');
const getRecipesBtn = document.getElementById('getRecipesBtn');
const demoBtn = document.getElementById('demoBtn');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const recipesDiv = document.getElementById('recipes');

// Initialize app when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up event listeners
    ingredientsInput.addEventListener('keypress', handleIngredientInput);
    getRecipesBtn.addEventListener('click', getRecipeRecommendations);
    demoBtn.addEventListener('click', loadDemoData);
    
    // Display daily health tip
    displayDailyHealthTip();
    
    // Load saved user data if available
    loadUserData();
}

// Handle ingredient input
function handleIngredientInput(e) {
    if (e.key === 'Enter') {
        const ingredient = e.target.value.trim().toLowerCase();
        if (ingredient && !selectedIngredients.includes(ingredient)) {
            selectedIngredients.push(ingredient);
            updateIngredientTags();
            e.target.value = '';
            saveUserData();
        }
    }
}

function updateIngredientTags() {
    ingredientTags.innerHTML = selectedIngredients.map(ingredient => 
        `<div class="ingredient-tag">
            ${ingredient}
            <span class="remove-tag" onclick="removeIngredient('${ingredient}')">×</span>
        </div>`
    ).join('');
}

function removeIngredient(ingredient) {
    selectedIngredients = selectedIngredients.filter(i => i !== ingredient);
    updateIngredientTags();
    saveUserData();
}

// API calls to backend
async function getRecipeRecommendations() {
    if (selectedIngredients.length === 0) {
        showError('Please add at least one ingredient!');
        return;
    }

    const dietaryNeeds = dietarySelect.value;
    showLoading(true);
    hideError();
    
    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/recipes/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ingredients: selectedIngredients,
                dietary_needs: dietaryNeeds,
                user_id: getUserId()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            displayRecipes(data.recipes);
            // Save to local database cache
            recipeDatabase.push(...data.recipes);
        } else {
            throw new Error(data.error || 'Failed to generate recipes');
        }

    } catch (error) {
        console.error('Error fetching recipes:', error);
        
        // Fallback to local generation if backend is unavailable
        console.log('Backend unavailable, using local generation...');
        const recipes = simulateAIRecipeGeneration(selectedIngredients, dietaryNeeds);
        displayRecipes(recipes);
        
        showError('Using offline mode - connect to internet for enhanced AI features');
    } finally {
        showLoading(false);
    }
}

// Save recipe to backend
async function saveRecipe(recipe) {
    try {
        const response = await fetch(`${API_BASE_URL}/recipes/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recipe: recipe,
                user_id: getUserId()
            })
        });

        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('Error saving recipe:', error);
        return false;
    }
}

// Get user's saved recipes
async function getUserRecipes() {
    try {
        const response = await fetch(`${API_BASE_URL}/recipes/user/${getUserId()}`);
        const data = await response.json();
        return data.recipes || [];
    } catch (error) {
        console.error('Error fetching user recipes:', error);
        return [];
    }
}

// Fallback AI recipe generation (when backend unavailable)
function simulateAIRecipeGeneration(ingredients, dietaryNeeds) {
    const recipeTemplates = [
        {
            name: "Nutritious {protein} and {vegetable} Stew",
            description: "A hearty, protein-rich stew perfect for building strength and providing essential nutrients.",
            baseIngredients: ["onion", "oil", "salt", "water"],
            instructions: "1. Heat oil in a pot and sauté onions until golden. 2. Add {protein} and cook until browned. 3. Add {vegetable} and other vegetables. 4. Add water and simmer for 30-45 minutes until tender. 5. Season with salt and serve hot.",
            nutritionBenefits: "High in protein for muscle development, rich in vitamins and minerals for immune support.",
            servings: 4,
            prepTime: "45 minutes"
        },
        {
            name: "Simple {grain} and {legume} Bowl",
            description: "A complete protein combination that's affordable and filling.",
            baseIngredients: ["water", "salt", "oil"],
            instructions: "1. Cook {grain} in salted water until tender. 2. In another pot, cook {legume} until soft. 3. Combine both and add a little oil. 4. Serve with any available vegetables on the side.",
            nutritionBenefits: "Complete amino acid profile, high fiber content, sustained energy release.",
            servings: 3,
            prepTime: "30 minutes"
        },
        {
            name: "Fresh {vegetable} and {protein} Salad",
            description: "A light, nutrient-dense meal perfect for hot climates.",
            baseIngredients: ["lemon", "salt", "oil"],
            instructions: "1. Wash and chop {vegetable} finely. 2. Cook {protein} and let cool, then dice. 3. Mix together with lemon juice, salt, and oil. 4. Let marinate for 10 minutes before serving.",
            nutritionBenefits: "Raw vegetables provide vitamin C and enzymes, lean protein supports growth.",
            servings: 2,
            prepTime: "15 minutes"
        }
    ];

    const proteins = ingredients.filter(i => 
        ['chicken', 'fish', 'beef', 'eggs', 'beans', 'lentils', 'peas'].some(p => i.includes(p))
    );
    const vegetables = ingredients.filter(i => 
        ['tomato', 'kale', 'cabbage', 'carrot', 'onion', 'spinach', 'pepper'].some(v => i.includes(v))
    );
    const grains = ingredients.filter(i => 
        ['rice', 'wheat', 'maize', 'millet', 'sorghum', 'oats'].some(g => i.includes(g))
    );
    const legumes = ingredients.filter(i => 
        ['beans', 'lentils', 'peas', 'chickpeas'].some(l => i.includes(l))
    );

    const recipes = [];
    
    // Generate recipes based on available ingredients
    if (proteins.length > 0 && vegetables.length > 0) {
        const template = { ...recipeTemplates[0] };
        template.name = template.name.replace('{protein}', proteins[0]).replace('{vegetable}', vegetables[0]);
        template.instructions = template.instructions.replace(/{protein}/g, proteins[0]).replace(/{vegetable}/g, vegetables[0]);
        template.usedIngredients = [proteins[0], vegetables[0], ...template.baseIngredients];
        template.id = generateId();
        recipes.push(template);
    }

    if (grains.length > 0 && legumes.length > 0) {
        const template = { ...recipeTemplates[1] };
        template.name = template.name.replace('{grain}', grains[0]).replace('{legume}', legumes[0]);
        template.instructions = template.instructions.replace(/{grain}/g, grains[0]).replace(/{legume}/g, legumes[0]);
        template.usedIngredients = [grains[0], legumes[0], ...template.baseIngredients];
        template.id = generateId();
        recipes.push(template);
    }

    if (vegetables.length > 1 && (proteins.length > 0 || grains.length > 0)) {
        const template = { ...recipeTemplates[2] };
        const protein = proteins[0] || grains[0];
        template.name = template.name.replace('{vegetable}', vegetables[1]).replace('{protein}', protein);
        template.instructions = template.instructions.replace(/{vegetable}/g, vegetables[1]).replace(/{protein}/g, protein);
        template.usedIngredients = [vegetables[1], protein, ...template.baseIngredients];
        template.id = generateId();
        recipes.push(template);
    }

    // Add dietary-specific modifications
    if (dietaryNeeds === 'children') {
        recipes.forEach(recipe => {
            recipe.nutritionBenefits += " Specially important for growing children's development.";
            recipe.instructions += " Cut ingredients into small, child-friendly pieces.";
        });
    } else if (dietaryNeeds === 'pregnant') {
        recipes.forEach(recipe => {
            recipe.nutritionBenefits += " Provides essential nutrients for maternal and fetal health.";
        });
    } else if (dietaryNeeds === 'low-cost') {
        recipes.forEach(recipe => {
            recipe.description += " Budget-friendly and uses affordable ingredients.";
        });
    }

    return recipes.slice(0, 3);
}

function displayRecipes(recipes) {
    if (recipes.length === 0) {
        showError('No recipes found with your ingredients. Try adding more common ingredients like rice, beans, or vegetables.');
        return;
    }

    recipesDiv.innerHTML = recipes.map(recipe => `
        <div class="recipe-card" onclick="selectRecipe('${recipe.id}')">
            <h3 class="recipe-title">${recipe.name}</h3>
            <p class="recipe-description">${recipe.description}</p>
            
            <div class="recipe-meta" style="display: flex; gap: 15px; margin-bottom: 15px; font-size: 14px; color: #4a5568;">
                <span>👥 Serves: ${recipe.servings || 'N/A'}</span>
                <span>⏱️ Prep: ${recipe.prepTime || 'N/A'}</span>
            </div>
            
            <div class="recipe-ingredients">
                <h4>🥘 Ingredients Used:</h4>
                <p class="ingredients-list">${recipe.usedIngredients ? recipe.usedIngredients.join(', ') : 'Various ingredients'}</p>
            </div>
            
            <div class="recipe-instructions">
                <h4>👩‍🍳 Instructions:</h4>
                <p>${recipe.instructions}</p>
            </div>
            
            <div class="nutrition-info">
                <h4>💪 Nutrition Benefits:</h4>
                <p>${recipe.nutritionBenefits}</p>
            </div>
        </div>
    `).join('');
}

async function selectRecipe(recipeId) {
    const recipe = recipeDatabase.find(r => r.id == recipeId) || 
                   { id: recipeId, name: "Selected Recipe" };
    
    // Save to backend
    const saved = await saveRecipe(recipe);
    
    if (saved) {
        showSuccess(`Recipe "${recipe.name}" saved to your meal plan!`);
    } else {
        showSuccess(`Recipe "${recipe.name}" selected! (Offline mode - will sync when online)`);
    }
}

// Health tips functionality
function generateHealthTips() {
    const tips = [
        "🥗 Eat a variety of colorful vegetables daily for different vitamins and minerals.",
        "💧 Drink clean water regularly - aim for 6-8 glasses per day.",
        "🥜 Include protein in every meal to support growth and healing.",
        "🌾 Choose whole grains over refined grains when possible.",
        "🥛 If available, include dairy or calcium-rich foods for bone health.",
        "🍊 Eat fruits rich in Vitamin C to boost immune system.",
        "🐟 Include iron-rich foods like dark leafy greens or fish when available."
    ];
    
    return tips[Math.floor(Math.random() * tips.length)];
}

function displayDailyHealthTip() {
    const tip = generateHealthTips();
    const tipElement = document.createElement('div');
    tipElement.className = 'nutrition-info';
    tipElement.style.marginBottom = '20px';
    tipElement.innerHTML = `
        <h4>💡 Daily Health Tip:</h4>
        <p>${tip}</p>
    `;
    document.querySelector('.input-section').appendChild(tipElement);
}

// Utility functions
function showLoading(show) {
    loadingDiv.style.display = show ? 'block' : 'none';
    getRecipesBtn.disabled = show;
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function hideError() {
    errorDiv.style.display = 'none';
}

function showSuccess(message) {
    // Create temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    document.querySelector('.container').appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function getUserId() {
    // Generate or retrieve user ID (in real app, this would be from authentication)
    let userId = localStorage.getItem('nutriai_user_id');
    if (!userId) {
        userId = 'user_' + generateId();
        localStorage.setItem('nutriai_user_id', userId);
    }
    return userId;
}

// Local storage for offline capability
function saveUserData() {
    const userData = {
        ingredients: selectedIngredients,
        lastUpdated: new Date().toISOString()
    };
    localStorage.setItem('nutriai_user_data', JSON.stringify(userData));
}

function loadUserData() {
    try {
        const userData = JSON.parse(localStorage.getItem('nutriai_user_data'));
        if (userData && userData.ingredients) {
            selectedIngredients = userData.ingredients;
            updateIngredientTags();
        }
    } catch (error) {
        console.log('No saved user data found');
    }
}

// Demo functionality for hackathon presentation
function loadDemoData() {
    selectedIngredients = ['chicken', 'tomatoes', 'kale', 'rice', 'beans'];
    updateIngredientTags();
    dietarySelect.value = 'children';
    saveUserData();
    
    showSuccess('Demo data loaded! Click "Get AI Recipe Recommendations" to see results.');
}

// Network status detection
function checkNetworkStatus() {
    return navigator.onLine;
}

// Offline/Online event handlers
window.addEventListener('online', function() {
    console.log('Connection restored - syncing data...');
    syncOfflineData();
});

window.addEventListener('offline', function() {
    console.log('Connection lost - switching to offline mode');
    showError('Offline mode activated - limited functionality available');
});

async function syncOfflineData() {
    // Sync any offline data when connection is restored
    const offlineRecipes = JSON.parse(localStorage.getItem('nutriai_offline_recipes') || '[]');
    
    for (const recipe of offlineRecipes) {
        await saveRecipe(recipe);
    }
    
    localStorage.removeItem('nutriai_offline_recipes');
}

// Error handling for API calls
function handleApiError(error) {
    console.error('API Error:', error);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return 'Network error - please check your internet connection';
    } else if (error.message.includes('404')) {
        return 'Service temporarily unavailable - using offline mode';
    } else if (error.message.includes('500')) {
        return 'Server error - please try again later';
    } else {
        return 'An unexpected error occurred - please try again';
    }
}

// Analytics and user tracking (for improvement)
function trackUserAction(action, data = {}) {
    const eventData = {
        action: action,
        timestamp: new Date().toISOString(),
        user_id: getUserId(),
        ingredients_count: selectedIngredients.length,
        ...data
    };
    
    // Send to backend analytics endpoint
    fetch(`${API_BASE_URL}/analytics/track`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData)
    }).catch(error => {
        // Silent fail for analytics
        console.log('Analytics tracking failed:', error);
    });
}

// Enhanced recipe selection with analytics
function selectRecipe(recipeId) {
    const recipe = recipeDatabase.find(r => r.id == recipeId);
    if (recipe) {
        trackUserAction('recipe_selected', { recipe_id: recipeId, recipe_name: recipe.name });
        saveRecipe(recipe);
    }
}

// Initialize tracking
document.addEventListener('DOMContentLoaded', function() {
    trackUserAction('app_loaded');
});