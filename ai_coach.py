import os
import google.generativeai as genai
from dotenv import load_dotenv
import db_manager

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


def construct_prompt(ctx, compliance_history="", preference_feedback="", active_goals=""):
    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan tilanne tänään ({ctx['date']}):
    - Ennustettu valmius (Body Battery): {ctx['predicted_charge']:.0f}/100
    - Unen kesto: {ctx['sleep_hours']:.1f} tuntia
    - Viimeaikaie kuormitus (7pv keskiarvo): {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}
    
    Tehtävä:
    Luo tarkka ja ammattimainen treenisuunnitelma tälle päivälle JSON-muodossa.
    
    TÄRKEÄÄ: Jos 'AKTIIVISET TAVOITTEET' mainitsee tietyn lajin (esim. Juoksu, Pyöräily), painota ohjelmassa kyseistä lajia.

    Format (JSON):
    [
        {{
            "day": 1,
            "activity": "Laji (esim. Juoksu)",
            "description": "Treenin tavoite",
            "duration_min": 45,
            "load_estimate": 60,
            "structure_summary": "ERITTÄIN LYHYT kaava (Max 15 sanaa). Esim: '10min VR + 40min PK + 5min VR'",
            "detailed_steps": [
                "Alkulämmittely: 10min ...",
                "Työosuus: 40min ...",
                "Loppuverryttely: 5min ..."
            ],
            "tips": "Vinkki"
        }}
    ]

    * load_estimate: Arvioitu kuormitus 0-100 (TSS-tyyppinen).
    
    Kieli: Suomi.
    """

def construct_multi_day_prompt(ctx, n_days, compliance_history="", preference_feedback="", active_goals=""):
    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan lähtötilanne:
    - Body Battery: {ctx['predicted_charge']:.0f}/100
    - Kuormitus: {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}
    
    Tehtävä:
    Luo progressiivinen ja YKSITYISKOHTAINEN treenisuunnitelma {n_days} päivälle JSON-muodossa.
    
    TÄRKEÄÄ: Jos 'AKTIIVISET TAVOITTEET' mainitsee tietyn lajin (esim. Juoksu, Pyöräily), painota ohjelmassa kyseistä lajia.

    Format (JSON):
    [
        {{
            "day": 1,
            "activity": "Laji",
            "description": "Lyhyt kuvaus tavoitteesta",
            "duration_min": 60,
            "load_estimate": 70,
            "structure_summary": "ERITTÄIN LYHYT kaava (Max 15 sanaa). Esim: '4x4min VK2'",
            "detailed_steps": [
                "Alkulämmittely: ...",
                "Työosuus: ...",
                "Loppuverryttely: ..."
            ],
            "tips": "Vinkki"
        }},
        {{
            "day": 2,
            ...
        }}
    ]
    
    * load_estimate: Arvioitu kuormitus 0-100 (TSS-tyyppinen).
    
    Kieli: Suomi.
    """

def generate_coach_advice(context, n_days=1, compliance_history="", preference_feedback=""):
    """Generates advice using Gemini."""
    if not api_key:
        return "Error: No API Key found in .env file."

    print(f"Calling Gemini Coach (Days: {n_days})...")
    genai.configure(api_key=api_key)
    # Using response_mime_type to enforce JSON
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    
    # Fetch Active Goals
    goals_list = db_manager.get_active_goals()
    goals_text = ""
    if goals_list:
        goals_text = "\n".join([f"- {g['type']}: {g['target']} ({g['description']})" for g in goals_list])
    else:
        goals_text = "Ei asetettuja tavoitteita."

    if n_days > 1:
        prompt = construct_multi_day_prompt(context, n_days, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text)
    else:
        prompt = construct_prompt(context, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text)
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting AI Coach: {e}"

def generate_trend_analysis(df_recent):
    """Analyzes the last 30 days of history."""
    if not api_key:
        return "Error: No API Key found."
    
    print("Thinking (Trend Analysis)...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Prepare data summary
    csv_data = df_recent[['date', 'bodyBatteryChargedValue', 'totalSleep_minutes', 'averageStressLevel', 'workout_calories']].to_csv(index=False)
    
    prompt = f"""
    You are an expert data analyst in sports physiology.
    Here is the last 30 days of data for an athlete (CSV format):
    
    {csv_data}
    
    Task:
    Analyze the trends in Recovery (BodyBattery), Sleep, and Activity.
    1. Identify the strongest correlation (e.g. "Does stress hurt recovery more than lack of sleep?").
    2. Check the weekend vs weekday pattern if visible.
    3. Give a summary of the "Activity Impact" - are high load days followed by poor recovery?
    
    Output in Finnish language. Keep it concise (bullet points).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing trends: {e}"
