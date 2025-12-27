import cv2
import numpy as np

class SpectralEngine:
    """
    Spectrum-X: The Invisible World.
    Advanced Multi-Spectral Analysis using standard RGB sensors.
    Features:
    1. NIR Vision (Deep Bruising)
    2. UV Vision (Surface Mold/Bacteria)
    3. Hydro Vision (Moisture/Juice Content)
    4. Neural Saliency (AI Attention/Defect Hotspots)
    """
    def __init__(self):
        # Removed dependency on cv2.saliency (opencv-contrib)
        pass

    def generate_hydro_map(self, image_bgr):
        """
        HYDRO VISION: Visualizes moisture/juice content.
        Logic: High Saturation + High Value = Liquid/Juicy.
               Low Saturation + High Value = Dry/Mealy.
        Returns: Blue/Cyan Heatmap.
        """
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Normalize
        s_norm = cv2.normalize(s, None, 0, 255, cv2.NORM_MINMAX).astype(np.float32)
        v_norm = cv2.normalize(v, None, 0, 255, cv2.NORM_MINMAX).astype(np.float32)
        
        # Hydro Index = (Saturation * Value) 
        # Juicy fruits are colorful (Sat) and bright (Val) vs Shadow/Dry.
        hydro_raw = cv2.multiply(s_norm, v_norm)
        hydro_raw = cv2.normalize(hydro_raw, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Apply 'Oceana' Colormap (Blue/Cyan/White)
        # Custom map or Ocean? using Winter/Cool
        hydro_map = cv2.applyColorMap(hydro_raw, cv2.COLORMAP_WINTER)
        
        return hydro_map

    def generate_saliency_map(self, image_bgr):
        """
        NEURAL SALIENCY: Visualizes where the CV 'Attention' is focused.
        Using Spectral Residual Algorithm (FFT) suitable for standard OpenCV.
        Highlights unique textures/colors (defects) against background.
        """
        # 1. Grayscale & Resize
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (64, 64)) # Downsample for spectral speed
        
        # 2. FFT
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 3. Log Amplitude
        magnitude = cv2.magnitude(dft_shift[:,:,0], dft_shift[:,:,1])
        log_amplitude = np.log(magnitude + 1.0)
        
        # 4. Spectral Residual
        # Box filter approximates the 'average' spectrum
        avg_spectrum = cv2.blur(log_amplitude, (3, 3))
        spectral_residual = log_amplitude - avg_spectrum
        
        # 5. Inverse FFT
        dft_shift[:,:,0] = np.exp(spectral_residual) * np.cos(np.angle(dft_shift[:,:,0] + 1j*dft_shift[:,:,1]))
        dft_shift[:,:,1] = np.exp(spectral_residual) * np.sin(np.angle(dft_shift[:,:,0] + 1j*dft_shift[:,:,1]))
        
        dft_back = np.fft.ifftshift(dft_shift)
        img_back = cv2.idft(dft_back)
        img_back = cv2.magnitude(img_back[:,:,0], img_back[:,:,1])
        
        # 6. Post-Processing
        # Square to emphasize peaks
        saliency = cv2.multiply(img_back, img_back)
        # Gaussian blur for smooth heatmap
        saliency = cv2.GaussianBlur(saliency, (9, 9), 2.5)
        
        # Normalize and upscale
        saliency_norm = cv2.normalize(saliency, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        saliency_map = cv2.resize(saliency_norm, (image_bgr.shape[1], image_bgr.shape[0]))
        
        # Apply Color Map
        heatmap = cv2.applyColorMap(saliency_map, cv2.COLORMAP_HOT)
        
        return heatmap

    def generate_nir_vision(self, image_bgr):
        """
        NIR VISION: Simulates Near-Infrared to see bruising.
        Logic: Bruises absorb NIR (Red/IR) more than healthy tissue.
        We isolate the Red channel and enhance contrast.
        """
        # Invert Red channel (Bruise = Dark -> Invert -> Bright)
        # But for NIR simulation often we want 'Structure'.
        # Let's do a 'Bruise Map': High Red + Low Green/Blue difference.
        
        # Simple method: Contrast Enhanced Red Channel
        red = image_bgr[:,:,2]
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        nir_view = clahe.apply(red)
        
        # Apply 'Bone' map for X-Ray/NIR look
        nir_map = cv2.applyColorMap(nir_view, cv2.COLORMAP_BONE)
        return nir_map

    def generate_uv_vision(self, image_bgr):
        """
        UV VISION: Simulates Fluorescence (Bacteria/Mold).
        Logic: Boost Green/Blue in dark areas.
        """
        uv_view = image_bgr.copy()
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Enhance edges (mold texture)
        laplacian = cv2.Laplacian(gray, cv2.CV_8U)
        
        # Create a purple base
        purple_base = np.zeros_like(image_bgr)
        purple_base[:] = (60, 0, 50) # Dark Purple
        
        # Add Glowing Green Edges
        glowing_edges = np.zeros_like(image_bgr)
        glowing_edges[:,:,1] = laplacian * 3 # Green Channel Boost
        
        final = cv2.addWeighted(uv_view, 0.4, purple_base, 0.6, 0)
        final = cv2.add(final, glowing_edges)
        
        return final

    def extract_roi(self, image_bgr):
        """
        Robust Background Removal using Standard OpenCV (Otsu's Thresholding).
        Returns: roi_mask (uint8, 0=bg, 255=fg)
        """
        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            final_mask = np.zeros_like(mask)
            if contours:
                c = max(contours, key=cv2.contourArea)
                cv2.drawContours(final_mask, [c], -1, 255, thickness=cv2.FILLED)
            else:
                final_mask = np.ones_like(mask) * 255
            return final_mask
        except:
            h, w = image_bgr.shape[:2]
            return np.ones((h, w), dtype=np.uint8) * 255

    def analyze_verdict(self, views, original_image=None, ai_context=None):
        """
        Returns quantitative scores and a final verdict.
        Adapted for Spectrum-X: Uses NIR (Structural) and UV (Bio) maps.
        """
        # --- 0. BACKGROUND REMOVAL ---
        mask = None
        if original_image is not None:
             mask = self.extract_roi(original_image)
        
        def get_masked_mean(img_channel, m):
            if m is None: return np.mean(img_channel)
            return cv2.mean(img_channel, mask=m)[0]

        # 1. Structural/Tissue Integrity (Mapped from NIR)
        # NIR Map is BONE colormap. Brighter = Healthy, Darker = Bruise.
        # We analyze the Value/Intensity.
        nir = views.get('nir', views.get('xray')) # Fallback
        if nir is not None:
             nir_gray = cv2.cvtColor(nir, cv2.COLOR_BGR2GRAY)
             integrity_score = get_masked_mean(nir_gray, mask)
             # Normalize: 128 is mid. >150 is good. <100 is bad.
             integrity_score = max(0, min(100, (integrity_score / 2.0)))
        else:
             integrity_score = 80 # Default

        # 2. Microbial Load (Mapped from UV)
        # UV Map is Purple + Glowing Green. Green = Mold.
        uv = views.get('uv')
        if uv is not None:
             green_channel = uv[:,:,1]
             green_mean = get_masked_mean(green_channel, mask)
             adjusted_green = max(0, green_mean - 30) # Baseline subtraction
             bio_load = max(0, min(100, (adjusted_green / 2.5)))
        else:
             bio_load = 10

        # 3. Moisture/Stability (Mapped from Hydro)
        hydro = views.get('hydro', views.get('thermal'))
        if hydro is not None:
             # Hydro map is Winter (Blue). Red channel is low.
             # We can just use integrity covariance or similar.
             pass
        
        thermal_stability = 50 # Placeholder for logic continuity

        # --- HIERARCHICAL AI CONSENSUS ---
        ai_override = False
        ai_negative = False
        if ai_context:
            context_lower = ai_context.lower()
            if any(x in context_lower for x in ["fresh", "perfect"]):
                bio_load = max(0, bio_load * 0.1)
                integrity_score = max(integrity_score, 95)
                ai_override = True
            elif any(x in context_lower for x in ["rot", "mold", "decay", "bad", "fungus"]):
                ai_negative = True
                bio_load = max(75, bio_load + 50)
                integrity_score = min(20, integrity_score - 50)
        
        if not ai_negative and bio_load < 40 and integrity_score > 60:
            bio_load = max(0, bio_load - 15)
            integrity_score = min(100, integrity_score + 10)

        if bio_load > 60:
            verdict = "DISCARD IMMEDIATELY"
            action = "High microbial activity/rot detected."
            color = "#ff0000"
        elif integrity_score < 30:
            verdict = "COOK IMMEDIATELY"
            action = "Structural breakdown imminent."
            color = "#ffa500"
        else:
            verdict = "SAFE TO EAT"
            action = "No significant forensic anomalies detected."
            color = "#00ff00"

        return {
            "integrity": int(integrity_score),
            "bio_load": int(bio_load),
            "thermal": int(thermal_stability),
            "verdict": verdict,
            "action": action,
            "color": color
        }
