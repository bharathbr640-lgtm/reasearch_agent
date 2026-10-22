# Milestone 2 Investigation Report: View 3 (Active Session), View 4 (Report View), & Test Gating

**Author**: `explorer_m2_3`  
**Date**: 2026-10-14  
**Target Milestone**: Milestone 2 (SPA Shell & High-Fidelity 4-View Layout)  
**Output Path**: `/Users/bharathbr/reasearch_agent/.agents/teamwork/explorer_m2_3/handoff.md`

---

## 1. Observation

Direct examination of the authoritative prototype (`/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html`), test suite (`research_orchestrator/tests/test_spa_structure.py`), and baseline pytest execution revealed the following concrete facts:

### A. Authoritative Prototype Structure for View 3 (`#view-active`)
In `stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` (lines 675–812):
1. **Container Element**:
   ```html
   <div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full" id="view-active">
   ```
2. **Breadcrumbs & Header**:
   - Breadcrumb navigation:
     - Dashboard button: `<button class="hover:text-indigo-600" onclick="switchView('dashboard')">Dashboard</button>`
     - Separator: `<span>/</span>`
     - Active indicator: `<span class="text-indigo-600 font-semibold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>Active Research Session</span>`
   - Session Header:
     - Title: `<span>Satellite Crop Yield Prediction</span>`
     - Session Badge: `<span class="text-xs font-mono px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-semibold uppercase">Session #AG-9042</span>`
     - Subtitle: `<p class="text-xs text-slate-500">Orchestrator dispatching parallel sub-agent workers across arXiv and Hugging Face repositories.</p>`
3. **Control Action Buttons**:
   - Pause / Resume toggle button:
     - ID: `id="btn-pause-session"`
     - Handler: `onclick="togglePauseResearch()"`
     - SVG icon: `id="icon-pause"`
     - Label: `<span id="label-pause">Pause Agents</span>`
   - "View Verified Report" CTA button:
     - Classes: `px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center gap-2 transition font-display`
     - Handler: `onclick="switchView('report')"`
     - Arrow SVG icon pointing right
4. **Overall Interactive Progress Bar Card**:
   - Outer container: `bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3`
   - Header with emerald pulsing dot: `<span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>`
   - Percentage text element: `<span class="text-indigo-600 font-mono" id="active-percent-text">78% Complete</span>`
   - Current stage text: `<span class="text-[11px] font-mono text-slate-500">Stage 3 of 4: Paper Finder Synthesizing</span>`
   - Progress bar track: `<div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">`
   - Progress bar fill: `<div class="bg-gradient-to-r from-indigo-500 to-indigo-600 h-2.5 rounded-full transition-all duration-700" id="active-progress-bar" style="width: 78%"></div>`
5. **4 Pipeline Agent State Cards (`grid grid-cols-1 md:grid-cols-4 gap-3.5`)**:
   - **01 Orchestrator**:
     - Style: `bg-white p-4 rounded-xl border border-emerald-200 shadow-sm space-y-2`
     - Badge: `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold">DONE</span>`
     - Description: `Specification defined into 3 research hypotheses & evaluation parameters.`
     - Sub-metric: Checkmark icon + `Spec locked in 1.4s` (`text-[10px] text-emerald-600 font-medium`)
   - **02 Project Finder**:
     - Style: `bg-white p-4 rounded-xl border border-emerald-200 shadow-sm space-y-2`
     - Badge: `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold">12 REPOS</span>`
     - Description: `Cloned metadata from GitHub, CropHarvest benchmarks & TorchGeo configs.`
     - Sub-metric: Checkmark icon + `Code analyzed` (`text-[10px] text-emerald-600 font-medium`)
   - **03 Paper Finder**:
     - Style: `bg-indigo-50/50 p-4 rounded-xl border border-indigo-300 shadow-sm space-y-2 relative overflow-hidden`
     - Badge: `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-600 text-white font-semibold animate-pulse">RUNNING</span>`
     - Description: `Semantic paper retrieval via arXiv embedding index. 18 relevant preprints indexed.`
     - Sub-metric: Ping dot (`animate-ping`) + `Filtering SOTA methods...` (`text-[10px] text-indigo-600 font-medium`)
   - **04 Evaluator**:
     - Style: `bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2 opacity-80`
     - Badge: `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">QUEUED</span>`
     - Description: `Awaiting Paper Finder completion to audit claims and score evidence base.`
     - Sub-metric: `Pending input feed` (`text-[10px] text-slate-400 font-medium`)
