"""AWS Bedrock client with template-based fallback.

Tries to call Claude via AWS Bedrock. If Bedrock is unavailable (no credentials,
network error, etc.), falls back to template-based narrative generation.
"""
import os
import json
import re


class BedrockClient:
    def __init__(self):
        self._boto_client = None
        self._init_attempted = False

    def _get_client(self):
        """Lazy-init boto3 Bedrock client. Returns None if unavailable."""
        if self._init_attempted:
            return self._boto_client
        self._init_attempted = True
        try:
            import boto3
            self._boto_client = boto3.client(
                "bedrock-runtime",
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
        except Exception:
            self._boto_client = None
        return self._boto_client

    async def invoke(self, system_prompt: str, user_message: str) -> str:
        """Call Claude via Bedrock, fall back to template if unavailable."""
        client = self._get_client()
        if client:
            try:
                return await self._call_bedrock(client, system_prompt, user_message)
            except Exception:
                pass
        return self._template_fallback(system_prompt, user_message)

    async def _call_bedrock(self, client, system_prompt: str, user_message: str) -> str:
        """Invoke Claude 3.5 Sonnet on Bedrock."""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        })
        response = client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _template_fallback(self, system_prompt: str, user_message: str) -> str:
        """Generate a narrative from the context data using templates."""
        ctx = self._parse_context(user_message)

        if "loan officer" in system_prompt.lower():
            return self._loan_officer_template(ctx)
        elif "farmer" in system_prompt.lower() or "advisor" in system_prompt.lower():
            return self._farmer_template(ctx)
        else:
            return self._scientist_template(ctx)

    def _parse_context(self, message: str) -> dict:
        """Extract key values from the narrative context string."""
        ctx = {}
        patterns = {
            "region": r"REGION:\s*(.+)",
            "crop": r"PRIMARY CROP:\s*(.+)",
            "temp": r"Temperature Anomaly:\s*([\-\d.]+)",
            "drought": r"Drought Index:\s*([\d.]+)",
            "rainfall": r"Rainfall Anomaly:\s*([\-\d.]+)",
            "ndvi": r"NDVI.*?:\s*([\d.]+)",
            "soil": r"Soil Moisture:\s*([\d.]+)",
            "stress": r"YIELD STRESS:\s*([\d.]+)",
            "risk_factor": r"LARGEST RISK FACTOR:\s*(.+)",
            "rate": r"Interest Rate:\s*([\d.]+)",
            "pd": r"Probability of Default.*?:\s*([\d.]+)",
            "premium": r"Insurance Premium:\s*\$?([\d.]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            ctx[key] = match.group(1).strip() if match else "N/A"
        return ctx

    def _loan_officer_template(self, ctx: dict) -> str:
        return (
            f"Current yield stress score of {ctx['stress']}/100 for {ctx['region']} "
            f"is driven primarily by {ctx['risk_factor']}, with temperature anomaly "
            f"at {ctx['temp']}°C above seasonal norm. Probability of default stands at "
            f"{ctx['pd']}%, warranting the recommended rate of {ctx['rate']}%. "
            f"NDVI health at {ctx['ndvi']} indicates "
            f"{'significant' if float(ctx.get('ndvi', 50) or 50) < 50 else 'moderate'} "
            f"vegetative stress. The insurance premium of ${ctx['premium']} reflects "
            f"current risk exposure for {ctx['crop']} cultivation in this region."
        )

    def _farmer_template(self, ctx: dict) -> str:
        return (
            f"Weather conditions in {ctx['region']} have been challenging this season, "
            f"and that's the main reason your rate is at {ctx['rate']}%. "
            f"The biggest factor right now is {ctx['risk_factor']} — "
            f"your land is showing some stress from recent conditions. "
            f"If things improve over the next couple of weeks, you should see "
            f"better terms on your {ctx['crop']} loan. Hang in there."
        )

    def _scientist_template(self, ctx: dict) -> str:
        return (
            f"Composite yield stress index of {ctx['stress']}/100 for {ctx['region']} "
            f"is dominated by {ctx['risk_factor']}. Temperature anomaly of {ctx['temp']}°C "
            f"with drought index at {ctx['drought']}/100 indicates "
            f"{'severe' if float(ctx.get('drought', 0) or 0) > 60 else 'moderate'} "
            f"water deficit conditions. NDVI health score of {ctx['ndvi']} and soil moisture "
            f"at {ctx['soil']}/100 suggest "
            f"{'critical' if float(ctx.get('soil', 50) or 50) < 35 else 'notable'} "
            f"edaphic stress affecting {ctx['crop']} root-zone viability."
        )
