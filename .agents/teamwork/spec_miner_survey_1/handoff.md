# UI Prototype Specification & Architectural Survey Report

**Author**: `spec_miner_survey_1`  
**Target Path**: `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html`  
**Authoritative Source**: `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` & `screen_1940b14692274c4197c2b8086465105d.png`  
**Backend Reference**: `/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py`  

---

## 1. Executive Summary & Architecture Overview

The Stitch interactive prototype UI ("AI Research Agent - Unified Workspace") is a sophisticated Single Page Application (SPA) designed to operate inside a single HTML file without requiring heavy frontend framework compilation (e.g. Vite, React, Vue build steps). It relies on:
- **Tailwind CSS via CDN** with runtime script configuration and forms/container-queries plugins.
- **Google Fonts** (`Inter`, `Plus Jakarta Sans`, and `JetBrains Mono`).
- **Material Symbols Outlined** and inline SVG iconography.
- **A 2-part persistent layout shell**:
  1. A left fixed/dark sidebar (`w-64`, `#0f111a`) with branding, global "New Research" CTA, navigation links, autonomous agent status telemetry, and user profile footer.
  2. A flex-1 main viewport containing 4 tabbed/swappable view containers (`#view-dashboard`, `#view-start`, `#view-active`, `#view-report`).
- **A persistent top-right Toast notification system** (`#toast-notification`) for transient feedback.
- **A fixed bottom floating bar** inside the Report View (`fixed bottom-0 right-0 left-64`).

---

## 2. Global Dependencies, Fonts, Tailwind Configuration & Styles

### 2.1 CDN Links & Metadata
```html
<!DOCTYPE html>
<html class="h-full bg-slate-100" lang="en">
<head>
  <meta charset="utf-8"/>
  <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
  <title>AI Research Agent - Unified Workspace</title>
  
  <!-- Preconnect -->
  <link href="https://fonts.googleapis.com" rel="preconnect"/>
  <link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
  
  <!-- Google Fonts: Inter, Plus Jakarta Sans, JetBrains Mono -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
  
  <!-- Material Symbols Outlined -->
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
  
  <!-- Tailwind CSS CDN with Plugins -->
  <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
```

### 2.2 Tailwind Custom Configuration
```javascript
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          900: '#1e1b4b',
        },
        primary: '#004ac6',
        'primary-container': '#2563eb',
        surface: '#f8f9ff',
        'surface-container-low': '#eff4ff',
        'surface-container': '#e5eeff',
      }
    }
  }
}
```

### 2.3 Custom Styles & Keyframes
```css
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
@keyframes pulse-slow {
  0%, 100% { opacity: 1; }
  50% { opacity: .45; }
}
.animate-pulse-slow {
  animation: pulse-slow 2.2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
.active-nav {
  background-color: rgba(99, 102, 241, 0.18) !important;
  color: #a5b4fc !important;
  border: 1px solid rgba(99, 102, 241, 0.3) !important;
}
.report-anchor.active-anchor {
  background-color: #eff4ff;
  color: #004ac6;
  border-left: 3px solid #2563eb;
  font-weight: 600;
}
```

### 2.4 Body Element Classes
```html
<body class="h-full text-slate-800 antialiased flex bg-[#f5f7fb] font-sans selection:bg-indigo-500 selection:text-white">
```

---

## 3. Persistent Layout Shell Specification

### 3.1 Global Toast Element
Located immediately inside `<body>` before the sidebar:
```html
<div class="fixed top-5 right-5 z-50 transform -translate-y-12 opacity-0 pointer-events-none transition-all duration-300 flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900 text-white shadow-xl border border-slate-800 text-xs font-medium" id="toast-notification">
  <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
  <span id="toast-message">Notification message</span>
</div>
```

