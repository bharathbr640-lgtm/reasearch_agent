# Milestone 2 Investigation Report: View 1 (Dashboard) & View 2 (Start Session View)

**Author**: `explorer_m2_2`  
**Milestone**: M2 (SPA Shell & High-Fidelity 4-View Layout)  
**Authoritative Prototype**: `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html`  
**Target Destination**: `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html`  
**Verification Baseline**: `research_orchestrator/tests/test_spa_structure.py`

---

## 1. Observation

Direct inspection of `stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` and `research_orchestrator/tests/test_spa_structure.py` revealed the following exact DOM locations and script definitions:

### 1.1 View 1: Dashboard (`#view-dashboard`)
- **Location in Prototype**: Lines 200–531.
- **Top-level Container**:
  ```html
  <div class="flex-1 flex overflow-hidden w-full" id="view-dashboard">
  ```
  *(Note: Visible by default; hidden when navigating away by adding `hidden` class).*
- **Sub-components Observed**:
  1. **Header Row (Lines 204–230)**:
     - `data-purpose="welcome-banner"`.
     - Status badge: `Workspace Active` with animated pulsing emerald/indigo dot `<span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>`.
     - Heading: `Good evening, Bharath.` (`text-2xl font-bold tracking-tight text-slate-900 font-display`).
     - Subtitle: `Turn a project idea into evidence-based research.` (`text-xs text-slate-500`).
     - Search input: `input` with search SVG, placeholder `"Search research, papers..."`.
     - Notification button: Bell SVG with `onclick="showToast('You have 2 agent completion alerts')"`.
  2. **Hero Overview Card (Lines 231–264)**:
     - Container: `data-purpose="hero-overview-card"` with gradient `bg-gradient-to-r from-[#17143a] via-[#241154] to-[#1a1444]` and radial dot grid texture.
     - Badges: `AI-POWERED RESEARCH` (`font-mono`) and `GitHub • Hugging Face` pill.
     - Copy: `From problem statement <span class="text-indigo-300">to verified research.</span>`
     - Subtitle: `Discover what has already been built, what has already been researched, and where the real gap is.`
     - Primary CTA: `Read Research Report` button with arrow icon, `onclick="switchView('report')"`.
  3. **Problem Statement Intake Section (Lines 265–302)**:
     - Container: `data-purpose="input-section"` (`bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4`).
     - Step pill: `01` indigo circle. Title: `Start with your problem`. Subtitle: `The Orchestrator will clarify the spec before research begins.`
     - Live character counter: `<span class="text-[10px] font-mono text-slate-400" id="dash-char-count">72 / 2500</span>`.
     - Problem textarea: `<textarea id="dashboard-input" oninput="updateDashboardCharCount(this)" rows="3">Build a system that predicts crop yield using satellite imagery and weather data.</textarea>`.
     - Suggested domains row: 5 clickable pills:
       - `Computer Vision` (`onclick="appendDomain('Computer Vision')"`)
       - `NLP` (`onclick="appendDomain('NLP')"`)
       - `Time Series` (`onclick="appendDomain('Time Series')"`)
       - `Recommendation` (`onclick="appendDomain('Recommendation')"`)
       - `Robotics` (`onclick="appendDomain('Robotics')"`)
     - Submit CTA: `Start Research` button (`onclick="startResearchProcess()"`).
  4. **4-Stage Research Workflow Grid (Lines 303–430)**:
     - Container: `data-purpose="research-workflow-section"`.
     - Header: Step `02` pill, title `Research workflow`, subtitle `Autonomous multi-agent execution pipeline`, and link `View live pipeline →` (`onclick="switchView('active')"`).
     - 4 interactive cards (`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5`), each clickable with `onclick="switchView('active')"`:
       - Step 1: Orchestrator -> `01` indigo pill, badge `Active` (`bg-indigo-50 text-indigo-700`), 3 items with checkmark SVG (`Understand problem`, `Ask clarifying questions`, `Create research spec`), status `Ready to prompt`.
       - Step 2: Project Finder -> `02` emerald pill, badge `Ready` (`bg-emerald-50 text-emerald-700`), 3 items (`Search GitHub repos`, `Search Hugging Face`, `Analyze implementations`), coverage `Full access`.
       - Step 3: Paper Finder -> `03` purple pill, badge `Queued` (`bg-purple-50 text-purple-700`), 3 items (`Semantic paper search`, `Extract methods`, `Find related work`), arXiv index `Semantic API`.
       - Step 4: Evaluator -> `04` amber pill, badge `Pending` (`bg-amber-50 text-amber-700`), 3 items (`Verify relevance`, `Compare evidence`, `Identify research gaps`), synthesis `Final audit`.
  5. **Dashboard Right Sidebar (Lines 432–530)**:
     - Container: `<aside class="w-80 flex-shrink-0 bg-white border-l border-slate-200/90 p-5 overflow-y-auto space-y-5">`.
     - **Recent research rail** (`data-purpose="recent-research-section"`):
       - Header with `View all →` (`onclick="switchView('report')"`).
       - 4 run items (all clickable `onclick="switchView('report')"`):
         - `Satellite crop yield prediction` (2 days ago, emerald dot).
         - `LLM for medical report analysis` (3 days ago, blue dot).
         - `Real-time object detection` (1 week ago, indigo dot).
         - `Soil moisture prediction using IoT` (1 week ago, amber dot).
     - **Research Snapshot 2x2 grid** (`data-purpose="metrics-grid"`):
       - 4 metric tiles (each clickable `onclick="switchView('report')"`):
         - `12` Projects found (blue)
         - `18` Papers found (purple)
         - `4` Gaps identified (amber)
         - `4` Verified reports (emerald)
     - **Research Quality Gauge section**:
       - Badge `VERIFIED` (`bg-emerald-50 text-emerald-700`).
       - Score `83%` (`Strong evidence base`).
       - Circular SVG radial gauge: `viewbox="0 0 36 36"` with `-rotate-90`, background ring `stroke-width="3.5"`, foreground stroke `stroke-dasharray="83, 100"`.
       - Linear indicator: `w-full bg-slate-200 rounded-full h-1.5` with child `bg-indigo-600 h-1.5 rounded-full style="width: 83%"`.

