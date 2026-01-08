import os
from google import genai
from dotenv import load_dotenv
import firestore_manager as db_manager

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def construct_prompt(ctx, compliance_history="", preference_feedback="", active_goals="", rejected_context=None):
    rejection_text = ""
    if rejected_context:
        rejection_text = f"""
        HUOMIO: Urheilija HYLKÄSI edellisen ehdotuksen.
        Hylätty treeni: {rejected_context.get('activity')} - {rejected_context.get('description')}
        Syy/Muutospyyntö: Urheilija halusi uuden vaihtoehdon. Varmista, että tämä ehdotus on erilainen.
        """

    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan tilanne tänään ({ctx['date']}):
    - Ennustettu valmius (Body Battery): {ctx['predicted_charge']:.0f}/100
    - Unen kesto: {ctx['sleep_hours']:.1f} tuntia
    - Viimeaikaie kuormitus (7pv keskiarvo): {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}

    {rejection_text}
    
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

def generate_coach_advice(user_id, context, n_days=1, compliance_history="", preference_feedback="", rejected_context=None):
    """Generates advice using Gemini."""
    if not api_key:
        return "Error: No API Key found in .env file."

    print(f"Calling Gemini Coach (Days: {n_days})...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Fetch Active Goals
        goals_list = db_manager.get_active_goals(user_id)
        goals_text = ""
        if goals_list:
            lines = []
            for g in goals_list:
                activity = g.get('activity_type', 'Unknown')
                value = g.get('target_value', 0)
                unit = g.get('target_unit', '')
                period = g.get('period_type', g.get('frequency', 'weekly'))
                date_str = f"- Date: {g.get('target_date')}" if g.get('target_date') else ""
                desc = f"({g.get('description', '')})" if g.get('description') else ""
                lines.append(f"- {activity}: {value} {unit} ({period}) {date_str} {desc}")
            goals_text = "\n".join(lines)
        else:
            goals_text = "Ei asetettuja tavoitteita."

        if n_days > 1:
            prompt = construct_multi_day_prompt(context, n_days, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text)
        else:
            prompt = construct_prompt(context, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text, rejected_context=rejected_context)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        return response.text
    except Exception as e:
        return f"Error contacting AI Coach: {e}"

def generate_trend_analysis(df_recent):
    """Analyzes the last 30 days of history."""
    if not api_key:
        return "Error: No API Key found."
    
    print("Thinking (Trend Analysis)...")
    
    try:
        client = genai.Client(api_key=api_key)
        
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
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error analyzing trends: {e}"

def generate_daily_insight(ctx):
    """
    Generates a short, daily coaching insight (1-2 sentences) based on metrics.
    """
    if not api_key:
        return "API Key missing. Cannot generate insight."
        
    prompt = f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Analysoi seuraavat mittarit ja anna YKSI TAI KAKSI tiivistä, motivoivaa lausetta siitä, miten urheilijan tulisi tänään toimia (levätä, treenata kovaa, palautella?).
    
    Mittarit:
    - TSB (Training Stress Balance / Vireystila): {ctx.get('tsb', 0)} (Positiivinen = Tuore, Negatiivinen = Rasittunut)
    - Body Battery (Lataus): {ctx.get('readiness', 0)}/100
    - Uni: {ctx.get('sleep_min', 0) / 60:.1f} tuntia
    - Krooninen kuormitus (CTL): {ctx.get('ctl', 0)}
    
    Ohje:
    - Pidä vastaus erittäin lyhyenä (max 30 sanaa).
    - Ole suora ja selkeä.
    - Kieli: Suomi.
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.replace('"', '').strip() # Clean quotes
    except Exception as e:
        print(f"Insight Error: {e}")
        return "Tänään on hyvä päivä kuunnella kehoa."
