
import os
import logging
from google import genai
from google.genai import types
from datetime import date
import firestore_manager as db_manager
import firestore_garmin_metrics
import json

logger = logging.getLogger(__name__)

class AIChatManager:
    """
    Manages interactive chat sessions with Gemini Flash,
    providing health context and enforcing guardrails.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Chat features will not work.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            
        # Updated to stable Flash
        self.model_name = "gemini-flash-latest"

    def _get_context_data(self, user_id: str) -> str:
        """
        Fetches relevant recent data to inject into system prompt.
        """
        try:
            # 1. User Profile (Zones, etc.)
            profile = db_manager.get_user_profile(user_id)
            
            # 2. Today's Metrics (if available)
            today = date.today().isoformat()
            metrics = firestore_garmin_metrics.get_user_daily_metrics(user_id, days=1)
            today_metric = metrics[0] if metrics else {}
            
            # 3. Recent Goals - Optional, keep context light for now
            
            context_str = f"""
            USER PROFILE:
            - Age: {profile.get('age', 'Unknown')}
            - Resting HR: {profile.get('resting_heart_rate', 'Unknown')}
            
            LATEST DATA ({today}):
            - Body Battery: {today_metric.get('bodyBatteryChargedValue', 'N/A')} (High), {today_metric.get('bodyBatteryLowestValue', 'N/A')} (Low)
            - Sleep: {today_metric.get('totalSleep_minutes', 0) // 60}h {today_metric.get('totalSleep_minutes', 0) % 60}min
            - Stress: {today_metric.get('averageStressLevel', 'N/A')}/100
            - Training Load (7d avg): {today_metric.get('workout_calories_roll_7d', 'N/A')}
            - Readiness (TSB): {today_metric.get('TSB', 'N/A')}
            """
            return context_str
        except Exception as e:
            logger.error(f"Failed to fetch context: {e}")
            return "CONTEXT: Data unavailable."

    def generate_reply(self, user_id: str, message: str, history: list) -> str:
        """
        Generates a reply using Gemini Flash with Guardrails.
        """
        if not self.client:
            return "AI Service Unavailable (Missing API Key)."

        # 1. Fetch Context
        context = self._get_context_data(user_id)

        # 2. Construct System Instruction (The Guardrails)
        system_instruction = f"""
        ROLE: You are 'Health AI Coach', an elite, empathetic, and data-driven endurance sports coach.
        
        {context}

        GUARDRAILS (STRICT RULES):
        1. SCOPE: You ONLY discuss training, running, cycling, swimming, recovery, sleep, nutrition, and physiology.
        2. REFUSAL: If the user asks about politics, coding, stock market, weather (unless for running), or general trivia -> REFUSE POLITELY.
        3. SAFETY: DO NOT provide medical diagnoses.
        4. DATA AWARENESS: If the context data contains 'N/A' or 'Unknown' for critical metrics, explicitly ask the user to Sync/Refresh their data via the dashboard button.
        5. TONE: Motivating, professional, yet friendly. Provide actionable advice based on available data.
        """

        # 3. Format History
        contents = []
        for msg in history:
            role = 'user' if msg.get('role') == 'user' else 'model'
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.get('content', ''))]
            ))
        
        contents.append(types.Content(
            role='user',
            parts=[types.Part.from_text(text=message)]
        ))

        try:
            # 4. Generate Content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.6, 
                    max_output_tokens=2000, 
                )
            )
            logger.info(f"Gemini Response Length: {len(response.text)}")
            return response.text
        except Exception as e:
            logger.error(f"Gemini Chat Error: {e}")
            return "Sorry, I'm having trouble thinking right now. Please try again."

# Singleton instance
chat_manager = AIChatManager()