---

### 1.2 View 2: Start Session View (`#view-start`)
- **Location in Prototype**: Lines 535–674.
- **Top-level Container**:
  ```html
  <div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full" id="view-start">
  ```
  *(Note: Hidden by default with `hidden` class).*
- **Sub-components Observed**:
  1. **Header with Breadcrumbs & Cancel Button (Lines 536–551)**:
     - Breadcrumb navigation: `<button onclick="switchView('dashboard')">Dashboard</button> <span>/</span> <span class="text-slate-800 font-semibold">New Research Intake</span>`.
     - Heading: `Start a New Research Session`.
     - Subtitle: `Provide an initial objective. Our multi-agent system will cross-reference state-of-the-art literature & codebases.`.
     - Action: `Cancel` button with back arrow SVG, `onclick="switchView('dashboard')"`.
  2. **Problem Intake Card (Lines 555–596)**:
     - Label: `1` circle + `Describe your research problem or project vision`.
     - Live character counter: `<span class="text-xs font-mono text-slate-400" id="start-char-count">118 / 2500</span>`.
     - Textarea: `<textarea id="start-problem-textarea" oninput="updateStartCharCount(this)" rows="4">Build an automated system that predicts regional crop yield using multi-spectral satellite imagery and temporal weather data.</textarea>`.
     - 4 Optional context tag chips:
       - `+ Domain: Agritech` -> `onclick="addContextTag(this, 'Domain: Agritech &amp; Remote Sensing')"`
       - `+ Dataset: Sentinel-2` -> `onclick="addContextTag(this, 'Dataset: Sentinel-2 &amp; MODIS')"`
       - `+ Tech: PyTorch ViT` -> `onclick="addContextTag(this, 'Tech: PyTorch / Vision Transformer')"`
       - `+ Constraint: Low-latency` -> `onclick="addContextTag(this, 'Constraint: Low-latency inference &lt; 200ms')"`
     - Status footer: Green checkmark SVG with `Orchestrator pre-checks passed`.
     - Submit CTA: `Start Research Pipeline` button (`onclick="startResearchProcess()"`).
  3. **4 Recommended Benchmark Preset Cards (Lines 598–633)**:
     - Header: `RECOMMENDED BENCHMARK TEST CASES`, right label: `Click to fill`.
     - 2x2 grid of preset cards, each calling `selectTestCase(title, description)` on click:
       - Preset 1: `Satellite Crop Yield` (Agritech badge) -> Sentinel-2 multispectral + weather variables.
         `onclick="selectTestCase('Crop Yield Prediction with Satellite Imagery', 'Predict crop yield across regional farmlands using Sentinel-2 multispectral imagery and daily weather variables (soil moisture, temperature) to forecast output 30 days before harvest.')"`
       - Preset 2: `Clinical LLM Summaries` (Healthcare badge) -> HIPAA-compliant EHR note summarization.
         `onclick="selectTestCase('Clinical LLM for Discharge Summaries', 'Design a privacy-preserving Clinical LLM system that ingests unstructured EHR notes and outputs compliant discharge summaries with verified citations to medical guidelines.')"`
       - Preset 3: `Edge Drone Detection` (Edge AI badge) -> Lightweight YOLO/MobileNet on Jetson Nano (<5W, >30FPS).
         `onclick="selectTestCase('Real-time Edge Drone Object Detection', 'Deploy a lightweight YOLO/MobileNet model on Jetson Nano capable of detecting agricultural pests in high-resolution video streams at &gt;30 FPS.')"`
       - Preset 4: `High-Freq Tick Anomaly` (FinTech badge) -> VAE & diffusion temporal baselines on order books.
         `onclick="selectTestCase('Financial Time Series Anomaly Engine', 'Detect market flash anomalies across high-frequency tick data using variational autoencoders and diffusion-based temporal baselines.')"`
  4. **Autonomous Pipeline Phases Side Card (Lines 636–672)**:
     - Container: `bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4`.
     - Title: `AUTONOMOUS PIPELINE PHASES`.
     - Subtitle: `When you launch, our specialized autonomous sub-agents execute sequentially:`.
     - 4 Sequential items:
       - 1: `Problem Deconstruction` (Orchestrator query expansions & taxonomic parameters).
       - 2: `Codebase Discovery` (Project Finder GitHub API & Hugging Face search).
       - 3: `Literature Synthesis` (Paper Finder arXiv semantic embeddings).
       - 4: `Gap Analysis & Audit` (Evaluator benchmark discrepancies & verified report).
     - Execution metric callout: `Average duration: ~45 seconds across 4 agent instances with parallel verification.`.

---

