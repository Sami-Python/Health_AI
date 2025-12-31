import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from predict_readiness import predict_latest
from predict_readiness import predict_latest
from predict_readiness import predict_latest
from ai_coach import generate_coach_advice, generate_trend_analysis
import db_manager # New DB Manager
import fetch_garmin_data
import process_garmin_data
import time
from streamlit_calendar import calendar # New Calendar
import base64

# Initialize DB
db_manager.init_db()

# --- Configuration & Styles ---
st.set_page_config(page_title="Personal AI Coach", page_icon="🏃", layout="wide")

st.markdown("""
<style>
    /* Global Variables & Fonts */
    :root {
        --primary-color: #4CAF50;
        --secondary-color: #262730;
        /* Light theme friendly colors */
        --card-bg: #ffffff; 
        --card-border: #f0f2f6;
        --text-color: #31333F;
        --subtext-color: #555;
    }

    /* Metric Cards (Top Row) */
    .metric-card {
        background: var(--card-bg);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid var(--card-border);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); /* Softer shadow */
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-color); /* Dark text */
        margin-top: 5px;
    }
    .metric-label {
        font-size: 13px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 600;
    }

    /* Sidebar & Text */
    /* Removed manual sidebar styling to respect user theme preferences */
    
    /* Modern Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Workout Cards (HTML Containers) */
    .workout-card {
        background: var(--card-bg);
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 15px;
        border: 1px solid var(--card-border);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .workout-card h4 {
        margin-top: 0;
        font-weight: 700;
        color: var(--text-color);
    }
    .structure-box {
        background-color: #f8f9fa; 
        padding: 12px; 
        border-radius: 8px; 
        margin: 10px 0;
        border-left: 3px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)





# --- Helper Functions ---
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def add_bg_from_local(image_file):
    try:
        bin_str = get_base64_of_bin_file(image_file)
        page_bg_img = f"""
        <style>
        .stApp {{
            /* Linear gradient overlay to make it lighter/faded */
            background-image: linear-gradient(rgba(255,255,255,0.7), rgba(255,255,255,0.7)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center top 50px; /* Moved up from 200px */
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Fail silently if image not found

@st.cache_data
def load_historical_data():
    try:
        df = pd.read_csv("Health_AI/data/garmin_merged_features.csv")
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def load_metrics():
    try:
        with open("model_metrics.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Add background image
add_bg_from_local("Health_AI/data/pictures/web_tausta.png")

# --- Load Data Early for Sidebar Info ---
df = load_historical_data()
latest_data_date = "N/A"
if not df.empty:
    latest_data_date = df['date'].max().strftime('%Y-%m-%d')

# --- Sidebar ---
st.sidebar.title("🛠️ Model Status")

# Data Status
st.sidebar.subheader("📅 Data Freshness")
st.sidebar.markdown(f"**Latest Data:** `{latest_data_date}`")

metrics = load_metrics()
if metrics:
    st.sidebar.subheader("🤖 Model Performance")
    st.sidebar.markdown(f"**Valid Accuracy (R²):** `{metrics['r2']:.2f}`")
    st.sidebar.markdown(f"**Mean Error (MAE):** `{metrics['mae']:.2f}`")
    st.sidebar.caption(f"Model Trained: {metrics['last_trained']}")
else:
    st.sidebar.warning("Model metrics not found.")

st.sidebar.divider()
st.sidebar.subheader("🚀 Actions")
if st.sidebar.button("🔄 Päivitä Data"):
    with st.spinner("Haetaan uutta dataa Garminilta..."):
        try:
            fetch_garmin_data.main()
            st.success("Data haettu!")
            
            with st.spinner("Koulutetaan mallia & analysoidaan..."):
                process_garmin_data.main_process()
                st.success("Malli on koulutettu!")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"Virhe päivityksessä: {e}")

st.sidebar.divider()
st.sidebar.subheader("🧠 Active Models")
st.sidebar.markdown("**Recovery Prediction:** `XGBoost (Gradient Boosting Regressor)`")
st.sidebar.markdown("**Coach & Trends:** `Gemini 2.5 Flash`")

st.sidebar.info("Model is updated manually via terminal.")


# --- Main App ---

# Side bar
# ... (omitted)

# Main Title
st.markdown("<h1 style='text-align: left; color: #333;'>🏃 Personal AI Coach</h1>", unsafe_allow_html=True)
st.caption("Data-Driven Recovery & Performance Optimization")

# 1. Predict Today
if 'prediction_context' not in st.session_state:
    with st.spinner("Analyzing physiological data..."):
        try:
            st.session_state.prediction_context = predict_latest()
        except Exception as e:
            st.error(f"Error predicting data: {e}")
            st.session_state.prediction_context = None

ctx = st.session_state.prediction_context

if ctx:
    # --- Top Metrics Row ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Body Battery Gauge
    bb_val = ctx['predicted_charge']
    bb_color = "#4CAF50" if bb_val >= 70 else "#FF9800" if bb_val >= 40 else "#F44336" # Hex for clear green/orange/red
    
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid {bb_color}" title="Ennuste huomisen Body Battery -lataukselle (0-100). Perustuu uneen, stressiin ja aktiivisuuteen.">
            <div class="metric-label">Predicted Charge</div>
            <div class="metric-value" style="color: {bb_color}">{bb_val:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        sleep_h = ctx['sleep_hours']
        st.markdown(f"""
        <div class="metric-card" title="Viime yön unien kokonaiskesto tunteina.">
            <div class="metric-label">Sleep Duration</div>
            <div class="metric-value">{sleep_h:.1f} h</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        load_7d = ctx['recent_load']
        st.markdown(f"""
        <div class="metric-card" title="7 päivän keskiarvo aktiivisista kaloreista. Kertoo treenikuormituksen tasosta.">
            <div class="metric-label">7-Day Load</div>
            <div class="metric-value">{load_7d:.0f} kcal</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        is_poor = ctx.get('poor_night_flag', 0) == 1
        status_text = "POOR" if is_poor else "OK"
        status_color = "#F44336" if is_poor else "#4CAF50"
        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid {status_color}" title="Kertoo putosiko Body Battery yön aikana alle 45.">
            <div class="metric-label">Night Quality</div>
            <div class="metric-value" style="color: {status_color}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Detail Expander ---
    with st.expander("ℹ️ Mihin ennuste (52) perustuu?"):
        st.write("Ennuste on laskettu XGBoost-mallilla käyttäen seuraavia tietoja:")
        dc1, dc2, dc3, dc4 = st.columns(4)
        dc1.metric("Eilinen Stressi", f"{ctx.get('yesterday_stress', 0):.0f}", help="Stressitaso 0-100 (Eilinen)")
        dc2.metric("Eilinen Body Battery", f"{ctx.get('yesterday_charge', 0):.0f}", help="Lataus eilen")
        dc3.metric("Eilinen Aktiivisuus", f"{ctx.get('yesterday_steps', 0):.0f}", "Askeleet")
        dc4.metric("Unen Kesto", f"{ctx.get('sleep_hours', 0):.1f} h", "Viime yö")
        st.caption("*Luku 52 on mallin arvio siitä, kuinka paljon Body Battery latautuu näillä lähtötiedoilla.*")

    # --- AI Coach Section ---
    st.divider()
    
    coach_tab1, coach_tab2 = st.tabs(["📋 Nykyinen ohjelma", "📅 Kalenteri"])
    
    with coach_tab1:
        st.markdown("### 🏃 Päivän Treeniohjelma")
        
        # Duration Selection
        n_days = st.slider("Suunnitelman kesto (päiviä)", 1, 7, 1, help="Valitse kuinka monelle päivälle haluat treeniohjelman.")
        
        # Load existing coach advice from DB
        latest_plan = db_manager.get_latest_plan()
        
        if st.button("Generoi Treeniohjelma"):
            with st.spinner(f"Coach is thinking... (Generoidaan {n_days} pv suunnitelma)"):
                # Fetch compliance history for context
                compliance_history = db_manager.get_compliance_stats()
                
                # Generate advice (now returns JSON string)
                advice_json_str = generate_coach_advice(ctx, n_days=n_days, compliance_history=compliance_history)
                
                try:
                    # Clean up JSON string if it contains markdown formatting
                    clean_json = advice_json_str.replace("```json", "").replace("```", "").strip()
                    advice_data = json.loads(clean_json)
                    
                    # Convert back to string for legacy storage/display if needed, but we rely on daily_workouts now
                    advice_text = "Tarkastele päiväkohtaisia treenejä."
                    
                    # Save Plan & Daily Workouts
                    plan_id = db_manager.save_plan(ctx, advice_text)
                    db_manager.save_daily_workouts(plan_id, advice_data)
                    
                    st.success("Ohjelma luotu! Katso alta.")
                    st.rerun()
                    
                except json.JSONDecodeError:
                    st.error("Virhe tekoälyn vastauksen käsittelyssä. Yritä uudelleen.")
                    st.text(advice_json_str) # Debug view

        # Display latest plan workouts
        if latest_plan:
            workouts = db_manager.get_plan_workouts(latest_plan['id'])
            
            if not workouts:
                # Fallback for old plans without granular workouts
                st.info("💡 Vanha tekstimuotoinen ohjelma:")
                st.markdown(latest_plan['content'])
            else:
                st.markdown(f"**📅 Luotu:** {latest_plan['date']}")
                
                for w in workouts:
                    content = w['content']
                    day_num = content.get('day', w['day'])
                    activity = content.get('activity', 'Treeni')
                    desc = content.get('description', '')
                    
                    # Handle new vs old structure fields
                    # Old: 'structure' (single string)
                    # New: 'structure_summary' (string) + 'detailed_steps' (list)
                    
                    structure_summary = content.get('structure_summary', content.get('structure', ''))
                    detailed_steps = content.get('detailed_steps', [])
                    
                    # Fallback if detailed_steps is empty but we have old structure string
                    if not detailed_steps and content.get('structure'):
                        detailed_steps = [content.get('structure')]

                    tips = content.get('tips', '')
                    status = w['status']
                    
                    # Determine border/bg logic for CSS only (or inline override)
                    # We'll use the .workout-card class but inject specific border colors via inline style for status
                    
                    status_color = "#4CAF50" if status == "DONE" else "#EF5350" if status == "SKIPPED" else "#ddd"
                    
                    # NOTE: Indentation in st.markdown can be interpreted as code blocks. 
                    # We remove indentation for the HTML string to strictly render as HTML.
                    # Colors updated for LIGHT theme (Dark text)
                    html_content = f"""
<div class="workout-card" style="border-left: 5px solid {status_color};">
<h4 style="color:#333; margin:0;">Päivä {day_num}: {activity}</h4>
<p style="margin: 8px 0; color: #555; font-size: 1.05rem;">{desc}</p>
<div class="structure-box">
<span style="color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">KESTO & TEHO</span><br>
<span style="font-weight: 500; font-size: 1.1rem; color: #000;">{structure_summary}</span>
</div>
</div>
"""
                    with st.container():
                        st.markdown(html_content, unsafe_allow_html=True)
                        
                        # Detailed instructions in expander
                        if detailed_steps:
                            with st.expander("Tarkemmat ohjeet", expanded=False):
                                for step in detailed_steps:
                                    st.markdown(f"- {step}")
                                if tips:
                                    st.info(f"💡 Vinkki: {tips}")
                        
                        # Buttons for Pending
                        if status == 'PENDING':
                            c1, c2, c3 = st.columns([1, 1, 4])
                            if c1.button("✅ Tehty", key=f"d_{w['id']}"):
                                db_manager.update_workout_status(w['id'], "DONE")
                                st.rerun()
                            if c2.button("⏭️ Väliin", key=f"s_{w['id']}"):
                                db_manager.update_workout_status(w['id'], "SKIPPED")
                                st.rerun()
                        else:
                            st.caption(f"Status: **{status}**")
                            
                            # Preference UI (Only show for completed/processed items, or always? Let's show always for feedback)
                            # But effectively we want feedback on completed items mostly.
                            # Let's show it always below status.
                            
                            current_pref = w.get('preference', 0)
                            st.write("---")
                            
                            # Confirmation / Thank you message
                            if current_pref > 0:
                                st.success("✅ Kiitos palautteesta! Tämä tieto välitetään tulevien treeniohjelmien suunnitteluun.")

                            st.markdown("**Arvioi treeni (toive jatkoon):**")
                            
                            # 3 columns for 1, 2, 3 stars
                            b1, b2, b3, _ = st.columns([1,1,1,3])
                            
                            def set_pref(wid, val):
                                db_manager.update_workout_preference(wid, val)
                                st.rerun()

                            # Use type="primary" to highlight the selected one
                            t1 = "primary" if current_pref == 1 else "secondary"
                            t2 = "primary" if current_pref == 2 else "secondary"
                            t3 = "primary" if current_pref == 3 else "secondary"
                            
                            lbl1 = "⭐" 
                            lbl2 = "⭐⭐" 
                            lbl3 = "⭐⭐⭐" 
                            
                            if b1.button(lbl1, key=f"p1_{w['id']}", help="Vähemmän näitä", type=t1):
                                set_pref(w['id'], 1)
                            if b2.button(lbl2, key=f"p2_{w['id']}", help="Neutraali / OK", type=t2):
                                set_pref(w['id'], 2)
                            if b3.button(lbl3, key=f"p3_{w['id']}", help="Enemmän näitä", type=t3):
                                set_pref(w['id'], 3)
                                
                            if current_pref == 1:
                                st.caption("Tallennettu: *Vähemmän näitä*")
                            elif current_pref == 3:
                                st.caption("Tallennettu: *Enemmän näitä!*")
    
    with coach_tab2:
        st.subheader("📅 Treenikalenteri")
        try:
            events = db_manager.get_calendar_events()
            
            calendar_options = {
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek"
                },
                "initialView": "dayGridMonth",
                "height": 650,
            }
            
            calendar(events=events, options=calendar_options)
        except Exception as e:
            st.error(f"Kalenterin latausvirhe: {e}")

else:
    st.warning("No prediction available. Check data files.")

st.divider()

# --- Historical Trends ---
st.subheader("📊 Historical Trends")
df = load_historical_data()

if not df.empty:
    # Loading indicator that stays until charts are ready
    status_msg = st.empty()
    status_msg.info(f"Analysoidaan {len(df)} päivän historiaa...")
    
    try:
        df_recent = df.sort_values('date').tail(30)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Recovery & Sleep", "Activity Impact", "🔬 Model Analysis", "📜 Valmennushistoria"])
        
        with tab1:
            plot_df = df_recent.copy()
            
            # Consistent Sleep processing
            if 'totalSleep_minutes' in plot_df.columns:
                 plot_df['Sleep (min)'] = plot_df['totalSleep_minutes']
            elif 'sleepingSeconds' in plot_df.columns:
                plot_df['Sleep (min)'] = plot_df['sleepingSeconds'] / 60.0
            else:
                plot_df['Sleep (min)'] = 0

            # Create thicker line chart
            fig = px.line(plot_df, x='date', y=['bodyBatteryChargedValue', 'Sleep (min)'], 
                          title="Body Battery Charge vs. Sleep",
                          color_discrete_map={"bodyBatteryChargedValue": "#4CAF50", "Sleep (min)": "#2196F3"})
            
            fig.update_traces(line=dict(width=3), mode='lines+markers') # Thicker lines
            fig.update_layout(
                hovermode="x unified",
                font=dict(size=14), # Increased font size
                legend=dict(font=dict(size=14))
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            y_col = 'bodyBatteryChargedValue'
            x_col = 'workout_calories' if 'workout_calories' in df_recent.columns else 'activeKilocalories'
            color_col = 'averageStressLevel' if 'averageStressLevel' in df_recent.columns else None
            
            fig2 = px.scatter(df_recent, x=x_col, y=y_col,
                              color=color_col,
                              title="Workout Load vs. Next Day Charge",
                              size_max=20)
            fig2.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
            fig2.update_layout(
                font=dict(size=14),
                legend=dict(font=dict(size=14))
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            st.markdown("### 🔬 Mallin Analyysi")
            st.markdown("Nämä kuvaajat kertovat, mihin mallin ennusteet perustuvat ja kuinka tarkkoja ne ovat.")
            
            mc1, mc2 = st.columns(2)
            
            with mc1:
                if os.path.exists("Health_AI/outputs/feature_importance.png"):
                    st.image("Health_AI/outputs/feature_importance.png", caption="Feature Importance (Mitkä asiat vaikuttavat eniten?)", use_container_width=True)
                else:
                    st.warning("Feature importance image not found.")
                    
            with mc2:
                 if os.path.exists("Health_AI/outputs/model_performance.png"):
                    st.image("Health_AI/outputs/model_performance.png", caption="Ennuste (Y) vs Todellinen (X)", use_container_width=True)
                 else:
                    st.warning("Model performance image not found.")
        
        with tab4:
             st.markdown("### 📜 Aiemmat Valmennusohjelmat")
             history = db_manager.get_recent_plans(limit=10)
             
             if not history:
                 st.info("Ei aiempaa historiaa.")
             
             for plan in history:
                 with st.container():
                     # Parse timestamp nicely
                     ts_str = str(plan['timestamp']).split('.')[0]
                     st.markdown(f"**📅 {ts_str}** | Ennuste: `{plan['charge']}`")
                     
                     with st.expander("Avaa ohjelma", expanded=False):
                         # Try to fetch granular workouts first
                         workouts = db_manager.get_plan_workouts(plan['id'])
                         if workouts:
                            for w in workouts:
                                content = w['content']
                                activity = content.get('activity', 'Treeni')
                                status = w['status']
                                icon = "✅" if status == "DONE" else "⏭️" if status == "SKIPPED" else "⏳"
                                st.markdown(f"{icon} **Päivä {w['day']}:** {activity}")
                         else:
                            st.info(plan['advice'])
                     
                     st.divider()
            
    except Exception as e:
        st.error(f"Virhe grafiikan piirrossa: {e}")
    finally:
        # Clear loading message once rendered (or failed)
        status_msg.empty()

    # --- AI Trend Analysis ---
    st.divider()
    
    with st.expander("📈 AI Trend Analysis", expanded=False):
        st.subheader("🤖 Trendianalyysi (30 pv)")
        
        # 1. Load existing analysis
        latest_analysis = db_manager.get_latest_analysis()
        cached_analysis = latest_analysis['content'] if latest_analysis else ""
                    
        # 3. Generate Button (Full Width)
        if st.button("🔴 Analysoi Trendit", help="Generoi uusi analyysi (Gemini 2.5)"):
            with st.spinner("Analysoidaan 30 päivän trendejä..."):
                # Prepare data (handle missing columns safely)
                analysis_df = df_recent.copy()
                # Ensure columns exist for the prompt
                if 'totalSleep_minutes' not in analysis_df.columns and 'sleepingSeconds' in analysis_df.columns:
                    analysis_df['totalSleep_minutes'] = analysis_df['sleepingSeconds'] / 60
                
                # Call AI
                new_analysis = generate_trend_analysis(analysis_df)
                
                # Save
                db_manager.save_analysis(new_analysis)
                
                cached_analysis = new_analysis
                st.success("Analyysi valmis! Katso alta:")
        
        # 2. Display existing (or newly generated)
        if cached_analysis:
            st.info("💡 Viimeisin analyysi:")
            st.markdown(cached_analysis)
        else:
            st.info("Ei tallennettua analyysiä. Paina nappia generoidaksesi.")
else:
    st.error("Ei historia-dataa saatavilla (Health_AI/data/garmin_merged_features.csv). Aja 'process_garmin_data.py' ensin.")
