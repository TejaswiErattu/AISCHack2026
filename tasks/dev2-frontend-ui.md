# Developer 2: Frontend UI

**Scope**: React app, Leaflet map, all visual panels, climate sliders, tab navigation, financial displays, comparison view.
**Independence**: Uses a local mock API layer (hardcoded JSON responses matching the API contracts). Zero dependency on backend being running. At integration time, swap mock for real `fetch()` calls.
**Convention**: Every subtask ends with visual verification + unit/component tests before moving on.

---

## Task 1: React Project Scaffold

### 1.1 Vite + React setup
- Initialize `frontend/` with Vite + React (TypeScript)
- Install dependencies: `react-leaflet`, `leaflet`, `axios` (or use fetch)
- Set up folder structure:
  ```
  frontend/
    src/
      api/           # API client + mock layer
      components/    # Reusable UI components
      panels/        # Loan Officer, Farmer, Climate Scientist panels
      hooks/         # Custom React hooks
      types/         # TypeScript interfaces matching API contracts
      data/          # Static mock data for development
      App.tsx
      main.tsx
    public/
    index.html
  ```
- Add basic CSS reset / global styles
- Configure proxy to `localhost:8000` for dev (vite.config.ts)

**Tests after 1.1:**
- [ ] `npm run dev` starts without errors
- [ ] App renders a "TerraLend" heading in browser
- [ ] Hot reload works on file changes
- [ ] TypeScript compiles without errors
- [ ] Build succeeds: `npm run build`

### 1.2 TypeScript types from API contracts
- Create `frontend/src/types/api.ts` — interfaces matching backend response shapes:
  - `Region`, `ClimateData`, `StressData`, `FinancialData`, `ComparisonData`, `SystemDetails`
  - `SimulateRequest`, `SimulateResponse`
- These types are the "contract" — must match what the backend returns exactly

**Tests after 1.2:**
- [ ] All types compile without errors
- [ ] Sample mock data objects conform to each type (TypeScript validates)

### 1.3 Mock API layer
- Create `frontend/src/api/mockData.ts` — hardcoded responses for every endpoint:
  - 20+ regions with realistic names, coords, crops
  - Climate data per region
  - Financial data per region
  - Comparison data per region
  - Simulation response examples
- Create `frontend/src/api/client.ts`:
  - Functions matching each API endpoint: `getRegions()`, `getClimate(id)`, `getStress(id)`, `getFinancial(id)`, `getComparison(id)`, `simulate(req)`
  - Each function reads from mock data with a small fake delay (200ms `setTimeout`)
  - Add a `USE_MOCK` flag (default `true`) — when `false`, makes real HTTP calls to backend
- This layer is what gets swapped at integration

**Tests after 1.3:**
- [ ] `getRegions()` returns array of 20+ regions
- [ ] `getClimate("central-valley-ca")` returns valid climate data
- [ ] `getClimate("nonexistent")` throws/rejects with meaningful error
- [ ] `simulate()` returns response with deltas
- [ ] Toggling `USE_MOCK=false` changes to real HTTP calls (test with nock or just verify fetch is called)

---

## Task 2: Interactive US Map

### 2.1 Leaflet map component
- Create `frontend/src/components/Map/RegionMap.tsx`:
  - Full-width map centered on continental US (lat ~39.8, lng ~-98.5, zoom 4)
  - Render circle markers for each region (from `getRegions()` response)
  - Marker color reflects yield stress score: green (0–30), yellow (31–60), orange (61–80), red (81–100)
  - Marker size is fixed (radius ~12px)
  - On click → call `onRegionSelect(regionId)` callback
  - Selected region marker gets a highlight ring / different style

**Tests after 2.1:**
- [ ] Map renders and shows US geography (tile layer loads)
- [ ] All 20+ region markers appear on map
- [ ] Clicking a marker triggers `onRegionSelect` with correct region ID
- [ ] Selected marker visually distinct from others
- [ ] Markers colored correctly based on stress score
- [ ] Map is responsive (fills container width)

### 2.2 Climate overlay toggles
- Add overlay toggle buttons above map: **Temperature** | **NDVI** | **Soil Moisture** | **Drought**
- When toggled ON, marker colors shift to reflect that specific metric instead of composite stress
- Each overlay has its own color scale (e.g., NDVI: brown→green, Soil moisture: red→blue)
- Multiple overlays can be toggled but only one color scale active (last toggled wins)
- Add translucent circles around markers that grow/shrink based on metric intensity