### 1.3 JavaScript Functions (Lines 984–1086)
- Prototype lines 1039–1086 define the exact interaction handlers:
  - `appendDomain(domain)`: Checks if domain exists in `#dashboard-input`, appends `" [" + domain + "]"`, updates character count, and triggers `showToast`.
  - `updateDashboardCharCount(el)`: Updates `#dash-char-count` to `${el.value.length} / 2500`.
  - `updateStartCharCount(el)`: Updates `#start-char-count` to `${el.value.length} / 2500`.
  - `selectTestCase(title, description)`: Sets `#start-problem-textarea.value = description`, updates start character count, and displays toast `Loaded benchmark: ${title}`.
  - `addContextTag(btn, tagText)`: Appends `" (" + tagText + ")"` to `#start-problem-textarea`, highlights button with indigo styles, updates character count, and displays toast `Tag appended: ${tagText}`.
  - `startResearchProcess()`: Displays toast `Initializing multi-agent pipeline...`, sets `currentProgress = 25`, updates `#active-progress-bar` to `25%` and text to `25% - Orchestrator parsing problem`, and calls `switchView('active')`.

---

## 2. Logic Chain

1. **Contract Compliance**:
   - `test_spa_structure.py::test_tier1_essential_spa_components_present` requires IDs `dashboard-input`, `dash-char-count`, `start-problem-textarea`, and `start-char-count`.
   - `test_spa_structure.py::test_tier1_dashboard_workflow_and_metrics` requires text tokens `"NLP"`, `"Computer Vision"`, `"Orchestrator"`, `"Project Finder"`, `"Paper Finder"`, and `"Evaluator"`.
   - `test_spa_structure.py::test_tier1_start_view_presets_and_intake` requires text tokens `"Crop Yield"`, `"Clinical LLM"`, or `"Drone"`.
   - `test_spa_structure.py::test_tier1_live_spa_view_containers_contract` checks for presence of `view-dashboard` and `view-start` alongside `view-active` and `view-report`.
   - All these exact IDs and text strings are directly present in the extracted markup.

2. **Visual Hierarchy & Styling Fidelity**:
   - View 1 uses a 2-column layout with horizontal flex: `<main class="flex-1 overflow-y-auto ...">` and `<aside class="w-80 flex-shrink-0 ...">`.
   - View 2 uses a CSS grid: `grid grid-cols-1 lg:grid-cols-3 gap-6 items-start` where the form is `lg:col-span-2` and the explanatory card is 1 column.
   - All design tokens match the Tailwind configuration (Inter, Plus Jakarta Sans, JetBrains Mono, indigo/emerald/purple/amber color coding).

3. **Routing Integration**:
   - `switchView(viewName)` seamlessly hides inactive views by toggling Tailwind's `hidden` class and updates navigation active indicators (`active-nav`).
   - When coupled with `explorer_m2_1`'s hash router (`#/dashboard`, `#/start`), callers can either call `switchView(name)` or set `window.location.hash = '#/' + name`.

---

## 3. Caveats

- **Active / Paused Telemetry Simulation**: In Milestone 2, `startResearchProcess()` sets `currentProgress = 25` and opens View 3 (`active`). In Milestone 3, this function will also dispatch `POST /chat` with the user's prompt. To prepare for M3, the Worker should ensure that `startResearchProcess()` reads the prompt value from either `#start-problem-textarea` or `#dashboard-input`.
- **Character Count Initial State**: In the prototype, `#dashboard-input` has default value length 72, matching `#dash-char-count` ("72 / 2500"). `#start-problem-textarea` has default length 118, matching `#start-char-count` ("118 / 2500"). If default text is altered, the initial counter string must be updated to match.
- No other caveats.

---

## 4. Conclusion & Drop-In Code Deliverables for Worker

Below is the complete, drop-in code for View 1, View 2, and their supporting JavaScript functions.

### 4.1 Exact HTML Markup for View 1: Dashboard (`#view-dashboard`)

