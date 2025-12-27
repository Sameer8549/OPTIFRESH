import cv2
import numpy as np

class BionicEngine:
    """
    The Bionic Vision Trinity:
    1. Forensic Scout (CLAHE + Morphology)
    2. Surgical Surgeon (Convex Hull)
    3. Chrono Oracle (Morphological Dilation)
    """
    def __init__(self):
        pass

    def detect_micro_fractures(self, image_bgr):
        """
        FORENSIC SCOUT: Reveals invisible skin damage using CLAHE.
        """
        # 1. Convert to LAB color space
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 2. Apply CLAHE to L-channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        
        # 3. Morphological Gradient to find micro-texture edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        gradient = cv2.morphologyEx(cl, cv2.MORPH_GRADIENT, kernel)
        
        # 4. Color map for visualization (High Contrast)
        # Invert so cracks are dark on light, or use Jet for heat
        heatmap = cv2.applyColorMap(gradient, cv2.COLORMAP_JET)
        
        # Blend with original for context
        enhanced_lab = cv2.merge((cl, a, b))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        final_view = cv2.addWeighted(enhanced_bgr, 0.7, heatmap, 0.3, 0)
        return final_view

    def generate_surgical_guide(self, image_bgr):
        """
        SURGICAL SURGEON: Draws cut-lines using Convex Hulls.
        """
        # 1. simplified segmentation for demo (Thresholding 'not green/fresh')
        # In real world, use YOLO mask. Here, heuristic color segmentation.
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        # Mask for "Not Green/Fresh" (Rot/Spots) - assuming dark/brown
        lower_rot = np.array([0, 50, 0])
        upper_rot = np.array([30, 255, 150]) # Brown/Orange range
        mask = cv2.inRange(hsv, lower_rot, upper_rot)
        
        # Clean noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
        
        surgical_view = image_bgr.copy()
        yield_loss = 0
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # Sort by area
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            for cnt in contours[:2]: # Top 2 defects
                if cv2.contourArea(cnt) < 500: continue
                
                # 2. Convex Hull (The 'Healthy Wrapper')
                hull = cv2.convexHull(cnt)
                
                # 3. Draw Cut Line (Dotted Blue)
                # Visualizing the hull itself as the cut line
                cv2.drawContours(surgical_view, [hull], -1, (255, 0, 0), 2, cv2.LINE_AA)
                
                # Draw bounding box for clearer "Block Removal" guide
                x, y, w, h = cv2.boundingRect(hull)
                cv2.rectangle(surgical_view, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(surgical_view, "CUT", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                
                yield_loss += (w*h)
                
        total_area = image_bgr.shape[0] * image_bgr.shape[1]
        yield_percent = max(0, 100 - int((yield_loss / total_area) * 100))
        
        return surgical_view, yield_percent

    def simulate_decay_spread(self, image_bgr):
        """
        CHRONO ORACLE: Simulates rot spread using Morphological Dilation.
        Returns: [Now, +24h, +48h] images
        """
        # 1. Get base 'Rot Mask'
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        lower_rot = np.array([0, 50, 0])
        upper_rot = np.array([30, 255, 150])
        mask = cv2.inRange(hsv, lower_rot, upper_rot)
        
        # Kernel for expansion
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7)) # Biological shape
        
        timeline = []
        
        # Stage 0: Now
        timeline.append(mask)
        
        # Stage 1: +24 Hrs (Dilate x5)
        future_1 = cv2.dilate(mask, kernel, iterations=5)
        timeline.append(future_1)
        
        # Stage 2: +48 Hrs (Dilate x15)
        future_2 = cv2.dilate(mask, kernel, iterations=15)
        timeline.append(future_2)
        
        # Visualize: Overlay red rot on original image for each stage
        visuals = []
        for stage_mask in timeline:
            vis = image_bgr.copy()
            # Make rot red
            vis[stage_mask > 0] = [0, 0, 150] # Dark Red
            visuals.append(vis)
            
        return visuals
