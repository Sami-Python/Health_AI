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

# Initialize DB
db_manager.init_db()

# --- Configuration & Styles ---
st.set_page_config(page_title="Sami's AI Coach", page_icon="🏃", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        text_align: center;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        color: white;
    }
    .metric-label {
        font-size: 14px;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Sidebar Text Size Increase */
    [data-testid="stSidebar"] {
        font_size: 1.2rem;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        font-size: 1.1rem !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 60px;
        font-size: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
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

st.title("🏃 Sami's AI Coach")
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
    with st.expander("🤖 Coach Advice (Treeniohjelma)", expanded=True):
        st.markdown("### 🏃 Päivän Treeniohjelma")
        
        # Duration Selection
        n_days = st.slider("Suunnitelman kesto (päiviä)", 1, 7, 1, help="Valitse kuinka monelle päivälle haluat treeniohjelman.")
        
        # Load existing coach advice from DB
        cached_advice = ""
        latest_plan = db_manager.get_latest_plan()
        if latest_plan:
            cached_advice = latest_plan.get("content", "")

        if st.button("Generoi Treeniohjelma"):
            with st.spinner(f"Coach is thinking... (Generoidaan {n_days} pv suunnitelma)"):
                advice = generate_coach_advice(ctx, n_days=n_days)
                
                # Save to DB
                db_manager.save_plan(ctx, advice)
                
                st.success("Plan Generated!")
                st.markdown(advice)
                cached_advice = advice # Update view immediately
        
        # Display existing if available (and not just generated to avoid dupes, logic handles via variable)
        elif cached_advice:
            st.info("💡 Viimeisin ohjelma:")
            st.markdown(cached_advice)

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

            # Duplicate chart removed

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
                         st.info(plan['advice'])
                     
                     # Status actions
                     status = plan.get('status', 'PENDING')
                     
                     # Check if status is None (legacy data)
                     if status is None: 
                         status = 'PENDING'

                     if status == 'PENDING':
                         c_h1, c_h2, c_h3 = st.columns([1, 1, 3])
                         if c_h1.button("✅ Tehty", key=f"done_{plan['id']}"):
                             db_manager.update_plan_status(plan['id'], "DONE")
                             st.rerun()
                         if c_h2.button("⏭️ Väliin", key=f"skip_{plan['id']}"):
                              db_manager.update_plan_status(plan['id'], "SKIPPED")
                              st.rerun()
                     else:
                         color = "green" if status == "DONE" else "orange"
                         st.markdown(f"Status: **:{color}[{status}]**")
                     
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
        analysis_file = "analysis_history.json"
        cached_analysis = ""
        if os.path.exists(analysis_file):
            with open(analysis_file, "r") as f:
                try:
                    cached_analysis = json.load(f).get("content", "")
                except:
                    pass
                    
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
                with open(analysis_file, "w") as f:
                    json.dump({"content": new_analysis, "date": str(pd.Timestamp.now())}, f)
                
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
