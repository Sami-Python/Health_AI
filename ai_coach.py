import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


def construct_prompt(ctx):
    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan tilanne tänään ({ctx['date']}):
    - Ennustettu valmius (Body Battery): {ctx['predicted_charge']:.0f}/100
    - Unen kesto: {ctx['sleep_hours']:.1f} tuntia
    - Uniscore: {ctx['sleep_score']}
    - Eilisen stressitaso: {ctx['yesterday_stress']}
    - Viimeaikaie kuormitus (7pv keskiarvo): {ctx['recent_load']:.0f}
    - Huono yö (BodyBattery < 45 yöllä): {'KYLLÄ' if ctx.get('poor_night_flag') == 1 else 'EI'}
    
    Tulkintaohje:
    - Charge < 40: Heikko palautuminen -> Suosittele lepoa tai aktiivista palautumista.
    - Charge 40-70: Kohtalainen -> PK-lenkki tai ylläpitävä treeni.
    - Charge > 70: Hyvä -> Vihreä valo koville tehoille (intervallit/voima).
    
    Tehtävä:
    Kirjoita ytimekäs ja motivoiva treenisuunnitelma tälle päivälle suomeksi.
    1. Analysoi palautumisen tila yhdellä lauseella.
    2. Määrää päivän treeni (Laji, Kesto, Teho).
    3. Anna yksi ravinto- tai elämäntapavinkki tälle päivälle.
    """

def construct_multi_day_prompt(ctx, n_days):
    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilijan lähtötilanne (Päivä 1):
    - Body Battery: {ctx['predicted_charge']:.0f}/100
    - Viimeaikaie kuormitus: {ctx['recent_load']:.0f}
    
    Tehtävä:
    Luo progressiivinen treenisuunnitelma seuraavalle {n_days} päivälle.
    Lähtötaso (Päivä 1) määrää ensimmäisen päivän, ja siitä eteenpäin ohjelman tulisi olla järkevästi jaksotettu (rasitus ja lepo).
    
    Format:
    Päivä 1: [Treeni] - [Perustelu]
    Päivä 2: [Treeni]
    ...
    
    Kieli: Suomi.
    """

def generate_coach_advice(context, n_days=1):
    """Generates advice using Gemini."""
    if not api_key:
        return "Error: No API Key found in .env file."

    print(f"Calling Gemini Coach (Days: {n_days})...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    if n_days > 1:
        prompt = construct_multi_day_prompt(context, n_days)
    else:
        prompt = construct_prompt(context)
    
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
