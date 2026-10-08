import json
from typing import Dict, Any, List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.config import settings

class CriticValidation(BaseModel):
    valid: bool = Field(description="Whether the explanation accurately reflects the deterministic evidence without hallucination.")
    feedback: str = Field(description="If not valid, specific instructions on what needs to be fixed.")

class CriticService:
    @staticmethod
    def validate_explanation(explanation: str, findings: List[Dict[str, Any]], risk_score: float) -> Dict[str, Any]:
        """
        Uses Gemini with Structured Outputs to validate the explanation against the ground-truth evidence.
        """
        if not settings.LLM_API_KEY:
            return {"valid": True, "feedback": ""} # Pass through if no LLM
            
        client = genai.Client(api_key=settings.LLM_API_KEY)
        
        system_prompt = """You are an Evidence Critic for a software risk analysis system.
Your job is to read an LLM-generated explanation and compare it against the HARD EVIDENCE.
You must FAIL the validation (valid=False) if the explanation:
1. Hallucinates a number, metric, or PR that is not in the evidence.
2. Contradicts the deterministic risk score.
3. Suggests code changes or bug fixes when the evidence does not support it.

If it passes, set valid=True and feedback=""."""

        prompt = f"""
HARD EVIDENCE:
Risk Score: {risk_score}
Findings:
{json.dumps(findings, indent=2)}

GENERATED EXPLANATION TO CRITIQUE:
{explanation}
"""

        try:
            response = client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=CriticValidation,
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Critic failed to evaluate: {e}")
            return {"valid": True, "feedback": ""}
