import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from predict_readiness import predict_latest
from ai_coach import generate_coach_advice, generate_trend_analysis

# Page Config
st.set_page_config(
    page_title="Garmin AI Coach",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- CSS for Mobile / Styling ---
# Dark theme optimization: Lighter cards, white text.
st.markdown("""
<style>
    .metric-card {
        background-color: #333333;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #ffffff;
    }
    .metric-label {
        color: #cccccc;
        font-size: 0.9rem;
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
        df = pd.read_csv("garmin_merged_features.csv")
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
st.sidebar.subheader("🧠 Active Models")
st.sidebar.markdown("**Recovery Prediction:** `XGBoost (Gradient Boosting Regressor)`")
st.sidebar.markdown("**Coach & Trends:** `Gemini 2.5 Flash`")

st.sidebar.info("Model is updated manually via terminal.")


# --- Main App ---

st.title("🏃 Garmin AI Coach")
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
    c1, c2, c3 = st.columns(3)
    
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
        
        # Load existing coach advice
        coach_file = "coach_history.json"
        cached_advice = ""
        if os.path.exists(coach_file):
            with open(coach_file, "r") as f:
                try:
                    cached_advice = json.load(f).get("content", "")
                except:
                    pass

        if st.button("Generoi Treeniohjelma"):
            with st.spinner(f"Coach is thinking... (Generoidaan {n_days} pv suunnitelma)"):
                advice = generate_coach_advice(ctx, n_days=n_days)
                
                # Save
                with open(coach_file, "w") as f:
                    json.dump({"content": advice, "date": str(pd.Timestamp.now())}, f)
                
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
    df_recent = df.sort_values('date').tail(30)
    
    tab1, tab2 = st.tabs(["Recovery & Sleep", "Activity Impact"])
    
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
    st.info("No historical data found.")
