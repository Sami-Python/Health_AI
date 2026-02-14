import os
from google import genai
from dotenv import load_dotenv
import firestore_manager as db_manager
import secret_loader

# Load API Key
# Prioritizes Env Var, then Secret Manager
api_key = secret_loader.get_secret("GEMINI_API_KEY")

def construct_prompt(ctx, compliance_history="", preference_feedback="", active_goals="", rejected_context=None):
    rejection_text = ""
    if rejected_context:
        rejection_text = f"""
        HUOMIO: Urheilija HYLKÄSI edellisen ehdotuksen.
        Hylätty treeni: {rejected_context.get('activity')} - {rejected_context.get('description')}
        Syy/Muutospyyntö: Urheilija halusi uuden vaihtoehdon. Varmista, että tämä ehdotus on erilainen.
        """
    
    # Interpret Body Battery level
    bb_value = ctx['predicted_charge']
    if bb_value >= 75:
        bb_interpretation = "🟢 ERINOMAINEN - Täysin palautunut, valmis kovaan treeniin"
    elif bb_value >= 60:
        bb_interpretation = "🟡 HYVÄ - Kohtalainen palautuminen, sopii kohtalaiseen treeniin"
    elif bb_value >= 40:
        bb_interpretation = "🟠 MATALA - Heikko palautuminen, suosittele KEVYT/LEPO"
    else:
        bb_interpretation = "🔴 KRIITTINEN - Erittäin huono palautuminen, suosittele LEPO"

    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan tilanne tänään ({ctx['date']}):
    - Body Battery (Palautuminen): {ctx['predicted_charge']:.0f}/100 → {bb_interpretation}
    - Unen kesto: {ctx['sleep_hours']:.1f} tuntia
    - Viimeaikainen kuormitus (7pv keskiarvo): {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}

    {rejection_text}
    
    ⚠️ KRIITTINEN OHJE - Body Battery Tulkinta:
    • 75-100: Erinomainen palautuminen → Suosittele tehokasta treeniä (intervals, kova tempo, pitkä kesto)
    • 60-74: Hyvä palautuminen → Suosittele kohtalaista treeniä (peruskestävyys, kevyt tempo)
    • 40-59: Matala palautuminen → Suosittele KEVYT aktiivinen palautuminen (VR-lenkki, mobility) TAI lepo
    • 0-39: Kriittinen väsymys → Suosittele PAKOLLINEN lepopäivä (Rest Day)
    
    Jos urheilija on subjektiivisesti väsynyt (huono uni, matala BB), ÄLÄ KOSKAAN suosittele kovaa treeniä!
    
    Tehtävä:
    Luo tarkka ja ammattimainen treenisuunnitelma tälle päivälle JSON-muodossa.
    
    TÄRKEÄÄ: Jos 'AKTIIVISET TAVOITTEET' mainitsee tietyn lajin (esim. Juoksu, Pyöräily), painota ohjelmassa kyseistä lajia.

        {{
            "day": 1,
            "activity": "Laji (esim. Juoksu, Pyöräily)",
            "description": "Treenin tavoite",
            "duration_min": 45,
            "load_estimate": 60,
            "structure_summary": "ERITTÄIN LYHYT kaava (Max 15 sanaa). Esim: '10min VR + 40min PK + 5min VR'",
            "detailed_steps": [
                "Alkulämmittely: 10min ...",
                "Työosuus: 40min ...",
                "Loppuverryttely: 5min ..."
            ],
            "garmin_workout": {{
                "workoutName": "AI Coach - [Date]",
                "workoutName": "AI Coach - [Date]",
                "sport": "RUNNING",
                "steps": [
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 1,
                        "intensity": "WARMUP",
                        "description": "Warm up",
                        "durationType": "TIME",
                        "durationValue": 600,
                        "targetType": "HEART_RATE",
                        "targetValueOne": 120,
                        "targetValueTwo": 140
                    }},
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 2,
                        "intensity": "INTERVAL",
                        "description": "Run Hard",
                        "durationType": "DISTANCE",
                        "durationValue": 1000,
                        "targetType": "PACE",
                        "targetValueOne": 240, 
                        "targetValueTwo": 260
                    }}
                ]
            }},
            "tips": "Vinkki"
        }}
    ]

    * garmin_workout:
        - durationType: TIME (seconds), DISTANCE (meters)
        - targetType: HEART_RATE (bpm), PACE (seconds/km), POWER (watts), CADENCE (rpm), NO_TARGET
        - intensity: WARMUP, COOLDOWN, INTERVAL, RECOVERY, REST


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
            "garmin_workout": {{
                "workoutName": "AI Coach - [Date]",
                "sport": "RUNNING",
                "steps": [
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 1,
                        "intensity": "WARMUP",
                        "description": "Warm up",
                        "durationType": "TIME",
                        "durationValue": 600,
                        "targetType": "HEART_RATE",
                        "targetValueOne": 120,
                        "targetValueTwo": 140
                    }},
                     {{
                        "type": "WorkoutStep",
                        "stepOrder": 2,
                        "intensity": "INTERVAL",
                        "description": "Run Hard",
                        "durationType": "DISTANCE",
                        "durationValue": 1000,
                        "targetType": "PACE",
                        "targetValueOne": 240, 
                        "targetValueTwo": 260
                    }}
                ]
            }},
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
        
        # Sort Race first
        goals_list.sort(key=lambda x: x.get('period_type') != 'race')
        
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
                
                if period == 'race':
                    # Special Format
                    lines.append(f"*** KISATAVOITE: {activity} - {desc or 'Kisa'} *** {date_str}. Tavoite: {value} {unit}.")
                else:
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
        error_str = str(e)
        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            print(f"Gemini Policy Error: {e}")
            # Raise a specific error string that main.py can catch
            raise Exception(f"QUOTA_EXCEEDED: {error_str}")
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
