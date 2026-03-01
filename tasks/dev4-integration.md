# Developer 4 (All Devs Together): Integration & Demo Hardening

**Scope**: Wire the three independent workstreams together, end-to-end testing, demo hardening.
**When**: After all three developers have completed their individual task lists.
**Who**: All three developers collaborate. Assign specific integration subtasks to whoever built the relevant piece.

---

## Task 1: Connect Frontend to Live Backend

### 1.1 Swap mock API layer for real HTTP calls
- In `frontend/src/api/client.ts`: set `USE_MOCK = false`
- Verify Vite proxy correctly forwards `/api/*` to `localhost:8000`
- Fix any type mismatches between frontend interfaces and actual backend responses
- Update any mock data fields that differ from real API response shapes

**Tests after 1.1:**
- [ ] `GET /regions` returns data and map populates from real backend
- [ ] Region click loads real climate + financial data
- [ ] All data types match (no TypeScript errors in console)
- [ ] Fallback: re-enable mock mode and verify frontend still works standalone
- [ ] Network tab shows correct API calls being made

### 1.2 Wire simulation to live backend
- Frontend sliders → `POST /simulate` to real backend
- Verify deltas compute correctly (real baseline vs simulated)
- Verify debouncing works with real network latency

**Tests after 1.2:**
- [ ] Moving temperature slider → backend receives correct POST body
- [ ] Financial panel updates with backend-computed values (not mock)
- [ ] Deltas match: (simulated rate - baseline rate) displayed correctly
- [ ] Rapid slider changes don't flood backend (debounce works)
- [ ] Reset to baseline restores real baseline values

---

## Task 2: Wire AI Narratives into Frontend

### 2.1 Narrative display integration
- Replace placeholder text in all three panels with real narrative from `GET /region/{id}/narrative?panel=X`
- Implement streaming display:
  - Use `EventSource` or `fetch()` with `ReadableStream` to connect to SSE endpoint
  - Text appears word-by-word / chunk-by-chunk
  - Show loading indicator while waiting for first chunk
- Cache narratives client-side: don't re-fetch on tab switch if climate inputs haven't changed

**Tests after 2.1:**
- [ ] Loan Officer panel shows Claude-generated narrative (clinical tone)
- [ ] Farmer panel shows Claude-generated narrative (empathetic tone)
- [ ] Scientist panel shows Claude-generated narrative (technical tone)
- [ ] Switching tabs doesn't trigger new Claude call (cached)
- [ ] Changing a slider triggers narrative regeneration
- [ ] Streaming text appears progressively (not all-at-once)
- [ ] Fallback text appears if Claude is slow or fails
- [ ] Loading indicator visible during narrative generation

### 2.2 Underwriting assistant UI integration
- Add "Generate Underwriting Proposal" button to Loan Officer panel
- On click: call `POST /region/{id}/underwriting`
- Display: Rate Floor, Rate Ceiling, Recommended Rate, Rationale text
- Add "Export Risk Memo" button → calls `POST /region/{id}/memo` → triggers download

**Tests after 2.2:**
- [ ] Button visible on Loan Officer panel
- [ ] Click triggers API call and shows loading state
- [ ] Floor/Ceiling/Recommended values displayed after response
- [ ] Rationale text rendered below rate bounds
- [ ] "Export Risk Memo" triggers file download
- [ ] Downloaded memo contains actual region data (not placeholder)
- [ ] Handles API failure gracefully (shows error, not crash)

### 2.3 Simulation Lab tab integration
- Add **Simulation Lab** as a 4th tab (or sub-section within Loan Officer)
- "Run Climate Stress Test" button → calls `POST /simulate/batch`
- Display Climate Resilience Report:
  - Table of 4 archetype results (name, stress score, interest rate, PD)
  - Spread visualization (best vs worst rate as a range bar)
  - AI-generated summary text
- Loading state: "Processing 4 climate scenarios..." with progress indication

**Tests after 2.3:**
- [ ] Simulation Lab tab accessible
- [ ] "Run" button triggers batch simulation API call
- [ ] Results table shows all 4 archetypes with correct values
- [ ] Spread bar/visualization renders correctly
- [ ] AI summary text displayed
- [ ] Loading state visible during 2-3 second processing
- [ ] Heuristic summary shown if Claude fails

