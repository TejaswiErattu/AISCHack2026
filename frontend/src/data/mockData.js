export const MOCK_REGIONS = [
  { id: "central-valley-ca",     name: "Central Valley, CA",      lat: 36.75,  lng: -119.77, primary_crop: "almonds",     stress_score: 42 },
  { id: "midwest-corn-belt-ia",  name: "Midwest Corn Belt, IA",   lat: 42.03,  lng: -93.47,  primary_crop: "corn",        stress_score: 26 },
  { id: "texas-panhandle-tx",    name: "Texas Panhandle, TX",     lat: 35.20,  lng: -101.83, primary_crop: "cotton",      stress_score: 53 },
  { id: "columbia-basin-wa",     name: "Columbia Basin, WA",      lat: 46.80,  lng: -119.30, primary_crop: "potatoes",    stress_score: 28 },
  { id: "mississippi-delta-ms",  name: "Mississippi Delta, MS",   lat: 33.40,  lng: -90.90,  primary_crop: "soybeans",    stress_score: 34 },
  { id: "san-joaquin-valley-ca", name: "San Joaquin Valley, CA",  lat: 36.33,  lng: -119.64, primary_crop: "grapes",      stress_score: 47 },
  { id: "nebraska-sandhills-ne", name: "Nebraska Sandhills, NE",  lat: 42.10,  lng: -101.20, primary_crop: "cattle/hay",  stress_score: 36 },
  { id: "kansas-wheat-belt-ks",  name: "Kansas Wheat Belt, KS",   lat: 38.50,  lng: -98.75,  primary_crop: "wheat",       stress_score: 32 },
  { id: "sacramento-valley-ca",  name: "Sacramento Valley, CA",   lat: 39.15,  lng: -121.69, primary_crop: "rice",        stress_score: 39 },
  { id: "florida-citrus-belt-fl",name: "Florida Citrus Belt, FL", lat: 28.10,  lng: -81.60,  primary_crop: "citrus",      stress_score: 31 },
  { id: "willamette-valley-or",  name: "Willamette Valley, OR",   lat: 44.75,  lng: -123.07, primary_crop: "berries",     stress_score: 23 },
  { id: "red-river-valley-nd",   name: "Red River Valley, ND",    lat: 47.90,  lng: -97.03,  primary_crop: "sugar beets", stress_score: 27 },
  { id: "yakima-valley-wa",      name: "Yakima Valley, WA",       lat: 46.60,  lng: -120.50, primary_crop: "apples",      stress_score: 26 },
  { id: "imperial-valley-ca",    name: "Imperial Valley, CA",     lat: 32.85,  lng: -115.57, primary_crop: "lettuce",     stress_score: 61 },
  { id: "snake-river-plain-id",  name: "Snake River Plain, ID",   lat: 42.87,  lng: -114.46, primary_crop: "potatoes",    stress_score: 29 },
  { id: "ozark-plateau-mo",      name: "Ozark Plateau, MO",       lat: 37.20,  lng: -92.50,  primary_crop: "cattle/hay",  stress_score: 27 },
  { id: "bluegrass-region-ky",   name: "Bluegrass Region, KY",    lat: 38.05,  lng: -84.50,  primary_crop: "tobacco",     stress_score: 25 },
  { id: "palouse-wa",            name: "Palouse, WA",             lat: 46.73,  lng: -117.17, primary_crop: "wheat",       stress_score: 24 },
  { id: "rio-grande-valley-tx",  name: "Rio Grande Valley, TX",   lat: 26.20,  lng: -98.23,  primary_crop: "citrus",      stress_score: 57 },
  { id: "shenandoah-valley-va",  name: "Shenandoah Valley, VA",   lat: 38.15,  lng: -79.07,  primary_crop: "apples",      stress_score: 24 },
]

export const MOCK_CLIMATE = {
  temperature_anomaly: 2.3,
  drought_index: 67,
  rainfall_anomaly: -34,
  ndvi_score: 48,
  soil_moisture: 31,
  yield_stress_score: 72
}

export const MOCK_FINANCIAL = {
  interest_rate: 7.8,
  probability_of_default: 0.18,
  insurance_premium: 1890,
  repayment_flexibility: 28,
  repayment_months: 36,
  rate_floor: 5.8,
  rate_ceiling: 8.2,
  baseline_rate: 7.2,
  delta_from_baseline: 0.6
}

export const MOCK_NARRATIVES = {
  loan_officer: "Current yield stress score of 72/100 is driven primarily by heat stress anomaly (+2.3°C above seasonal norm), contributing 45% of composite risk. Probability of default has increased to 18%, adjusting the recommended rate to 7.8%. Vegetation health indicators (NDVI: 48) suggest early-stage crop stress consistent with multi-week heat exposure. Rate stabilization would require sustained precipitation above -10% of seasonal average for a minimum of 14 days.",
  farmer: "It's been an unusually hot and dry stretch this season, and that's the main reason your rate is sitting a bit higher than normal right now. Your land is showing some stress from the heat — nothing catastrophic, but it's real. If conditions cool down and you get some decent rainfall over the next two weeks, your terms should start improving.",
  scientist: "Composite yield stress index of 72/100 is dominated by heat_stress_index (67.3, contributing 0.45 of weighted score) and drought_index (54.1, contributing 0.32). NDVI health score of 48 indicates moderate vegetative stress consistent with cumulative thermal anomaly of +2.3°C above 30-year seasonal mean. Soil moisture deficit of 31/100 suggests approximately 38% below field capacity — approaching critical threshold for root-zone stress in almond cultivation."
}

export const MOCK_SIMULATION = [
  { name: "Dust Bowl Echo", icon: "🌵", color: "#EF4444", stress_score: 94, interest_rate: 9.2, pd: 0.31 },
  { name: "The Deluge", icon: "🌊", color: "#3B82F6", stress_score: 61, interest_rate: 7.1, pd: 0.14 },
  { name: "Late Frost", icon: "🌨️", color: "#8B5CF6", stress_score: 78, interest_rate: 8.3, pd: 0.22 },
  { name: "Baseline", icon: "📊", color: "#10B981", stress_score: 31, interest_rate: 6.1, pd: 0.08 },
]