```html
<!-- ============================================================== -->
<!-- VIEW 1: DASHBOARD                                              -->
<!-- ============================================================== -->
<div class="flex-1 flex overflow-hidden w-full" id="view-dashboard">
  <!-- Main Scrollable Area -->
  <main class="flex-1 overflow-y-auto px-8 py-6 space-y-6">
    <!-- Top Header Row -->
    <div class="flex items-center justify-between pb-1">
      <div class="space-y-1" data-purpose="welcome-banner">
        <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-100/80 text-indigo-700 text-[11px] font-medium">
          <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
          Workspace Active
        </div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 font-display">
          Good evening, Bharath.
        </h1>
        <p class="text-xs text-slate-500">
          Turn a project idea into evidence-based research.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <div class="relative">
          <input class="pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 w-64 shadow-sm" placeholder="Search research, papers..." type="text"/>
          <svg class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24">
            <path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" stroke-linecap="round" stroke-linejoin="round"></path>
          </svg>
        </div>
        <button aria-label="Notifications" class="w-8 h-8 rounded-xl border border-slate-200 bg-white flex items-center justify-center text-slate-600 hover:text-slate-900 shadow-sm transition" onclick="showToast('You have 2 agent completion alerts')" type="button">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.8" viewbox="0 0 24 24">
            <path d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" stroke-linecap="round" stroke-linejoin="round"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- BEGIN: HeroCard (wide) -->
    <section class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#17143a] via-[#241154] to-[#1a1444] p-6 text-white shadow-lg shadow-indigo-950/15 border border-indigo-900/40" data-purpose="hero-overview-card">
      <div class="absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:14px_14px] pointer-events-none"></div>
      <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div class="space-y-2 max-w-xl">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-md bg-white/10 text-indigo-200 border border-white/10 font-mono">
              AI-POWERED RESEARCH
            </span>
            <div class="flex items-center gap-1.5 text-[10px] bg-white/10 px-2.5 py-0.5 rounded-full text-indigo-100">
              <span>GitHub</span>
              <span class="text-indigo-400">•</span>
              <span>Hugging Face</span>
            </div>
          </div>
          <h2 class="text-xl font-extrabold text-white tracking-tight font-display">
            From problem statement <span class="text-indigo-300">to verified research.</span>
          </h2>
          <p class="text-xs text-indigo-100/80 leading-relaxed font-normal">
            Discover what has already been built, what has already been researched, and where the real gap is.
          </p>
        </div>
        <div class="flex-shrink-0">
          <button class="py-2.5 px-5 rounded-xl bg-white text-slate-900 font-semibold text-xs tracking-tight shadow-md hover:bg-slate-50 active:scale-[0.98] transition flex items-center justify-center gap-2 font-display" onclick="switchView('report')" type="button">
            <span>Read Research Report</span>
            <svg class="w-3.5 h-3.5 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24">
              <path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </button>
        </div>
      </div>
    </section>
    <!-- END: HeroCard -->

    <!-- BEGIN: ProblemStatementInput (wide desktop) -->
    <section class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4" data-purpose="input-section">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold text-[11px]">01</span>
          <div>
            <h3 class="text-sm font-bold text-slate-900 tracking-tight font-display">Start with your problem</h3>
            <p class="text-[11px] text-slate-500">The Orchestrator will clarify the spec before research begins.</p>
          </div>
        </div>
        <span class="text-[10px] font-mono text-slate-400" id="dash-char-count">72 / 2500</span>
      </div>
      <!-- Input box area -->
      <div class="relative rounded-xl border border-slate-200 bg-slate-50/60 p-3 focus-within:border-indigo-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100 transition">
        <textarea class="w-full text-xs text-slate-800 placeholder-slate-400 bg-transparent border-0 p-0 focus:ring-0 resize-none font-normal leading-relaxed" id="dashboard-input" oninput="updateDashboardCharCount(this)" placeholder="Example: Build a system that predicts crop yield using satellite imagery and weather data." rows="3">Build a system that predicts crop yield using satellite imagery and weather data.</textarea>
      </div>
      <!-- Domains & CTA row -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">Suggested domains:</span>
          <div class="flex flex-wrap gap-1.5">
            <button class="text-[11px] font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 px-2.5 py-1 rounded-full border border-slate-200/70 transition" onclick="appendDomain('Computer Vision')" type="button">Computer Vision</button>
            <button class="text-[11px] font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 px-2.5 py-1 rounded-full border border-slate-200/70 transition" onclick="appendDomain('NLP')" type="button">NLP</button>
            <button class="text-[11px] font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 px-2.5 py-1 rounded-full border border-slate-200/70 transition" onclick="appendDomain('Time Series')" type="button">Time Series</button>
            <button class="text-[11px] font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 px-2.5 py-1 rounded-full border border-slate-200/70 transition" onclick="appendDomain('Recommendation')" type="button">Recommendation</button>
            <button class="text-[11px] font-medium bg-slate-100 text-slate-700 hover:bg-slate-200/70 px-2.5 py-1 rounded-full border border-slate-200/70 transition" onclick="appendDomain('Robotics')" type="button">Robotics</button>
          </div>
        </div>
        <button class="py-2.5 px-5 rounded-xl bg-indigo-600 text-white font-semibold text-xs tracking-tight shadow-sm shadow-indigo-600/30 hover:bg-indigo-700 active:scale-[0.98] transition flex items-center justify-center gap-2 font-display self-end md:self-auto" onclick="startResearchProcess()" type="button">
          <span>Start Research</span>
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.2" viewbox="0 0 24 24">
            <path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke-linecap="round" stroke-linejoin="round"></path>
          </svg>
        </button>
      </div>
    </section>
    <!-- END: ProblemStatementInput -->

    <!-- BEGIN: ResearchWorkflow (4-Column Pipeline Grid) -->
    <section class="space-y-3" data-purpose="research-workflow-section">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="flex items-center justify-center w-5 h-5 rounded-full bg-slate-200 text-slate-700 font-bold text-[11px]">02</span>
          <div>
            <h3 class="text-sm font-bold text-slate-900 tracking-tight font-display">Research workflow</h3>
            <p class="text-[11px] text-slate-500">Autonomous multi-agent execution pipeline</p>
          </div>
        </div>
        <span class="text-xs font-semibold text-indigo-600 font-display cursor-pointer hover:underline" onclick="switchView('active')">View live pipeline →</span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <!-- Step 1: Orchestrator -->
        <article class="bg-white rounded-xl p-4 border border-indigo-200 shadow-sm relative flex flex-col justify-between hover:border-indigo-400 transition cursor-pointer" onclick="switchView('active')">
          <div>
            <div class="flex items-center gap-2 mb-2.5">
              <span class="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center">01</span>
              <h4 class="text-xs font-bold text-slate-900 font-display">Orchestrator</h4>
              <span class="ml-auto text-[9px] font-semibold uppercase tracking-wide bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded border border-indigo-100 font-mono">Active</span>
            </div>
            <ul class="text-[11px] text-slate-600 space-y-1.5 pl-0.5">
              <li class="flex items-center gap-1.5">
                <svg class="w-3 h-3 text-indigo-600 flex-shrink-0" fill="currentColor" viewbox="0 0 20 20"><path clip-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill-rule="evenodd"></path></svg>
                <span>Understand problem</span>
              </li>
              <li class="flex items-center gap-1.5">
                <svg class="w-3 h-3 text-indigo-600 flex-shrink-0" fill="currentColor" viewbox="0 0 20 20"><path clip-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill-rule="evenodd"></path></svg>
                <span>Ask clarifying questions</span>
              </li>
              <li class="flex items-center gap-1.5">
                <svg class="w-3 h-3 text-indigo-600 flex-shrink-0" fill="currentColor" viewbox="0 0 20 20"><path clip-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill-rule="evenodd"></path></svg>
                <span>Create research spec</span>
              </li>
            </ul>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
            <span>Status</span>
            <span class="text-indigo-600 font-medium">Ready to prompt</span>
          </div>
        </article>
        <!-- Step 2: Project Finder -->
        <article class="bg-white rounded-xl p-4 border border-emerald-200 shadow-sm relative flex flex-col justify-between hover:border-emerald-400 transition cursor-pointer" onclick="switchView('active')">
          <div>
            <div class="flex items-center gap-2 mb-2.5">
              <span class="w-5 h-5 rounded-full bg-emerald-600 text-white font-bold text-[10px] flex items-center justify-center">02</span>
              <h4 class="text-xs font-bold text-slate-900 font-display">Project Finder</h4>
              <span class="ml-auto text-[9px] font-semibold uppercase tracking-wide bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-100 font-mono">Ready</span>
            </div>
            <ul class="text-[11px] text-slate-600 space-y-1.5 pl-0.5">
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>Search GitHub repos</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>Search Hugging Face</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>Analyze implementations</span>
              </li>
            </ul>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
            <span>Coverage</span>
            <span class="text-emerald-600 font-medium">Full access</span>
          </div>
        </article>
        <!-- Step 3: Paper Finder -->
        <article class="bg-white rounded-xl p-4 border border-purple-200 shadow-sm relative flex flex-col justify-between hover:border-purple-400 transition cursor-pointer" onclick="switchView('active')">
          <div>
            <div class="flex items-center gap-2 mb-2.5">
              <span class="w-5 h-5 rounded-full bg-purple-600 text-white font-bold text-[10px] flex items-center justify-center">03</span>
              <h4 class="text-xs font-bold text-slate-900 font-display">Paper Finder</h4>
              <span class="ml-auto text-[9px] font-semibold uppercase tracking-wide bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded border border-purple-100 font-mono">Queued</span>
            </div>
            <ul class="text-[11px] text-slate-600 space-y-1.5 pl-0.5">
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                <span>Semantic paper search</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                <span>Extract methods</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                <span>Find related work</span>
              </li>
            </ul>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
            <span>ArXiv Index</span>
            <span class="text-purple-600 font-medium">Semantic API</span>
          </div>
        </article>
        <!-- Step 4: Evaluator -->
        <article class="bg-white rounded-xl p-4 border border-amber-200 shadow-sm relative flex flex-col justify-between hover:border-amber-400 transition cursor-pointer" onclick="switchView('active')">
          <div>
            <div class="flex items-center gap-2 mb-2.5">
              <span class="w-5 h-5 rounded-full bg-amber-600 text-white font-bold text-[10px] flex items-center justify-center">04</span>
              <h4 class="text-xs font-bold text-slate-900 font-display">Evaluator</h4>
              <span class="ml-auto text-[9px] font-semibold uppercase tracking-wide bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded border border-amber-100 font-mono">Pending</span>
            </div>
            <ul class="text-[11px] text-slate-600 space-y-1.5 pl-0.5">
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>Verify relevance</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>Compare evidence</span>
              </li>
              <li class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>Identify research gaps</span>
              </li>
            </ul>
          </div>
          <div class="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
            <span>Synthesis</span>
            <span class="text-amber-600 font-medium">Final audit</span>
          </div>
        </article>
      </div>
    </section>
    <!-- END: ResearchWorkflow -->
  </main>

  <!-- BEGIN: Dashboard Right Sidebar -->
  <aside class="w-80 flex-shrink-0 bg-white border-l border-slate-200/90 p-5 overflow-y-auto space-y-5">
    <!-- Recent Research Section -->
    <section class="space-y-3" data-purpose="recent-research-section">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-bold text-slate-900 tracking-tight font-display">Recent research</h3>
        <button class="text-[11px] font-semibold text-indigo-600 hover:text-indigo-700" onclick="switchView('report')" type="button">View all →</button>
      </div>
      <div class="divide-y divide-slate-100">
        <!-- Item 1 -->
        <article class="py-2.5 flex items-center justify-between gap-3 first:pt-0 last:pb-0 group cursor-pointer hover:bg-slate-50/80 -mx-2 px-2 rounded-lg transition" onclick="switchView('report')">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-slate-800 group-hover:text-indigo-600 truncate transition">Satellite crop yield prediction</p>
            <span class="text-[10px] text-slate-400">2 days ago</span>
          </div>
          <span class="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" title="Completed"></span>
        </article>
        <!-- Item 2 -->
        <article class="py-2.5 flex items-center justify-between gap-3 first:pt-0 last:pb-0 group cursor-pointer hover:bg-slate-50/80 -mx-2 px-2 rounded-lg transition" onclick="switchView('report')">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-slate-800 group-hover:text-indigo-600 truncate transition">LLM for medical report analysis</p>
            <span class="text-[10px] text-slate-400">3 days ago</span>
          </div>
          <span class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" title="Completed"></span>
        </article>
        <!-- Item 3 -->
        <article class="py-2.5 flex items-center justify-between gap-3 first:pt-0 last:pb-0 group cursor-pointer hover:bg-slate-50/80 -mx-2 px-2 rounded-lg transition" onclick="switchView('report')">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-slate-800 group-hover:text-indigo-600 truncate transition">Real-time object detection</p>
            <span class="text-[10px] text-slate-400">1 week ago</span>
          </div>
          <span class="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" title="Completed"></span>
        </article>
        <!-- Item 4 -->
        <article class="py-2.5 flex items-center justify-between gap-3 first:pt-0 last:pb-0 group cursor-pointer hover:bg-slate-50/80 -mx-2 px-2 rounded-lg transition" onclick="switchView('report')">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-slate-800 group-hover:text-indigo-600 truncate transition">Soil moisture prediction using IoT</p>
            <span class="text-[10px] text-slate-400">1 week ago</span>
          </div>
          <span class="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" title="Completed"></span>
        </article>
      </div>
    </section>

    <!-- Divider -->
    <hr class="border-slate-100"/>

    <!-- Research Snapshot Section -->
    <section class="space-y-3" data-purpose="metrics-grid">
      <h3 class="text-xs font-bold text-slate-900 tracking-tight font-display">Research snapshot</h3>
      <div class="grid grid-cols-2 gap-2.5 text-center">
        <div class="bg-blue-50/70 p-3 rounded-xl border border-blue-100 cursor-pointer hover:bg-blue-100/60 transition" onclick="switchView('report')">
          <span class="block text-xl font-extrabold text-blue-700 font-display">12</span>
          <span class="text-[10px] font-medium text-blue-600/90 leading-tight">Projects found</span>
        </div>
        <div class="bg-purple-50/70 p-3 rounded-xl border border-purple-100 cursor-pointer hover:bg-purple-100/60 transition" onclick="switchView('report')">
          <span class="block text-xl font-extrabold text-purple-700 font-display">18</span>
          <span class="text-[10px] font-medium text-purple-600/90 leading-tight">Papers found</span>
        </div>
        <div class="bg-amber-50/70 p-3 rounded-xl border border-amber-100 cursor-pointer hover:bg-amber-100/60 transition" onclick="switchView('report')">
          <span class="block text-xl font-extrabold text-amber-700 font-display">4</span>
          <span class="text-[10px] font-medium text-amber-600/90 leading-tight">Gaps identified</span>
        </div>
        <div class="bg-emerald-50/70 p-3 rounded-xl border border-emerald-100 cursor-pointer hover:bg-emerald-100/60 transition" onclick="switchView('report')">
          <span class="block text-xl font-extrabold text-emerald-700 font-display">4</span>
          <span class="text-[10px] font-medium text-emerald-600/90 leading-tight">Verified reports</span>
        </div>
      </div>
    </section>

    <!-- Divider -->
    <hr class="border-slate-100"/>

    <!-- Research Quality Gauge Section -->
    <section class="bg-slate-50/70 p-4 rounded-2xl border border-slate-200/80 space-y-3">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-xs font-bold text-slate-900 tracking-tight font-display">Research quality</h3>
          <p class="text-[10px] text-slate-500">Evidence coverage</p>
        </div>
        <span class="inline-block px-2 py-0.5 rounded text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
          VERIFIED
        </span>
      </div>
      <div class="flex items-center justify-between pt-1">
        <div>
          <div class="text-2xl font-black text-slate-900 font-display">83%</div>
          <span class="text-[10px] font-medium text-emerald-700">Strong evidence base</span>
        </div>
        <!-- Radial Progress Gauge -->
        <div class="w-12 h-12 relative flex items-center justify-center">
          <svg class="w-full h-full -rotate-90" viewbox="0 0 36 36">
            <path class="text-slate-200" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" stroke-width="3.5"></path>
            <path class="text-indigo-600" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" stroke-dasharray="83, 100" stroke-linecap="round" stroke-width="3.5"></path>
          </svg>
        </div>
      </div>
      <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
        <div class="bg-indigo-600 h-1.5 rounded-full" style="width: 83%"></div>
      </div>
    </section>
  </aside>
  <!-- END: Dashboard Right Sidebar -->
</div>
```