### 3.2 Left Dark Sidebar (`<aside>`)
- Dimensions: `w-64 flex-shrink-0 bg-[#0f111a] text-slate-300 flex flex-col border-r border-slate-800/80 z-30`
- **Sub-components**:
  1. **Brand Header**:
     - Action: `onclick="switchView('dashboard')"`
     - Icon container: `w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30` with sparkles SVG.
     - Title: `text-[13px] font-bold tracking-tight text-white font-display` ("AI Research Agent")
     - Subtitle: `text-[10px] text-slate-400 font-medium tracking-tight` ("Autonomous Agent System")
     - Status dot: `w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50` (title="System Online")
  2. **Primary CTA Button**:
     - ID: `btn-sidebar-new`, `onclick="switchView('start')"`
     - Classes: `w-full py-2.5 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs tracking-tight shadow-md shadow-indigo-600/30 flex items-center justify-center gap-2 transition active:scale-[0.98]`
     - Plus icon SVG + "New Research"
  3. **Navigation Links Group (`<nav class="flex-1 px-3 py-3 space-y-1 overflow-y-auto no-scrollbar text-xs">`)**:
     - Section Title: `text-[10px] font-semibold uppercase tracking-wider text-slate-500 font-mono` ("Navigation")
     - Button `nav-dashboard`: `onclick="switchView('dashboard')"`. Active class: `active-nav`. Icon: grid icon. Label: "Dashboard".
     - Button `nav-active`: `onclick="switchView('active')"`. Inactive class: `text-slate-400 hover:text-white hover:bg-slate-800/60`. Icon: file/document. Label: "My Research" + ping dot badge `<span class="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>`.
     - Button `nav-report`: `onclick="switchView('report')"`. Inactive class. Icon: history clock. Label: "Final Reports" + count badge `<span class="ml-auto text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">4</span>`.
     - Link Saved Findings: bookmark icon + `onclick="showToast('Opened Saved Findings bookmarks')"`.
     - Link Knowledge Base: book icon + `onclick="showToast('Semantic Knowledge Base index loaded')"`.
  4. **Autonomous Agents Status Section**:
     - Section Title: `text-[10px] font-semibold uppercase tracking-wider text-slate-500 font-mono` ("Autonomous Agents")
     - Agent 1: Orchestrator -> `w-2 h-2 rounded-full bg-indigo-400 animate-pulse`, Badge `STANDBY` (`bg-indigo-500/20 text-indigo-300 font-mono text-[9px] px-1.5 py-0.5 rounded`).
     - Agent 2: Project Finder -> `w-2 h-2 rounded-full bg-emerald-400`, Badge `READY` (`bg-emerald-500/20 text-emerald-300 font-mono text-[9px]`).
     - Agent 3: Paper Finder -> `w-2 h-2 rounded-full bg-purple-400`, Badge `QUEUED` (`bg-purple-500/20 text-purple-300 font-mono text-[9px]`).
     - Agent 4: Evaluator -> `w-2 h-2 rounded-full bg-amber-400`, Badge `PENDING` (`bg-amber-500/20 text-amber-300 font-mono text-[9px]`).
  5. **Sidebar User Profile Footer**:
     - Container: `p-3 border-t border-slate-800/70 bg-[#0c0e15]`
     - Avatar: `w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 text-white font-semibold text-xs flex items-center justify-center ring-2 ring-slate-800 shadow-sm flex-shrink-0` with initial "B".
     - Name: "Bharath R" (`text-xs font-semibold text-white font-display`)
     - Email: "bharath@workspace.ai" (`text-[10px] text-slate-400`)
     - Settings Button: Cog icon button `onclick="showToast('User settings opened')"`.

---

## 4. Deep Structural Breakdown of All 4 SPA Views

The SPA views are held in a flex container:
`<div class="flex-1 flex overflow-hidden">`

### 4.1 View 1: Dashboard (`#view-dashboard`)
Active by default (`flex-1 flex overflow-hidden w-full`). Consists of:
- **Left Main Scrollable Column (`main.flex-1.overflow-y-auto.px-8.py-6.space-y-6`)**:
  1. **Top Header Row**:
     - Left:
       - Pill: `inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-100/80 text-indigo-700 text-[11px] font-medium` with `w-1.5 h-1.5 bg-indigo-500 animate-pulse` dot ("Workspace Active").
       - Heading: `h1.text-2xl.font-bold.tracking-tight.text-slate-900.font-display` ("Good evening, Bharath.")
       - Subtitle: `p.text-xs.text-slate-500` ("Turn a project idea into evidence-based research.")
     - Right:
       - Search Box: `input.pl-8.pr-3.py-1.5.text-xs.rounded-xl.border.border-slate-200.bg-white.text-slate-700.placeholder-slate-400.w-64.shadow-sm` ("Search research, papers...") with search SVG.
       - Notifications Button: `button.w-8.h-8.rounded-xl.border.border-slate-200.bg-white.shadow-sm` with bell SVG, `onclick="showToast('You have 2 agent completion alerts')"`.
  2. **Hero Overview Card**:
     - Gradient: `rounded-2xl bg-gradient-to-r from-[#17143a] via-[#241154] to-[#1a1444] p-6 text-white shadow-lg shadow-indigo-950/15 border border-indigo-900/40`
     - Background Texture: `absolute inset-0 opacity-15 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:14px_14px]`
     - Badges: `AI-POWERED RESEARCH` badge + `GitHub • Hugging Face` pill.
     - Headline: `From problem statement <span class="text-indigo-300">to verified research.</span>`
     - Subheading: "Discover what has already been built, what has already been researched, and where the real gap is."
     - CTA Button: `Read Research Report` with arrow SVG, `onclick="switchView('report')"`.
  3. **Problem Statement Intake Section**:
     - Card: `bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4`
     - Step Number: `01` in indigo-100 pill. Title: "Start with your problem", Subtitle: "The Orchestrator will clarify the spec before research begins."
     - Character Counter: `id="dash-char-count"` ("72 / 2500")
     - Textarea: `id="dashboard-input"` oninput `updateDashboardCharCount(this)`, rows 3. Default: `"Build a system that predicts crop yield using satellite imagery and weather data."`
     - Suggested Domains Row: "SUGGESTED DOMAINS:" with clickable chips:
       `Computer Vision`, `NLP`, `Time Series`, `Recommendation`, `Robotics` (each calls `appendDomain('...')`).
     - Submit CTA: `Start Research` button with right arrow SVG, calls `startResearchProcess()`.
  4. **Research Workflow (4-Column Pipeline Grid)**:
     - Header: Step `02`, Title: "Research workflow", subtitle: "Autonomous multi-agent execution pipeline", link: "View live pipeline →" (`onclick="switchView('active')"`).
     - 4 Columns (`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5`):
       - Step 1: Orchestrator -> `01` indigo circle, badge `ACTIVE`, 3 checklist items with checkmarks ("Understand problem", "Ask clarifying questions", "Create research spec"), Status: "Ready to prompt".
       - Step 2: Project Finder -> `02` emerald circle, badge `READY`, 3 bullet items ("Search GitHub repos", "Search Hugging Face", "Analyze implementations"), Coverage: "Full access".
       - Step 3: Paper Finder -> `03` purple circle, badge `QUEUED`, 3 bullet items ("Semantic paper search", "Extract methods", "Find related work"), ArXiv Index: "Semantic API".
       - Step 4: Evaluator -> `04` amber circle, badge `PENDING`, 3 bullet items ("Verify relevance", "Compare evidence", "Identify research gaps"), Synthesis: "Final audit".

