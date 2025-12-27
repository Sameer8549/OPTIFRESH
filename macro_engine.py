"""
MacroEngine: Nutri-Scanner & Biological Impact Quantification
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

class MacroEngine:
    """
    The Nutri-Scanner.
    Quantifies the biological impact (Calories, Macros, Glycemic Load).
    """
    def __init__(self):
        # Database per 100g
        self.macro_db = {
            "Apple": {"kcal": 52, "carb": 14, "sugar": 10, "prot": 0.3, "fat": 0.2, "gi": 36},
            "Banana": {"kcal": 89, "carb": 23, "sugar": 12, "prot": 1.1, "fat": 0.3, "gi": 51},
            "Orange": {"kcal": 47, "carb": 12, "sugar": 9, "prot": 0.9, "fat": 0.1, "gi": 43},
            "Tomato": {"kcal": 18, "carb": 3.9, "sugar": 2.6, "prot": 0.9, "fat": 0.2, "gi": 15},
            "Potato": {"kcal": 77, "carb": 17, "sugar": 0.8, "prot": 2.0, "fat": 0.1, "gi": 78}, # High GI
            "Avocado": {"kcal": 160, "carb": 9, "sugar": 0.7, "prot": 2.0, "fat": 15, "gi": 15},
            "Default": {"kcal": 50, "carb": 10, "sugar": 5, "prot": 1, "fat": 0.5, "gi": 50}
        }

    def analyze_macros(self, item_name, freshness_score, estimated_weight_g=150):
        """
        Returns nutritional breakdown with "Ripeness Adjustments".
        """
        match = "Default"
        for k in self.macro_db:
            if k in item_name:
                match = k
                break
        
        base = self.macro_db[match].copy()
        
        # --- RIPENESS ADJUSTMENT ---
        # As fruit ripens, starch converts to sugar.
        # Total Carbs stay roughly same, but Sugar % increases, causing GI spike.
        
        sugar_mod = 1.0
        gi_mod = 0
        
        if freshness_score > 85: # "Too Fresh" / Underripe usually? 
            # Actually freshness here maps to "Quality". 
            # Let's assume High Freshness = Perfectly Ripe for generic case, 
            # but for Banana: Bright Yellow (Fresh) = High Sugar vs Green.
            pass
        
        # If item is "Banana" and "Ripe"
        if "Banana" in match:
            # Assume detected item is yellow/ripe if freshness is high
            sugar_mod = 1.2 # More sugar
            gi_mod = 5      # Higher spike
            
        # Scaling by weight
        factor = estimated_weight_g / 100.0
        
        final_macros = {
            "kcal": int(base['kcal'] * factor),
            "carbs": round(base['carb'] * factor, 1),
            "sugar": round(base['sugar'] * factor * sugar_mod, 1),
            "protein": round(base['prot'] * factor, 1),
            "fat": round(base['fat'] * factor, 1),
            "glycemic_index": base['gi'] + gi_mod
        }
        
        # Spike Warning
        warning = "Low Glycemic Impact (Stable)"
        if final_macros['glycemic_index'] > 70: warning = "High Insulin Spike Risk"
        elif final_macros['glycemic_index'] > 55: warning = "Moderate Glycemic Impact"
        
        return final_macros, warning