---

### 4.2 Exact HTML Markup for View 2: Start Session (`#view-start`)

```html
<!-- ============================================================== -->
<!-- VIEW 2: START A RESEARCH (04)                                 -->
<!-- ============================================================== -->
<div class="hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full" id="view-start">
  <!-- Header with breadcrumbs -->
  <div class="flex items-center justify-between pb-2 border-b border-slate-200/80">
    <div class="space-y-1">
      <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
        <button class="hover:text-indigo-600" onclick="switchView('dashboard')">Dashboard</button>
        <span>/</span>
        <span class="text-slate-800 font-semibold">New Research Intake</span>
      </div>
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 font-display">Start a New Research Session</h1>
      <p class="text-xs text-slate-500">Provide an initial objective. Our multi-agent system will cross-reference state-of-the-art literature &amp; codebases.</p>
    </div>
    <button class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-600 hover:text-slate-900 shadow-sm flex items-center gap-1.5" onclick="switchView('dashboard')">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24"><path d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" stroke-linecap="round" stroke-linejoin="round"></path></svg>
      Cancel
    </button>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
    <!-- Left 2 Cols: Interactive Intake Form -->
    <div class="lg:col-span-2 space-y-6">
      <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
        <div class="flex items-center justify-between">
          <label class="text-sm font-bold text-slate-900 font-display flex items-center gap-2">
            <span class="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold text-[11px] flex items-center justify-center">1</span>
            Describe your research problem or project vision
          </label>
          <span class="text-xs font-mono text-slate-400" id="start-char-count">118 / 2500</span>
        </div>
        <div class="relative rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 focus-within:border-indigo-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100 transition">
          <textarea class="w-full text-xs text-slate-800 placeholder-slate-400 bg-transparent border-0 p-0 focus:ring-0 resize-none font-normal leading-relaxed" id="start-problem-textarea" oninput="updateStartCharCount(this)" placeholder="State your technical problem, baseline assumptions, expected inputs and target output metrics..." rows="4">Build an automated system that predicts regional crop yield using multi-spectral satellite imagery and temporal weather data.</textarea>
        </div>
        <!-- Optional Context Tags / Adders -->
        <div class="space-y-2">
          <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-mono">Optional context tags:</span>
          <div class="flex flex-wrap gap-2">
            <button class="px-3 py-1 text-xs rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 border border-slate-200 transition flex items-center gap-1.5" onclick="addContextTag(this, 'Domain: Agritech &amp; Remote Sensing')">
              <span class="text-indigo-500 font-bold">+</span> Domain: Agritech
            </button>
            <button class="px-3 py-1 text-xs rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 border border-slate-200 transition flex items-center gap-1.5" onclick="addContextTag(this, 'Dataset: Sentinel-2 &amp; MODIS')">
              <span class="text-indigo-500 font-bold">+</span> Dataset: Sentinel-2
            </button>
            <button class="px-3 py-1 text-xs rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 border border-slate-200 transition flex items-center gap-1.5" onclick="addContextTag(this, 'Tech: PyTorch / Vision Transformer')">
              <span class="text-indigo-500 font-bold">+</span> Tech: PyTorch ViT
            </button>
            <button class="px-3 py-1 text-xs rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 border border-slate-200 transition flex items-center gap-1.5" onclick="addContextTag(this, 'Constraint: Low-latency inference &lt; 200ms')">
              <span class="text-indigo-500 font-bold">+</span> Constraint: Low-latency
            </button>
          </div>
        </div>
        <div class="pt-4 border-t border-slate-100 flex items-center justify-between">
          <span class="text-xs text-slate-500 flex items-center gap-1.5">
            <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" stroke-width="2" viewbox="0 0 24 24"><path d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
            Orchestrator pre-checks passed
          </span>
          <button class="py-2.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs tracking-tight shadow-md shadow-indigo-600/30 flex items-center gap-2 active:scale-95 transition font-display" onclick="startResearchProcess()">
            <span>Start Research Pipeline</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.2" viewbox="0 0 24 24">
              <path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Research Test Cases Card Group (Clicking fills prompt) -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold text-slate-900 tracking-tight font-display uppercase">Recommended Benchmark Test Cases</h3>
          <span class="text-[11px] text-slate-400">Click to fill</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- Benchmark 1 -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 hover:border-indigo-400 hover:shadow-md cursor-pointer transition group" onclick="selectTestCase('Crop Yield Prediction with Satellite Imagery', 'Predict crop yield across regional farmlands using Sentinel-2 multispectral imagery and daily weather variables (soil moisture, temperature) to forecast output 30 days before harvest.')">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-bold text-slate-900 group-hover:text-indigo-600 font-display">Satellite Crop Yield</span>
              <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">Agritech</span>
            </div>
            <p class="text-[11px] text-slate-500 line-clamp-2">Multispectral satellite imagery + daily temporal weather forecasts for 30-day pre-harvest projections.</p>
          </div>
          <!-- Benchmark 2 -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 hover:border-indigo-400 hover:shadow-md cursor-pointer transition group" onclick="selectTestCase('Clinical LLM for Discharge Summaries', 'Design a privacy-preserving Clinical LLM system that ingests unstructured EHR notes and outputs compliant discharge summaries with verified citations to medical guidelines.')">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-bold text-slate-900 group-hover:text-indigo-600 font-display">Clinical LLM Summaries</span>
              <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">Healthcare</span>
            </div>
            <p class="text-[11px] text-slate-500 line-clamp-2">HIPAA compliant summarization of EHR notes with cited guideline justification.</p>
          </div>
          <!-- Benchmark 3 -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 hover:border-indigo-400 hover:shadow-md cursor-pointer transition group" onclick="selectTestCase('Real-time Edge Drone Object Detection', 'Deploy a lightweight YOLO/MobileNet model on Jetson Nano capable of detecting agricultural pests in high-resolution video streams at &gt;30 FPS.')">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-bold text-slate-900 group-hover:text-indigo-600 font-display">Edge Drone Detection</span>
              <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-purple-50 text-purple-700">Edge AI</span>
            </div>
            <p class="text-[11px] text-slate-500 line-clamp-2">Under 5W power envelope, real-time pest detection on low-cost edge accelerators.</p>
          </div>
          <!-- Benchmark 4 -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 hover:border-indigo-400 hover:shadow-md cursor-pointer transition group" onclick="selectTestCase('Financial Time Series Anomaly Engine', 'Detect market flash anomalies across high-frequency tick data using variational autoencoders and diffusion-based temporal baselines.')">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-xs font-bold text-slate-900 group-hover:text-indigo-600 font-display">High-Freq Tick Anomaly</span>
              <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">FinTech</span>
            </div>
            <p class="text-[11px] text-slate-500 line-clamp-2">Tick-level latency anomaly detection on order book depth fluctuations.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Right 1 Col: "What Happens Next" 4-Step Pipeline -->
    <div class="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4">
      <h3 class="text-xs font-bold text-slate-900 font-display uppercase tracking-wide">Autonomous Pipeline Phases</h3>
      <p class="text-[11px] text-slate-500">When you launch, our specialized autonomous sub-agents execute sequentially:</p>
      <div class="space-y-3 pt-2">
        <div class="flex gap-3">
          <span class="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center flex-shrink-0">1</span>
          <div>
            <h4 class="text-xs font-semibold text-slate-900">Problem Deconstruction</h4>
            <p class="text-[11px] text-slate-500">Orchestrator generates targeted query expansions &amp; taxonomic parameters.</p>
          </div>
        </div>
        <div class="flex gap-3">
          <span class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center flex-shrink-0">2</span>
          <div>
            <h4 class="text-xs font-semibold text-slate-900">Codebase Discovery</h4>
            <p class="text-[11px] text-slate-500">Project Finder queries GitHub API &amp; Hugging Face models for runnable architectures.</p>
          </div>
        </div>
        <div class="flex gap-3">
          <span class="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center flex-shrink-0">3</span>
          <div>
            <h4 class="text-xs font-semibold text-slate-900">Literature Synthesis</h4>
            <p class="text-[11px] text-slate-500">Paper Finder accesses arXiv semantic embeddings for peer-reviewed SOTA papers.</p>
          </div>
        </div>
        <div class="flex gap-3">
          <span class="w-6 h-6 rounded-full bg-amber-100 text-amber-700 text-xs font-bold flex items-center justify-center flex-shrink-0">4</span>
          <div>
            <h4 class="text-xs font-semibold text-slate-900">Gap Analysis &amp; Audit</h4>
            <p class="text-[11px] text-slate-500">Evaluator identifies benchmark discrepancies and generates your verified report.</p>
          </div>
        </div>
      </div>
      <div class="mt-4 p-3 bg-indigo-50/70 border border-indigo-100 rounded-xl text-[11px] text-indigo-900">
        <span class="font-semibold">Average duration:</span> ~45 seconds across 4 agent instances with parallel verification.
      </div>
    </div>
  </div>
</div>
```