- **Right Sidebar (`aside.w-80.flex-shrink-0.bg-white.border-l.border-slate-200/90.p-5.overflow-y-auto.space-y-5`)**:
  1. **Recent Research**:
     - Header with "View all →" (`onclick="switchView('report')"`).
     - 4 items:
       - Satellite crop yield prediction (2 days ago, emerald dot)
       - LLM for medical report analysis (3 days ago, blue dot)
       - Real-time object detection (1 week ago, indigo dot)
       - Soil moisture prediction using IoT (1 week ago, amber dot)
  2. **Research Snapshot**:
     - 2x2 grid of metric boxes (clickable `onclick="switchView('report')"`):
       - 12 Projects found (blue)
       - 18 Papers found (purple)
       - 4 Gaps identified (amber)
       - 4 Verified reports (emerald)
  3. **Research Quality Gauge**:
     - Evidence coverage badge: `VERIFIED`
     - Score: `83%` - "Strong evidence base"
     - SVG Circular Gauge (`stroke-dasharray="83, 100"`)
     - Horizontal Progress Bar (`width: 83%`)

---

### 4.2 View 2: Start a Research Session (`#view-start`)
Initially hidden (`hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full`). Structure:
1. **Header & Breadcrumbs**:
   - Breadcrumb: `Dashboard / New Research Intake` (Dashboard clickable to return).
   - Title: "Start a New Research Session"
   - Subtitle: "Provide an initial objective. Our multi-agent system will cross-reference state-of-the-art literature & codebases."
   - Button: "Cancel" with back arrow, calls `switchView('dashboard')`.
2. **2-Column Layout (`grid grid-cols-1 lg:grid-cols-3 gap-6 items-start`)**:
   - **Left Form Section (`lg:col-span-2 space-y-6`)**:
     - Problem Vision Card (`bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5`):
       - Label: `1` circle + "Describe your research problem or project vision"
       - Counter: `id="start-char-count"` ("118 / 2500")
       - Textarea: `id="start-problem-textarea"`, oninput `updateStartCharCount(this)`, rows 4. Default: `"Build an automated system that predicts regional crop yield using multi-spectral satellite imagery and temporal weather data."`
       - Optional Context Tags:
         - `+ Domain: Agritech` -> `addContextTag(this, 'Domain: Agritech & Remote Sensing')`
         - `+ Dataset: Sentinel-2` -> `addContextTag(this, 'Dataset: Sentinel-2 & MODIS')`
         - `+ Tech: PyTorch ViT` -> `addContextTag(this, 'Tech: PyTorch / Vision Transformer')`
         - `+ Constraint: Low-latency` -> `addContextTag(this, 'Constraint: Low-latency inference < 200ms')`
       - Card Footer: Status "Orchestrator pre-checks passed" (green checkmark) + CTA "Start Research Pipeline" (`onclick="startResearchProcess()"`).
     - Recommended Benchmark Test Cases Card Group:
       - Header: "RECOMMENDED BENCHMARK TEST CASES", right note: "Click to fill".
       - 4 Cards in 2x2 grid:
         1. Satellite Crop Yield (`Agritech` badge) -> Sentinel-2 multispectral + weather variables.
         2. Clinical LLM Summaries (`Healthcare` badge) -> HIPAA-compliant EHR note summarization.
         3. Edge Drone Detection (`Edge AI` badge) -> Lightweight YOLO/MobileNet on Jetson Nano (<5W, >30FPS).
         4. High-Freq Tick Anomaly (`FinTech` badge) -> VAE & diffusion temporal baselines on order books.
         - Action: Clicking any card invokes `selectTestCase(title, description)` which populates `#start-problem-textarea` and shows a toast.
   - **Right Phase Explanation Card (`bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-4`)**:
     - Header: "AUTONOMOUS PIPELINE PHASES"
     - Subtitle: "When you launch, our specialized autonomous sub-agents execute sequentially:"
     - 4 Steps:
       1. Problem Deconstruction (Orchestrator query expansions)
       2. Codebase Discovery (Project Finder GitHub + HF search)
       3. Literature Synthesis (Paper Finder arXiv semantic embeddings)
       4. Gap Analysis & Audit (Evaluator benchmark audit)
     - Average duration callout: `~45 seconds across 4 agent instances with parallel verification.`

