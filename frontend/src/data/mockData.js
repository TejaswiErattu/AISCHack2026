export const MOCK_REGIONS = [
  { id: "central-valley-ca", name: "Central Valley, CA", lat: 36.7468, lng: -119.7726, primary_crop: "almonds", stress_score: 72 },
  { id: "san-joaquin-ca", name: "San Joaquin Valley, CA", lat: 37.2059, lng: -120.2114, primary_crop: "tomatoes", stress_score: 65 },
  { id: "imperial-valley-ca", name: "Imperial Valley, CA", lat: 32.8370, lng: -115.5694, primary_crop: "lettuce", stress_score: 88 },
  { id: "salinas-valley-ca", name: "Salinas Valley, CA", lat: 36.6777, lng: -121.6555, primary_crop: "strawberries", stress_score: 41 },
  { id: "columbia-basin-wa", name: "Columbia Basin, WA", lat: 46.6021, lng: -119.5618, primary_crop: "potatoes", stress_score: 28 },
  { id: "willamette-or", name: "Willamette Valley, OR", lat: 44.5646, lng: -123.2620, primary_crop: "grapes", stress_score: 19 },
  { id: "yakima-wa", name: "Yakima Valley, WA", lat: 46.6021, lng: -120.5059, primary_crop: "apples", stress_score: 33 },
  { id: "wheat-belt-ks", name: "Wheat Belt, KS", lat: 38.5266, lng: -96.7265, primary_crop: "wheat", stress_score: 58 },
  { id: "great-plains-tx", name: "Texas High Plains", lat: 33.5779, lng: -101.8552, primary_crop: "sorghum", stress_score: 77 },
  { id: "red-river-nd", name: "Red River Valley, ND", lat: 47.9253, lng: -97.0329, primary_crop: "sunflowers", stress_score: 41 },
  { id: "nebraska-panhandle", name: "Nebraska Panhandle", lat: 41.8534, lng: -103.0012, primary_crop: "corn", stress_score: 53 },
  { id: "oklahoma-panhandle", name: "Oklahoma Panhandle", lat: 36.7748, lng: -100.4517, primary_crop: "wheat", stress_score: 69 },
  { id: "south-dakota-plains", name: "South Dakota Plains", lat: 44.3683, lng: -100.3510, primary_crop: "soybeans", stress_score: 37 },
  { id: "corn-belt-ia", name: "Corn Belt, IA", lat: 42.0115, lng: -93.2105, primary_crop: "corn", stress_score: 34 },
  { id: "illinois-farmland", name: "Central Illinois", lat: 40.3363, lng: -89.0022, primary_crop: "soybeans", stress_score: 29 },
  { id: "indiana-corn", name: "Indiana Corn Belt", lat: 40.2672, lng: -86.1349, primary_crop: "corn", stress_score: 31 },
  { id: "ohio-farmland", name: "Western Ohio", lat: 40.4173, lng: -83.8065, primary_crop: "soybeans", stress_score: 26 },
  { id: "minnesota-fields", name: "Southern Minnesota", lat: 44.0130, lng: -94.4660, primary_crop: "corn", stress_score: 22 },
  { id: "mississippi-delta", name: "Mississippi Delta", lat: 33.4510, lng: -90.5624, primary_crop: "cotton", stress_score: 81 },
  { id: "georgia-peanuts", name: "Southwest Georgia", lat: 31.5785, lng: -84.2557, primary_crop: "peanuts", stress_score: 74 },
  { id: "florida-citrus", name: "Central Florida", lat: 28.0836, lng: -81.9614, primary_crop: "citrus", stress_score: 62 },
  { id: "carolina-tobacco", name: "North Carolina Piedmont", lat: 35.7596, lng: -79.0193, primary_crop: "tobacco", stress_score: 47 },
  { id: "louisiana-sugarcane", name: "Louisiana Sugarcane Belt", lat: 29.9511, lng: -91.1339, primary_crop: "sugarcane", stress_score: 55 },
  { id: "arkansas-rice", name: "Arkansas Grand Prairie", lat: 34.7465, lng: -91.7337, primary_crop: "rice", stress_score: 43 },
  { id: "snake-river-id", name: "Snake River Plain, ID", lat: 42.5950, lng: -114.4600, primary_crop: "potatoes", stress_score: 36 },
  { id: "san-luis-valley-co", name: "San Luis Valley, CO", lat: 37.5783, lng: -106.1350, primary_crop: "potatoes", stress_score: 49 },
  { id: "utah-farm-belt", name: "Utah Cache Valley", lat: 41.7370, lng: -111.8338, primary_crop: "dairy/hay", stress_score: 31 },
  { id: "arizona-salt-river", name: "Salt River Valley, AZ", lat: 33.4484, lng: -112.0740, primary_crop: "cotton", stress_score: 91 },
  { id: "new-mexico-pecos", name: "Pecos Valley, NM", lat: 33.3943, lng: -104.5230, primary_crop: "pecans", stress_score: 66 },
  { id: "hudson-valley-ny", name: "Hudson Valley, NY", lat: 41.7004, lng: -73.9210, primary_crop: "apples", stress_score: 18 },
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