**Tests after 2.2:**
- [ ] Toggle buttons render and are clickable
- [ ] Toggling NDVI overlay changes marker colors to NDVI scale
- [ ] Toggling back to default restores composite stress colors
- [ ] Overlay circles scale correctly (high drought → larger circle)
- [ ] Active toggle visually highlighted (button state)

---

## Task 3: Region Selection & Data Loading

### 3.1 State management for selected region
- Create `frontend/src/hooks/useRegionData.ts`:
  - Manages: `selectedRegionId`, `climateData`, `stressData`, `financialData`, `comparisonData`
  - On region select: loads all data from API client (parallel calls)
  - Exposes loading state per data type
  - Exposes error state
- Wire into `App.tsx` — region select from map triggers data load

**Tests after 3.1:**
- [ ] Selecting a region triggers all 4 API calls
- [ ] Loading states transition: `idle` → `loading` → `loaded`
- [ ] Error state set if any call fails
- [ ] Switching regions cancels/ignores stale responses from previous region
- [ ] All data available after loading completes

### 3.2 Region info header
- Create `frontend/src/components/RegionHeader.tsx`:
  - Shows: region name, primary crop, lat/lng coordinates
  - Shows loading spinner when data is fetching
  - Shows "Select a region on the map" placeholder when no region selected

**Tests after 3.2:**
- [ ] Shows placeholder when no region selected
- [ ] Shows region name and crop after selection
- [ ] Shows loading state during data fetch
- [ ] Updates when different region selected

---

## Task 4: Financial Output Panel

### 4.1 Financial output cards
- Create `frontend/src/components/Financial/FinancialPanel.tsx`:
  - Four output cards in a grid:
    1. **Interest Rate** — large number (e.g., "6.4%"), delta indicator ("↑ +0.3% from baseline")
    2. **Probability of Default** — percentage with delta
    3. **Insurance Premium** — dollar amount per season with delta
    4. **Repayment Flexibility** — 0–100 score with delta
  - Delta colors: red for worse (higher rate, higher PD, higher premium, lower flexibility), green for better
- Create `frontend/src/components/Financial/OutputCard.tsx` — reusable card component:
  - Props: `label`, `value`, `unit`, `delta`, `deltaDirection` (higher-is-worse or higher-is-better)

**Tests after 4.1:**
- [ ] All four cards render with correct values from mock data
- [ ] Delta indicators show correct direction and color
- [ ] Positive delta on interest rate shows red (worse)
- [ ] Positive delta on flexibility shows green (better)
- [ ] Cards handle missing delta gracefully (no delta shown)
- [ ] Responsive layout: 2x2 grid on desktop, stacked on mobile

### 4.2 Yield stress score display
- Create `frontend/src/components/Financial/StressGauge.tsx`:
  - Visual gauge/meter showing stress score 0–100
  - Color gradient from green (0) to red (100)
  - Numeric label below
  - Breakpoints labeled: "Low" (0–30), "Moderate" (31–60), "High" (61–80), "Severe" (81–100)

**Tests after 4.2:**
- [ ] Gauge renders at correct position for given stress score
- [ ] Color matches score (green for low, red for high)
- [ ] Label text matches breakpoint range
- [ ] Handles edge values: 0, 50, 100
- [ ] Animates smoothly when value changes

---

## Task 5: Climate Shock Simulator

### 5.1 Slider components
- Create `frontend/src/components/Simulator/ClimateSliders.tsx`:
  - **Temperature anomaly slider**: range -3°C to +5°C, step 0.1, default 0
  - **Drought intensity slider**: range 0 to 100, step 1, default from climate data
  - **Rainfall anomaly slider**: range -80% to +80%, step 1, default from climate data
  - Each slider shows current value label
  - On release (not during drag): calls `onSimulate(params)` callback
  - "Reset to baseline" button restores all sliders to current climate data values

**Tests after 5.1:**
- [ ] All three sliders render with correct ranges
- [ ] Sliders initialize to current climate data values
- [ ] Dragging updates the displayed value label
- [ ] Callback fires on mouse/touch release, not during drag
- [ ] Reset button restores all values
- [ ] Slider step increments are correct

