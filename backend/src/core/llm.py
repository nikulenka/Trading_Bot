
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_signal(self, context: dict) -> dict:
        """
        Sends technical context to Gemini and returns a structured analysis.
        """
        if not self.model:
            return {"decision": "ERROR", "confidence": 0, "reason": "API Key missing"}

        prompt = f"""
        You are a senior crypto trading analyst. Review the following technical market data for BTC/USDT and validate the potential trade signal.

        Context:
        {json.dumps(context, indent=2)}

        Task:
        1. Analyze the indicators (RSI, MACD, ADX, Support/Resistance).
        2. Determine if the technicals support the strategy's signal.
        3. Identify any major risks or contradictions (e.g., divergence, weak trend).
        
        Output Format (JSON only):
        {{
            "decision": "CONFIRM" or "REJECT" or "NEUTRAL",
            "confidence": float (0.0 to 1.0),
            "reason": "concise explanation (max 1 sentence)",
            "risk_level": "LOW" or "MEDIUM" or "HIGH"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Cleanup markdown if present
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return {"decision": "ERROR", "confidence": 0, "reason": str(e)}