6. **Live Telemetry & Evidence Stream Console**:
   - Container: `bg-slate-900 text-slate-200 rounded-2xl p-5 border border-slate-800 shadow-xl space-y-3 font-mono`
   - Header: Green dot + `Live Agent Telemetry & Evidence Stream` + `STREAMING • 482 events`
   - Log Stream Element:
     ```html
     <div class="space-y-2 text-xs max-h-64 overflow-y-auto no-scrollbar font-normal text-slate-300" id="telemetry-log">
     ```
   - 6 Pre-populated initial telemetry event rows with colored agent tags:
     - `[16:42:01] [Orchestrator]` (text-indigo-400): Task formulated
     - `[16:42:04] [ProjectFinder]` (text-emerald-400): Extracted PyTorch repo: nasaharvest/crop-mask
     - `[16:42:07] [ProjectFinder]` (text-emerald-400): Verified HuggingFace model weight: ibm-nasa-geospatial/Prithvi-100M
     - `[16:42:12] [PaperFinder]` (text-purple-400): Matched arXiv:2308.12879
     - `[16:42:18] [PaperFinder]` (text-purple-400): Extracted metric: R² = 0.84
     - `[16:42:22] [Evaluator]` (text-amber-400): Gap detected: Current models lack validation under severe drought anomaly conditions.

---

### B. Authoritative Prototype Structure for View 4 (`#view-report`)
In `stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` (lines 815–979):
1. **Container Element**:
   ```html
   <div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full pb-24" id="view-report">
   ```
   *Note: `pb-24` ensures content is not obscured by the fixed bottom action bar.*
2. **Breadcrumbs & Report Header**:
   - Breadcrumbs: `Dashboard` (`switchView('dashboard')`) / `Research Runs` (`switchView('active')`) / `Report #REP-0824`
   - Title: `<h1 class="text-2xl font-bold tracking-tight text-slate-900 font-display">Crop Yield Prediction via Satellite & Weather</h1>`
   - Badge: `<span class="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold flex items-center gap-1 font-mono">VERIFIED REPORT</span>`
   - Confidence Pill: `Agent Confidence: 8.7 / 10` (`bg-indigo-50 border border-indigo-100 rounded-xl px-3 py-1.5`)
   - Return Button: `<button ... onclick="switchView('dashboard')">Back to Dashboard</button>`
3. **4-Metric Summary Ribbon (`grid grid-cols-2 md:grid-cols-4 gap-3.5`)**:
   - `Projects Analyzed`: `12` (`text-blue-700 font-extrabold text-2xl`), subtext `8 with open-source PyTorch weights`
   - `arXiv Papers Synthesized`: `18` (`text-purple-700 font-extrabold text-2xl`), subtext `Published between 2021 - 2024`
   - `Synthesized Findings`: `8` (`text-indigo-700 font-extrabold text-2xl`), subtext `Verified by cross-agent consensus`
   - `Unsolved Gaps Found`: `4` (`text-amber-600 font-extrabold text-2xl`), subtext `High commercial opportunity`