### 5.2 Shock event toggle buttons
- Create `frontend/src/components/Simulator/ShockToggles.tsx`:
  - Three buttons: **Drought Shock** | **Flash Flood** | **Early Frost**
  - Each sets sliders to preset extreme values:
    - Drought: temp +4°C, drought 90, rainfall -60%
    - Flash Flood: temp +1°C, drought 10, rainfall +70%
    - Early Frost: temp -3°C, drought 30, rainfall -20%
  - Clicking fires simulation immediately (no need to release slider)
  - Active toggle is visually highlighted; clicking again resets to baseline

**Tests after 5.2:**
- [ ] Each toggle sets sliders to correct preset values
- [ ] Simulation fires immediately on toggle click
- [ ] Active toggle visually distinct
- [ ] Clicking active toggle resets to baseline
- [ ] Only one toggle active at a time
- [ ] Sliders update their position/labels to match preset values

### 5.3 Simulation state management
- Create `frontend/src/hooks/useSimulation.ts`:
  - Manages simulation request/response state
  - On simulate: calls `simulate()` API, updates financial data with response
  - Tracks baseline values (from initial load) and current simulated values
  - Computes deltas: `current - baseline` for each financial output
  - Debounce: only one pending simulation at a time; new request cancels old
- Wire simulation results into financial panel + stress gauge

**Tests after 5.3:**
- [ ] Simulation call triggers on slider release
- [ ] Financial panel updates with simulated values
- [ ] Deltas correctly computed against baseline
- [ ] Debouncing: rapid changes result in only one API call
- [ ] Loading state during simulation
- [ ] Resetting sliders restores baseline values in financial panel
- [ ] Stress gauge updates with simulated stress score

---

## Task 6: Dual Panel UI (Three-Tab Navigation)

### 6.1 Tab navigation component
- Create `frontend/src/components/Layout/TabNavigation.tsx`:
  - Three tabs: **Loan Officer** | **Farmer** | **Climate Scientist**
  - Default: Loan Officer
  - Animated underline indicator on active tab
  - Smooth panel transition on switch (CSS transition or framer-motion)

**Tests after 6.1:**
- [ ] All three tabs render
- [ ] Loan Officer is default active
- [ ] Clicking another tab switches active state
- [ ] Active tab visually distinct (underline + bold/color)
- [ ] Transition animates (not instant jump)

### 6.2 Loan Officer panel
- Create `frontend/src/panels/LoanOfficerPanel.tsx`:
  - Yield stress score gauge (prominent)
  - All 4 financial output cards with deltas
  - Narrative placeholder (text area for AI narrative — shows static placeholder text until AI integration)
  - "Old System vs TerraLend" comparison block

**Tests after 6.2:**
- [ ] Panel renders with all components
- [ ] Financial data populates from mock
- [ ] Comparison block shows old vs new values
- [ ] Narrative placeholder visible with placeholder text
- [ ] Layout is clean and professional

### 6.3 Farmer panel
- Create `frontend/src/panels/FarmerPanel.tsx`:
  - "Your Loan Terms Today" summary card (large, friendly):
    - Interest rate (large font)
    - Monthly/seasonal payment estimate
    - "What's affecting your rate" — top contributing factor in plain text
  - "What could improve your terms" — simple bullet points
  - Seasonal outlook placeholder (next 30 days text)
  - Narrative placeholder (empathetic tone)

**Tests after 6.3:**
- [ ] Panel renders with summary card
- [ ] Interest rate displayed prominently
- [ ] Contributing factor shown in plain language (not technical indices)
- [ ] Layout feels friendly and non-technical
- [ ] Narrative placeholder visible

### 6.4 Climate Scientist panel
- Create `frontend/src/panels/ClimateScientistPanel.tsx`:
  - Raw index values table: all 5 climate inputs with labels and current values
  - Stress formula breakdown: bar chart or horizontal bars showing each factor's weighted contribution
  - Dominant factor highlighted
  - Narrative placeholder (technical tone)

**Tests after 6.4:**
- [ ] Panel renders with raw index table
- [ ] All 5 climate values displayed with correct labels
- [ ] Factor contribution bars rendered (weighted values)
- [ ] Dominant factor visually highlighted
- [ ] Layout is data-dense and technical-looking

