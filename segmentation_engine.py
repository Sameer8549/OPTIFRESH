"""
SegmentationEngine: Intelligent Background Removal & ROI Extraction
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import cv2
import numpy as np

class SegmentationEngine:
    """
    True-Yield: Real Machine Learning Segmentation.
    Uses K-Means Clustering to mathematically separate Fresh vs Rot pixels.
    No simulations. Pure unsupervised learning on pixel data.
    """
    def __init__(self):
        pass

    def perform_segmentation(self, image_bgr, k=3):
        """
        Runs K-Means Clustering to separate the image into k distinct color regions.
        Returns:
            - quantized_img: Visual representation of clusters.
            - mask_img: Binary mask of the 'Defect' cluster.
            - yield_metrics: Dictionary with Yield %, Defect Area, etc.
        """
        # 1. Pre-process
        # Reshape to 2D array of pixels
        pixel_values = image_bgr.reshape((-1, 3))
        # Convert to float32
        pixel_values = np.float32(pixel_values)

        # 2. Define Criteria & Run K-Means
        # Stop after 100 iterations or accuracy epsilon 0.2
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        
        # k=3 (Fresh, Rot, Background/Shadow)
        _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # 3. Reconstruct Image (Quantized View)
        centers = np.uint8(centers)
        segmented_data = centers[labels.flatten()]
        quantized_img = segmented_data.reshape(image_bgr.shape)

        # 4. Identify Defect Cluster
        # Logic: The 'Rot' cluster is usually darker (Low Value) or distinct Hue compared to 'Fresh'.
        # Assume Background is handled or is one cluster.
        # We look for the cluster that is NOT the background (corners) and NOT the majority fresh color.
        
        # Simple Heuristic: 
        # - Find largest cluster (Fresh).
        # - Find cluster with lowest brightness that isn't the background?
        # - Actually, Rot is often darker than Fresh.
        
        # Let's count labels
        unique, counts = np.unique(labels, return_counts=True)
        cluster_stats = dict(zip(unique, counts))
        total_pixels = image_bgr.shape[0] * image_bgr.shape[1]
        
        # Sort clusters by size
        sorted_clusters = sorted(cluster_stats.items(), key=lambda item: item[1], reverse=True)
        # 0 is largest (Likely Fresh or Background). 1 is mid. 2 is smallest (Likely Defect or Stem).
        
        # Better Heuristic: Analyze Center Colors
        fresh_cluster = None
        defect_cluster = None
        
        # Convert centers to HSV to judge 'Rot-ness'
        centers_hsv = cv2.cvtColor(np.array([centers]), cv2.COLOR_BGR2HSV)[0]
        
        # Assume the cluster with highest Saturation + Value is Fresh?
        # Assume cluster with lowest Value is Rot/Background?
        
        # Let's just create masks for all 3 and let user see, or try to auto-detect.
        # Auto-logic:
        # - Calculate 'Score' for each center: Brightness + Saturation.
        # - Lowest score = Defect? (Rot is dark/brown).
        # - Highest score = Fresh? (Bright/Colorful).
        
        scores = []
        for i, center in enumerate(centers_hsv):
            # Score = Value (Brightness). Rot is dark.
            score = center[2] 
            scores.append((i, score))
            
        scores.sort(key=lambda x: x[1]) # Ascending order of brightness
        
        # Darkest is usually background or deep rot.
        # Brightest is Fresh.
        # Mid is usually transition/rot.
        
        # Let's try to identify the clusters based on size too.
        # If the darkest cluster is HUGE (>50%), it's probably Background (black).
        # We ignore it.
        
        background_idx = -1
        defect_idx = -1
        fresh_idx = -1
        
        for idx, score in scores:
            size_pct = cluster_stats[idx] / total_pixels
            
            # If very large and very dark, it's background
            if size_pct > 0.4 and score < 50:
                background_idx = idx
            else:
                # Evaluating remaining as Food
                pass
                
        # Remainder logic
        remaining = [c[0] for c in scores if c[0] != background_idx]
        
        if len(remaining) >= 2:
            # Between the remaining, the brighter one is Fresh, darker is Defect
            # Sort by score (brightness)
            rem_scores = sorted([(r, centers_hsv[r][2]) for r in remaining], key=lambda x: x[1])
            defect_idx = rem_scores[0][0] # Darker
            fresh_idx = rem_scores[-1][0] # Brighter
        elif len(remaining) == 1:
            fresh_idx = remaining[0]
            # No defect found?
            
        # 5. Calculate Metrics
        fresh_pixels = cluster_stats.get(fresh_idx, 0)
        defect_pixels = cluster_stats.get(defect_idx, 0)
        
        # If we failed to find distinct defect, assume 0
        if defect_idx == -1: defect_pixels = 0
            
        yield_pct = (fresh_pixels / (fresh_pixels + defect_pixels)) * 100 if (fresh_pixels + defect_pixels) > 0 else 0
        
        # 6. Generate Defect Mask
        # Use flat mask first to match labels.flatten() dimension
        flat_mask = np.zeros(image_bgr.shape[0] * image_bgr.shape[1], dtype=np.uint8)
        if defect_idx != -1:
            # Set pixels belonging to defect_idx to 255
            flat_mask[labels.flatten() == defect_idx] = 255
            
        mask = flat_mask.reshape(image_bgr.shape[:2])
        
        # Post-process mask
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        
        return quantized_img, mask, {
            "yield_pct": int(yield_pct),
            "defect_area_px": defect_pixels,
            "fresh_area_px": fresh_pixels,
            "clusters_found": k
        }

    def analyze_verdict(self, metrics):
        """
        Returns a verdict based on Real Yield %.
        """
        yield_pct = metrics['yield_pct']
        
        if yield_pct > 90:
            return "GRADE A (Fresh)", "High yield. Minimal waste detected.", "#00ff00"
        elif yield_pct > 75:
            return "GRADE B (Salvageable)", "Defects detected. Trim required.", "#ffa500"
        else:
            return "GRADE C (Waste)", "Significant spoilage. Low yield.", "#ff0000"