---

### 4.3 View 3: Active Research Session (`#view-active`)
Initially hidden (`hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full`). Structure:
1. **Header & Action Bar**:
   - Breadcrumbs: `Dashboard / Active Research Session` with animated ping dot.
   - Title: "Satellite Crop Yield Prediction" + Badge `Session #AG-9042` (`bg-indigo-100 text-indigo-800 font-mono font-semibold`).
   - Subtitle: "Orchestrator dispatching parallel sub-agent workers across arXiv and Hugging Face repositories."
   - Action Buttons:
     - Pause/Resume Button: `id="btn-pause-session" onclick="togglePauseResearch()"` with pause SVG icon and `<span id="label-pause">Pause Agents</span>`.
     - "View Verified Report" CTA Button: `onclick="switchView('report')"`.
2. **Interactive Progress Bar**:
   - Card: `bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3`
   - Progress Status: Green pulse dot + `Pipeline Progress: <span class="text-indigo-600 font-mono" id="active-percent-text">78% Complete</span>`
   - Stage Indicator: `Stage 3 of 4: Paper Finder Synthesizing`
   - Bar Fill: `id="active-progress-bar"` (`bg-gradient-to-r from-indigo-500 to-indigo-600 h-2.5 rounded-full transition-all duration-700 style="width: 78%"`).
3. **4 Pipeline Agent State Cards (`grid grid-cols-1 md:grid-cols-4 gap-3.5`)**:
   - Agent 1: `01 Orchestrator` -> Badge `DONE` (emerald), status "Spec locked in 1.4s".
   - Agent 2: `02 Project Finder` -> Badge `12 REPOS` (emerald), status "Code analyzed".
   - Agent 3: `03 Paper Finder` -> Active card (`bg-indigo-50/50 border-indigo-300`), Badge `RUNNING` (indigo pulse), status "Filtering SOTA methods..." (ping dot).
   - Agent 4: `04 Evaluator` -> Queued card (`opacity-80`), Badge `QUEUED`, status "Pending input feed".
4. **Live Evidence Stream Console & Telemetry Log**:
   - Card: `bg-slate-900 text-slate-200 rounded-2xl p-5 border border-slate-800 shadow-xl space-y-3 font-mono`
   - Header: Emerald dot + "Live Agent Telemetry & Evidence Stream", Right: `STREAMING • 482 events`.
   - Scrollable Terminal: `id="telemetry-log"` (`max-h-64 overflow-y-auto no-scrollbar font-normal text-slate-300`).
   - Entries have timestamp `[16:42:01]`, agent tag `[Orchestrator]`, and message with styled links/code tags.

---

### 4.4 View 4: Final Research Report (`#view-report`)
Initially hidden (`hidden flex-1 overflow-y-auto px-8 py-6 space-y-6 w-full pb-24`). Note: `pb-24` ensures content is not obstructed by the floating bottom bar!
Structure:
1. **Header & Breadcrumbs**:
   - Breadcrumbs: `Dashboard / Research Runs / Report #REP-0824`
   - Title: "Crop Yield Prediction via Satellite & Weather"
   - Status Badge: `VERIFIED REPORT` with green checkmark (`bg-emerald-50 text-emerald-700 border-emerald-200 font-mono`).
   - Confidence Pill: "Agent Confidence: 8.7 / 10" (`bg-indigo-50 text-indigo-700`).
   - Button: "Back to Dashboard" (`onclick="switchView('dashboard')"`).
2. **4 Metrics Snapshot Ribbon (`grid grid-cols-2 md:grid-cols-4 gap-3.5`)**:
   - Card 1: Projects Analyzed: `12` (`text-blue-700 font-extrabold text-2xl`), "8 with open-source PyTorch weights".
   - Card 2: arXiv Papers Synthesized: `18` (`text-purple-700 font-extrabold text-2xl`), "Published between 2021 - 2024".
   - Card 3: Synthesized Findings: `8` (`text-indigo-700 font-extrabold text-2xl`), "Verified by cross-agent consensus".
   - Card 4: Unsolved Gaps Found: `4` (`text-amber-600 font-extrabold text-2xl`), "High commercial opportunity".
