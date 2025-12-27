"""
SensoryEngine: Digital Palate for Taste & Texture Prediction
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern

class SensoryEngine:
    """
    Taste & Texture engine.
    Predicts internal properties from external visual cues.
    """
    def __init__(self):
        self.flavor_db = {
            "Apple": {"base_sweet": 7, "base_crunch": 8, "base_acid": 4},
            "Banana": {"base_sweet": 8, "base_crunch": 2, "base_acid": 2},
            "Orange": {"base_sweet": 6, "base_crunch": 3, "base_acid": 8},
            "Tomato": {"base_sweet": 4, "base_crunch": 5, "base_acid": 6},
            "Grape": {"base_sweet": 9, "base_crunch": 6, "base_acid": 3},
            "Default": {"base_sweet": 5, "base_crunch": 5, "base_acid": 5}
        }

    def predict_sensory_profile(self, image_bgr, item_name, freshness_score, texture_entropy):
        """
        Returns a dictionary of 0-10 scores for: Crunch, Sweetness, Juiciness, Mealiness.
        """
        # 1. Get Base Profile
        match = "Default"
        for k in self.flavor_db:
            if k in item_name:
                match = k
                break
        base = self.flavor_db[match]
        
        # 2. Derive Visual Metrics
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Color Saturation (Correlates with Ripeness/Sugar in fruit)
        # Higher Saturation + High Value = Sweeter (usually)
        mean_sat = np.mean(s)
        mean_val = np.mean(v)
        
        # Texture Impact on Crunch
        # High Entropy = Rough/Wrinkled = Low Crunch
        # Low Entropy = Taut/Smooth = High Crunch
        # texture_entropy is usually 1.0 (smooth) to 4.0 (rough)
        
        # --- CALCULATE SCORES ---
        
        # A. CRUNCH INDEX (Bio-Physical Snap)
        # Base crunch decays rapidly with freshness loss
        freshness_factor = (freshness_score / 100.0)
        
        # Entropy penalty: If entropy > 2.0, crunch drops fast.
        entropy_penalty = max(0, (texture_entropy - 1.5) * 2) 
        
        crunch = base['base_crunch'] * freshness_factor
        crunch -= entropy_penalty
        crunch = max(1, min(10, crunch))
        
        # B. SWEETNESS (Virtual Brix)
        # Sweetness peaks at "Ripe" (70-90 freshness), drops if "Overripe/Rotten" (<40)
        # But for bananas, overripe = sweeter. 
        # General rule: Ripe color (Saturation > 100) boosts sweetness.
        
        sweet_boost = 0
        if mean_sat > 100 and mean_val > 100:
            sweet_boost = 1.5 # Ripe and bright
            
        sweet = base['base_sweet'] + sweet_boost
        if freshness_score < 30: # Rotten usually ferments/sours
            sweet -= 4
        elif freshness_score < 60: # Overripe
            sweet += 1 # Often sweeter before rot
            
        sweet = max(1, min(10, sweet))
        
        # C. JUICINESS (Hydro-Pressure)
        # High Turgidity (Freshness) = High Juice.
        # Shiny Skin (High Specularity) -> often juicy.
        # We use a proxy: Freshness * Saturation
        juice = (freshness_score / 10.0) 
        if mean_sat < 60: juice -= 2 # Dull skin = dry
        juice = max(1, min(10, juice))
        
        # D. MEALINESS (The "Yuck" Factor)
        # Inverse of Crunch + Freshness.
        # Valid mostly for Apples, Pears.
        mealy = 0
        if "Apple" in item_name or "Pear" in item_name:
            if freshness_score < 70 and crunch < 5:
                mealy = 8 # High mealiness risk
            elif freshness_score < 85:
                mealy = 4
        
        return {
            "Crunch": int(crunch),
            "Sweetness": int(sweet),
            "Juiciness": int(juice),
            "Mealiness": int(mealy),
            "Acid": base['base_acid']
        }
