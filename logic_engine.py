"""
LogicEngine: Multi-Sensor Decision Fusion & System Orchestration
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import numpy as np
import random
import cv2

class LogicEngine:
    """
    The 'Brain' of OPTIFRESH.
    Decides the SYSTEM MODE based on multi-sensor fusion.
    """
    
    def __init__(self):
        pass
        
    
    def _detect_if_uncut(self, img_bgr, item_name):
        """
        Hyper-Robust Heuristic (v2.5): Detects if a fruit/veg is uncut (Whole).
        Uses 'Solidity' (Convex Hull Ratio) and local variance.
        """
        if img_bgr is None: return False
        import cv2
        
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 100)
        
        # 1. Geometric Solidity Analysis
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: return False
        
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0: return False
        
        # Solidity = Area / ConvexHullArea. 
        # Whole fruits are solid (solidity > 0.85) even if they have a small leaf/stem appendage.
        # Cut items usually have concave profiles or internal voids (lower solidity).
        solidity = float(area) / hull_area
        
        # 2. Surface Variance (Check center only to avoid edge shadows)
        h, w = gray.shape
        # Ensure center patch is within bounds
        ch, cw = h//4, w//4
        center_patch = gray[ch:3*ch, cw:3*cw]
        if center_patch.size == 0: return False
        
        lap = cv2.Laplacian(center_patch, cv2.CV_64F)
        var_lap = np.var(lap) 
        
        # 3. Decision Matrix
        # v2.5 Thresholds: Relaxed for real-world lighting and generic descriptions
        is_solid = solidity > 0.85 
        is_smooth = var_lap < 650  # Increased from 450 to handle more texture/noise
        is_large = area > (h * w * 0.03) # Lowered from 0.05
        
        critical_items = ['apple', 'pear', 'melon', 'orange', 'onion', 'potato', 'mango', 'papaya', 'tomato', 'fruit', 'vegetable']
        name_lower = item_name.lower()
        is_critical = any(x in name_lower for x in critical_items)
        
        # LOGIC: If it's a critical whole-mass item and it's solid/smooth, it's likely UNCUT.
        if is_critical and is_solid and is_smooth and is_large:
            return True
        
        return False

    def determine_system_mode(self, analysis_data):
        """
        Determines the status using simple human logic.
        """
        base_data = analysis_data.get('base_data', {})
        surgical_data = analysis_data.get('surgical_data', {})
        item_info = analysis_data.get('item_info', {})
        freshness = analysis_data.get('final_freshness', 0)
        img_bgr = analysis_data.get('img_bgr')
        name = item_info.get('understandable_name', '').lower()
        
        # 1. SAFETY CHECK
        is_high_risk = base_data.get('risk_level', '') == 'High'
        is_bad = freshness < 25
        issues = any(x in str(base_data.get('mold_info', [])).lower() for x in ['mold', 'fungal', 'chaos'])
        
        if (is_high_risk and (is_bad or issues)) or freshness < 15:
            return {
                "key": "MODE_HAZARD",
                "title": "Safety Warning",
                "message": "This looks unsafe. It's better to throw it away.",
                "theme": "#ff4b4b"
            }

        # 2. CUT CHECK
        is_whole = self._detect_if_uncut(img_bgr, name)
        if is_whole:
                return {
                    "key": "MODE_INTERNAL_REQ",
                    "title": "Cut Required",
                    "message": f"I need to see the inside of this {name} to be sure.",
                    "theme": "#00bbff"
                }


        return {
            "key": "MODE_STANDARD",
            "title": "Quality Check",
            "message": f"Comprehensive Bio-Scan for your {name}.",
            "theme": "#00ffcc"
        }