3. **Main Report Body (`grid grid-cols-1 lg:grid-cols-4 gap-6 items-start`)**:
   - **Left Sticky TOC Navigation (`aside.bg-white.rounded-xl.p-3.border.border-slate-200/90.shadow-sm.space-y-1.text-xs.font-medium`)**:
     - Header: "REPORT SECTIONS"
     - Links:
       - `01 Executive Summary` (`#rep-sec-1`, class `report-anchor active-anchor`)
       - `02 Problem Definition` (`#rep-sec-2`)
       - `03 Existing Repos & Models` (`#rep-sec-3`)
       - `04 Comparative Matrix` (`#rep-sec-4`)
       - `05 Identified Research Gaps` (`#rep-sec-5`)
       - `06 Next Actionable Step` (`#rep-sec-6`)
   - **Right Content Column (`lg:col-span-3 space-y-6`)**:
     - Section 01: Executive Summary (`#rep-sec-1`):
       - Heading with indigo dot.
       - Detailed summary paragraph.
       - Amber callout box: "Core Agent Finding: Over 70% of open-source repositories suffer from severe temporal data leakage..."
     - Section 04: Comparative Evaluation Matrix (`#rep-sec-4`):
       - Header: "04 Comparative Evaluation Matrix", subtitle "Verified by Evaluator Agent".
       - Data Table:
         - Columns: `Architecture / Repo`, `Modality`, `Reported R²`, `Code Quality`, `Evaluation Status`.
         - Row 1: `Prithvi-100M GeoFM` | `Multispectral ViT` | `0.86` | badge `Verified HF` | `Ready for fine-tune`
         - Row 2: `CropHarvest Bi-LSTM` | `Optical + ERA5` | `0.79` | badge `Apache 2.0` | `Baseline valid`
         - Row 3: `SatYield 3D-CNN` | `Sentinel-2 only` | `0.72` | badge `No Lic.` | `Spatial leakage risk`
     - Section 06: Recommended Next Step Card (`#rep-sec-6`):
       - Dark gradient: `bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-indigo-800 space-y-3`.
       - Header: badge `RECOMMENDED PATH`, "Estimated Setup: 2 days".
       - Title: "Fine-tune Prithvi-100M with Spatially Disjoint Holdouts".
       - Action Buttons:
         - "Export Starter Notebook (.ipynb)": `bg-white text-slate-900 font-bold`, `onclick="showToast('Exported PyTorch scaffold starter notebook')"`.
         - "Add to Workspace Backlog": `bg-white/10 text-white border border-white/20`, `onclick="showToast('Research ticket added to workspace backlog')"`.
4. **Sticky Bottom Report Action Bar**:
   - Fixed Position: `fixed bottom-0 right-0 left-64 bg-white/95 backdrop-blur border-t border-slate-200 px-8 py-3.5 flex items-center justify-between z-20 shadow-lg`
   - Left Notice: Emerald dot + "Report generated and verified by 4 autonomous agents in 42.8 seconds"
   - Right Buttons:
     - "Share Report": `onclick="shareReport()"` (copies URL to clipboard).
     - "Export Full Research Spec (PDF)": `onclick="exportFullSpec()"`, indigo button with download icon.

---

## 5. UI Interactivity & Client-side State Model

### 5.1 State Variables
- `sessionId`: client-generated UUID or timestamp string (e.g. `AG-${Date.now()}`).
- `activeResearchInterval`: timer reference for simulating/polling telemetry events.
- `currentProgress`: integer percentage (e.g. 25 -> 78 -> 100).
- `isPaused`: boolean flag for pausing agent telemetry simulation/polling.
- `chatHistory`: array of `{ role: 'user' | 'assistant', content: string }`.

### 5.2 Key Event Functions
1. `switchView(viewName)`:
   - Toggles `.hidden` class on `#view-dashboard`, `#view-start`, `#view-active`, `#view-report`.
   - Adds/removes `.active-nav` on `#nav-dashboard`, `#nav-active`, `#nav-report`.
   - Invokes view-specific triggers (e.g. `startLiveTelemetrySimulation()` for `active`, scroll to top for `report`).
2. `showToast(message)`:
   - Manipulates `#toast-notification` classes: removes `-translate-y-12 opacity-0 pointer-events-none`, adds `translate-y-0 opacity-100`.
   - Clears after 2800ms.
3. `appendDomain(domain)`:
   - Reads `#dashboard-input`, checks for duplication, appends ` [${domain}]`, updates character counter, displays toast.
4. `updateDashboardCharCount(el)` / `updateStartCharCount(el)`:
   - Updates `#dash-char-count` / `#start-char-count` with `${el.value.length} / 2500`.
5. `selectTestCase(title, description)`:
   - Sets `#start-problem-textarea` value, updates char count, triggers toast feedback.
6. `addContextTag(btn, tagText)`:
   - Appends ` (${tagText})` to textarea, changes button styling to indicate selection (`bg-indigo-100 text-indigo-800 border-indigo-300`), triggers toast.
7. `startResearchProcess()`:
   - Retrieves problem statement from either `#dashboard-input` or `#start-problem-textarea`.
   - Resets progress bar to 25%, sets header text to "25% - Orchestrator parsing problem", and switches view to `active`.
8. `togglePauseResearch()`:
   - Toggles `isPaused`, flips label between "Pause Agents" and "Resume Agents", displays toast.
9. `shareReport()`:
   - Uses `navigator.clipboard.writeText(window.location.href)` and triggers toast.