4. **Main Report Body Layout (`grid grid-cols-1 lg:grid-cols-4 gap-6 items-start`)**:
   - **Sticky Table of Contents Navigation (`aside.bg-white rounded-xl p-3 border border-slate-200/90 shadow-sm space-y-1 text-xs font-medium`)**:
     - Heading: `<div class="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">Report Sections</div>`
     - 6 Section Anchor Links:
       - `<a class="report-anchor active-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-1">01 Executive Summary</a>`
       - `<a class="report-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-2">02 Problem Definition</a>`
       - `<a class="report-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-3">03 Existing Repos & Models</a>`
       - `<a class="report-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-4">04 Comparative Matrix</a>`
       - `<a class="report-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-5">05 Identified Research Gaps</a>`
       - `<a class="report-anchor block px-3 py-2 rounded-lg text-slate-700 hover:bg-slate-50 transition" href="#rep-sec-6">06 Next Actionable Step</a>`
   - **Main Report Content Sections (`lg:col-span-3 space-y-6`)**:
     - **Section 01 Executive Summary (`#rep-sec-1`)**:
       - Container: `<section class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3" id="rep-sec-1">`
       - Heading with indigo dot: `01 Executive Summary`
       - Overview paragraph describing Sentinel-2 optical + Sentinel-1 SAR + ERA5-Land reanalysis with R² of 0.82 to 0.87.
       - Amber Callout Box:
         ```html
         <div class="p-3 bg-amber-50 rounded-xl border border-amber-200/80 text-xs text-amber-900">
           <strong class="font-semibold">Core Agent Finding:</strong> Over 70% of open-source repositories suffer from severe temporal data leakage due to non-contiguous train/test geographic splits. Implementing spatial leave-one-region-out cross validation drops claimed performance by ~14%, highlighting an immediate opportunity for rigorous modeling.
         </div>
         ```
     - **Section 04 Comparative Evaluation Matrix (`#rep-sec-4`)**:
       - Container: `<section class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4" id="rep-sec-4">`
       - Header with indigo dot, title, and `<span class="text-[10px] font-mono text-slate-400">Verified by Evaluator Agent</span>`
       - Responsive data table (`overflow-x-auto`):
         - Columns: `Architecture / Repo`, `Modality`, `Reported R²`, `Code Quality`, `Evaluation Status`
         - Row 1: `Prithvi-100M GeoFM` | `Multispectral ViT` | `0.86` (indigo-700 font-bold) | `Verified HF` (badge) | `Ready for fine-tune`
         - Row 2: `CropHarvest Bi-LSTM` | `Optical + ERA5` | `0.79` (indigo-700 font-bold) | `Apache 2.0` (badge) | `Baseline valid`
         - Row 3: `SatYield 3D-CNN` | `Sentinel-2 only` | `0.72` (slate-500 font-bold) | `No Lic.` (badge amber) | `Spatial leakage risk`
     - **Section 06 Recommended Next Step Card (`#rep-sec-6`)**:
       - Container: `<section class="bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-indigo-800 space-y-3" id="rep-sec-6">`
       - Badges: `RECOMMENDED PATH`, `Estimated Setup: 2 days`
       - Title: `Fine-tune Prithvi-100M with Spatially Disjoint Holdouts`
       - Body: Pre-trained weights from Hugging Face, spatial attention regression head, benchmark on USDA NASS ground truth dataset using block-level k-fold cross validation.
       - Action buttons:
         - `Export Starter Notebook (.ipynb)` (`onclick="showToast('Exported PyTorch scaffold starter notebook')"` )
         - `Add to Workspace Backlog` (`onclick="showToast('Research ticket added to workspace backlog')"` )
5. **Sticky Bottom Action Bar**:
   - Fixed Toolbar:
     ```html
     <div class="fixed bottom-0 right-0 left-64 bg-white/95 backdrop-blur border-t border-slate-200 px-8 py-3.5 flex items-center justify-between z-20 shadow-lg">
     ```
   - Left side: `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>Report generated and verified by 4 autonomous agents in 42.8 seconds</span>`
   - Right side:
     - Share Report button: `onclick="shareReport()"`
     - Export Full Spec (PDF) button: `onclick="exportFullSpec()"`

---

### C. Client-Side JavaScript Logic for Views 3 & 4
In `stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` (lines 983–1132):
```javascript
let activeResearchInterval = null;
let currentProgress = 78;
let isPaused = false;

// Telemetry event logs generator
function startLiveTelemetrySimulation() {
  if (activeResearchInterval) clearInterval(activeResearchInterval);
  const bar = document.getElementById('active-progress-bar');
  const txt = document.getElementById('active-percent-text');

  activeResearchInterval = setInterval(() => {
    if (isPaused) return;
    if (currentProgress < 98) {
      currentProgress += 3;
      if (bar) bar.style.width = currentProgress + '%';
      if (txt) txt.innerText = currentProgress + '% Complete';
    }
  }, 1800);
}

// Pause/Resume Agents toggle
function togglePauseResearch() {
  isPaused = !isPaused;
  const btn = document.getElementById('label-pause');
  if (isPaused) {
    if (btn) btn.innerText = 'Resume Agents';
    showToast('Multi-agent pipeline paused');
  } else {
    if (btn) btn.innerText = 'Pause Agents';
    showToast('Multi-agent pipeline resumed');
  }
}

// Report sharing
function shareReport() {
  navigator.clipboard?.writeText(window.location.href);
  showToast('Direct report link copied to clipboard!');
}

// Full specification export
function exportFullSpec() {
  showToast('Generating signed PDF specification package...');
  setTimeout(() => {
    showToast('Research Spec #REP-0824 downloaded successfully');
  }, 1200);
}
```

---

### D. Test Suite Gating & Baseline Test Run
1. Baseline test run command:
   ```bash
   cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/ -v
   ```
   **Observed Result**: `91 passed, 1 skipped in 2.91s`.