---

### 4.3 Exact JavaScript Functions for Views 1 & 2

```javascript
// Domain Appender on Dashboard
function appendDomain(domain) {
  const input = document.getElementById('dashboard-input');
  if (!input) return;
  if (!input.value.includes(domain)) {
    input.value = input.value.trim() + " [" + domain + "]";
    updateDashboardCharCount(input);
    if (typeof showToast === 'function') {
      showToast('Added domain filter: ' + domain);
    }
  }
}

// Live Character Counters with null-safety
function updateDashboardCharCount(el) {
  const counter = document.getElementById('dash-char-count');
  if (counter && el) {
    counter.innerText = el.value.length + " / 2500";
  }
}

function updateStartCharCount(el) {
  const counter = document.getElementById('start-char-count');
  if (counter && el) {
    counter.innerText = el.value.length + " / 2500";
  }
}

// Select Benchmark Preset Card Handler
function selectTestCase(title, description) {
  const area = document.getElementById('start-problem-textarea');
  if (area) {
    area.value = description;
    updateStartCharCount(area);
  }
  if (typeof showToast === 'function') {
    showToast('Loaded benchmark: ' + title);
  }
}

// Optional Context Tag Adder
function addContextTag(btn, tagText) {
  const area = document.getElementById('start-problem-textarea');
  if (area) {
    area.value = area.value.trim() + " (" + tagText + ")";
    updateStartCharCount(area);
  }
  if (btn) {
    btn.classList.add('bg-indigo-100', 'text-indigo-800', 'border-indigo-300');
  }
  if (typeof showToast === 'function') {
    showToast('Tag appended: ' + tagText);
  }
}

// Start Research Action from Dashboard or Start View
function startResearchProcess() {
  if (typeof showToast === 'function') {
    showToast('Initializing multi-agent pipeline...');
  }
  
  // Visual progress setup for Active View transition
  const bar = document.getElementById('active-progress-bar');
  const txt = document.getElementById('active-percent-text');
  if (bar) bar.style.width = '25%';
  if (txt) txt.innerText = '25% - Orchestrator parsing problem';
  
  // Switch to Active View (supports hash router or direct function)
  if (typeof switchView === 'function') {
    switchView('active');
  } else {
    window.location.hash = '#/active';
  }
}
```

