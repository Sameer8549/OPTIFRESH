"""
FutureEngine: Stochastic Decay Simulation & Expiration Countdown
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import pandas as pd
import numpy as np
import cv2
from datetime import datetime, timedelta

class FutureEngine:
    def __init__(self):
        pass

    def predict_decay_curve(self, item_name, current_freshness, temp_c, humidity_percent, is_cut=False):
        """
        Generates a 72-hour decay curve data suitable for charting.
        Returns a Pandas DataFrame.
        """
        # Base decay rate (percent per hour)
        # Higher temp = faster decay.
        # Temp baseline: 20C. Rate doubles every 10C.
        decay_factor = 2.0 ** ((temp_c - 20) / 10.0)
        
        # Humidity effect: Extreme high humidity accelerates mold (accelerates decay), 
        # Extreme low humidity accelerates wilting (also decay).
        # Optimal ~ 85-90% for veg, but we simplify: moisture accelerates rot.
        humid_factor = 1.0 + (max(0, humidity_percent - 70) / 100.0)
        
        base_rate_per_hour = 0.5 * decay_factor * humid_factor
        
        # Specific item logic (very basic)
        if "Banana" in item_name or "Berry" in item_name:
            base_rate_per_hour *= 1.5
        elif "Potato" in item_name or "Onion" in item_name:
            base_rate_per_hour *= 0.2
            
        # --- CUT ITEM ACCELERATION ---
        if is_cut:
            # Cut items decay significantly faster (roughly 4x-6x faster)
            base_rate_per_hour *= 5.0

        hours = list(range(0, 73, 6)) # Every 6 hours up to 3 days
        freshness_points = []
        
        current = current_freshness
        
        timestamps = []
        now = datetime.now()
        
        for h in hours:
            # Non-linear decay (accelerates as it rots)
            # If fresh (>80), decay is slow. If rotting (<50), decay is fast.
            stage_accel = 1.0
            if current < 50: stage_accel = 1.5
            if current < 20: stage_accel = 2.0
            
            loss = base_rate_per_hour * h * stage_accel
            # Not exact integration, just a projection
            val = max(0, current - (base_rate_per_hour * h * stage_accel))
            
            freshness_points.append(val)
            timestamps.append((now + timedelta(hours=h)).strftime("%H:%M"))

        return pd.DataFrame({
            "Time": timestamps,
            "Predicted Freshness": freshness_points
        }).set_index("Time")

    def predict_scenario_comparison(self, item_name, current_freshness, current_temp, current_humidity):
        """
        Generates comparison data for Room Temp vs Optimized Storage.
        """
        # Scenario 1: Current Conditions (Room Temp usually)
        df_current = self.predict_decay_curve(item_name, current_freshness, current_temp, current_humidity)
        
        # Scenario 2: Optimized (Refrigeration/Storage)
        # Assume ideal fridge: 4C, 90% Humidity (crisper)
        df_optimized = self.predict_decay_curve(item_name, current_freshness, 4, 90)
        
        # Merge
        result = pd.DataFrame(index=df_current.index)
        result["Current Environment"] = df_current["Predicted Freshness"]
        result["Optimized Storage (4°C)"] = df_optimized["Predicted Freshness"]
        
        return result

    def predict_expiration_time(self, item_name, current_freshness, temp, humidity, is_cut=False):
        """
        Returns a string representing the estimated Time of Death (0% Freshness).
        """
        # Calculate decay rate per hour
        decay_factor = 2.0 ** ((temp - 20) / 10.0)
        humid_factor = 1.0 + (max(0, humidity - 70) / 100.0)
        base_rate = 0.5 * decay_factor * humid_factor
        
        if "Banana" in item_name or "Berry" in item_name: base_rate *= 1.5
        
        # --- CUT ITEM ACCELERATION ---
        if is_cut:
            # Cut items expire much faster
            base_rate *= 6.0 
        
        if base_rate <= 0: return "Indefinite (Frozen)"
        
        # Hours until freshness hits 20% (Spoiled threshold)
        if current_freshness <= 20: 
            return "ALREADY EXPIRED"
            
        hours_left = (current_freshness - 20) / base_rate
        
        if hours_left < 1: 
            return "Critical (< 1 Hour)"
        
        expiry_date = datetime.now() + timedelta(hours=hours_left)
        
        # Format: "Thursday, 4:30 PM"
        return expiry_date.strftime("%A, %I:%M %p")

    def generate_decay_sequence(self, image_bgr, stages=5):
        """
        Generates a sequence of images simulating progressive decay.
        Returns: List of BGR images.
        """
        sequence = []
        current_img = image_bgr.copy().astype(np.float32)
        h, w = current_img.shape[:2]
        
        # Seed noise for consistent "mold growth"
        np.random.seed(42)
        mold_map = np.random.randint(0, 255, (h, w), dtype=np.uint8)
        _, mold_mask = cv2.threshold(mold_map, 250, 255, cv2.THRESH_BINARY) # Rare spots
        mold_mask = cv2.GaussianBlur(mold_mask, (5,5), 0)
        
        for i in range(stages):
            # 1. Oxidation (Darkening)
            # Subtract constant from all channels
            current_img = cv2.subtract(current_img, np.array([2.0, 3.0, 5.0, 0.0][:3], dtype=np.float32)) 
            
            # 2. Desaturation (Graying out)
            # Convert to HSV, lower Saturation, back to BGR
            temp_u8 = np.clip(current_img, 0, 255).astype(np.uint8)
            hsv = cv2.cvtColor(temp_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:,:,1] *= 0.9 # 10% saturation loss per step
            current_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
            
            # 3. Mold Growth (Spreading Noise)
            # Dilate the mold mask to make spots grow
            kernel = np.ones((3,3), np.uint8)
            mold_mask = cv2.dilate(mold_mask, kernel, iterations=1 + i)
            
            # Overlay Mold (Green/White fuzz)
            # We blend a "mold color" (Grayscale/Greenish) where mask is active
            # Mold color: roughly (200, 220, 200) BGR
            mold_layer = np.zeros_like(current_img)
            mold_layer[:] = [200, 220, 200]
            
            # Extract mold region
            mold_region = cv2.bitwise_and(mold_layer, mold_layer, mask=mold_mask)
            
            # Alpha blend: 0.3 opacity
            # Only where mold exists
            mask_bool = mold_mask > 0
            current_img[mask_bool] = current_img[mask_bool] * 0.7 + mold_layer[mask_bool] * 0.3
            
            # 4. Structural Collapse (Blurring)
            if i > 2:
                current_img = cv2.GaussianBlur(current_img, (3,3), 0)
            
            sequence.append(np.clip(current_img, 0, 255).astype(np.uint8))
            
        return sequence