10. `exportFullSpec()`:
    - Triggers toast notifications simulating PDF spec package generation and download.

---

## 6. Integration Specification with FastAPI Backend

In `research_orchestrator/app/main.py`:
- `POST /chat` expects:
  ```json
  {
    "session_id": "string",
    "message": "string"
  }
  ```
- Returns:
  ```json
  {
    "reply": "string",
    "finalized": true,
    "output_dir": "/path/to/output/or/null"
  }
  ```

### Integration Requirements for Workers:
1. **Starting Research**:
   - When the user clicks "Start Research" on Dashboard or "Start Research Pipeline" on Start View:
     - Generate a new `sessionId` (e.g., `AG-${Math.floor(1000 + Math.random() * 9000)}`).
     - Display this session ID in the Active View header (`Session #AG-...`).
     - Immediately switch to `active` view.
     - Send `POST /chat` with `{ session_id: sessionId, message: problemText }`.
2. **Active View Chat Stream & Telemetry**:
   - The Active View already has a `#telemetry-log` terminal.
   - An implementation should append outgoing user messages and incoming Orchestrator replies to the live log / chat stream.
   - Maintain interactive input controls in the Active View so the user can answer clarifying questions asked by the Orchestrator.
3. **Completion & Report Population**:
   - When `data.finalized === true`:
     - Update progress bar to `100% Complete`.
     - Update Agent 4 (Evaluator) status badge to `DONE`.
     - Enable or auto-switch to Report View.
     - Populate executive summary and findings with the orchestrator's finalized reply or summary content.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Shell / Layout | Fixed Left Dark Sidebar | Persistent navigation and agent status rail (`w-64`, `#0f111a`) | Click events on nav buttons | Toggles active views and visual indicators | N/A (Static layout) | `screen_...html:76-193` |
