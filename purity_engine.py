import cv2
import numpy as np

class PurityEngine:
    """
    Simulates 'UV-C' Scan to detect chemical residues, artificial wax, and pesticide coatings.
    """
    def __init__(self):
        pass

    def analyze_surface_contaminants(self, image_bgr, item_name):
        """
        Analyzes specular reflection and surface uniformity to detect artificial coating.
        """
        # 1. Specular Reflection Analysis (Wax Detection)
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # Threshold for very bright spots (glare)
        _, glare_mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
        glare_ratio = cv2.countNonZero(glare_mask) / (gray.shape[0] * gray.shape[1])
        
        wax_risk = "Low"
        wax_score = 10
        if glare_ratio > 0.02: # Too shiny
            wax_risk = "High (Artificial Glazing)"
            wax_score = 90
        elif glare_ratio > 0.005:
            wax_risk = "Moderate (Natural Polish)"
            wax_score = 45
            
        # 2. Pesticide Residue (High Frequency Noise on smooth skin)
        # Laplace Edge Detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        chem_score = int(min(100, variance / 10)) # Heuristic mapping
        chem_risk = "Clean"
        if chem_score > 60: chem_risk = "Trace Residue Detected"
        if chem_score > 150: chem_risk = "High Chemical Load"
        
        return {
            "wax_score": wax_score,
            "wax_risk": wax_risk,
            "chem_score": chem_score,
            "chem_risk": chem_risk,
            "composite_purity": 100 - max(wax_score, chem_score)
        }

    def generate_uv_map(self, image_bgr, contaminant_data):
        """
        Generates a UV-Fluorescence view.
        Normal skin = Purple/Dim.
        Contaminants = Glowing Green/Neon.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        
        # Shift Hue towards "UV Purple" (approx 130-160 range in OpenCV scale if mapped, 
        # but we'll manually tint).
        
        # 1. Create Base UV (dark purple)
        uv_base = np.zeros_like(image_bgr)
        uv_base[:,:] = (60, 0, 80) # Dark purple BGR
        
        # 2. Add structural details from original image (luminance) but tinted purple
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        uv_detail = cv2.merge([gray, gray//2, gray]) # Tinted
        
        # 3. Highlight Contaminants (Glare/Wax spots -> Neon Green)
        _, glare_mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        glare_mask = cv2.GaussianBlur(glare_mask, (9,9), 0)
        
        neon_layer = np.zeros_like(image_bgr)
        neon_layer[:] = (0, 255, 0) # Neon Green
        
        # Blend: Detail + Neon where glare is
        final = cv2.addWeighted(uv_detail, 0.6, uv_base, 0.4, 0)
        
        # Add glow
        if contaminant_data['wax_score'] > 40:
            final = cv2.bitwise_and(final, final, mask=cv2.bitwise_not(glare_mask))
            glowing_glare = cv2.bitwise_and(neon_layer, neon_layer, mask=glare_mask)
            final = cv2.add(final, glowing_glare)
            
        return final