2. The single skipped test in the entire repository is:
   `tests/test_spa_structure.py::test_tier1_live_spa_view_containers_contract SKIPPED [ 97%]`
3. Source code of `test_tier1_live_spa_view_containers_contract` (`research_orchestrator/tests/test_spa_structure.py`, lines 130–144):
   ```python
   def test_tier1_live_spa_view_containers_contract(sync_client: TestClient):
       """When M2 unified workspace is deployed to static/index.html, verify 4 view containers on live server."""
       response = sync_client.get("/")
       assert response.status_code == 200
       soup = BeautifulSoup(response.text, "html.parser")

       # If M2 unified workspace layout has been deployed to static/index.html
       dash = soup.find(id="view-dashboard")
       if dash is not None:
           for vid in ["view-dashboard", "view-start", "view-active", "view-report"]:
               assert soup.find(id=vid) is not None, f"Live SPA missing view container #{vid}"
       else:
           # Pre-M2 stage: initial template verified by test_tier1_live_root_page_serves_html
           pytest.skip("M2 SPA layout not yet deployed to static/index.html (current milestone is M1)")
   ```
4. Current `static/index.html` (M1 simple chat template) contains `<div class="container">` and `<div id="chat">`, but has no `<div id="view-dashboard">`. Hence `dash` is `None` and pytest skips this test.
5. Headless Playwright Chromium tests in `tests/test_spa_structure.py`:
   - `test_tier4_playwright_zero_uncaught_errors`: PASSED against the prototype.
   - `test_tier4_playwright_view_switching_navigation`: PASSED against the prototype (verifies visibility toggling across `#view-start`, `#view-active`, `#view-report`, and `#view-dashboard`).

---

## 2. Logic Chain

1. **Premise 1 (Test Gating Mechanism)**: `test_tier1_live_spa_view_containers_contract` inspects the live response from `GET /`. If `soup.find(id="view-dashboard")` returns an element, it enforces that all four container IDs (`view-dashboard`, `view-start`, `view-active`, `view-report`) exist in the DOM.
2. **Premise 2 (Current State)**: In M1, `static/index.html` was the minimalist single-column chat page. Because `#view-dashboard` was not present, the test executed line 143 (`pytest.skip(...)`).
3. **Premise 3 (M2 Deployment)**: When `research_orchestrator/static/index.html` is replaced with the full unified workspace containing all 4 views (`#view-dashboard`, `#view-start`, `#view-active`, `#view-report`), `soup.find(id="view-dashboard")` will return the dashboard container.
4. **Premise 4 (Automatic Unskipping)**: The test enters the `if dash is not None:` branch and asserts that `view-dashboard`, `view-start`, `view-active`, and `view-report` are all present. Since all four IDs are present, all assertions succeed, `pytest.skip` is bypassed, and the test transitions from SKIPPED to PASSED.
5. **Premise 5 (Zero Regressions)**: Because `GET /` serves `static/index.html` with status 200, all other 91 tests (including `test_tier1_get_root_serves_html`, `test_tier1_live_root_page_serves_html`, all API contract tests, and Playwright tests) will continue to pass. The test suite will achieve 100% pass (92 passed, 0 skipped, 0 failed).

---

## 3. Caveats

1. **Milestone Scope Separation**:
   - In **Milestone 2**, the objective is static UI fidelity, full DOM structural compliance, and client-side view switching.
   - Dynamic message streaming from `POST /chat` and live agent event feeding into `#telemetry-log` are slated for **Milestone 3**.
   - Dynamic report hydration from `outputs/{session_id}/research_spec.json` is slated for **Milestone 4**.
2. **Fixed Bottom Action Bar Layout**:
   - The sticky action bar in View 4 has CSS class `left-64` (`fixed bottom-0 right-0 left-64`). This aligns with the fixed sidebar (`w-64`). On viewports where the sidebar is rendered, this avoids overlapping the sidebar.
3. **Table of Contents Anchors vs Rendered Sections**:
   - The prototype TOC lists 6 sections (`01 Executive Summary`, `02 Problem Definition`, `03 Existing Repos & Models`, `04 Comparative Matrix`, `05 Identified Research Gaps`, `06 Next Actionable Step`).
   - The prototype HTML explicitly renders sections `id="rep-sec-1"`, `id="rep-sec-4"`, and `id="rep-sec-6"`. `test_tier1_essential_spa_components_present` and `test_tier1_report_view_sections` specifically require `rep-sec-1`, `rep-sec-4`, and `rep-sec-6`. These must remain present with their exact IDs.
