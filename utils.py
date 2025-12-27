"""
Utils: Unified Visual Overlays & Spatial Consensus Mapping
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import cv2
import numpy as np

def apply_visual_overlays(image, spoilage_data, item_info):
    # Feature 8: Unified OpenCV + Streamlit Visualization
    output = image.copy()
    h, w = output.shape[:2]
    
    # 1. Cyber-Vision Corner Brackets
    border_color = (0, 255, 204) # Cyan
    if spoilage_data['risk_level'] == "Medium": border_color = (0, 165, 255) # Orange
    elif spoilage_data['risk_level'] == "High": border_color = (0, 0, 255) # Red
    
    # Draw corner brackets
    length = 50
    # Top Left
    cv2.line(output, (20, 20), (20+length, 20), border_color, 2)
    cv2.line(output, (20, 20), (20, 20+length), border_color, 2)
    # Top Right
    cv2.line(output, (w-20, 20), (w-20-length, 20), border_color, 2)
    cv2.line(output, (w-20, 20), (w-20, 20+length), border_color, 2)
    # Bottom Left
    cv2.line(output, (20, h-20), (20+length, h-20), border_color, 2)
    cv2.line(output, (20, h-20), (20, h-20-length), border_color, 2)
    # Bottom Right
    cv2.line(output, (w-20, h-20), (w-20-length, h-20), border_color, 2)
    cv2.line(output, (w-20, h-20), (w-20, h-20-length), border_color, 2)
    
    # 2. Information Header (Neuro-Identified Name)
    name = item_info['understandable_name']
    cv2.putText(output, f"TARGET: {name}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, border_color, 2)
    cv2.putText(output, f"Q-INDEX: {spoilage_data['freshness_score']:.1f}%", (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, border_color, 1)

    # 3. Dynamic Biological Heatmap
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 100)
    heatmap_base = cv2.GaussianBlur(edges, (31, 31), 0)
    heatmap = cv2.applyColorMap(heatmap_base, cv2.COLORMAP_HOT)
    
    alpha = 0.25
    overlayed = cv2.addWeighted(output, 1 - alpha, heatmap, alpha, 0)
    
    # 4. Mold Cluster Analysis (Synced with Engine)
    # Background Masking (Ignore white studio backgrounds)
    _, bg_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    interest_mask = bg_mask
    
    # 4. Scanline Effect (Spatially consistent)
    for i in range(0, h, 15):
        cv2.line(overlayed, (0, i), (w, i), (0, 0, 0), 1)

    # 5. Mold Cluster Analysis (Synced with Engine)
    # Check if the engine actually reported mold
    reported_strains = spoilage_data.get('mold_types', [])
    if "No Visible Biological Clusters" in reported_strains:
        return overlayed
        
    masks = [
        cv2.bitwise_and(cv2.inRange(hsv, (35, 45, 45), (85, 255, 170)), interest_mask), # Green
        cv2.bitwise_and(cv2.inRange(hsv, (0, 0, 0), (180, 255, 20)), interest_mask),    # Black
        cv2.bitwise_and(cv2.inRange(hsv, (0, 0, 235), (180, 25, 255)), interest_mask)   # White
    ]
    
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            x, y, w_c, h_c = cv2.boundingRect(cnt)
            if x <= 5 or y <= 5 or (x+w_c) >= (w-5): continue
            if area > 1000:
                cv2.drawContours(overlayed, [cnt], -1, (0, 0, 255), 2)
                cv2.putText(overlayed, "BIO-HAZARD", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    return overlayed

