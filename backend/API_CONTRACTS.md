# TerraLend API Contracts

Base URL: `http://localhost:8000`

All responses are `application/json`. Error responses follow the format `{"detail": "..."}`.

---

## GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

---

## GET /regions

List all selectable US agricultural regions.

**Response:** `List[RegionResponse]` (20+ items)
```json
[
  {
    "region_id": "central-valley-ca",
    "name": "Central Valley, CA",
    "lat": 36.75,
    "lng": -119.77,
    "primary_crop": "almonds"
  },
  {
    "region_id": "midwest-corn-belt-ia",
    "name": "Midwest Corn Belt, IA",
    "lat": 42.03,
    "lng": -93.47,
    "primary_crop": "corn"
  }
]
```

**Fields:**
| Field | Type | Description |
|---|---|---|
| region_id | string | Unique slug (use in all `/region/{id}/` endpoints) |
| name | string | Display name |
| lat | float | Center latitude |
| lng | float | Center longitude |
| primary_crop | string | Primary crop for the region |

---

## GET /region/{region_id}/climate

Current climate data for a region.

**Example:** `GET /region/central-valley-ca/climate`

**Response:** `ClimateResponse`
```json
{
  "temperature_anomaly": 1.2,
  "drought_index": 45.0,
  "rainfall_anomaly": -15.0,
  "ndvi_score": 62.0,
  "soil_moisture": 40.0
}
```

**Fields:**
| Field | Type | Range | Description |
|---|---|---|---|
| temperature_anomaly | float | -5 to +8 | °C above/below seasonal norm |
| drought_index | float | 0–100 | Higher = more drought |
| rainfall_anomaly | float | -80 to +80 | % deviation from seasonal avg |
| ndvi_score | float | 0–100 | Vegetation health (higher = healthier) |
| soil_moisture | float | 0–100 | Soil moisture level (higher = wetter) |

**Errors:**
- `404 {"detail": "Region not found"}` — invalid region_id

---

## GET /region/{region_id}/stress

Yield stress score and factor breakdown.

**Example:** `GET /region/central-valley-ca/stress`

**Response:** `StressResponse`
```json
{
  "yield_stress_score": 42.45,
  "breakdown": {
    "heat_stress": 15.75,
    "drought": 11.25,
    "rainfall_anomaly": 3.75,
    "ndvi_deficit": 5.7,
    "soil_moisture_deficit": 6.0
  }
}
```

**Fields:**
| Field | Type | Range | Description |
|---|---|---|---|
| yield_stress_score | float | 0–100 | Composite stress (higher = worse) |
| breakdown | object | — | Each factor's weighted contribution to the score |

**Breakdown keys:** `heat_stress`, `drought`, `rainfall_anomaly`, `ndvi_deficit`, `soil_moisture_deficit`. Values sum to `yield_stress_score`.

**Errors:**
- `404 {"detail": "Region not found"}` — invalid region_id

---

## GET /region/{region_id}/financial

TerraLend's dynamically computed financial outputs for a region.

**Example:** `GET /region/central-valley-ca/financial`

**Response:** `FinancialResponse`
```json
{
  "interest_rate": 6.75,
  "probability_of_default": 0.1561,
  "insurance_premium": 1709.4,
  "repayment_flexibility": 57.55,
  "baseline_rate": 6.9
}
```

**Fields:**
| Field | Type | Range | Description |
|---|---|---|---|
| interest_rate | float | 3.0–15.0 | TerraLend dynamic rate (%) |
| probability_of_default | float | 0.01–0.50 | Probability of default (0–1) |
| insurance_premium | float | varies | Insurance premium ($/season) |
| repayment_flexibility | float | 0–100 | Flexibility score (higher = more flexible) |
| baseline_rate | float | — | Old system's static rate for comparison (%) |

**Errors:**
- `404 {"detail": "Region not found"}` — invalid region_id

---

## GET /region/{region_id}/comparison

