"""
RecommendationEngine: Intelligent Usage & Salvage Directives
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

class RecommendationEngine:
    def __init__(self):
        # Database for different freshness levels: [Gourmet, Daily, Salvage]
        self.recipes = {
            "Tomato": {
                "Gourmet": ["Tamatar Shorba", "Fresh Kachumber Salad", "Stuffed Tomatoes (Bharwan Tamatar)"],
                "Daily": ["Tomato Rasam", "Tamatar ki Chutney", "Sev Tameta Nu Shaak"],
                "Salvage": ["Homemade Tomato Puree", "South Indian Thokku (Pickle)", "Tomato Rice Base"]
            },
            "Banana": {
                "Gourmet": ["Kachhe Kele Ki Tikki", "Banana Walnut Lassi", "Caramelized Banana Rabri"],
                "Daily": ["Kele Ki Sabzi", "Banana Sheera (Prasad)", "Banana Milkshake"],
                "Salvage": ["Mangalore Buns", "Sweet Paniyaram", "Banana Fritters (Guggula)"]
            },
            "Onion": {
                "Gourmet": ["Bharwan Pyaaz", "Caramelized Onion Kulcha", "Laccha Pyaaz Salad"],
                "Daily": ["Pyaaz Pakoda", "Aloo Pyaaz Paratha", "Onion Raita"],
                "Salvage": ["Birista (Fried Onions)", "Onion Tomato Masala Base", "Onion Chutney"]
            },
            "Potato": {
                "Gourmet": ["Bharwan Dum Aloo", "Tandoori Aloo", "Aloo Tikki Chaat"],
                "Daily": ["Jeera Aloo", "Aloo Gobi Adraki", "Batata Vada"],
                "Salvage": ["Aloo Paratha Stuffing", "Mashed Potato Bharta", "Cutlets"]
            },
            "Mango": {
                "Gourmet": ["Royal Mango Falooda", "Mango Kulfi", "Fresh Aamras Puri"],
                "Daily": ["Mango Lassi", "Keri no Ras", "Mango Milkshake"],
                "Salvage": ["Aam Ka Achaar", "Mango Jam (Chunda)", "Fajeto (Mango Kadhi)"]
            },
            "Apple": {
                "Gourmet": ["Apple Rabri", "Apple Jalebi", "Kashmiri Apple Curry"],
                "Daily": ["Apple Halwa", "Fruit Chaat", "Apple Murabba"],
                "Salvage": ["Apple Chutney", "Stewed Apples", "Apple Jam"]
            },
            "Paneer": {
                "Gourmet": ["Paneer Tikka Masala", "Shahi Paneer", "Malai Kofta"],
                "Daily": ["Matar Paneer", "Paneer Bhurji", "Palak Paneer"],
                "Salvage": ["Paneer Paratha", "Bread Paneer Rolls", "Paneer Cutlets"]
            },
            "Okra": {
                "Gourmet": ["Kurkuri Bhindi", "Bharwan Bhindi", "Dahi Bhindi"],
                "Daily": ["Bhindi Masala", "Aloo Bhindi Fry", "Bhindi Do Pyaza"],
                "Salvage": ["Bhindi Kadhi", "Fried Bhindi Snacks", "Bhindi Sambhar"]
            },
            "Carrot": {
                "Gourmet": ["Gajar Ka Halwa", "Carrot Kheer", "Glazed Baby Carrots"],
                "Daily": ["Gajar Matar Sabzi", "Vegetable Pulao", "Carrot Raita"],
                "Salvage": ["Gajar Ka Achar", "Vegetable Stock", "Carrot Soup"]
            },
             "Spinach": {
                "Gourmet": ["Palak Chaat", "Corn Palak", "Lasooni Palak"],
                "Daily": ["Palak Paneer", "Aloo Palak", "Dal Palak"],
                "Salvage": ["Hara Bhara Kabab", "Palak Paratha", "Palak Soup"]
            },
            "Default": {
                "Gourmet": ["Vegetable Jalfrezi", "Tawa Masala Fry", "Navratan Korma"],
                "Daily": ["Mix Veg Sabzi", "Tehri / Pulao", "Vegetable Dal"],
                "Salvage": ["Pav Bhaji (Mash)", "Vegetable Cutlets", "Mix Veg Pickle"]
            }
        }

    def get_recommendation(self, item_name, severity):
        freshness = 100 - severity
        
        # Determine Condition Category
        if freshness > 80:
            category = "Gourmet"
            action = "Fresh"
            usage = "Item is at peak freshness. Ideal for raw eating."
        elif freshness > 50:
            category = "Daily"
            action = "Good"
            usage = "Good for standard cooking."
        elif freshness > 25:
            category = "Salvage"
            action = "Usage Advised"
            usage = "Needs to be used soon. Ideal for pureeing or cooking."
        else:
            category = "Salvage"
            action = "Safety Warning"
            usage = "This looks unsafe. It's better to throw it away."

        # Fetch Recipes
        suggested_recipes = []
        found_key = "Default"
        for key in self.recipes:
            if key.lower() in item_name.lower():
                found_key = key
                break
        
        suggested_recipes = self.recipes[found_key][category]
        
        if freshness <= 25:
            suggested_recipes = ["No safe recipes. Composting only."]

        return {
            "action": action,
            "usage_advice": usage,
            "recipes": suggested_recipes,
            "freshness_tier": category
        }

class ReasoningEngine:
    def generate_explanation(self, item_info, spoilage_data, weather_data, recommendations, eco_data=None, nut_data=None):
        # Feature 7: Simple Explainable Decision Reasoning
        severity = spoilage_data['severity']
        freshness = spoilage_data['freshness_score']
        stage = spoilage_data['stage']
        item_name = item_info['understandable_name']
        
        explanation = f"### 💡 Details: {item_name}\n\n"
        
        # 1. Vision
        explanation += f"**What I see:** This looks like a **{item_name}**. "
            
        # 2. Quality
        explanation += f"\n\n**Quality:** **{freshness:.0f}%** ({stage}). "
        if eco_data:
            explanation += f"It has lost about **{eco_data['loss_percentage']:.0f}%** of its value."
        
        # 3. Nutrition
        if nut_data:
            explanation += f"\n\n**Nutrients:** About **{nut_data['retention_rate']:.0f}%** of nutrients are still there."

        # 4. Findings
        explanation += f"\n\n**My Check:** "
        molds = spoilage_data.get('mold_types', [])
        if molds and "No" not in molds[0]:
            explanation += f"I found some **{', '.join(molds)}**. "
        else:
            explanation += "Everything looks normal on the surface."
        
        # 5. Recommendation
        explanation += f"\n\n**Advice:** {recommendations['action']}. {recommendations['usage_advice']}"
        
        return explanation

    def analyze_weather_impact(self, item_name, temp, humidity):
        """
        Generates specific bio-ambient insights.
        """
        insight = "Weather conditions are stable for this item."
        risk_color = "#00ffcc" # Green
        
        item_lower = item_name.lower()
        
        # High Heat Logic
        if temp > 28:
            if any(x in item_lower for x in ['milk', 'dairy', 'curd', 'paneer']):
                insight = f"⚠️ High Heat ({temp}°C): Spoilage risk is high. Refrigerate immediately or consume within 45 mins."
                risk_color = "#ff4b4b"
            elif any(x in item_lower for x in ['banana', 'mango', 'papaya']):
                insight = f"🔥 Heat Warning ({temp}°C): Accelerates ripening process. Shelf-life reduced by ~40%. Expect rapid sugar conversion."
                risk_color = "#ffa500"
            elif any(x in item_lower for x in ['spinach', 'lettuce', 'leafY']):
                insight = f"☀️ Wilting Risk: High temperature will cause rapid cellular dehydration. Revive with ice water shock."
                risk_color = "#ffa500"
            else:
                insight = f"Warm ({temp}°C): This can lead to spoilage. Keep in a cool area."
                risk_color = "#ffff00"
                
        # High Humidity Logic
        elif humidity > 70:
            if any(x in item_lower for x in ['bread', 'roti', 'bakery']):
                insight = f"💧 High Humidity ({humidity}% RH): Mold might grow soon. Use it quickly."
                risk_color = "#ff4b4b"
            elif any(x in item_lower for x in ['spice', 'powder', 'salt']):
                insight = f"💧 Clumping Risk: High humidity will degrade potency and cause caking. Ensure airtight seal."
                risk_color = "#ffa500"
            elif any(x in item_lower for x in ['onion', 'garlic', 'potato']):
                insight = f"🌫️ Danger: High humidity might cause rot. Store with good airflow."
                risk_color = "#ffa500"
        
        # Cold Logic
        elif temp < 12:
            if 'banana' in item_lower:
                insight = f"❄️ Chilling Injury: Too cold ({temp}°C). Skin will blacken and cell walls will rupture. Move to warmer spot."
                risk_color = "#00ccff"
            elif 'tomato' in item_lower:
                insight = f"❄️ Texture Loss: Cold storage damages flavor volatiles and causes mealiness."
                risk_color = "#00ccff"

        return insight, risk_color
