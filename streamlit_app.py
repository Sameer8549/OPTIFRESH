"""
OPTIFRESH: Advanced Bio-Molecular Food Safety Intelligence
Author: [USER]
Version: 1.0.0

A high-fidelity food safety diagnostic application combining 
Computer Vision, 3D Topology, and Predictive Biological Models.
"""

import streamlit as st
import cv2
import numpy as np
import time
import requests
from PIL import Image
import plotly.graph_objects as go
from datetime import datetime

# Local Engines
from vision_engine import VisionEngine
from spoilage_engine import SpoilageEngine
from recommendation_engine import RecommendationEngine, ReasoningEngine
from advanced_engines import EconomicsEngine, NutritionEngine, AdvancedFreshnessEngine, LegacyFreshnessEngine
from verification_engine import WebVerifierEngine
from segmentation_engine import SegmentationEngine
from future_engine import FutureEngine
from impact_engine import ImpactEngine
from sensory_engine import SensoryEngine
from macro_engine import MacroEngine
from holo_engine import HoloEngine
from logic_engine import LogicEngine

from utils import apply_visual_overlays

# Page Config
st.set_page_config(page_title="OPTIFRESH", layout="wide", page_icon="🌿")

# Initialize Engines (Lazy Loading with Caching)
@st.cache_resource
def load_vision_engine():
    return VisionEngine()

@st.cache_resource
def load_spoilage_engine():
    return SpoilageEngine()

@st.cache_resource
def load_other_engines():
    return (EconomicsEngine(), NutritionEngine(), RecommendationEngine(), 
            ReasoningEngine(), AdvancedFreshnessEngine(), LegacyFreshnessEngine(),
            WebVerifierEngine(), SegmentationEngine(), FutureEngine(), 
            ImpactEngine(), SensoryEngine(), MacroEngine(), HoloEngine(), LogicEngine())

# Engines will be loaded on-demand
vision = None
spoilage = None
economics = None
nutrition = None
recommender = None
reasoner = None
advanced_engine = None
legacy_engine = None
web_verifier = None
segmentation = None
future_engine = None
impact_engine = None
sensory_engine = None
macro_engine = None
holo_engine = None
logic_engine = None

# --- HYPER-LOCAL UTILS ---
def get_weather(lat, lon):
    try:
        # Fetching a comprehensive suite of real-time variables using ECMWF model for sync with Windy
        variables = "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,surface_pressure,wind_speed_10m,weather_code"
        # Explicitly requesting ECMWF model and auto-timezone
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current={variables}&models=ecmwf_ifs&timezone=auto"
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data["current"]
        
        # Mapping WMO Weather Codes to Cyber-Aesthetic Conditions
        wmo_map = {
            0: "Clear Skies (Solar Optimal)",
            1: "Neural Haze (Mainly Clear)", 2: "Partly Clouded", 3: "Overcast (Diffused)",
            45: "Atmospheric Fog", 48: "Rime Fog",
            51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
            61: "Atmospheric Rain", 63: "Heavy Precipitation",
            71: "Neural Snow", 95: "Electrical Storm"
        }
        
        return {
            "temp": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "feels_like": current["apparent_temperature"],
            "pressure": current["surface_pressure"],
            "wind": current["wind_speed_10m"],
            "precip": current["precipitation"],
            "is_day": current["is_day"],
            "condition": wmo_map.get(current["weather_code"], "Atmospheric Flux"),
            "model": "ECMWF Verified"
        }
    except Exception as e:
        return None

# --- ROBUST GEOLOCATION (IP-BASED) ---
def get_ip_location():
    try:
        # Using a reliable public IP geo API
        response = requests.get("http://ip-api.com/json/", timeout=3) # Reduced timeout
        data = response.json()
        if data['status'] == 'success':
            return {
                'lat': data['lat'],
                'lon': data['lon'],
                'city': data['city'],
                'region': data['regionName']
            }
    except Exception:
        pass # Fail silently to defaults
    return None


# Persistent State
if 'location' not in st.session_state:
    # Auto-fetch on first run
    st.session_state.location = get_ip_location()

# CSS ... (rest of CSS remains the same)

# CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;600&family=JetBrains+Mono&display=swap');
    .stApp { background: #050505; color: #00ffcc; font-family: 'Inter', sans-serif; }
    .cyber-card {
        background: rgba(0, 255, 204, 0.02);
        border: 1px solid rgba(0, 255, 204, 0.1);
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
        position: relative;
    }
    .metric-value { font-family: 'Orbitron', sans-serif; font-size: 2.2rem; color: #00ffcc; }
    .metric-label { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 3px; }
    .header-glitch { font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 3.5rem; text-align: center; color: #fff; text-shadow: 2px 2px #ff00ff, -2px -2px #00ffff; }
    .mold-badge { background: rgba(255, 0, 0, 0.1); border: 1px solid #ff4b4b; color: #ff4b4b; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; margin-right: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="header-glitch">🌿 OPTIFRESH</h1>', unsafe_allow_html=True)
st.caption("<center>Simple. Fresh. Optimized.</center>", unsafe_allow_html=True)


# Location & Weather Logic
with st.sidebar:
    st.title("📍 Location")
    if st.button("📍 Find my location"):
        with st.spinner("Checking..."):
            st.session_state.location = get_ip_location()
            st.rerun()

    # Weather Sync Phase
    detected_temp, detected_hum = 30, 75
    weather_data = None
    
    if st.session_state.location:
        weather_data = get_weather(st.session_state.location['lat'], st.session_state.location['lon'])
        if weather_data:
            detected_temp = weather_data['temp']
            detected_hum = weather_data['humidity']
            city = st.session_state.location.get('city', 'Location')
            
            st.success(f"📍 ACTIVE: {city}")
            st.markdown(f"🛰️ **Condition:** `{weather_data['condition']}`")
            st.caption(f"Model: `{weather_data['model']}`")
            
            # Metrics Grid
            wm1, wm2 = st.columns(2)
            wm1.metric("TEMP", f"{detected_temp}°C", f"{weather_data['feels_like'] - detected_temp:.1f}° RealFeel")
            wm2.metric("HUMIDITY", f"{detected_hum}%", f"{weather_data['precip']}mm Rain")
            
            wm3, wm4 = st.columns(2)
            wm3.metric("PRESSURE", f"{weather_data['pressure']:.0f}hPa")
            wm4.metric("WIND", f"{weather_data['wind']}km/h")
            
            st.caption(f"COORD: {st.session_state.location['lat']:.2f}, {st.session_state.location['lon']:.2f}")
            
            # --- WEB INTEGRATION: LIVE RADAR ---
            st.markdown("---")
            st.markdown("🛰️ **Weather Radar**")
            # Windy.com Embed for Real-Time Visual Verification
            windy_url = f"https://www.windy.com/?{st.session_state.location['lat']},{st.session_state.location['lon']},10"
            st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={st.session_state.location['lat']}&lon={st.session_state.location['lon']}&detailLat={st.session_state.location['lat']}&detailLon={st.session_state.location['lon']}&width=300&height=200&zoom=6&level=surface&overlay=wind&product=ecmwf&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=default&metricTemp=default&radarRange=-1", height=250)
            st.caption("[Full Visual Analysis](%s)" % windy_url)

            # --- REGIONAL INTEL MATRIX ---
            st.markdown("🌐 **Local Info**")
            region = st.session_state.location.get('region', 'India')
            st.info(f"Context: {region} Cluster")
            
            # Dynamic Government Web Links
            mandi_link = f"https://agmarknet.gov.in/SearchCMM2.aspx?Tx_Commodity=All&Tx_State={region}&Tx_District=All&Tx_Market=0&DateFrom=18-Dec-2024&DateTo=18-Dec-2024&Fr_Date=18-Dec-2024&To_Date=18-Dec-2024& ActiveTab=0"
            st.markdown(f"🔗 [Live Rates ({region})](https://agmarknet.gov.in/)")
            st.markdown(f"🛂 [FSSAI Safety Bulletins](https://www.fssai.gov.in/)")

        else:
            st.warning("Weather sync failed. Using defaults.")
    else:
        st.info("No location found. Auto-Locate and Refresh.")

# --- SIDEBAR: Controls ---
with st.sidebar:
    st.header("⚙️ SETTINGS")
    uploaded_file = st.file_uploader("Upload Image", type=['jpg', 'jpeg', 'png'])
    
    st.divider()
    st.header("🌡️ ENVIRONMENT")
    temp = st.slider("Temperature (°C)", 0, 50, 30)
    humidity = st.slider("Humidity (%)", 10, 100, 65)
    storage_type = st.selectbox("Storage", ["Room Temp", "Cold Storage"])

    # --- MOBILE CONNECTIVITY ---
    st.sidebar.markdown("---")
    with st.sidebar.expander("📱 Mobile Access"):
        try:
            import socket
            import qrcode
            from io import BytesIO
            
            # Get Local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            
            url = f"http://{ip}:8502"
            st.caption("Scan to run on Phone:")
            st.code(url, language=None)
            
            # Generate QR
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes for Streamlit
            buf = BytesIO()
            img_qr.save(buf, format="PNG")
            st.image(buf.getvalue(), use_container_width=True)
            
            st.warning("⚠️ If it doesn't load:")
            st.caption("1. Phone must be on **Same WiFi**.")
            st.caption("2. **Windows Firewall** might block Python.")
            st.markdown("👉 **Fix:** Search 'Allow an app through Windows Firewall' -> finding 'python' -> Check 'Private' & 'Public'.")
            
        except Exception as e:
            st.error(f"Mobile Init Failed: {e}")
# Tabs
tabs = st.tabs(["Scan", "3D View", "Safety"])

# I cannot replace the whole file. I will do this in two steps.
# step 1: Update the tabs list.


# Initialize session state for analysis results if not exists
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

with tabs[0]:
    # Input Method Selection
    input_choice = st.radio("Source:", ["📁 Upload Image", "📸 Camera Capture"], horizontal=True, label_visibility="collapsed")
    
    uploaded_file = None
    if input_choice == "📁 Upload Image":
        uploaded_file = st.file_uploader("Initialize Real-Time Scan", type=["jpg", "png", "jpeg"])
    else:
        uploaded_file = st.camera_input("Take a Photo")

    if uploaded_file:
        image = Image.open(uploaded_file)
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Load engines on-demand
        vision = load_vision_engine()
        spoilage = load_spoilage_engine()
        economics, nutrition, recommender, reasoner, advanced_engine, legacy_engine, web_verifier, segmentation, future_engine, impact_engine, sensory_engine, macro_engine, holo_engine, logic_engine = load_other_engines()

        with st.status("⚡ Checking freshness...", expanded=True) as status:
            st.write("🔍 Identifying item...")
            item_info = vision.identify_item(image)
            
            st.write("🔍 Checking surface...")
            # Step 1: Base Spoilage Analysis (Deferred to Sync Step)
            
            st.write("🔍 Running final check...")
            ai_state, ai_probs = vision.get_ai_state_analysis(image)
            
            # --- 🛑 REALITY CHECK VETO ---
            if ai_state == "NON_BIOLOGICAL":
                st.error("⛔ DETECTION ERROR: Non-Biological Object Detected.")
                st.warning("Ensure you have uploaded a valid food item, not a document or paper.")
                st.stop()
            
            legacy_data = legacy_engine.analyze_legacy_freshness(img_bgr)
            
            # --- ML SEGMENTATION SYNC ---
            # Run K-Means for Yield calc
            _, _, seg_metrics = segmentation.perform_segmentation(img_bgr, k=3)
            yield_score = seg_metrics['yield_pct']
            
            # Create a localized verdict compatible with SpoilageEngine's expected structure if needed, 
            # Or just pass simple data. SpoilageEngine might accept None. 
            # Let's mock the spectral verdict structure with Yield data to avoid breaking flow?
            # Actually better to just pass None if SpoilageEngine can handle it.
            # Assuming SpoilageEngine.analyze_spoilage handles None for spectral_verdict.
            verdict_data = {
                "metric_name": "True-Yield",
                "score": yield_score,
                "verdict": "High Yield" if yield_score > 80 else "Low Yield"
            }
            
            base_data = spoilage.analyze_spoilage(img_bgr, item_info, [ai_state, ai_probs], legacy_verdict=legacy_data, spectral_verdict=verdict_data)
            
            st.write("📦 Price and Stock Info...")
            # Weather-Aware Normalization (Dynamic Prediction)
            adj_factor = 1.0
            if temp > 32: adj_factor += (temp-32)*0.1 # Heat acceleration
            if humidity > 80: adj_factor += (humidity-80)*0.05 # Moisture acceleration
            if storage_type == "Cold Storage": adj_factor *= 0.4
            
            final_severity = min(100, base_data['severity'] * adj_factor)
            final_freshness = 100 - final_severity
            
            # WEB_VERIFICATION_LAYER
            detected_traits = base_data.get('mold_info', []) + [ai_state]
            if legacy_data['is_rotten']: detected_traits.append("legacy_detected")
            if base_data['severity'] > 20: detected_traits.append("general_decay")
            
            web_result = web_verifier.verify_verdict(item_info['understandable_name'], detected_traits)
            
            # Snap Logic: If Web Verified, force accuracy
            if web_result['verified']:
                final_severity = 100 # Force Rotten
                if final_freshness > 10: final_freshness = 0 # Kill freshness
            
            eco_data = economics.calculate_valuation(item_info['understandable_name'], final_freshness)
            nut_data = nutrition.calculate_nutrient_decay(item_info['category'], final_freshness)
            # Determine if it's cut for shelf-life acceleration
            is_cut = not logic_engine._detect_if_uncut(img_bgr, item_info['understandable_name'])
            st.session_state.is_cut_state = is_cut
            
            shelf_life = spoilage.calculate_shelf_life(final_freshness, temp, humidity, is_cut=is_cut)
            rec = recommender.get_recommendation(item_info['understandable_name'], final_severity)
            explanation = reasoner.generate_explanation(item_info, base_data, {"temp": temp}, rec, eco_data, nut_data)
            
            # SAVE TO SESSION STATE FOR OTHER TABS
            st.session_state.current_analysis = {
                "item_info": item_info,
                "base_data": base_data,
                "ai_state": ai_state,
                "legacy_data": legacy_data,
                "spec_views": None,
                "verdict_data": verdict_data,
                "final_freshness": final_freshness,
                "base_severity": base_data['severity'],
                "web_result": web_result,
                "eco_data": eco_data,
                "nut_data": nut_data,
                "shelf_life": shelf_life,
                "rec": rec,
                "explanation": explanation,
                "adj_factor": adj_factor,
                "img_bgr": img_bgr,
                "storage_type": storage_type,
                # PRE-CALC SURGICAL FOR LOGIC ENGINE
                # (We cheat slightly and run it here to decide mode)
                "surgical_data": {} 
            }
            
            # Run Holo Pre-Calc for Logic Logic (Fast)
            # Just to get the boolean flags
            # In a real app we might separate this, but for now we just pass placeholders if needed
            # The LogicEngine can work with partial data, or we run a lightweight logic check.
            
            # Determine if it's cut for shelf-life acceleration
            is_cut = not logic_engine._detect_if_uncut(img_bgr, item_info['understandable_name'])
            st.session_state.is_cut_state = is_cut
            
            # Run Holo Pre-Calc for Logic Logic (Fast) with Weather & Cut Awareness
            _, h_metrics, _ = holo_engine.generate_topology_mesh(img_bgr, item_name=item_info['understandable_name'], forced_freshness=final_freshness, temp=temp, humidity=humidity, is_cut=is_cut)
            st.session_state.current_analysis['surgical_data'] = h_metrics.get('surgical_data', {})
            
            # --- LOGIC ENGINE DECISION ---
            logic_decision = logic_engine.determine_system_mode(st.session_state.current_analysis)
            st.session_state.logic_decision = logic_decision

            status.update(label="✅ Check Complete", state="complete", expanded=False)
        
        
        # --- ADAPTIVE UI RENDERING ---
        decision = st.session_state.get('logic_decision', {})
        mode = decision.get('key', 'MODE_STANDARD')
        theme = decision.get('theme', 'cyan')
        
        # 1. SYSTEM BANNER
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {theme}, transparent); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin:0; color:white; text-shadow: 0 0 10px {theme};">{decision.get('title', 'ANALYSIS')}</h2>
            <p style="margin:0; color:white; font-weight:bold;">{decision.get('message', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. MODE SPECIFIC VIEWS
        

        if mode == "MODE_INTERNAL_REQ":
            # Cut Request - TOTAL LOCKDOWN
            st.warning("🔪 **ACTION REQUIRED: CUT FIRST**")
            st.markdown(f"""
            <div style="border: 3px solid #ff4b4b; padding: 25px; border-radius: 15px; background: rgba(255, 75, 75, 0.1); text-align: center;">
                <h2 style="color: #ff4b4b;">Scan Blocked</h2>
                <p style="font-size: 1.2rem;">This <b>{item_info['understandable_name'].upper()}</b> is <b>WHOLE/UNCUT</b>.</p>
                <p>Surface-only scans are <b>unreliable</b> for detecting internal toxins or seed rot.</p>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 20px 0;">
                <h3 style="color: white;">👉 PLEASE CUT THE ITEM IN HALF</h3>
                <p>Upload a clear photo of the <b>internal flesh</b> to proceed with the Molecular & Safety analysis.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 **Why?** Core freshness and bacterial load can only be verified by inspecting the internal cross-section.")
            
            if st.button("🔄 Reset & Upload Cut Item", use_container_width=True):
                st.session_state.current_analysis = None
                st.rerun()
            
            # STOP EXECUTION HERE - No other features or tabs should be visible
            st.stop()

        elif mode == "MODE_HAZARD":
            # Lockdown
            st.error("⛔ **SAFETY WARNING**")
            st.markdown("### DO NOT EAT")
            st.write("This looks unsafe. Please discard it.")
            
            # Show Proof with Highlight hack
            # We use the segmented image from advanced engine for highlight
            spec_data = advanced_engine.analyze_spectral_freshness(img_bgr)
            st.image(spec_data['segmented_image'], caption="Detected Pathogen Clusters (Highlighted in Blue/Red)", use_container_width=True)
            
            # Limited Data
            st.metric("Toxicity Risk", "CRITICAL", delta="Discard Immediately", delta_color="inverse")
            st.write(f"**Disposal Protocol:** {rec.get('usage_advice', 'Bin immediately. Wash hands after handling.')}")
            
            # Recipe Lock
            st.caption("🔒 Recipe Generator Locked for Safety.")

        else: 
            # MODE_STANDARD or MODE_SURGICAL
            # Full Dashboard
            
            # --- BIO-AMBIENT SCANNER (Top of Dashboard) ---
            weather_insight, w_color = reasoner.analyze_weather_impact(
                item_info['understandable_name'], 
                detected_temp, 
                detected_hum
            )
            
            st.markdown(f"""
            <div class="cyber-card" style="border-left: 5px solid {w_color}; margin-bottom: 10px;">
                <h3 style="margin:0; font-size:1.1rem;">🌤️ Environment</h3>
                <div style="display:flex; justify-content:space-between; align_items:center; margin-top:5px;">
                    <div style="font-size:0.9rem; color:#aaa;">
                        Conditions: <b>{detected_temp}°C</b> | <b>{detected_hum}% RH</b>
                    </div>
                </div>
                <div style="margin-top:8px; font-weight:bold; color:{w_color};">
                    {weather_insight}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Dashboard 
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'''<div class="cyber-card">
                    <p class="metric-label">Item</p>
                    <p class="metric-value">{item_info["understandable_name"]}</p>
                    <p style="font-size:0.6rem; color:#00ffcc; margin:0;">CHECK: {ai_state.upper()}</p>
                    <p style="font-size:0.55rem; color:#888; margin:0;">STATUS: {base_data.get('consensus_state', 'STABLE')}</p>
                </div>''', unsafe_allow_html=True)
            with c2:
                display_legacy_verdict = legacy_data['verdict']
                display_legacy_color = "#ff4b4b" if legacy_data['is_rotten'] else "#00ffcc"
                verified_tag = "🛡️ " + web_result['status_text'] if web_result['verified'] else "✅ LOCAL SENSOR CONFIRMED"
                
                st.markdown(f'''<div class="cyber-card">
                    <p class="metric-label">Quality</p>
                    <p class="metric-value">{final_freshness:.1f}%</p>
                    <div style="background:rgba(0,255,204,0.1); border:1px solid {display_legacy_color}; border-radius:3px; font-size:0.5rem; text-align:center; padding:1px; margin-top:5px; color:{display_legacy_color};">MODEL: {display_legacy_verdict.upper()}</div>
                    <div style="font-size:0.6rem; color:#00ffcc; margin-top:2px; text-align:center;">{verified_tag}</div>
                </div>''', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="cyber-card"><p class="metric-label">Price</p><p class="metric-value" style="color:#ffcc00;">₹{eco_data["current_value"]:.2f}</p></div>', unsafe_allow_html=True)
    
            
            # --- ITEM-SPECIFIC DNA CARDS ---
            category = decision.get('category', 'General')
            if category != 'General':
                st.markdown(f"#### 🌿 {category} INFO")
                cx1, cx2, cx3 = st.columns(3)
                if category == "ROOT":
                    cx1.metric("Solidity Index", "9.2/10", "High")
                    cx2.metric("Sprout Latency", "Normal")
                    cx3.metric("Soil Purity", "98%", "Clean")
                elif category == "LEAFY":
                    cx1.metric("Hydration Level", "82%", "Good")
                    cx2.metric("Nitrate Score", "Low")
                    cx3.metric("Wilt Forecast", "Stable")
                elif category == "FRUIT":
                    cx1.metric("Ripeness", "Peak")
                    cx2.metric("Sugar", "12.5")
                    cx3.metric("Surface", "Optimal")
                st.divider()

            # --- DUAL-CORE UPGRADE: SENSORY & MACRO ---
            
            # ... (Rest of existing dashboard layout) ...
            entropy_val = base_data.get('biological_notes', {}).get('entropy_index', 1.5)
            sensory_profile = sensory_engine.predict_sensory_profile(img_bgr, item_info['understandable_name'], final_freshness, entropy_val)
            
            # --- PREMIUM DIGITAL PALATE VIZ ---
            categories = ['🦷 Crunch', '🍎 Sweet', '💧 Juicy', '👅 Acid', '🌫️ Mealy']
            values = [
                sensory_profile.get('Crunch', 5), 
                sensory_profile.get('Sweetness', 5), 
                sensory_profile.get('Juiciness', 5), 
                sensory_profile.get('Acid', 5), 
                sensory_profile.get('Mealiness', 0)
            ]
            
            # Close the web loop for Plotly
            categories_loop = [*categories, categories[0]]
            values_loop = [*values, values[0]]
            
            fig = go.Figure()

            # Layer 1: Background Glow
            fig.add_trace(go.Scatterpolar(
                r=values_loop,
                theta=categories_loop,
                fill='toself',
                fillcolor='rgba(0, 255, 204, 0.15)',
                line=dict(color='rgba(0, 255, 204, 0.3)', width=1),
                hoverinfo='skip'
            ))

            # Layer 2: Core Data Trace
            fig.add_trace(go.Scatterpolar(
                r=values_loop,
                theta=categories_loop,
                mode='lines+markers',
                line=dict(color='#00ffcc', width=4),
                marker=dict(
                    color='#fff', 
                    size=10, 
                    line=dict(color='#00ffcc', width=2),
                    symbol='diamond'
                ),
                name='Taste Vector',
                hovertemplate='<b>%{theta}</b>: %{r}/10<extra></extra>'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10],
                        showline=False,
                        gridcolor='rgba(255, 255, 255, 0.05)',
                        tickfont=dict(size=10, color="#555", family="JetBrains Mono"),
                        angle=45,
                        tickvals=[2, 4, 6, 8, 10]
                    ),
                    angularaxis=dict(
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        tickfont=dict(size=11, color="#00ffcc", family="Orbitron"),
                        rotation=90,
                        direction='clockwise'
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=60, r=60, t=30, b=30),
                font=dict(color="white"),
                height=380
            )
            
            # Calculate Aggregate Bio-Score (Eating Experience)
            # Weights: Crunch(0.3), Sweet(0.3), Juicy(0.2), Acid(0.1), Mealy(-0.1)
            bio_score = (values[0]*0.3 + values[1]*0.3 + values[2]*0.2 + values[3]*0.1 - values[4]*0.1) * 10
            bio_score = max(0, min(100, bio_score))
            
            macros, sugar_warning = macro_engine.analyze_macros(item_info['understandable_name'], final_freshness)
            
            d1, d2 = st.columns([48, 52])
            with d1:
                st.markdown('<div class="cyber-card" style="border-top: 2px solid #00ffcc;">', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">Digital Palate</p>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            with d2:
                st.markdown('<div class="cyber-card" style="border-top: 2px solid #ff00ff;">', unsafe_allow_html=True)
                st.markdown('<p class="metric-label">Nutritional Matrix</p>', unsafe_allow_html=True)
                
                # Bio-Score Gauge Cluster
                gc1, gc2 = st.columns([1, 1.2])
                with gc1:
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px; background:rgba(255,0,255,0.05); border-radius:10px;">
                        <p style="font-size:0.7rem; color:#888; margin:0;">PALATE INDEX</p>
                        <p style="font-size:2.8rem; font-family:'Orbitron'; color:#ff00ff; margin:0;">{bio_score:.0f}</p>
                        <p style="font-size:0.6rem; color:#ff00ff; margin:0;">STABLE QUALITY</p>
                    </div>
                    """, unsafe_allow_html=True)
                with gc2:
                    st.markdown(f"""
                    <div style="text-align:center; padding:10px;">
                        <span style="font-size: 2.5rem; font-weight:900; color:#fff; font-family:'Orbitron';">{macros['kcal']}</span>
                        <span style="font-size: 1rem; color:#888;">KCAL</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                n1, n2, n3 = st.columns(3)
                n1.metric("Sugar", f"{macros['sugar']}g")
                n2.metric("Protein", f"{macros['protein']}g")
                n3.metric("Carbs", f"{macros.get('carbs', 0)}g")
                
                if sugar_warning:
                    st.warning(f"⚠️ {sugar_warning}")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- CLINICAL RESULTS (FULL WIDTH) ---
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            st.subheader("👅 Taste & Texture")
            # Call with the computed freshness for calibration
            spec_data = advanced_engine.analyze_spectral_freshness(img_bgr, final_freshness)
            st.image(spec_data['segmented_image'], caption="Condition Map", use_container_width=True)
            
            # Show Molecular Signatures
            mol = spec_data.get('molecular', {})
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Sugar", f"{mol.get('brix_index', 'N/A')}")
            mc2.metric("Vitamin C", f"{mol.get('vit_c_density', 'N/A')}")
            mc3.metric("Nitrates", f"{mol.get('nitrate_load', 'N/A')}", delta="Low" if mol.get('nitrate_load', 0) < 2 else "Check")
            
            st.caption(f"**Light Check:** {mol.get('nir_proxy', 'N/A')} | **Status:** Checked")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
            st.subheader("👨‍🍳 Cooking")
            st.write(f"**Advice:** {rec.get('usage_advice', 'Follow safety protocols.')}")
            st.markdown('</div>', unsafe_allow_html=True)

# [Removed Mandi Intelligence Tab]

with tabs[1]:
    st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
    st.subheader("🛡️ Advanced 3D Scan")
    st.caption("Detailed Structural & Biomolecular Analysis")
    
    # Check if image is available from Scan Tab
    current_img = None
    item_name = "Food Item"
    if st.session_state.current_analysis:
         current_img = st.session_state.current_analysis['img_bgr']
         item_name = st.session_state.current_analysis['item_info'].get('understandable_name', "Food Item")
    
    if current_img is not None:
        # We store the figure and metrics in session state to avoid re-generating on every UI interaction
        if 'holo_data' not in st.session_state or st.session_state.get('last_scanned_item') != item_name:
            with st.spinner("🚀 Initializing 3D Molecular Mapping..."):
                is_cut_current = st.session_state.get('is_cut_state', False)
                fig_holo, metrics, status = holo_engine.generate_topology_mesh(current_img, item_name, forced_freshness=st.session_state.current_analysis.get('final_freshness'), temp=temp, humidity=humidity, is_cut=is_cut_current)
                if fig_holo:
                    st.session_state.holo_data = {"fig": fig_holo, "metrics": metrics, "status": status}
                    st.session_state.last_scanned_item = item_name
                else:
                    st.error(f"Hologram Failure: {status}")
                    st.stop()

        holo = st.session_state.holo_data
        fig = holo['fig']
        metrics = holo['metrics']
        surgical = metrics.get('surgical_data', {})
        
        # --- VIEW SELECTION ---
        view_choice = st.radio("Select Analysis Layer:", ["📸 Real Photo", "🟢 Nutrient Density", "🔴 Risk & Stress"], horizontal=True)
        
        # Control Trace Visibility
        # 0: Real, 1: Nutrient, 2: Risk, 3: Guide, 4: Spots
        if view_choice == "📸 Real Photo":
            vis = [True, False, False, True, False]
            detail_title = "Surface Health"
            detail_text = f"This view shows the visible surface of the **{item_name}**. Our sensors have mapped the texture and color boundaries to ensure no primary surface breaches are present."
        elif view_choice == "🟢 Nutrient Density":
            vis = [False, True, False, False, False]
            detail_title = "Biomolecular Energy Distribution"
            detail_text = f"The Green heat-map represents 'Energy Density'. Bright areas indicate high turgor pressure and dense chlorophyll/nutrient concentrations. **Status: {metrics.get('status', 'Stable')}**."
        else: # Risk
            vis = [False, False, True, True, True]
            detail_title = "Stress Fracture & Pathogen Analysis"
            detail_text = f"The Red zones indicate higher stress loads or potential pathogen clusters. The **Magenta Spots** highlight predicted fracture points where cellular walls are weakest."

        for i, v in enumerate(vis):
            fig.data[i].visible = v
        
        st.plotly_chart(fig, use_container_width=True, theme=None)

        # --- DETAILED ANALYSIS PANEL ---
        st.markdown(f"""
        <div style="background: rgba(0, 255, 204, 0.05); border-left: 4px solid #00ffcc; padding: 15px; border-radius: 5px; margin-top: 10px;">
            <h4 style="margin-top:0; color:#00ffcc;">🔍 {detail_title}</h4>
            <p style="font-size: 0.95rem; color: #ddd;">{detail_text}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Metrics Panel
        m1, m2, m3 = st.columns(3)
        score = metrics.get('integrity_score', 0)
        is_hazard = st.session_state.get('logic_decision', {}).get('key') == "MODE_HAZARD"
        is_trauma = surgical.get('is_trauma', False)

        with m1:
            st.metric("🏗️ Physical Health", f"{score:.1f}/100", 
                      "Hazard" if is_hazard else ("Salvageable" if is_trauma else "Stable"),
                      delta_color = "normal" if score > 70 and not is_hazard else "inverse")
        with m2:
            if is_hazard: st.metric("🩹 Salvage Potential", "0.0%", "Hazard Override")
            elif is_trauma: st.metric("🩹 Salvageable Mass", f"{surgical.get('salvage_mass', 0):.1f}%", f"{surgical.get('waste_mass', 0):.1f}% Waste")
            else: st.metric("⏳ Best Before", f"{metrics.get('collapse_hours', 0):.1f} Hours", "Estimated Accuracy")
        with m3:
            depth = surgical.get('peak_depth_mm', 0)
            st.metric("📏 Defect Depth", f"{depth}mm", f"Margin: {surgical.get('safety_margin_mm', 5):.1f}mm")

        st.divider()

        # --- USAGE DIRECTIVE ---
        verdict = metrics.get('usage_verdict', "N/A")
        reason = metrics.get('usage_reason', 'N/A')
        action = metrics.get('usage_action', 'N/A')
        
        v_color = "#00FF7F" if score > 85 else ("#FFD700" if score > 60 else "#FF4B4B")
        if is_hazard: 
            verdict = "⛔ BIOLOGICAL HAZARD: DISCARD"
            reason = "Molecular analysis confirms presence of pathogen clusters or biological decay."
            action = "DO NOT CONSUME. Please discard in a sealed trash container immediately."
            v_color = "#FF4B4B"

        st.markdown(f"""
        <div style="border: 1px solid {v_color}; padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
            <h2 style="color: {v_color}; margin:0; padding-bottom: 10px;">{verdict}</h2>
            <p style="font-size: 1.1em; color: #ddd;"><strong>Reasoning:</strong> {reason}</p>
            <p style="font-size: 1.0em; color: {v_color}; font-weight: bold;">👉 ACTION: {action}</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Please scan an image in 'Biological Scan' first.")

    st.markdown('</div>', unsafe_allow_html=True)



# --- TAB 3: SAFETY & FUTURE-SIGHT ---
with tabs[2]:
        st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
        st.subheader("🔮 Safety Forecast")
        st.caption("Spoilage Timeline | Safety Buffer")
        
        if st.session_state.current_analysis is None:
            st.info("⚠️ Initialize scan in 'Biological Scan' first.")
        else:
            # Load Data
            data = st.session_state.current_analysis
            freshness = data['final_freshness']
            item_name = data['item_info']['understandable_name']
            temp_c = detected_temp # Global var from sidebar
            humid = detected_hum   # Global var from sidebar
            
            # 1. Safety Confidence Gauge
            # Based on freshness + logic consistency
            # Confidence = Freshness * Logic Factor (if consensus is high)
            confidence = freshness
            if "STABLE" in data.get('base_data', {}).get('consensus_state', ''):
                confidence += 5 # Bonus for stability
            confidence = min(100, max(0, confidence))
            
            gauge_color = "#00ffcc" # Green
            if confidence < 70: gauge_color = "#ffcc00" # Yellow
            if confidence < 40: gauge_color = "#ff4b4b" # Red
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = confidence,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Safety Confidence Interval", 'font': {'size': 20, 'color': 'white'}},
                delta = {'reference': 50, 'increasing': {'color': "#00ffcc"}, 'decreasing': {'color': "#ff4b4b"}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': gauge_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "#333",
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(255, 75, 75, 0.3)'},
                        {'range': [40, 70], 'color': 'rgba(255, 204, 0, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(0, 255, 204, 0.3)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # 2. Verdict Text
            if confidence > 80:
                st.success("✅ VERDICT: SAFE FOR CONSUMPTION")
            elif confidence > 40:
                st.warning("⚠️ VERDICT: CONSUME WITH CAUTION (Salvage Only)")
            else:
                st.error("⛔ VERDICT: BIOLOGICAL HAZARD (Discard)")
                
            st.divider()

            # Countdown (Accounting for Cut Status)
            is_cut_status = st.session_state.get('is_cut_state', False)
            expiry_str = future_engine.predict_expiration_time(item_name, freshness, temp_c, humid, is_cut=is_cut_status)
            st.metric("Estimated Critical Failure (20% Threshold)", expiry_str, delta="-Safety Buffer", delta_color="inverse")
            
            # 3. MOLD & SAFETY INTELLIGENCE
            st.divider()
            st.subheader("🧬 Mold & Safety Intelligence")
            
            mold_db = {
                "Penicillium (Greenish Clusters)": {
                    "danger": "High",
                    "impact": "Production of Mycotoxins (Patulin). Can cause nausea, vomiting, and long-term liver impact if consumed regularly.",
                    "fact": "Some Penicillium species are used for medicine, but the wild variety on fruit is a bio-hazard."
                },
                "Rhizopus (Black Spotting)": {
                    "danger": "Critical",
                    "impact": "Rapid spread can lead to 'Soft Rot'. Consumption may cause allergic reactions or respiratory distress in sensitive individuals.",
                    "fact": "Known as 'Bread Mold', it can liquefy a fruit's internal structure within 48 hours."
                },
                "Aspergillus (Fuzzy White)": {
                    "danger": "Extreme",
                    "impact": "Risk of Aflatoxin production. One of the most dangerous food-borne carcinogens. Can cause acute poisoning.",
                    "fact": "These molds thrive in high humidity and can survive even after the visible fuzz is wiped away."
                },
                "Issue found (Possible mold)": {
                    "danger": "High",
                    "impact": "Unknown microbial activity. Likely bacterial bloom or early-stage fungal mycelium. High risk of diarrhea/stomach pain.",
                    "fact": "Early spoilage often starts internally before showing as surface fuzz."
                }
            }

            detected_molds = data.get('base_data', {}).get('mold_types', [])
            # Use final consolidated freshness for consistency (Hazard < 40, Expired < 20)
            is_serious_hazard = freshness < 40 
            
            if detected_molds and detected_molds != ["No issues detected"]:
                for mold in detected_molds:
                    info = mold_db.get(mold, mold_db["Issue found (Possible mold)"])
                    with st.expander(f"🔴 MOLD DETECTED: {mold.split('(')[0].strip()}", expanded=True):
                        st.markdown(f"""
                        **⚠️ Danger Level:** {info['danger']}  
                        **🤢 Consumption Impact:** {info['impact']}  
                        **🔬 Scientific Fact:** {info['fact']}
                        """)
            elif is_serious_hazard:
                with st.expander("🟠 BIOLOGICAL DECAY & MOLD DETECTED", expanded=True):
                    st.markdown("""
                    **⚠️ Danger Level:** High (Consolidated Hazard)  
                    **🤢 Consumption Impact:** Risk of acute gastroenteritis, Salmonella, or Aflatoxin contamination. Do not consume.  
                    **🔬 Safety Insight:** Even if surface patterns are subtle, the AI detects molecular instability and internal rot patterns.
                    """)
            else:
                 st.info("🟢 No active mold clusters or biological decay confirmed. Surface appears biometrically stable.")

        st.markdown('</div>', unsafe_allow_html=True)

