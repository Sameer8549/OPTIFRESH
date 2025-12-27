"""
AdvancedEngines: Economics, Nutrition, and Legacy Freshness Models
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

class EconomicsEngine:
    def __init__(self):
        # Base prices (simulated ₹/kg or ₹/unit for Indian Mandi)
        self.base_prices = {
            "Tomato": 40.0,
            "Banana": 60.0, # per dozen
            "Apple": 180.0,
            "Mango": 250.0,
            "Paneer": 450.0,
            "Onion": 35.0,
            "Potato": 25.0,
            "Okra": 50.0,
            "Bhindi": 50.0,
            "Milk": 65.0, # per litre
            "Default": 100.0
        }

    def calculate_valuation(self, item_name, freshness_score):
        # Try to find match in base_prices
        base_price = 100.0
        for key, price in self.base_prices.items():
            if key.lower() in item_name.lower():
                base_price = price
                break
        
        # Value drop in Indian market context
        drop_threshold = 30
        effective_freshness = max(0, freshness_score - drop_threshold)
        value_factor = effective_freshness / (100 - drop_threshold)
        
        current_value = base_price * value_factor
        loss_value = base_price - current_value
        
        return {
            "base_price": base_price,
            "current_value": current_value,
            "loss_value": loss_value,
            "loss_percentage": (loss_value / base_price) * 100,
            "currency": "₹"
        }

class NutritionEngine:
    def __init__(self):
        # Baseline nutrient factors for Indian diet
        self.nutrient_map = {
            "Fruit": {"Vitamin C": 100, "Fiber": 80, "Antioxidants": 120},
            "Vegetable": {"Iron": 90, "Folate": 70, "Potassium": 110},
            "Packaged Food": {"Protein": 150, "Calcium": 130, "Energy": 200},
            "Default": {"Vitamins": 100, "Fiber": 100, "Proteins": 100}
        }

    def calculate_nutrient_decay(self, category, freshness_score):
        nutrients = self.nutrient_map.get(category, self.nutrient_map["Default"])
        decay_factor = (freshness_score / 100) ** 1.5
        
        retained = {n: val * decay_factor for n, val in nutrients.items()}
        lost = {n: val * (1 - decay_factor) for n, val in nutrients.items()}
            
        return {
            "retention_rate": decay_factor * 100,
            "retained": retained,
            "lost": lost
        }

import cv2
import numpy as np

class AdvancedFreshnessEngine:
    def __init__(self):
        self.model = None

    def _load_yolo(self):
        from ultralytics import YOLO
        if self.model is None:
            # Load the nano model for speed/accuracy balance
            self.model = YOLO("yolov8n.pt") 

    def _simulate_nir_reflectance(self, rgb_avg):
        """
        Simulates Near-Infrared (NIR) reflectance from RGB data.
        Proxy for cellular density and hydration.
        """
        r, g, b = rgb_avg
        return (0.5 * r + 0.3 * g + 0.2 * b) / 255.0

    def analyze_molecular_signatures(self, img_bgr, mask, freshness_score):
        """
        2.0 Upgrade: Derives molecular chemical signatures using RGB->NIR Re-constuction.
        """
        if img_bgr is None or np.count_nonzero(mask) == 0: return {}
        
        # Calculate mean color of the object only
        avg_bgr = cv2.mean(img_bgr, mask=mask)[:3]
        avg_rgb = avg_bgr[::-1]
        
        nir_proxy = self._simulate_nir_reflectance(avg_rgb)
        
        # Molecular Calibration Math (Simulation of state-of-the-art sensor data)
        # Brix (Sugar) proxy: Correlates with NIR reflectance and color maturity
        brix = (nir_proxy * 12) + (freshness_score / 100.0 * 3) 
        # Vitamin C (Ascorbic Acid): Correlates with Hue stability (Green->Red transition)
        vit_c = (avg_rgb[1] / (avg_rgb[0] + 1e-7)) * 100 
        # Nitrate Load: Correlates with specific Blue reflectance noise in produce
        nitrates = (avg_rgb[2] / (avg_rgb[1] + 1e-7)) * 5
        
        return {
            "brix_index": round(brix, 2),
            "vit_c_density": round(vit_c, 1),
            "nitrate_load": round(nitrates, 2),
            "nir_proxy": round(nir_proxy, 3)
        }

    def analyze_spectral_freshness(self, image, current_freshness=100):
        """
        Performs the 'Internal Quality & Ripeness Scan' with MOLECULAR v2.0 upgrade.
        """
        self._load_yolo()
        
        # 1. YOLO Detection
        results = self.model(image, verbose=False)
        boxes = results[0].boxes
        
        x1, y1, x2, y2 = 0, 0, image.shape[1], image.shape[0]
        detected_label = "Unknown"
        max_area = 0
        for box in boxes:
            b = box.xyxy[0].cpu().numpy().astype(int)
            area = (b[2]-b[0]) * (b[3]-b[1])
            if area > max_area:
                x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
                max_area = area
                detected_label = results[0].names[int(box.cls[0])]

        # 2. GrabCut Segmentation
        mask = np.zeros(image.shape[:2], np.uint8)
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)
        rect = (max(0, x1-5), max(0, y1-5), min(image.shape[1]-x1, x2-x1+10), min(image.shape[0]-y1, y2-y1+10))
        
        try:
            cv2.grabCut(image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
            img_segmented = image * mask2[:, :, np.newaxis]
        except:
            img_segmented = image
            mask2 = np.ones(image.shape[:2], dtype=np.uint8)

        # 3. Molecular Reconstruction (v2.0)
        molecular_data = self.analyze_molecular_signatures(image, mask2, current_freshness)
        
        # 4. Ripeness Detection (HSV)
        hsv = cv2.cvtColor(img_segmented, cv2.COLOR_BGR2HSV)
        active_pixels = (mask2 > 0)
        if np.any(active_pixels):
            mean_hue = np.mean(hsv[:,:,0][active_pixels])
        else:
            mean_hue = 0
            
        ripeness_stage = "Standard"
        ripeness_color = "cyan"
        label_lower = detected_label.lower()
        if "banana" in label_lower:
            if mean_hue < 25: ripeness_stage = "Over-Ripe"; ripeness_color="brown"
            elif mean_hue < 35: ripeness_stage = "Perfectly Ripe"; ripeness_color="gold"
            else: ripeness_stage = "Under-Ripe"; ripeness_color="lightgreen"
        elif "apple" in label_lower:
            if mean_hue < 10 or mean_hue > 160: ripeness_stage = "Ripe"; ripeness_color="red"
            else: ripeness_stage = "Tart / Crispy"; ripeness_color="green"

        # 5. Defect Heatmap (Lab Contrast)
        lab = cv2.cvtColor(img_segmented, cv2.COLOR_BGR2LAB)
        l, _, _ = cv2.split(lab)
        l_inv = cv2.bitwise_not(l)
        l_inv = cv2.bitwise_and(l_inv, l_inv, mask=mask2)
        _, defect_mask = cv2.threshold(l_inv, 210, 255, cv2.THRESH_BINARY)
        
        defect_overlay = img_segmented.copy()
        # Highlight defect clusters in Neon Magenta
        defect_overlay[defect_mask > 0] = [214, 0, 255] 
        
        defect_pct = (np.count_nonzero(defect_mask) / np.count_nonzero(mask2)) * 100 if np.count_nonzero(mask2) > 0 else 0

        return {
            "yolo_label": detected_label,
            "molecular": molecular_data,
            "segmented_image": defect_overlay,
            "raw_segment": img_segmented,
            "mask": mask2,
            "ripeness": {"stage": ripeness_stage, "color": ripeness_color},
            "defect_pct": defect_pct
        }

        
class LegacyFreshnessEngine:
    """
    The 'Old School' Computer Vision Model
    Uses aggressive color thresholding and contour density to detect 'Bad Spots'.
    """
    def __init__(self):
        pass

    def analyze_legacy_freshness(self, image):
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 1. Define 'Rotten' Color Ranges (Aggressive)
        # Green/Blue Mold
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        # Dark Black/Brown Rot
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([180, 255, 60]) # Very dark
        
        # White Fuzz (Tricky, requires context, but legacy model was simple)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        # Create Masks
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)
        mask_white = cv2.inRange(hsv, lower_white, upper_white)
        
        # Combine (Simple OR logic)
        combined_mask = cv2.bitwise_or(mask_green, mask_dark)
        # We exclude white from 'combined' simple mask often because of background, 
        # but let's include it with a strict ROI check in the loop if needed.
        # For legacy 'simple' model, we often just summed pixels.
        
        # Calculate 'Bad' Surface Area
        total_pixels = image.shape[0] * image.shape[1]
        green_pixels = cv2.countNonZero(mask_green)
        dark_pixels = cv2.countNonZero(mask_dark)
        
        # Legacy Rule: If > 5% of surface is 'Bad Color', it's Rotten.
        bad_ratio = (green_pixels + dark_pixels) / total_pixels
        
        is_rotten = False
        confidence = 0
        
        if bad_ratio > 0.05:
            is_rotten = True
            confidence = min(100, bad_ratio * 1000) # Scale up quickly
        
        return {
            "is_rotten": is_rotten,
            "legacy_score": 100 - confidence, # 0 = Rotten, 100 = Fresh
            "bad_ratio": bad_ratio,
            "verdict": "Rotten" if is_rotten else "Fresh"
        }