| 2 | Shell / Toast | Floating Toast Alerts | Fixed top-right notification toast (`#toast-notification`) | `showToast(msg)` call with string | Animate down into view for 2.8s, then slide out | Gracefully handles missing elements | `screen_...html:71-74, 1026-1037` |
| 3 | Shell / Nav | View Switching Router | Client-side tabbed router managing 4 views without page reloads | `switchView('dashboard'\|'start'\|'active'\|'report')` | Reveals selected container, hides others, updates `.active-nav` | Defaults cleanly if invalid view name passed | `screen_...html:989-1023` |
| 4 | Dashboard View | Welcome & System Status | Workspace status indicator ("Workspace Active") and greeting | DOM Load | Rendered badge with pulsing indicator | N/A | `screen_...html:205-216` |
| 5 | Dashboard View | Search Input & Alert Bell | Top-bar search filter input and notification bell button | Text input, Bell click | Search focus state, Toast alert for notifications | Safe no-op if input empty | `screen_...html:218-229` |
| 6 | Dashboard View | Hero Overview Card | Gradient hero section with "AI-Powered Research" highlights and direct CTA to Report | Click on "Read Research Report" | Invokes `switchView('report')` | N/A | `screen_...html:231-264` |
| 7 | Dashboard View | Problem Statement Intake Card | Main problem definition textarea with live character counter | User typing in `#dashboard-input` | Updates `#dash-char-count` (`X / 2500`) | N/A | `screen_...html:266-280, 1049-1051` |
| 8 | Dashboard View | Domain Filter Chips | 5 suggested domains (Computer Vision, NLP, Time Series, Recommendation, Robotics) | Click on domain chip | Appends ` [Domain]` to textarea without duplicates | Ignored if domain already in textarea | `screen_...html:283-291, 1040-1047` |
| 9 | Dashboard View | Quick Start CTA Button | "Start Research" button on Dashboard | Click | Initializes progress to 25%, shows toast, opens Active View | N/A | `screen_...html:294-299, 1058-1068` |
| 10 | Dashboard View | 4-Stage Workflow Grid | Interactive 4-card overview of pipeline (Orchestrator, Project Finder, Paper Finder, Evaluator) | Click on card or "View live pipeline →" | Transitions to Active View (`switchView('active')`) | N/A | `screen_...html:304-430` |
| 11 | Dashboard View | Recent Research Rail | Sidebar list of 4 recent research sessions with colored completion dots | Click on research item | Transitions to Report View (`switchView('report')`) | N/A | `screen_...html:434-474` |
| 12 | Dashboard View | Research Metrics Snapshot | 2x2 grid showing Projects (12), Papers (18), Gaps (4), Reports (4) | Click on metric box | Transitions to Report View (`switchView('report')`) | N/A | `screen_...html:478-498` |
| 13 | Dashboard View | Research Quality Gauge | Circular radial SVG gauge and linear progress bar showing 83% evidence coverage | Static SVG / DOM | Rendered 83% gauge with `stroke-dasharray="83, 100"` | N/A | `screen_...html:502-528` |
| 14 | Start View | Header & Breadcrumb Nav | Breadcrumb path (`Dashboard / New Research Intake`) and Cancel button | Click on "Dashboard" or "Cancel" | Transitions to Dashboard View (`switchView('dashboard')`) | N/A | `screen_...html:537-551` |
| 15 | Start View | Intake Form & Context Tags | Problem textarea + 4 context tags (+ Agritech, + Sentinel-2, + PyTorch ViT, + Low-latency) | Click on tag chip | Appends tag text in parentheses, highlights tag chip, shows toast | Allows multiple tags | `screen_...html:555-583, 1079-1085` |
| 16 | Start View | Recommended Benchmark Presets | 4 preset benchmark test case cards (Crop Yield, Clinical LLM, Edge Drone, Tick Anomaly) | Click on preset card | Replaces textarea with preset description, updates char count, shows toast | Safe string replacement | `screen_...html:598-633, 1071-1076` |
| 17 | Start View | Start Research Pipeline CTA | Primary form submission button with pre-check validation indicator | Click | Invokes `startResearchProcess()`, transitions to Active View | N/A | `screen_...html:584-595` |
| 18 | Start View | Autonomous Pipeline Guide | Explanatory side card detailing sequential multi-agent roles and ~45s estimated duration | Static DOM | Visual step list (1-4) with color-coded badges | N/A | `screen_...html:636-673` |
| 19 | Active View | Breadcrumbs & Session Header | Header showing session identifier (`#AG-9042`) and active pulsing status | DOM Load / State | Displays session ID and status subtitle | N/A | `screen_...html:679-695` |
| 20 | Active View | Pipeline Pause/Resume Toggle | Button toggling agent execution | Click `#btn-pause-session` | Toggles `isPaused`, updates button text, fires toast alert | Pauses progress bar simulation | `screen_...html:698-701, 1104-1114` |
| 21 | Active View | View Report Header CTA | Direct shortcut button to Report View | Click | Transitions to Report View (`switchView('report')`) | N/A | `screen_...html:702-705` |
| 22 | Active View | Live Progress Meter | Progress bar with percentage and stage text | Progress updates | Animates progress fill width and text (e.g. 78% Complete) | Clamps at 98% in simulation | `screen_...html:709-720, 1088-1102` |
| 23 | Active View | Multi-Agent State Cards | 4 cards showing state of Orchestrator (DONE), Project Finder (12 REPOS), Paper Finder (RUNNING), Evaluator (QUEUED) | Pipeline state updates | Displays badges, descriptions, execution timing | Fallback to static mock state | `screen_...html:722-768` |
| 24 | Active View | Telemetry Console Log | Monospace terminal window streaming live events with timestamp and agent tags | Dynamic log events | Appends or displays timestamped log entries | Scrollable container (`max-h-64 no-scrollbar`) | `screen_...html:770-810` |
| 25 | Report View | Header & Confidence Metric | Report identifier (`#REP-0824`), `VERIFIED REPORT` badge, confidence score `8.7 / 10` | DOM Load | Rendered title, confidence pill, back button | N/A | `screen_...html:817-844` |
| 26 | Report View | 4 Metric Summary Ribbon | 4 metrics cards: Projects Analyzed (12), Papers Synthesized (18), Findings (8), Gaps Found (4) | DOM Load | Metric cards with distinct font-display numbers and subtext | N/A | `screen_...html:846-867` |
| 27 | Report View | Sticky Table of Contents | Sticky sidebar navigation indexing 6 report sections | Click on TOC links | Smooth scrolls to section anchor, applies `.active-anchor` | Native anchor fallback | `screen_...html:871-879` |
| 28 | Report View | Executive Summary Section | Section 01: Summary text with bold key metrics and amber callout for core findings | DOM Load | Rendered prose with highlighted callout box | N/A | `screen_...html:883-894` |
| 29 | Report View | Comparative Evaluation Matrix | Section 04: Data table comparing architectures, modalities, R², code quality, and evaluation status | DOM Load / Data | Rendered responsive table with colored badges | Horizontally scrollable on small screens | `screen_...html:896-939` |
| 30 | Report View | Recommended Next Step Card | Section 06: Dark gradient card with action buttons ("Export Starter Notebook", "Add to Backlog") | Click on action buttons | Triggers corresponding toast confirmations | Safe mock callbacks | `screen_...html:942-959` |
| 31 | Report View | Sticky Floating Action Bar | Fixed bottom toolbar (`left-64 bottom-0 right-0`) with generation duration and action buttons | Click "Share Report" or "Export Full Spec (PDF)" | Copies URL to clipboard or triggers PDF export toast | Uses `navigator.clipboard` | `screen_...html:963-978, 1116-1126` |
| 32 | Backend Integration | FastAPI `/chat` Dispatch | Client POST request to `/chat` with session_id and user prompt | Prompt submission | Receives `reply`, `finalized`, and `output_dir` | Reverts user message, alerts error toast | `ORIGINAL_REQUEST.md`, `app/main.py:35-64` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Domain Chip Appender | Clicking "Computer Vision" when "[Computer Vision]" is already in textarea | Ignores click; does not duplicate text or spam redundant toast. |
| 2 | Start View Preset Case | Clicking a test case after the user has manually typed custom text | Entire textarea content is cleanly replaced by the selected benchmark description and character counter updates immediately. |
| 3 | Context Tag Buttons | Clicking multiple context tags sequentially | Successive tags are appended in parentheses separated by spaces; buttons adopt active styling (`bg-indigo-100 text-indigo-800`). |
| 4 | Character Counters | Inputting text exceeding 2500 characters | Counter string dynamically displays `> 2500 / 2500`; textarea accommodates input without breaking layout. |
| 5 | View Switching | Switching views repeatedly in rapid succession | All views cleanly toggle `.hidden`; active navigation states on the sidebar correspond accurately without CSS leaks. |
| 6 | Telemetry Simulation | Navigating away from Active View while simulation timer is running | Interval continues in background until reset by `startResearchProcess()` or paused via `togglePauseResearch()`. |
| 7 | Bottom Action Bar on Report | Scrolling to the very bottom of Report View | `pb-24` on `#view-report` ensures the last card and buttons are fully visible and not hidden behind the fixed bottom bar. |
| 8 | Clipboard Share | Browser environment where `navigator.clipboard` is restricted or undefined | Safe optional chaining `navigator.clipboard?.writeText(...)` prevents unhandled runtime exceptions. |
| 9 | Backend Error during `/chat` | Network failure or 500 error from `/chat` endpoint | Should catch error, keep session state intact, and display an error toast notification to the user without crashing the UI. |