Old system vs TerraLend side-by-side comparison.

**Example:** `GET /region/central-valley-ca/comparison`

**Response:** `ComparisonResponse`
```json
{
  "old_system": {
    "interest_rate": 6.9,
    "probability_of_default": 0.05,
    "insurance_premium": 1200.0,
    "repayment_flexibility": 100.0,
    "baseline_rate": 6.9
  },
  "terralend": {
    "interest_rate": 6.75,
    "probability_of_default": 0.1561,
    "insurance_premium": 1709.4,
    "repayment_flexibility": 57.55,
    "baseline_rate": 6.9
  }
}
```

**Notes:**
- `old_system` values are **static** — they never change regardless of climate data. They represent traditional bank underwriting.
- `terralend` values are **dynamic** — computed from current climate data each request.
- Both objects have the same `FinancialResponse` shape.

**Errors:**
- `404 {"detail": "Region not found"}` — invalid region_id

---

## POST /simulate

Climate shock simulator. Merge overrides with current climate data, recompute stress + financial outputs, return results with deltas.

**Request:** `SimulateRequest`
```json
{
  "region_id": "central-valley-ca",
  "temperature_delta": 2.5,
  "drought_index": 70
}
```

**Request fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| region_id | string | Yes | Region to simulate |
| temperature_delta | float | No | °C to ADD to current temperature anomaly |
| drought_index | float | No | Override drought index (0–100, replaces current) |
| rainfall_anomaly | float | No | Override rainfall anomaly (-80 to +80, replaces current) |
| ndvi_score | float | No | Override NDVI score (0–100, replaces current) |
| soil_moisture | float | No | Override soil moisture (0–100, replaces current) |

**Note:** `temperature_delta` is **additive** (current + delta). All other overrides are **replacements**. Omitted fields keep their current values.

**Response:** `SimulateResponse`
```json
{
  "region_id": "central-valley-ca",
  "baseline": {
    "interest_rate": 6.75,
    "probability_of_default": 0.1561,
    "insurance_premium": 1709.4,
    "repayment_flexibility": 57.55,
    "baseline_rate": 6.9
  },
  "simulated": {
    "interest_rate": 7.06,
    "probability_of_default": 0.1952,
    "insurance_premium": 1896.96,
    "repayment_flexibility": 41.92,
    "baseline_rate": 6.9
  },
  "stress_score": 58.08,
  "baseline_stress": 42.45,
  "deltas": {
    "stress_score": 15.63,
    "interest_rate": 0.31,
    "probability_of_default": 0.0391,
    "insurance_premium": 187.56,
    "repayment_flexibility": -15.63
  }
}
```

**Response fields:**
| Field | Type | Description |
|---|---|---|
| region_id | string | Region that was simulated |
| baseline | FinancialResponse | Financial outputs from current climate (before overrides) |
| simulated | FinancialResponse | Financial outputs after applying overrides |
| stress_score | float | Simulated yield stress score (0–100) |
| baseline_stress | float | Current yield stress score before overrides (0–100) |
| deltas | object | `simulated - baseline` for each field (positive = increase) |

**Delta keys:** `stress_score`, `interest_rate`, `probability_of_default`, `insurance_premium`, `repayment_flexibility`.

**Errors:**
- `404 {"detail": "Region not found"}` — invalid region_id
- `422` — validation error (missing region_id, malformed JSON)

---

## Available Region IDs

```
central-valley-ca        midwest-corn-belt-ia     texas-panhandle-tx
columbia-basin-wa        mississippi-delta-ms     san-joaquin-valley-ca
nebraska-sandhills-ne    kansas-wheat-belt-ks     sacramento-valley-ca
florida-citrus-belt-fl   willamette-valley-or     red-river-valley-nd
yakima-valley-wa         imperial-valley-ca       snake-river-plain-id
ozark-plateau-mo         bluegrass-region-ky      palouse-wa
rio-grande-valley-tx     shenandoah-valley-va
```