---

## 5. Verification Method

To verify the integration independently:

1. **Static Markup & Component Integrity Tests**:
   ```bash
   pytest research_orchestrator/tests/test_spa_structure.py -v
   ```
   *Expected outcome*:
   - `test_tier1_spa_four_view_containers_present_in_prototype`: PASSED
   - `test_tier1_essential_spa_components_present`: PASSED
   - `test_tier1_dashboard_workflow_and_metrics`: PASSED
   - `test_tier1_start_view_presets_and_intake`: PASSED
   - `test_tier1_live_spa_view_containers_contract`: Unskips and PASSES when deployed to `research_orchestrator/static/index.html`.

2. **DOM Assertion Checks**:
   Confirm that `research_orchestrator/static/index.html` contains:
   - `<div ... id="view-dashboard">`
   - `<div ... id="view-start">`
   - `<textarea id="dashboard-input">`
   - `<span id="dash-char-count">`
   - `<textarea id="start-problem-textarea">`
   - `<span id="start-char-count">`

3. **Playwright Navigation & Interaction Verification**:
   ```bash
   pytest research_orchestrator/tests/test_spa_structure.py -k "playwright" -v
   ```
   *Expected outcome*: Zero uncaught JavaScript errors, and successful navigation between `#view-dashboard`, `#view-start`, `#view-active`, and `#view-report`.