4. **No Caveats Beyond Above**.

---

## 4. Conclusion

1. **View 3 (`#view-active`) Implementation Requirements**:
   - Must use container `<div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full" id="view-active">`.
   - Must include breadcrumbs with Dashboard link and active session indicator.
   - Must include `#AG-9042` session badge and status subtitle.
   - Must include `#btn-pause-session`, `#icon-pause`, `#label-pause`, and `togglePauseResearch()` function.
   - Must include "View Verified Report" button invoking `switchView('report')`.
   - Must include progress bar with `#active-progress-bar`, `#active-percent-text`, and current stage text.
   - Must include 4 pipeline agent status cards for Orchestrator (`DONE`), Project Finder (`12 REPOS`), Paper Finder (`RUNNING`), and Evaluator (`QUEUED`).
   - Must include `#telemetry-log` inside dark slate container pre-populated with timestamped telemetry events.

2. **View 4 (`#view-report`) Implementation Requirements**:
   - Must use container `<div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full pb-24" id="view-report">`.
   - Must include breadcrumbs, title, `VERIFIED REPORT` badge, confidence score `8.7 / 10`, and `Back to Dashboard` button.
   - Must include 4-metric ribbon (Projects: 12, Papers: 18, Findings: 8, Gaps: 4).
   - Must include sticky Table of Contents indexing 6 sections with `#rep-sec-1` marked as `active-anchor`.
   - Must include Section 01 (`#rep-sec-1`) with amber callout box (`Core Agent Finding: ...`).
   - Must include Section 04 (`#rep-sec-4`) with 5-column Comparative Evaluation Matrix data table.
   - Must include Section 06 (`#rep-sec-6`) dark gradient Recommended Next Step card.
   - Must include sticky bottom toolbar with `Share Report` (`shareReport()`) and `Export Full Research Spec (PDF)` (`exportFullSpec()`).

3. **Test Gating Verification**:
   - Once the unified workspace is placed into `research_orchestrator/static/index.html`, `test_tier1_live_spa_view_containers_contract` will immediately detect `#view-dashboard` on `GET /`, assert all 4 view containers, unskip, and pass.

---

## 5. Verification Method

### A. Automated PyTest Execution
Run the full test suite from the repository root:
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/ -v
```
**Expected Outcome**: 92 passed, 0 skipped, 0 failed.

To run only the SPA DOM and Playwright test suite:
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/test_spa_structure.py -v
```
**Expected Outcome**: All 10 tests in `test_spa_structure.py` pass with 0 skipped.

### B. Playwright Headless Chromium Direct Verification
Verify that both the prototype and live SPA execute in headless Chromium without console errors or uncaught exceptions:
```bash
cd /Users/bharathbr/reasearch_agent/research_orchestrator && python3 -m pytest tests/test_spa_structure.py -k "playwright" -v
```
**Expected Outcome**:
- `test_tier4_playwright_zero_uncaught_errors`: PASSED
- `test_tier4_playwright_view_switching_navigation`: PASSED

### C. Live Server DOM Inspection
Verify the 4 view containers and key elements against the live FastAPI app:
```python
from starlette.testclient import TestClient
from bs4 import BeautifulSoup
from app.main import app

client = TestClient(app)
resp = client.get("/")
assert resp.status_code == 200
soup = BeautifulSoup(resp.text, "html.parser")
assert soup.find(id="view-dashboard") is not None
assert soup.find(id="view-start") is not None
assert soup.find(id="view-active") is not None
assert soup.find(id="view-report") is not None
assert soup.find(id="btn-pause-session") is not None
assert soup.find(id="active-progress-bar") is not None
assert soup.find(id="telemetry-log") is not None
assert soup.find(id="rep-sec-1") is not None
assert soup.find(id="rep-sec-4") is not None
assert soup.find(id="rep-sec-6") is not None
```

### D. Invalidation Conditions
- Any removal or renaming of `#view-active`, `#view-report`, `#btn-pause-session`, `#active-progress-bar`, `#telemetry-log`, `#rep-sec-1`, `#rep-sec-4`, or `#rep-sec-6`.
- Missing or malformed JavaScript functions (`switchView`, `togglePauseResearch`, `startLiveTelemetrySimulation`, `shareReport`, `exportFullSpec`).
- Introduction of any new backend dependencies in `requirements.txt`.