---

## Task 3: End-to-End Flow Verification

### 3.1 Full demo flow test
Walk through the exact demo script from PRD Section 11.2:

1. [ ] App loads — map visible with colored region markers
2. [ ] Click Central Valley, CA — overlays render, data loads
3. [ ] Financial outputs populate in < 2 seconds
4. [ ] Loan Officer view shows clinical narrative
5. [ ] Switch to Farmer view — same data, different tone
6. [ ] Switch to Climate Scientist view — raw indices visible
7. [ ] Move temperature slider +3°C — rate increases visibly
8. [ ] Trigger drought shock toggle — stress spikes, rate jumps
9. [ ] Claude narrative updates within 3 seconds
10. [ ] Return sliders to baseline — rate recovers
11. [ ] Open Simulation Lab — run stress test
12. [ ] Resilience report shows 4 archetype results + spread
13. [ ] Generate underwriting proposal — floor/ceiling displayed
14. [ ] Export risk memo — file downloads

### 3.2 Cross-component consistency
- [ ] Stress score in gauge matches stress score in scientist panel
- [ ] Interest rate in financial panel matches rate in comparison panel
- [ ] Insurance premium in financial panel matches value in farmer panel
- [ ] All panels show identical underlying data (no stale values)
- [ ] Simulation results are consistent across all panels after slider change

### 3.3 Error resilience
- [ ] Kill backend → frontend shows error state, doesn't crash
- [ ] Block Bedrock credentials → all AI features gracefully fall back
- [ ] Set `DEMO_MODE=true` → everything works with mock data
- [ ] Slow network simulation (throttle to 3G) → app remains usable
- [ ] Rapidly clicking regions → no race conditions in displayed data

---

## Task 4: Demo Mode Hardening

### 4.1 Deterministic demo mode
- Create `DEMO_MODE=true` behavior:
  - All climate data from mocks (no NOAA calls)
  - All AI narratives from fallback templates (no Bedrock calls)
  - App is fully functional with zero external dependencies
- Test: disconnect wifi → app still works completely

### 4.2 Demo seed data verification
- For demo region (Central Valley, CA), verify:
  - [ ] Base climate data produces moderate stress (~40-50) — interesting but not alarming
  - [ ] Base financial outputs are in realistic range (rate ~5.5-6.5%)
  - [ ] Temperature +3°C produces noticeable rate increase (~1-2%)
  - [ ] Drought shock produces dramatic rate jump (~2-3% increase)
  - [ ] Delta between old system rate and TerraLend rate is meaningful and favorable
  - [ ] Batch simulation produces a 2-4% spread between best and worst

### 4.3 Performance verification
- [ ] Region select → full data display: < 2 seconds
- [ ] Slider release → financial update: < 2 seconds
- [ ] Claude narrative: < 3 seconds (streaming first token)
- [ ] Batch simulation: < 5 seconds total
- [ ] Tab switch: instant (< 100ms)
- [ ] No memory leaks on repeated region switches (check DevTools)

---

## Task 5: Final Polish

### 5.1 Comparison panel positioning
- Ensure "Old System vs TerraLend" comparison is immediately visible on load (PRD: "awe first")
- Should be the first thing judges see before interacting with anything

### 5.2 Error message cleanup
- No raw error objects shown to user
- No console errors in production build
- Loading states for every async operation
- Graceful degradation messaging

### 5.3 Build & deployment
- [ ] `npm run build` succeeds with no warnings
- [ ] Backend starts clean: `python -m uvicorn backend.main:app`
- [ ] Create `start.sh` script that launches both backend and frontend
- [ ] Document startup instructions in README.md
- [ ] Test with ngrok for remote demo access

---

## Summary Checklist

- [ ] Task 1: Frontend ↔ Backend API Connection
- [ ] Task 2: AI Narrative + Simulation Lab UI Wiring
- [ ] Task 3: End-to-End Flow Verification
- [ ] Task 4: Demo Mode Hardening
- [ ] Task 5: Final Polish & Deployment
