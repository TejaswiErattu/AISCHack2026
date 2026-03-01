# backend/services/ai/narrative.py

def get_dominant_factor(climate_inputs: dict) -> tuple[str, float]:
    """
    Identifies which climate factor is contributing most to the stress.
    Weights are based on the formula in Task 3.1 of the Backend Core.
    """
    weights = {
        "heat_stress": 0.30,
        "drought_index": 0.25,
        "rainfall_anomaly": 0.20,
        "ndvi_score": 0.15,
        "soil_moisture": 0.10
    }
    
    # Calculate weighted score for each factor to see which 'hurts' the most
    scored_factors = {k: v * weights.get(k, 0) for k, v in climate_inputs.items()}
    dominant = max(scored_factors, key=scored_factors.get)
    return dominant, scored_factors[dominant]

def build_narrative_context(
    region_name: str,
    primary_crop: str,
    climate_inputs: dict,
    yield_stress_score: float,
    financial_outputs: dict
) -> str:
    """
    Task 2.2: Formats all data into the user message payload that Claude receives.
    This creates the 'Fact Sheet' the AI reads before it writes the narrative.
    """
    dom_factor, _ = get_dominant_factor(climate_inputs)
    
    context = f"""
    DATA SUMMARY FOR AI ANALYSIS:
    ------------------------------
    REGION: {region_name}
    PRIMARY CROP: {primary_crop}
    
    CLIMATE METRICS:
    - Temperature Anomaly: {climate_inputs.get('temperature_anomaly')}°C
    - Drought Index: {climate_inputs.get('drought_index')}/100
    - Rainfall Anomaly: {climate_inputs.get('rainfall_anomaly')}%
    - NDVI Vegetation Health: {climate_inputs.get('ndvi_score')}/100
    - Soil Moisture: {climate_inputs.get('soil_moisture')}/100
    
    AGGREGATED YIELD STRESS: {yield_stress_score}/100
    LARGEST RISK FACTOR: {dom_factor}
    
    FINANCIAL DATA:
    - Calculated Interest Rate: {financial_outputs.get('interest_rate')}%
    - Probability of Default (PD): {financial_outputs.get('probability_of_default')}%
    - Recommended Insurance Premium: ${financial_outputs.get('insurance_premium')}
    """
    return context