### 6.5 Panel switching data persistence
- Verify: switching tabs does NOT trigger new API calls
- All panels read from the same state (hook)
- Simulation results persist across tab switches

**Tests after 6.5:**
- [ ] Switch from Loan Officer → Farmer → back: no API calls fired
- [ ] Simulated values persist across tab switches
- [ ] All panels show consistent data (same stress score, same rates)
- [ ] No flash of loading state on tab switch

---

## Task 7: Old System vs TerraLend Comparison

### 7.1 Comparison component
- Create `frontend/src/components/Comparison/ComparisonPanel.tsx`:
  - Two-column layout: "Old System" (left, muted) vs "TerraLend" (right, highlighted)
  - Rows: Rate, Basis, Update Frequency, Risk Model, Farmer Visibility
  - Old System column never changes (static values)
  - TerraLend column updates dynamically with simulation
  - Visual emphasis on the differences (color coding, arrows)

**Tests after 7.1:**
- [ ] Both columns render with correct data
- [ ] Old system values remain static after simulation
- [ ] TerraLend values update after simulation
- [ ] Visual distinction between columns (old = muted, new = highlighted)
- [ ] Rate difference shown prominently (delta between old and new)
- [ ] Responsive layout (stacks vertically on mobile)

---

## Task 8: Loading States & Error Handling

### 8.1 Loading state components
- Create `frontend/src/components/common/LoadingSpinner.tsx` — reusable spinner
- Create `frontend/src/components/common/ErrorBanner.tsx` — dismissable error message
- Create `frontend/src/components/common/Skeleton.tsx` — skeleton loading placeholder
- Add loading states to: map data load, financial panel, simulation, narrative

**Tests after 8.1:**
- [ ] Spinner renders and animates
- [ ] Error banner shows message and dismiss button
- [ ] Skeleton renders as gray placeholder blocks
- [ ] Financial panel shows skeletons during load
- [ ] Map shows spinner during region data fetch
- [ ] Error banner appears on failed API call

### 8.2 Empty state & placeholder
- "Select a region on the map to get started" when no region selected
- All panels show helpful placeholder content pre-selection
- Sliders disabled until region selected

**Tests after 8.2:**
- [ ] Empty state visible on initial load
- [ ] Sliders disabled before region selection
- [ ] Selecting a region removes empty state
- [ ] All panels show content after region selected

---

## Task 9: Visual Polish & Layout

### 9.1 Overall layout
- Header: TerraLend logo/name + tagline
- Layout: Map (top or left) | Panels + Controls (right or bottom)
- Tab navigation between panels
- Sliders in a collapsible sidebar or below the map
- Responsive breakpoints: desktop (1200px+), tablet (768px+), mobile (< 768px)

### 9.2 Color system & typography
- Define CSS custom properties for:
  - Primary colors (professional blue/green palette)
  - Stress color scale (green → yellow → orange → red)
  - Delta colors (green = good, red = bad)
  - Text hierarchy (headings, body, labels, values)
- Apply consistently across all components

### 9.3 Animations & micro-interactions
- Smooth transitions on: tab switch, data load, slider interaction
- Number values animate when changing (count-up effect)
- Map markers pulse briefly on data update
- Delta indicators fade in on change

**Tests after 9.1–9.3:**
- [ ] App looks professional and cohesive
- [ ] Works on 1920px, 1366px, 768px, and 375px widths
- [ ] All stress colors consistent across components
- [ ] Animations don't jank or cause layout shifts
- [ ] Accessible: text is readable, contrast ratios pass WCAG AA

---

## Summary Checklist

- [ ] Task 1: React Scaffold + Mock API Layer
- [ ] Task 2: Interactive US Map with Overlays
- [ ] Task 3: Region Selection & Data Loading
- [ ] Task 4: Financial Output Panel + Stress Gauge
- [ ] Task 5: Climate Shock Simulator (Sliders + Toggles)
- [ ] Task 6: Three-Tab Panel Navigation (Loan Officer, Farmer, Scientist)
- [ ] Task 7: Old System vs TerraLend Comparison
- [ ] Task 8: Loading States & Error Handling
- [ ] Task 9: Visual Polish & Layout
