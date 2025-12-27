"""
HoloEngine: 3D Topology Analysis & Structural Decay Forecasting
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

import streamlit as st
import numpy as np
import cv2
import plotly.graph_objects as go
from PIL import Image
import random

# Try imports for Advanced AI
try:
    from transformers import pipeline
    import torch
    # Try importing rembg for advanced background removal
    from rembg import remove
    REMBG_AVAILABLE = True
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    TRANSFORMERS_AVAILABLE = False
    # Check specifically which one failed if needed, but for now we group them
    try:
        from transformers import pipeline
        TRANSFORMERS_AVAILABLE = True
    except ImportError:
        pass

class HoloEngine:
    """
    3D View Engine.
    Features:
    - 3D View (DPT)
    - Remove Background
    - X-Ray View
    """
    
    def __init__(self):
        self.depth_pipe = None
        self.model_status = "Not Loaded"
        
    def _load_depth_pipeline(self):
        """Lazy load Hugging Face Depth Estimation"""
        if not TRANSFORMERS_AVAILABLE: return None
        if self.depth_pipe is None:
            with st.spinner("🔮 Setting up 3D view..."):
                try:
                    device = 0 if torch.cuda.is_available() else -1
                    self.depth_pipe = pipeline(task="depth-estimation", model="Intel/dpt-hybrid-midas", device=device)
                    self.model_status = "Active"
                except Exception as e:
                    st.error(f"Depth AI Load Error: {e}")
                    self.model_status = "Error"
        return self.depth_pipe

    def _remove_background(self, pil_image):
        """
        Uses 'rembg' (if available) or Color/Depth Heuristics to remove background.
        """
        if REMBG_AVAILABLE:
            try:
                # Rembg requires the input to be RGB
                return remove(pil_image)
            except Exception:
                return pil_image # Fallback
        return pil_image # Heuristic fallback would happen in loop

    def generate_topology_mesh(self, image_bgr, item_name="Food", forced_freshness=None, temp=25, humidity=60, is_cut=False):
        """
        Generates a 3D View.
        Features:
        1. Reality View
        2. Shape Map
        3. Cutting Guide
        4. Freshness Stats (Calibrated and Synched)
        """
        if not TRANSFORMERS_AVAILABLE:
            return None, {}, "System Missing: 'transformers' or 'torch'."
            
        pipe = self._load_depth_pipeline()
        if not pipe:
            return None, {}, "3D Model failed to load."
            
        # 1. Prepare Image
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_rgb)
        
        # Remove Background
        if REMBG_AVAILABLE:
             with st.spinner("Finding shape..."):
                try:
                    pil_image_clean = remove(pil_image)
                except Exception:
                    pil_image_clean = pil_image
        else:
             pil_image_clean = pil_image
        
        # 2. Depth Inference
        clean_rgb = pil_image_clean.convert("RGB")
        try:
            result = pipe(clean_rgb)
            depth_map = result["depth"]
        except Exception as e:
            return None, {}, f"Inference Error: {e}"

        # 3. Mesh Generation (Grid Based)
        mesh_res = 100 
        w_orig, h_orig = pil_image_clean.size
        scale = mesh_res / w_orig
        target_height = int(h_orig * scale)
        
        # Resize inputs
        small_color = pil_image_clean.resize((mesh_res, target_height))
        small_depth = depth_map.resize((mesh_res, target_height))
        
        # Data Arrays
        color_arr = np.array(small_color) # RGBA
        depth_arr = np.array(small_depth)
        
        h, w = depth_arr.shape
        
        # Generate Grid Coordinates
        x_grid = np.linspace(0, w, w)
        y_grid = np.linspace(0, h, h)
        xv, yv = np.meshgrid(x_grid, y_grid)
        
        # Flatten basic arrays
        x_flat = xv.flatten()
        y_flat = h - yv.flatten()
        z_flat = depth_arr.flatten() / 255.0 * 60 # Amplify depth
        
        # --- DATA FLATTENING & MASKING ---
        if color_arr.shape[2] == 4:
            alpha_flat = color_arr[:,:,3].flatten()
            mask_valid = alpha_flat > 50
        else:
            mask_valid = np.ones_like(z_flat, dtype=bool)

        r_flat = color_arr[:,:,0].flatten()
        g_flat = color_arr[:,:,1].flatten()
        b_flat = color_arr[:,:,2].flatten()
        
        vertex_colors = [f'rgba({r},{g},{b},{1.0 if m else 0.0})' for r,g,b,m in zip(r_flat, g_flat, b_flat, mask_valid)]
        
        # --- 3D CHECK ---
        # A. Shape Stress (Curvature)
        depth_float = depth_arr.astype(float)
        laplacian = cv2.Laplacian(depth_float, cv2.CV_64F)
        stress_map = np.abs(laplacian)
        
        s_min, s_max = np.percentile(stress_map, 5), np.percentile(stress_map, 95)
        stress_norm = np.clip((stress_map - s_min) / (s_max - s_min + 1e-5), 0, 1)
        stress_flat = stress_norm.flatten()
        
        # B. Visual Defect Confirmation (Color Darkening)
        # Convert to LAB for perceptual lightness analysis
        small_bgr = cv2.cvtColor(color_arr[:,:,:3], cv2.COLOR_RGB2BGR) # Use RGB part
        lab = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2LAB)
        l_channel = lab[:,:,0]
        
        # Invert L so dark spots = high value
        l_inv = 255 - l_channel
        l_norm = l_inv / 255.0
        
        # C. Consensus Logic (Intersection)
        # High Stress AND High Darkness = Structural Failure (Rot/Bruise)
        # Just Stress = Wrinkle (Maybe natural)
        # Just Dark = Surface Spot (Maybe natural)
        failure_map = (stress_norm * 0.7) + (l_norm * 0.3) # Weighted consensus
        failure_flat = failure_map.flatten()
        
        # --- NEW DETAILS (2.1) ---
        # 1. Energy Map (Inverse of Failure + Intensity Boost)
        # Healthy parts have high turgor and bright color
        nutrient_map = (1.0 - failure_map) * (l_channel / 255.0) 
        nutrient_flat = nutrient_map.flatten()
        
        # 2. Defect Depth Penetration (mm)
        # Heuristic: Stress * Factor based on item density
        base_depth_limit = 15 # mm for fruit
        depth_penetration = (failure_map * 20) * (stress_norm * 1.5) # Deeper for high stress
        peak_depth = np.max(depth_penetration)
        
        # 3. Cutting Guide Prediction
        # Find the centroid of the failing mass and draw a dividing plane
        fail_mask = failure_map > 0.4
        cut_plane_x = []
        cut_plane_y = []
        cut_plane_z = []
        
        if np.any(fail_mask):
            # Find the average location of the damage
            fail_coords = np.where(fail_mask)
            cy, cx = np.mean(fail_coords[0]), np.mean(fail_coords[1])
            
            # Draw a "Blade" line at the edge of the damage
            # Simplified: Horizontal/Vertical plane depending on spread
            std_y, std_x = np.std(fail_coords[0]), np.std(fail_coords[1])
            
            if std_x > std_y: # Wider damage, cut vertically
                plane_x = [cx + std_x, cx + std_x]
                plane_y = [0, h]
            else: # Taller damage, cut horizontally
                plane_x = [0, w]
                plane_y = [cy + std_y, cy + std_y]
                
            cut_plane_x = [plane_x[0], plane_x[1], None]
            cut_plane_y = [h - plane_y[0], h - plane_y[1], None]
            cut_plane_z = [0, 60, None] # Extends from bottom to top

        # D. Metrics Calculation (Enhanced)
        avg_stress = np.mean(stress_norm)
        peak_failure = np.max(failure_map)
        
        # Integrity Score (100 = Perfect, 0 = Collapsed)
        integrity_score = 100 - (avg_stress * 40) - (peak_failure * 30)
        
        # --- SYNC LOGIC (v2.6) ---
        if forced_freshness is not None:
             # Force alignment with Scan Tab
             integrity_score = forced_freshness
        
        integrity_score = max(0, min(100, integrity_score))
        
        # Scaling Factor for secondary metrics (Depth, Salvage) based on integrity
        # If integrity is > 90, we should suppress "Ghost" defects
        metric_scale = 1.0
        if integrity_score > 90:
             metric_scale = (100 - integrity_score) / 10 # 0.0 at 100, 1.0 at 90
        
        # --- PHYSICALLY ACCURATE COLLAPSE FORECAST (v3.5) ---
        # Base Hours left to reach structural failure
        if peak_failure > 0.8: # Critical structural breach
            hours_base = 12 + (integrity_score * 0.5) 
        elif peak_failure > 0.5:
            hours_base = 24 + (integrity_score * 1.5)
        else:
            hours_base = 72 + (integrity_score * 2.0)

        # Apply Weather Decay Factors
        # Temp: Every 10 degrees above 20 doubles decay (halves life)
        # Humidity: Moisture accelerates rot
        decay_weather = (2.0 ** ((temp - 20) / 10.0)) * (1.0 + (max(0, humidity - 70) / 100.0))
        
        # Apply Cut Status Accelerator
        if is_cut:
            decay_weather *= 5.0 # Cut items collapse 5x faster
            
        hours_left = hours_base / (decay_weather + 0.1)
             
        # --- SAVE LOGIC ---
        surgical_data = self.analyze_surgical_metrics(mask_valid, failure_flat, stress_flat)
        
        # Apply scaling to prevent ghost defects on fresh items
        surgical_data['peak_depth_mm'] = round(float(peak_depth * metric_scale), 1)
        surgical_data['safety_margin_mm'] = 5.0 * metric_scale
        
        if integrity_score > 92:
             # Force zero waste for excellent items
             surgical_data['salvage_mass'] = 100.0
             surgical_data['waste_mass'] = 0.0
             surgical_data['is_trauma'] = False
        
        # --- COOKING IDEAS ---
        usage_verdict, usage_reason, usage_action = self._get_indian_usage(item_name, integrity_score)
        
        
        metrics = {
            "integrity_score": integrity_score,
            "collapse_hours": hours_left,
            "peak_stress": np.max(stress_norm),
            "status": "Critical" if integrity_score < 70 else "Stable",
            "usage_verdict": usage_verdict,
            "usage_reason": usage_reason,
            "usage_action": usage_action,
            "surgical_data": surgical_data
        }
        # --- VISUAL INTELLIGENCE (Item-Aware Rendering) ---
        item_lower = item_name.lower()
        is_fruit = any(x in item_lower for x in ['apple', 'banana', 'mango', 'pear', 'grape', 'orange', 'papaya', 'pomegranate', 'tomato', 'pepper'])
        
        if is_fruit:
            material_config = dict(ambient=0.4, diffuse=0.6, specular=1.5, roughness=0.1, fresnel=2.0)
            material_name = "Bio-Glass (Fruit)"
        else:
            material_config = dict(ambient=0.6, diffuse=0.8, specular=0.1, roughness=0.9, fresnel=0.1)
            material_name = "Bio-Matte (Veg)"

        # --- MESH GENERATION ---
        i_indices = []
        j_indices = []
        k_indices = []
        
        for r in range(h - 1):
            for c in range(w - 1):
                v1 = r * w + c
                v2 = r * w + (c + 1)
                v3 = (r + 1) * w + c
                v4 = (r + 1) * w + (c + 1)
                
                if not (mask_valid[v1] and mask_valid[v2] and mask_valid[v3] and mask_valid[v4]):
                    continue
                
                # Tri 1
                i_indices.append(v1)
                j_indices.append(v2)
                k_indices.append(v3)
                # Tri 2
                i_indices.append(v2)
                j_indices.append(v4)
                k_indices.append(v3)

        # --- VISUAL LAYERS ---
        # 1. Real
        mesh_reality = go.Mesh3d(
            x=x_flat, y=y_flat, z=z_flat,
            i=i_indices, j=j_indices, k=k_indices,
            vertexcolor=vertex_colors, name="Real", showscale=False,
            lighting=material_config
        )
        
        # 2. Energy
        mesh_nutrient = go.Mesh3d(
            x=x_flat, y=y_flat, z=z_flat,
            i=i_indices, j=j_indices, k=k_indices,
            intensity=nutrient_flat,  colorscale='Greens', 
            name="Energy", showscale=True,
            colorbar=dict(title="Energy", x=1.1),
            visible=False 
        )

        # 3. Risk
        mesh_stress = go.Mesh3d(
            x=x_flat, y=y_flat, z=z_flat,
            i=i_indices, j=j_indices, k=k_indices,
            intensity=failure_flat, colorscale='Reds', 
            name="Risk", showscale=True,
            colorbar=dict(title="Issues"),
            visible=False 
        )
        
        # 4. Guide
        surgical_guide = go.Scatter3d(
            x=cut_plane_x, y=cut_plane_y, z=cut_plane_z,
            mode='lines', line=dict(color='#00FF00', width=10),
            name="Guide", visible=True
        )

        # 5. Spots
        fracture_x = []
        fracture_y = []
        fracture_z = []
        mask_fracture = failure_flat > 0.65
        if np.sum(mask_fracture) > 0:
             fx, fy, fz = x_flat[mask_fracture], y_flat[mask_fracture], z_flat[mask_fracture]
             for i in range(0, len(fx), 2):
                 fracture_x.append(fx[i]); fracture_y.append(fy[i]); fracture_z.append(fz[i] + 1.0)
                 
        fractures = go.Scatter3d(
            x=fracture_x, y=fracture_y, z=fracture_z,
            mode='markers', marker=dict(size=3, color='magenta'),
            name="Spots", visible=False
        )

        fig = go.Figure(data=[mesh_reality, mesh_nutrient, mesh_stress, surgical_guide, fractures])
        
        # No more Plotly Buttons - we handle this via Streamlit UI
        
        fig.update_layout(
            title=dict(text=f"The {item_name}", font=dict(color="#00FFCC", size=20)),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='black',
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, b=0, t=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig, metrics, "Success"

    def analyze_surgical_metrics(self, mask_valid, failure_map, stress_norm):
        """
        Differentiates Systemic Rot from Localized Trauma (Bites/Cuts).
        """
        # 1. Total Volume Analysis
        total_pixels = np.sum(mask_valid)
        if total_pixels == 0: return {"is_trauma": False, "salvage_mass": 0, "waste_mass": 0}
        
        # 2. Failure Analysis
        failure_thresh = 0.6
        failed_pixels = np.sum((failure_map > failure_thresh) & mask_valid)
        
        defect_ratio = failed_pixels / total_pixels
        peak_stress = np.max(stress_norm)
        
        # 3. Trauma Logic (Heuristic)
        # Bites/Cuts are usually: 
        # - Small Area (< 25% of surface)
        # - High Intensity (Deep damage, Peak > 0.8)
        # - High Stress Gradients (Sharp edges, not diffuse rot)
        
        is_trauma = False
        
        if defect_ratio < 0.25 and peak_stress > 0.75:
            # Small area but high stress -> Likely a Bite
            is_trauma = True
        
        # 4. Mass Calculation
        # Assume density is uniform for simplicity
        waste_pct = max(5, defect_ratio * 100 * 1.5) # Add 50% buffer for safety margin
        salvage_pct = 100 - waste_pct
        
        return {
            "is_trauma": is_trauma,
            "salvage_mass": salvage_pct,
            "waste_mass": waste_pct,
            "defect_ratio": defect_ratio
        }

    def _get_indian_usage(self, item_name, score):
        """
        Returns intelligent Indian-Specific Usage recommendations.
        Logic: Item Category (Fruit/Veg) + Structure Score = Specific Desi Dish.
        """
        # 1. Categorize Item (Heuristic)
        item_lower = item_name.lower()
        is_fruit = any(x in item_lower for x in ['apple', 'banana', 'mango', 'pear', 'grape', 'orange', 'papaya', 'pomegranate'])
        is_veg = any(x in item_lower for x in ['tomato', 'onion', 'potato', 'spinach', 'gourd', 'brinjal', 'pepper', 'capsicum'])
        
        # Default Fallback
        cat = "produce"
        if is_fruit: cat = "fruit"
        if is_veg: cat = "veg"

        # 2. Map Integrity to Desi Strategy
        if score > 85:
            # High Integrity (Crunchy/Firm)
            if cat == "fruit":
                verdict = "🥗 MASALA CHAAT / KACHUMBER"
                reason = "Structure is crisp (High Turgor). Do not cook, you will lose the 'Crunch'."
                action = "Chop, sprinkle Chaat Masala and Lemon."
            else: # Veg/General
                verdict = "🥗 FRESH SALAD / RAITA CRUNCH"
                reason = "Perfectly firm. Ideal for adding texture to Raita or eating raw."
                action = "Slice for Kebab side or Kachumber."
                
        elif score > 60:
            # Medium Integrity (Softening/Relaxed)
            if cat == "fruit":
                verdict = "🍹 FRESH JUICE / SHAKE"
                reason = "Structure is relaxing. Juices are accessible. Good for immediate energy."
                action = "Blend with milk or ice."
            else: # Veg
                verdict = "🥘 SHAHI SABZI / DUM PUKHT"
                reason = "Structure softens. Ideal for slow-cooking where it absorbs masala."
                action = "Use in Aloo Gobi or Mix Veg Sabzi."

        else:
            # Low Integrity (Mushy/Fractured) - MASSIVE UTILITY for SAVING FOOD
            if cat == "fruit":
                verdict = "🥣 ROYAL HALWA / KHEER"
                reason = "**Structure Fracture Detected**. Texture is gone. Transform into a rich dessert."
                action = "Mash and slow cook with Ghee, Sugar, and Cardamom (Halwa)."
            else: # Veg
                verdict = "🥣 TADKA CHUTNEY / GRAVY BASE"
                reason = "**Structural Collapse**. Perfect for thickening gravies or making chutneys."
                action = "Puree with Garlic/Chilli for Chutney or Curry Base."
        
        return verdict, reason, action

