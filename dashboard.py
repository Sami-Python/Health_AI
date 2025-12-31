import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from predict_readiness import predict_latest
from ai_coach import generate_coach_advice, generate_trend_analysis
import db_manager # New DB Manager
import fetch_garmin_data
import process_garmin_data
import time
from streamlit_calendar import calendar # New Calendar
import base64
from datetime import datetime, timedelta

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


    # Metrics moved to Home Tab


# --- AI Coach Section ---
st.divider()

coach_tab0, coach_tab1, coach_tab2, coach_tab3, coach_tab4 = st.tabs(["🏠 Etusivu", "📋 Ohjelma", "📅 Kalenteri", "➕ Kirjaa", "🎯 Tavoitteet"])

with coach_tab0:
        if not ctx:
             st.warning("No prediction available. Check data files.")
        
        if ctx:
            st.markdown("### 👋 Tervetuloa Sami!")
            
            # --- Top Metrics Row (Moved here) ---
            c1, c2, c3, c4 = st.columns(4)
            
            # Body Battery Gauge
            bb_val = ctx['predicted_charge']
            bb_color = "#4CAF50" if bb_val >= 70 else "#FF9800" if bb_val >= 40 else "#F44336"
            
            with c1:
                st.markdown(f"""
                <div class="metric-card" style="border: 2px solid {bb_color}">
                    <div class="metric-label">Battery Charge</div>
                    <div class="metric-value" style="color: {bb_color}">{bb_val:.0f}</div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                sleep_h = ctx['sleep_hours']
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Sleep Duration</div>
                    <div class="metric-value">{sleep_h:.1f} h</div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                load_7d = ctx['recent_load']
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">7-Day Load</div>
                    <div class="metric-value">{load_7d:.0f} kcal</div>
                </div>
                """, unsafe_allow_html=True)
            
            with c4:
                is_poor = ctx.get('poor_night_flag', 0) == 1
                status_text = "POOR" if is_poor else "OK"
                status_color = "#F44336" if is_poor else "#4CAF50"
                st.markdown(f"""
                <div class="metric-card" style="border: 2px solid {status_color}">
                    <div class="metric-label">Night Quality</div>
                    <div class="metric-value" style="color: {status_color}">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("ℹ️ Statistiikan tiedot", expanded=False):
                st.write("Datan lähde: Garmin Connect. Ennuste perustuu edellisten päivien kuormitusdataan.")

        st.divider()
        
        # --- Next Workout & Weekly Status ---
        col_next, col_weekly = st.columns([3, 2])
        
        with col_next:
            st.markdown("### 🔜 Seuraava Treeni")
            next_w = db_manager.get_next_workout()
            if next_w:
                content = next_w['content']
                w_act = content.get("activity", "Treeni")
                w_desc = content.get("description", "")
                w_dur = content.get("duration_min", "?")
                w_struct = content.get("structure_summary", "")
                # Format Date
                try:
                    w_date_obj = datetime.strptime(next_w['date'].split(' ')[0], '%Y-%m-%d')
                    date_display = w_date_obj.strftime('%d.%m. (Tänään)' if w_date_obj.date() == datetime.now().date() else '%d.%m.%Y')
                except:
                    date_display = next_w['date']
                    
                st.markdown(f"""
                <div class="workout-card" style="border-left: 6px solid #FF9800; background-color: #fff8e1;">
                    <h3 style="margin:0; color: #E65100;">{w_act} <span style="font-size: 0.8em; color: #666;">({date_display})</span></h3>
                    <p style="font-size: 1.1rem; font-weight: bold; margin: 10px 0;">⏱️ {w_dur} min &nbsp;|&nbsp; {w_struct}</p>
                    <p>{w_desc}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Ei tulevia treenejä kalenterissa. Generoi uusi ohjelma!")
                
        with col_weekly:
             st.markdown("### 📅 Viikon Tilanne")
             weekly_stats = db_manager.get_weekly_stats()
             if weekly_stats:
                dates = sorted(weekly_stats.keys())
                done = sum([weekly_stats[d]['done'] for d in dates])
                manual = sum([weekly_stats[d]['manual'] for d in dates])
                planned = sum([weekly_stats[d]['planned'] for d in dates])
                total_done = done + manual
                
                if planned > 0:
                    pct = min(int((total_done / planned) * 100), 100)
                else:
                    pct = 0
                
                st.metric("Toteutunut Kuormitus", f"{pct}%", f"{total_done} / {planned} Au")
                st.progress(pct / 100)
                st.caption(f"Yhteensä {total_done} kuormitusyksikköä tällä viikolla.")
             else:
                st.caption("Ei dataa.")

with coach_tab1:
        st.markdown("### 🏃 Päivän Treeniohjelma")
        
        # Duration Selection
        n_days = st.slider("Suunnitelman kesto (päiviä)", 1, 7, 1, help="Valitse kuinka monelle päivälle haluat treeniohjelman.")
        
        # Load existing coach advice from DB
        latest_plan = db_manager.get_latest_plan()
        
        if st.button("Generoi Treeniohjelma"):
            with st.spinner(f"Coach is thinking... (Generoidaan {n_days} pv suunnitelma)"):
                # Fetch compliance and preference history
                compliance_history = db_manager.get_compliance_stats()
                preference_history = db_manager.get_preference_history()
                
                # Generate advice (now returns JSON string)
                advice_json_str = generate_coach_advice(ctx, n_days=n_days, compliance_history=compliance_history, preference_feedback=preference_history)
                
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

with coach_tab3:
        st.subheader("➕ Kirjaa Manuaalinen Treeni")
        st.info("Kirjaa treeni, jota ei ollut ohjelmassa tai jonka teit ilman älykelloa.")
        
        with st.form("manual_entry_form"):
            m_date = st.date_input("Päivämäärä", value=datetime.now())
            m_activity = st.selectbox("Laji", ["Juoksu", "Hiihto", "Kuntosali", "Pyöräily", "Uinti", "Kävely", "Muu"])
            m_duration = st.number_input("Kesto (min)", min_value=1, value=45, step=5)
            m_rpe = st.slider("Rasittavuus (RPE 1-10)", 1, 10, 5, help="1 = Todella kevyt, 10 = Maksimi")
            m_notes = st.text_area("Muistiinpanot", placeholder="Fiilikset, sykkeet jne.")
            
            if st.form_submit_button("Tallenna Treeni"):
                db_manager.log_manual_workout(m_date, m_activity, m_duration, m_rpe, m_notes)
                st.success("Treeni tallennettu!")
                st.rerun()

with coach_tab4:
        st.subheader("🎯 Aseta Tavoitteet")
        
        # 1. Add New Goal
        with st.expander("➕ Lisää uusi tavoite", expanded=False):
            with st.form("add_goal_form"):
                g_type = st.selectbox("Tavoitteen tyyppi", [
                    "Juoksu",
                    "Hiihto",
                    "Pyöräily",
                    "Uinti",
                    "Kuntosali",
                    "Viikkokilometrit (Yleinen)", 
                    "Viikon Treenitunnit", 
                    "Unen Keskiarvo (7pv)", 
                    "Painonpudotus / Kehonkoostumus"
                ])
                g_target = st.text_input("Tavoitearvo (esim. 30 km, 8h, 80/100)")
                g_desc = st.text_area("Lisätiedot / Kuvaus", placeholder="Esim. Juokse 30km tällä viikolla rauhallisella sykkeellä.")
                # Default 7 days from now
                default_end = datetime.now() + timedelta(days=7)
                g_end = st.date_input("Määräpäivä", value=default_end)
                
                if st.form_submit_button("Tallenna Tavoite"):
                    if g_target:
                        db_manager.add_goal(g_type, g_target, g_end, g_desc)
                        st.success("Tavoite tallennettu!")
                        st.rerun()
                    else:
                        st.error("Täytä tavoitearvo.")

        # 2. Active Goals List
        st.markdown("### 🏆 Aktiiviset Tavoitteet")
        active_goals = db_manager.get_active_goals()
        
        if not active_goals:
            st.info("Ei aktiivisia tavoitteita. Aseta uusi tavoite yltä.")
        
        for g in active_goals:
            # Calculate time remaining
            try:
                # Handle both datetime and string dates from DB
                if isinstance(g['end'], str):
                    end_date_obj = datetime.strptime(g['end'].split(' ')[0], '%Y-%m-%d')
                else:
                    end_date_obj = g['end']
                    
                days_left = (end_date_obj - datetime.now()).days
            except:
                days_left = "?"
                end_date_obj = datetime.now()

            end_str = end_date_obj.strftime('%d.%m.%Y')
            
            with st.container():
                st.markdown(f"""
                <div class="workout-card" style="border-left: 5px solid #2196F3;">
                    <h4 style="margin:0;">{g['type']}</h4>
                    <p style="font-size: 1.2rem; font-weight: bold; margin: 5px 0;">🎯 {g['target']}</p>
                    <p style="color:#666;">{g['description']}</p>
                    <p style="font-size: 0.9rem; color: {'#F44336' if isinstance(days_left, int) and days_left < 1 else '#4CAF50'}">⏳ Aikaa jäljellä: {days_left} pv ({end_str})</p>
                </div>
                """, unsafe_allow_html=True)
                
                gc1, gc2, _ = st.columns([1, 1, 3])
                if gc1.button("✅ Valmis", key=f"g_done_{g['id']}"):
                    db_manager.complete_goal(g['id'], True)
                    st.rerun()
                if gc2.button("❌ Epäonnistui", key=f"g_fail_{g['id']}"):
                    db_manager.complete_goal(g['id'], False)
                    st.rerun()



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
        
        tab1, tab2, tab5, tab3, tab4 = st.tabs(["Recovery & Sleep", "Activity Impact", "📊 Viikon Kuormitus", "🔬 Model Analysis", "📜 Valmennushistoria"])
        
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

        with tab5:
            st.markdown("### 📊 Viikon Kuormitus (Suunniteltu vs Toteutunut)")
            weekly_stats = db_manager.get_weekly_stats()
            
            if weekly_stats:
                # Convert dict to easy dataframe for Plotly
                # Dict structure: {'2023-12-31': {'planned': 0, 'done': 0, 'manual': 0}}
                dates = sorted(weekly_stats.keys())
                planned = [weekly_stats[d]['planned'] for d in dates]
                done = [weekly_stats[d]['done'] for d in dates]
                manual = [weekly_stats[d]['manual'] for d in dates]
                
                import plotly.graph_objects as go
                
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(name='Suunniteltu', x=dates, y=planned, marker_color='#BDBDBD'))
                fig3.add_trace(go.Bar(name='Tehty (Ohjelma)', x=dates, y=done, marker_color='#4CAF50'))
                fig3.add_trace(go.Bar(name='Tehty (Manuaalinen)', x=dates, y=manual, marker_color='#2196F3'))
                
                fig3.update_layout(barmode='group', title="Viikon Kuormitus (Load = Kesto * Teho)", yaxis_title="Kuormitusyksiköt (Au)")
                st.plotly_chart(fig3, use_container_width=True)
                
                # Compliance donut
                total_planned = sum(planned)
                total_done = sum(done) + sum(manual)
                if total_planned > 0:
                    comp_rate = min(total_done / total_planned * 100, 100) # Cap at 100 visually or show overachievement?
                    st.metric("Toteutunut Kuormitus %", f"{comp_rate:.0f}%", f"{total_done} / {total_planned} yksikköä")
                else:
                    st.info("Ei suunniteltuja treenejä tälle ajalle.")
            else:
                st.info("Ei dataa.")
                        
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
