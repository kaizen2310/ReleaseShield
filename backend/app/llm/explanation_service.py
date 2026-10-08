import json
from typing import Dict, Any
from google import genai
from google.genai import types
from app.config import settings

class LLMExplanationService:
    @staticmethod
    def generate_explanation(evidence: Dict[str, Any]) -> str:
        """
        Uses Gemini to generate an evidence-driven explanation of the risk score.
        """
        if not settings.LLM_API_KEY:
            return "LLM API Key not configured. Explanation unavailable."
            
        client = genai.Client(api_key=settings.LLM_API_KEY)
        
        system_prompt = """You are a software release risk analyst.
Explain only the structured evidence provided to you.
Do not invent metrics or facts.
Do not modify the supplied numerical risk score.
Do not introduce external assumptions.
Clearly distinguish observed evidence from recommendations.
Format your response nicely in markdown."""

        prompt = f"""
Please explain the following risk assessment evidence for release {evidence.get('release')} of {evidence.get('repository')}.

Risk Score: {evidence.get('risk_score')}
Risk Level: {evidence.get('risk_level')}
Trend: {evidence.get('trend')}
Data Confidence: {evidence.get('confidence')}

Findings:
{json.dumps(evidence.get('findings', []), indent=2)}

Recommendations:
{json.dumps(evidence.get('recommendations', []), indent=2)}
"""

        try:
            response = client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2, # Keep it deterministic and factual
                )
            )
            return response.text
        except Exception as e:
            return f"Failed to generate explanation: {str(e)}"