---

## 7. Five-Component Handoff Protocol

### 1. Observation
- Inspected `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.html` (1,133 lines, 69,172 bytes).
- Inspected `/Users/bharathbr/reasearch_agent/stitch_screen/screen_1940b14692274c4197c2b8086465105d.png` (82,822 bytes) confirming the high visual fidelity, sidebar color `#0f111a`, gradient hero banner, radial gauge, and dark telemetry log console.
- Inspected `/Users/bharathbr/reasearch_agent/research_orchestrator/app/main.py` lines 22-31 defining `ChatRequest(session_id: str, message: str)` and `ChatResponse(reply: str, finalized: bool, output_dir: str | None)`.
- Inspected `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html` (295 lines) confirming it is currently a rudimentary chat prototype lacking the modern Stitch unified workspace layout.

### 2. Logic Chain
1. `ORIGINAL_REQUEST.md` specifically mandates replacing `research_orchestrator/static/index.html` with the Stitch prototype UI while preserving 100% visual fidelity across all 4 SPA views (Dashboard, Start, Active, Report).
2. The Stitch prototype HTML is already self-contained: it loads Tailwind CSS with plugins via CDN, imports required Google Fonts and icons, and manages tabbed views via the `switchView()` function.
3. Because the existing backend in `app/main.py` serves `static/index.html` on `GET /` and exposes `POST /chat`, replacing `research_orchestrator/static/index.html` with this unified workspace structure requires:
   - Maintaining the exact HTML layout, classes, and IDs for the sidebar, shell, and 4 views.
   - Wiring the "Start Research" actions in Dashboard and Start View to invoke `POST /chat`.
   - Streaming or displaying chat messages in the Active View console.
   - Transitioning to or rendering results in the Report View when `finalized: true`.
4. No new backend dependencies (e.g. Node, Webpack, Vite, React) are needed because the prototype operates entirely with native browser JavaScript and Tailwind CDN.

### 3. Caveats
- The prototype currently contains mock simulation logic (`startLiveTelemetrySimulation()`, hardcoded progress 78%, hardcoded log events). For live backend integration, this simulation should seamlessly coexist or blend with live messages from `POST /chat` and the orchestrator's thoughts.
- In `POST /chat`, communication is turn-based async (`Runner.run(orchestrator_agent)`). While the backend runs, the client should show an active progress or typing state in the Active View.

### 4. Conclusion
The Stitch interactive prototype (`screen_1940b14692274c4197c2b8086465105d.html`) provides a complete, production-grade visual specification for the Research Agent SPA. The implementation team can directly adapt this HTML structure into `research_orchestrator/static/index.html`, wiring the existing JavaScript hooks to `fetch('/chat', ...)` with zero additional backend dependencies.

### 5. Verification Method
1. **File Inspection**:
   - Inspect `/Users/bharathbr/reasearch_agent/research_orchestrator/static/index.html` to confirm inclusion of Tailwind CDN, Google Fonts, left dark sidebar, and 4 view divs (`#view-dashboard`, `#view-start`, `#view-active`, `#view-report`).
2. **HTTP Server Check**:
   - Launch FastAPI backend:
     ```bash
     cd /Users/bharathbr/reasearch_agent/research_orchestrator && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
     ```
   - Run `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/` -> Expected: `200`.
   - Run `curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"session_id":"test","message":"hello"}'` -> Expected: valid JSON with `reply` and `finalized` keys.
3. **Browser / Playwright UI Verification**:
   - Verify view switching: clicking "New Research", "Dashboard", "My Research", and "Final Reports" toggles the views without console errors.
