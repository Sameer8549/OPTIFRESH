import cv2
import numpy as np
import random

class DeepScanEngine:
    """
    Simulates 'X-Ray' Vision by correlating surface biomarkers with internal defects.
    Predicts: Spongy Tissue (Mango), Core Rot (Apple), Hollow Heart (Potato).
    """
    def __init__(self):
        self.defect_map = {
            "Mango": {"defect": "Spongy Tissue", "mechanism": "Premature ripening near stone", "risk_factor": "Shoulder acidity"},
            "Apple": {"defect": "Core Rot", "mechanism": "Fungal entry via calyx", "risk_factor": "Open sinus"},
            "Potato": {"defect": "Hollow Heart", "mechanism": "Rapid growth stress", "risk_factor": "Oversized/Irregular"},
            "Tomato": {"defect": "Internal Browning", "mechanism": "Viral infection (ToBRFV)", "risk_factor": "Mosaic pattern"},
            "Watermelon": {"defect": "Hollow Heart/Mealiness", "mechanism": "Pollination defect", "risk_factor": "Asymmetry"},
             "Default": {"defect": "Hidden Decay", "mechanism": "Sub-surface bruising", "risk_factor": "Impact trauma"}
        }

    def analyze_internal_structure(self, item_name, freshness_score):
        """
        Returns probabilistic internal state.
        """
        match = "Default"
        for key in self.defect_map:
            if key.lower() in item_name.lower():
                match = key
                break
        
        info = self.defect_map[match]
        
        # Heuristic: Lower freshness = Higher risk of internal failure logic
        # But specifically, certain defects happen even in fresh-looking fruit.
        
        # Simulating a risk score based on "biomarkers" (randomized based on freshness for demo)
        # In a real model, this would use 'surface_tension' or 'calyx_color'.
        base_risk = max(0, (100 - freshness_score) * 0.8)
        
        # Add some "hidden risk" volatility
        hidden_risk = random.randint(0, 20) 
        total_risk = min(100, base_risk + hidden_risk)
        
        return {
            "defect_name": info['defect'],
            "mechanism": info['mechanism'],
            "risk_score": total_risk,
            "integrity": max(0, 100 - total_risk),
            "verdict": "Structurally Sound" if total_risk < 40 else "Internal Anomaly Detected"
        }

    def generate_xray_vision(self, image_bgr, risk_score):
        """
        Generates a pseudo-X-Ray heatmap.
        Darker/Blue = Dense/Healthy.
        Red/White = Hollow/Rot.
        """
        # 1. Grayscale
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # 2. Invert (Bones are white logic, but here Rot is 'Hot')
        # We want healthy (dense) to be cool colors, rot (air/mush) to be hot.
        
        # Create a heatmap base
        heatmap_base = cv2.applyColorMap(gray, cv2.COLORMAP_BONE)
        
        # 3. Simulate Defect overlays if risk is high
        if risk_score > 40:
            # Create 'hot spots'
            overlay = np.zeros_like(gray)
            h, w = gray.shape
            # Random center rot
            cv2.circle(overlay, (w//2, h//2), h//4, (255), -1)
            # Blur it heavily
            overlay = cv2.GaussianBlur(overlay, (101, 101), 0)
            
            # Apply Red color map to the defect
            defect_map = cv2.applyColorMap(overlay, cv2.COLORMAP_JET)
            
            # Blend: Base Bone Map + Defect Jet Map
            # We want the defect to show up as glowing red/yellow inside the blue bone structure
            heatmap_base = cv2.addWeighted(heatmap_base, 0.7, defect_map, 0.5, 0)
            
        return heatmap_base
