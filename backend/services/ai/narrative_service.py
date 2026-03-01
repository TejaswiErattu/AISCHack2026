# backend/services/ai/narrative_service.py
from .bedrock_client import BedrockClient
from ...prompts import LOAN_OFFICER_SYSTEM_PROMPT, FARMER_SYSTEM_PROMPT, CLIMATE_SCIENTIST_SYSTEM_PROMPT
from ...narrative import build_narrative_context

class NarrativeService:
    def __init__(self, bedrock_client: BedrockClient):
        # Task 2.3: Initializing with the Bedrock wrapper
        self.client = bedrock_client
        self.prompts = {
            "loan_officer": LOAN_OFFICER_SYSTEM_PROMPT,
            "farmer": FARMER_SYSTEM_PROMPT,
            "scientist": CLIMATE_SCIENTIST_SYSTEM_PROMPT
        }

    async def generate(self, context_data: dict, panel: str) -> str:
        """
        Task 2.3: Builds prompt, calls Claude, and returns the narrative.
        """
        # Pick the right 'personality' prompt
        system_prompt = self.prompts.get(panel, LOAN_OFFICER_SYSTEM_PROMPT)
        
        # Turn Developer 1's raw numbers into the 'translator' text
        user_message = build_narrative_context(
            region_name=context_data['region_name'],
            primary_crop=context_data['primary_crop'],
            climate_inputs=context_data['climate_inputs'],
            yield_stress_score=context_data['yield_stress_score'],
            financial_outputs=context_data['financial_outputs']
        )
        
        # Send to Claude 3.5 Sonnet
        response = await self.client.invoke(system_prompt, user_message)
        
        # Task 2.3 Fallback: If AI fails, return a generic message (we will add real fallbacks in Task 2.4)
        return response if response else "Narrative temporarily unavailable due to API timeout."