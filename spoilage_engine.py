"""
SpoilageEngine: Scientific Biological Spoilage & Pathogen Scoring
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops

class SpoilageEngine:
    def __init__(self):
        self.history = {} # Simple memory for progression (item_name: history_list)

    def analyze_spoilage(self, image, item_info, ai_state_info=None, legacy_verdict=None, spectral_verdict=None):
        # Feature 2 Upgrade: Scitific Biological Detection (No Pre-trained dependency for scoring)
        
        # --- KEYWORD SAFETY LOCK (CRITICAL) ---
        item_lower = item_info.get("understandable_name", "").lower()
        hazard_keywords = ["mold", "rot", "decay", "spoil", "damage", "bruise", "bite", "eaten", "fungus", "fungal"]
        keyword_hazardous = any(word in item_lower for word in hazard_keywords)
        
        # --- FORENSIC OVERRIDE (CRITICAL SYNC) ---
        if spectral_verdict:
            if spectral_verdict['verdict'] == "Discard":
                return {
                    "severity": 100,
                    "freshness_score": 0,
                    "stage": "Spoiled",
                    "risk_level": "High",
                    "consensus_state": "Discard",
                    "ai_opinion": "Checked: Spoiled",
                    "mold_types": ["Issue found"],
                    "defects": {"Issues": 100, "Texture": 100, "Color": 100},
                    "biological_notes": {"surface_variance": 999, "entropy_index": 9.9}
                }
            elif spectral_verdict['verdict'] == "COOK IMMEDIATELY":
                 # Force at least 65 severity (Spoiled/Early Spoilage range)
                 pass # We will apply a floor later, or handle here.
                 
        # 1. Micro-Texture Entropy (Baseline detection to ensure non-zero scores)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # High variance in a smooth fruit often means surface irregularities (scratches/aging)
        baseline_entropy = min(10, laplacian_var / 500) 

        # 2. Color Degradation (Bruising/Oxidation)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Detect Brown/Dark patches (typical of bruising)
        # Bruising range in HSV: low Value and specific Hue
        brown_mask = cv2.inRange(hsv, (0, 20, 20), (30, 150, 100))
        bruise_density = np.sum(brown_mask > 0) / (image.shape[0] * image.shape[1])
        bruising_score = min(100, bruise_density * 500 + baseline_entropy)

        # 3. Structural Wilting (LBP Entropy Breakdown)
        radius = 3
        n_points = 24
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        # SHANNON ENTROPY: Measures complexity. 
        # Smooth surfaces (Fresh) = Low Entropy. Wrinkled/Wilted = High Entropy.
        entropy = -np.sum(hist * np.log2(hist + 1e-7))
        # Calibration: LBP 'uniform' entropy for a smooth surface is around 1.0-2.0.
        # Wilt/Rot surfaces spikes this above 3.5.
        wilt_score = max(0, (entropy - 1.5) * 40) 
        if laplacian_var < 400: wilt_score *= 0.2 # Massive bonus for low micro-variance

        # 4. Scientific Mold Intelligence (Cluster & Texture Analysis)
        # Create a "Biological Interest Mask" (Mask out the background)
        # Assuming white/light background for studio photos
        _, bg_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        # Also mask out very dark shadows
        _, shadow_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        interest_mask = cv2.bitwise_and(bg_mask, shadow_mask)

        # Refined thresholds (Synched with utils.py later)
        greenish_mold = cv2.bitwise_and(cv2.inRange(hsv, (35, 45, 45), (85, 255, 170)), interest_mask)
        black_mold = cv2.bitwise_and(cv2.inRange(hsv, (0, 0, 0), (180, 255, 20)), interest_mask)
        white_mold = cv2.bitwise_and(cv2.inRange(hsv, (0, 0, 235), (180, 25, 255)), interest_mask)

        def filter_mold_clusters(mask, min_area=100, is_white=False):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            mold_count = 0
            total_mold_area = 0
            height, width = mask.shape
            center = (width // 2, height // 2)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                x, y, w, h_rect = cv2.boundingRect(cnt)
                
                # SEED/CORE FILTER: Ignore dark clusters near the center in Apples
                dist_from_center = np.sqrt((x + w/2 - center[0])**2 + (y + h_rect/2 - center[1])**2)
                if not is_white and "Apple" in item_info.get("understandable_name", ""):
                    if dist_from_center < (min(width, height) * 0.22): # Deep seed shield
                        continue 
                
                # Filter out linear artifacts (edge lines)
                if w / (h_rect + 1) > 5 or h_rect / (w + 1) > 5: continue

                if min_area < area < (image.size * 0.04): 
                    mold_count += 1
                    total_mold_area += area
            return mold_count, total_mold_area

        mold_info = []
        mold_score = 0
        g_count, g_area = filter_mold_clusters(greenish_mold, 500)
        b_count, b_area = filter_mold_clusters(black_mold, 300)
        w_count, w_area = filter_mold_clusters(white_mold, 1200, is_white=True)

        # DEEP SCAN TEXTURE VERIFICATION (GLCM)
        glcm_res = "Smooth"
        try:
            patch_size = 32
            # Analysis points (Golden Ratio spots often contain the flesh)
            test_points = [(height//2, width//2), (height//3, width//3), (2*height//3, 2*width//3)]
            homogeneity = 0
            count = 0
            for py, px in test_points:
                if 0 <= py < height-patch_size and 0 <= px < width-patch_size:
                    p = gray[py:py+patch_size, px:px+patch_size]
                    if np.mean(p) < 240: # Don't analyze pure background
                        glcm = graycomatrix(p, [1], [0], 256, symmetric=True, normed=True)
                        homogeneity += graycoprops(glcm, 'homogeneity')[0, 0]
                        count += 1
            if count > 0:
                avg_homo = homogeneity / count
                if avg_homo < 0.2: glcm_res = "Textured/Fuzzy"
        except: pass

        if g_count > 1 and glcm_res == "Textured/Fuzzy": 
            mold_info.append("Penicillium (Greenish Clusters)")
            mold_score += 30 # Increased severity
        if b_count > 0 and glcm_res == "Textured/Fuzzy": 
            mold_info.append("Rhizopus (Black Spotting)")
            mold_score += 45
        if w_count > 3 and glcm_res == "Textured/Fuzzy": 
            mold_info.append("Aspergillus (Fuzzy White)")
            mold_score += 30
        
        # 5. LIGHT CHECK (Color analysis)
        # Science: Freshness correlates with Chlorophyll (Green Ratio)
        # Bruising correlates with Hemoglobin-like browning in infrared (Red/Blue Ratio)
        b_avg, g_avg, r_avg = cv2.mean(image, mask=interest_mask)[:3]
        green_ratio = g_avg / (r_avg + 1e-7) # High = Fresh
        red_blue_ratio = r_avg / (b_avg + 1e-7) # High = Oxidized/Bruised
        
        item_lower = item_info.get("understandable_name", "").lower()
        is_red_fruit = any(x in item_lower for x in ["apple", "tomato", "pomegranate"])
        
        spectral_stress = 0
        # LEAF FILTER: If 'Apple' and green_ratio is low, check if it's just the leaf area
        if "apple" in item_lower and green_ratio < 0.6:
            # We assume a single leaf is fine and shouldn't drop freshness to 70% (Salvage)
            spectral_stress += 5 # Minimal penalty for leaf-related color shifts
        elif green_ratio < 0.8 and not is_red_fruit: 
            spectral_stress += 20 
            
        # Red-Skin Support: Red apples have high R/B ratios naturally.
        if is_red_fruit:
           if red_blue_ratio > 2.5: spectral_stress += 10 # Only high-intensity oxidation
        elif red_blue_ratio > 1.5: 
           spectral_stress += 15
        
        # 6. TEXTURE CHECK
        fractal_energy = 0
        fractal_contrast = 0
        try:
            if count > 0:
                p = gray[height//2:height//2+patch_size, width//2:width//2+patch_size]
                glcm = graycomatrix(p, [1], [0], 256, symmetric=True, normed=True)
                fractal_energy = graycoprops(glcm, 'energy')[0, 0]
                fractal_contrast = graycoprops(glcm, 'contrast')[0, 0]
                
                # Scientific Law: 
                # - Fresh skin is UNIFORM (High Energy, Low Contrast)
                # - Mold is FRACTAL (Low Energy, High Contrast)
                if fractal_energy < 0.08 and fractal_contrast > 650:
                    mold_score = max(mold_score, 75)
                    mold_info.append("Issue found (Possible mold)")
        except: pass

        # AI-State Consensus Engine (VETO LOGIC V3 - Scientific)
        consensus_state = "Neutral"
        clip_fresh_prob = 0
        clip_mold_prob = 0
        
        if ai_state_info:
            clip_probs = ai_state_info[1]
            clip_fresh_prob = clip_probs.get("perfectly fresh fruit skin", 0) + clip_probs.get("pristine surface texture", 0)
            clip_mold_prob = clip_probs.get("microscopic fungal mold", 0) + clip_probs.get("white fuzzy mycelium", 0) + clip_probs.get("blue-green penicillium mold", 0)
            clip_bg_prob = clip_probs.get("studio background", 0)
            clip_seed_prob = clip_probs.get("natural seeds", 0)

        # 5. Synthesis (SCIENTIFIC CONSENSUS V5 - ULTRA CALIBRATED)
        heuristic_severity = (bruising_score * 0.1 + wilt_score * 0.2 + mold_score * 0.5 + spectral_stress * 0.2)
        
        # Red-Fruit Bias Compensation (v2.4 - Appendage Aware)
        item_lower = item_info.get("understandable_name", "").lower()
        is_red_fruit = any(x in item_lower for x in ["apple", "tomato", "pomegranate", "pepper", "capsicum", "chilli"])
        
        if is_red_fruit:
            # Whole red fruits shouldn't hit 'Salvage' (70%) based on surface color alone
            heuristic_severity *= 0.45 # Aggressive compensation for healthy skin
            consensus_state = "Red Fruit Check"

        # BACKGROUND REJECTION (Safety for studio shots)
        if clip_bg_prob > 0.6 and not keyword_hazardous:
            heuristic_severity *= 0.1
            mold_score = 0
            
        # SAFETY CONSTRAINTS V3
        if keyword_hazardous:
             # If the AI explicitly named 'Mold' or 'Decay' in the description, trust it.
             severity = max(heuristic_severity, 90)
             consensus_state = "Hazard Alert (Keyword)"
        elif mold_score > 20:
             # Trust heuristic Clusters over CLIP skin confidence
             severity = max(heuristic_severity, 75)
             consensus_state = "Pathogen Cluster Lockdown"
        
        # FINAL CONSENSUS CALCULATION
        elif clip_mold_prob > 0.8: # Even stricter AI confirmation
             severity = max(heuristic_severity, 85) 
        elif fractal_contrast > 1400 and fractal_energy < 0.02: 
             severity = max(heuristic_severity, 80) 
        elif (clip_fresh_prob > 0.45 or fractal_energy > 0.10) and not is_red_fruit and not keyword_hazardous:
             # Freshness veto for green items - BLOCKED if keywords or heuristics suggest mold
             severity = heuristic_severity * 0.05
             consensus_state = "Checked: Fresh"
        elif is_red_fruit and clip_fresh_prob > 0.4 and not keyword_hazardous:
             # Freshness veto for red items - BLOCKED if keywords or heuristics suggest mold
             severity = min(heuristic_severity, 8) 
             consensus_state = "Checked: Good"
        else:
            severity = heuristic_severity
            if keyword_hazardous: severity = max(severity, 90)

        # Final labels (Simple & Human)
        quality_score = 100 - severity
        if quality_score > 92: stage = "Excellent"
        elif quality_score > 75: stage = "Pristine"
        elif quality_score > 50: stage = "Good"
        elif quality_score > 25: stage = "Bad"
        else: stage = "Warning"

        risk_level = "Low"
        if severity > 75 or clip_mold_prob > 0.6: risk_level = "High"
        elif severity > 40: risk_level = "Medium"

        return {
            "severity": severity,
            "freshness_score": quality_score,
            "stage": stage,
            "risk_level": risk_level,
            "consensus_state": consensus_state,
            "ai_opinion": ai_state_info[0] if ai_state_info else "N/A",
            "mold_types": mold_info if mold_info else ["No issues detected"],
            "defects": {
                "Color": min(100, spectral_stress * 3),
                "Texture": min(100, (1-fractal_energy)*100),
                "Issues": min(100, mold_score)
            },
            "biological_notes": {
                "quality": quality_score,
                "issues": mold_info
            }
        }

    def calculate_shelf_life(self, freshness_score, temp, humidity, is_cut=False):
        # Advanced shelf-life estimation in hours
        base_rate = 1.0 # Base decay rate per hour
        if temp > 25: base_rate *= 1.5
        if humidity > 70: base_rate *= 1.3
        if is_cut: base_rate *= 5.0 # Cut items decay much faster
        
        # Remaining life estimated to reach "Spoiled" (threshold 30)
        remaining_percentage = max(0, freshness_score - 30)
        hours_left = remaining_percentage / (base_rate + 0.1)
        
        days = int(hours_left // 24)
        hours = int(hours_left % 24)
        
        if days > 0:
            return f"{days} Days, {hours} Hours"
        else:
            return f"{hours} Hours"

    def predict_progression(self, item_name, current_severity):
        # Simple state tracking
        if item_name not in self.history:
            self.history[item_name] = []
        
        self.history[item_name].append(current_severity)
        
        if len(self.history[item_name]) < 2:
            return "Stable", "Deterioration rate is currently baseline."
        
        rate = self.history[item_name][-1] - self.history[item_name][-2]
        if rate > 10: 
            return "Rapidly Increasing", "High risk of rapid decay within 6 hours."
        elif rate > 2: 
            return "Slowly Increasing", "Standard oxidation/aging process detected."
        else: 
            return "Stable", "No significant progression detected in this interval."

    def safety_forecast(self, current_severity):
        forecasts = []
        for hours in [6, 12, 24]:
            projected = min(100, current_severity + (hours * 1.5))
            if projected > 70: safety, color = "Unsafe", "#ff4b4b"
            elif projected > 40: safety, color = "Consume Soon", "#ffa500"
            else: safety, color = "Safe", "#00cc66"
            forecasts.append({"time": f"{hours}h", "safety": safety, "color": color})
            
        return forecasts
