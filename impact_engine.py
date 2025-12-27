"""
ImpactEngine: Environmental & Sustainability Metric Modeling
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import random

class ImpactEngine:
    def __init__(self):
        # Data Sources (Simulated for Prototype)
        self.water_footprint = {
            "Apple": 70, # Liters per fruit
            "Beef": 15000, # Liters per kg
            "Banana": 80,
            "Tomato": 13,
            "Potato": 25,
            "Cheese": 300,
            "Bread": 40,
            "Default": 50
        }
        
        self.co2_footprint = { # g CO2 per unit
            "Apple": 35,
            "Beef": 27000,
            "Banana": 80,
            "Tomato": 50,
            "Potato": 40,
            "Cheese": 800,
            "Bread": 60,
            "Default": 50
        }

        self.toxin_map = {
            "Apple": {"mold": "Patulin", "risk": "Kidney Damage, Nausea", "action": "DISCARD ENTIRE FRUIT. Patulin diffuses into healthy tissue."},
            "Bread": {"mold": "Rhizopus/Penicillium", "risk": "Allergic Reaction, Respiratory Distress", "action": "Discard entire loaf if porous. Soft foods allow deep mold penetration."},
            "Cheese": {"mold": "Mycotoxins", "risk": "Acute Toxicity", "action": "Hard cheese: Cut 1 inch around mold. Soft cheese: DISCARD."},
            "Tomato": {"mold": "Alternaria", "risk": "Tenuazonic Acid", "action": "DISCARD. Soft tissue allows rapid toxin spread."},
            "Potato": {"mold": "Solanine (Green)", "risk": "Neurotoxicity", "action": "Cut away green parts deeply. If widespread, discard."},
            "Onion": {"mold": "Black Mold (Aspergillus)", "risk": "Allergy/Lung Infection", "action": "Remove affected layers. Inner layers often safe."},
             "Default": {"mold": "Unknown Mycotoxins", "risk": "Gastrointestinal Distress", "action": "When in doubt, throw it out."}
        }
        
    def calculate_environmental_impact(self, item_name, weight_g=150):
        # Find closest match
        match = "Default"
        for key in self.water_footprint:
            if key.lower() in item_name.lower():
                match = key
                break
        
        water = self.water_footprint[match]
        co2 = self.co2_footprint[match]
        
        return {
            "water_l": water,
            "co2_g": co2,
            "scarcity_impact": "High" if water > 100 else "Moderate"
        }

    def calculate_health_risk(self, item_name, verdict):
        if "SAFE" in verdict:
            return {
                "status": "Safe", 
                "toxin": "None", 
                "medical_risk": "None (Safe)", 
                "clinical_action": "Safe to consume.",
                "medical_advice": "Rich in nutrients. Safe to consume."
            }
            
        match = "Default"
        for key in self.toxin_map:
            if key.lower() in item_name.lower():
                match = key
                break
                
        data = self.toxin_map[match]
        return {
            "status": "Hazard",
            "toxin": data['mold'],
            "medical_risk": data['risk'],
            "clinical_action": data['action']
        }

    def get_circular_advice(self, item_name):
        # Regrow logic
        regrowable = {
            "Onion": "Plant the root base in 1 inch of water. New greens will shoot in 3-5 days.",
            "Potato": "Cut into chunks with 'eyes'. Dry for a day, then bury in soil.",
            "Celery": "Place base in warm water bowl. Translant to soil when leaves appeal.",
            "Lettuce": "Place base in water. New leaves will grow from the center.",
            "Tomato": "Ferment seeds from pulp, dry, and plant. (Hard to regrow from scrap directly).",
            "Mint": "Place stem cutting in water until roots appear."
        }
        
        match = None
        for key in regrowable:
            if key.lower() in item_name.lower():
                match = regrowable[key]
                break
                
        if match:
            return {"can_regrow": True, "method": match, "compost_score": 100}
        else:
            return {"can_regrow": False, "method": "Not easily regrowable. Best for Composting.", "compost_score": 90}
