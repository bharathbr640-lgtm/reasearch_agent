import os
import sys
import json
import time
from pathlib import Path
import streamlit as st

# Add current directory to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils import load_env_vars
from subagent_1.agent import PriorArtDiscoveryAgent
from subagent_2.agent import PaperFinderAgent

# Page configuration
st.set_page_config(
    page_title="AI Research Literature Discovery Pipeline",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .paper-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #3b82f6;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.5rem;
    }
    .badge-blue { background-color: #dbeafe; color: #1e40af; }
    .badge-purple { background-color: #f3e8ff; color: #6b21a8; }
    .badge-green { background-color: #dcfce7; color: #166534; }
    .badge-amber { background-color: #fef3c7; color: #92400e; }
    .badge-red { background-color: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

# Load environment
env = load_env_vars()
api_key = env.get("OLLAMA_API_KEY", "")

# Sidebar Navigation
st.sidebar.title("🔬 Research Agent")
st.sidebar.markdown("**Two-Agent Literature Discovery**")

mode = st.sidebar.radio(
    "Select Execution Mode:",
    [
        "🚀 Full Pipeline (Both Agents)",
        "🎯 Subagent 1 (Prior-Art Standalone)",
        "📚 Subagent 2 (Paper Finder Standalone)",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Settings")
headless_mode = st.sidebar.toggle("Run Playwright Headless (Background)", value=False,
                                 help="If turned OFF, Playwright opens a visible browser window on your screen to verify pages.")
model_name = st.sidebar.selectbox("LLM Engine:", ["gpt-oss:120b"], index=0)

# Sidebar MCP Status
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 MCP Tool Stack")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    st.caption("✓ Exa MCP")
    st.caption("✓ Hugging Face")
with col_s2:
    st.caption("✓ Firecrawl MCP")
    st.caption("✓ Playwright MCP")


# Initialize session state for all modes
if "s1_history" not in st.session_state:
    st.session_state.s1_history = []
if "s1_idea" not in st.session_state:
    st.session_state.s1_idea = ""
if "s1_statement" not in st.session_state:
    st.session_state.s1_statement = ""
if "s1_findings" not in st.session_state:
    st.session_state.s1_findings = None
if "s1_stage" not in st.session_state:
    st.session_state.s1_stage = "interview" # interview, confirmed, searching, complete

if "s2_findings" not in st.session_state:
    st.session_state.s2_findings = None

if "pipeline_stage" not in st.session_state:
    st.session_state.pipeline_stage = "stage1_interview" # stage1_interview, stage1_confirm, stage1_searching, stage1_done, stage2_searching, pipeline_complete


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_s1_agent():
    return PriorArtDiscoveryAgent(
        model=model_name,
        api_key=api_key,
        headless_playwright=headless_mode,
    )

def get_s2_agent():
    return PaperFinderAgent(
        model=model_name,
        api_key=api_key,
    )

def render_closeness_badge(closeness: str):
    colors = {
        "exact_match": "badge-red",
        "close_variant": "badge-amber",
        "partial_overlap": "badge-blue",
        "tangential": "badge-purple",
    }
    cls = colors.get(closeness, "badge-blue")
    return f'<span class="badge {cls}">{closeness.replace("_", " ").upper()}</span>'

def render_status_badge(status: str):
    colors = {
        "active": "badge-green",
        "archived": "badge-red",
        "demo": "badge-amber",
        "unknown": "badge-blue",
    }
    cls = colors.get(status, "badge-blue")
    return f'<span class="badge {cls}">{status.upper()}</span>'


# =========================================================================
# MODE 1: SUBAGENT 1 STANDALONE (PRIOR-ART DISCOVERY)
# =========================================================================
if mode == "🎯 Subagent 1 (Prior-Art Standalone)":
    st.markdown('<div class="main-header">🎯 Subagent 1: Prior-Art Discovery</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Runs a Plan-Mode clarification interview, searches Exa, Firecrawl, Hugging Face, verifies live candidate pages with Playwright, and emits structured prior-art findings.</div>', unsafe_allow_html=True)

    tab_interview, tab_report, tab_json = st.tabs(["💬 Clarification & Discovery", "📄 Prior-Art Report", "📦 JSON Contract"])

    with tab_interview:
        # Step 1: Initial idea or ongoing interview
        if st.session_state.s1_stage == "interview":
            st.subheader("Step 1: Plan-Mode Clarification Interview")
            st.caption("The agent asks one focused question at a time across all 6 core dimensions.")

            # Display conversation history
            for msg in st.session_state.s1_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                elif msg["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.write(msg["content"])

            # If no history, prompt for initial idea
            if not st.session_state.s1_history:
                user_idea_input = st.text_area(
                    "What project or architecture idea would you like to research?",
                    placeholder="e.g. A local-first biometric earbud tracker that maps focus states to Spotify playlists using on-device EEG signals.",
                    height=100,
                )
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("Start Interview", type="primary"):
                        if user_idea_input.strip():
                            st.session_state.s1_idea = user_idea_input.strip()
                            agent = get_s1_agent()
                            history = [
                                {"role": "system", "content": "You are Prior-Art Discovery Agent running a plan-mode interview across 6 dimensions (core idea, inputs/outputs, techniques, novelty claim, domain keywords, scope boundaries). Ask only ONE single focused question at a time. When clear, output [INTERVIEW_COMPLETE] and a 1-paragraph plain-language problem statement."},
                                {"role": "user", "content": f"Here is my project idea: {st.session_state.s1_idea}"},
                            ]
                            with st.spinner("Analyzing project idea..."):
                                turn = agent.get_interview_turn(history)
                            if turn["is_complete"]:
                                st.session_state.s1_statement = turn["statement"]
                                st.session_state.s1_stage = "confirm"
                            else:
                                history.append({"role": "assistant", "content": turn["question"]})
                            st.session_state.s1_history = history
                            st.rerun()
                        else:
                            st.warning("Please enter a project idea first.")

            # If interview is underway, accept response
            else:
                user_response = st.chat_input("Your answer...")
                if user_response:
                    st.session_state.s1_history.append({"role": "user", "content": user_response})
                    agent = get_s1_agent()
                    with st.spinner("Thinking..."):
                        turn = agent.get_interview_turn(st.session_state.s1_history)
                    if turn["is_complete"]:
                        st.session_state.s1_statement = turn["statement"]
                        st.session_state.s1_stage = "confirm"
                    else:
                        st.session_state.s1_history.append({"role": "assistant", "content": turn["question"]})
                    st.rerun()

                # Action buttons to fast-track
                col_c1, col_c2 = st.columns([2, 5])
                with col_c1:
                    if st.button("Synthesize Statement Now", help="End interview and generate the problem statement immediately"):
                        agent = get_s1_agent()
                        with st.spinner("Synthesizing problem statement..."):
                            statement = agent.synthesize_problem_statement(st.session_state.s1_history)
                        st.session_state.s1_statement = statement
                        st.session_state.s1_stage = "confirm"
                        st.rerun()

        # Step 2: Problem statement confirmation
        elif st.session_state.s1_stage == "confirm":
            st.subheader("Step 2: Confirm Problem Statement")
            st.info("Review and edit the synthesized problem statement before running the multi-MCP prior-art search.")

            confirmed_text = st.text_area(
                "Understood Problem Statement:",
                value=st.session_state.s1_statement,
                height=150,
            )

            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 4])
            with col_btn1:
                if st.button("✅ Confirm & Launch Prior-Art Search", type="primary"):
                    st.session_state.s1_statement = confirmed_text
                    st.session_state.s1_stage = "searching"
                    st.rerun()
            with col_btn2:
                if st.button("🔄 Back to Interview"):
                    st.session_state.s1_stage = "interview"
                    st.rerun()

        # Step 3: Searching
        elif st.session_state.s1_stage == "searching":
            st.subheader("Step 3: Conducting Multi-MCP Prior-Art Discovery")
            progress_box = st.empty()
            progress_bar = st.progress(0)

            def update_progress(msg: str):
                progress_box.info(f"⏳ {msg}")

            agent = get_s1_agent()
            update_progress("Starting prior-art discovery across Exa, Firecrawl, Hugging Face, and Playwright...")
            progress_bar.progress(20)

            with st.spinner("Executing searches and browser verification..."):
                findings = agent.execute_prior_art_discovery(
                    st.session_state.s1_statement,
                    headless_playwright=headless_mode,
                    progress_callback=update_progress,
                )
                st.session_state.s1_findings = findings
                st.session_state.s1_stage = "complete"
                progress_bar.progress(100)
                st.success("✓ Prior-art discovery complete!")
                st.rerun()

        # Step 4: Complete
        elif st.session_state.s1_stage == "complete":
            st.subheader("Prior-Art Discovery Complete")
            st.success("Prior art discovery has finished! View the full report and JSON contract below.")

            if st.session_state.s1_findings:
                closest = st.session_state.s1_findings.get("closest_match_summary")
                gaps = st.session_state.s1_findings.get("gaps_identified")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("**Closest Prior-Art Match:**")
                    st.info(closest or "None found.")
                with col_m2:
                    st.markdown("**Innovation Gaps Identified:**")
                    st.warning(gaps or "None identified.")

            col_r1, col_r2 = st.columns([2, 5])
            with col_r1:
                if st.button("🔄 Run New Prior-Art Search"):
                    st.session_state.s1_stage = "interview"
                    st.session_state.s1_history = []
                    st.session_state.s1_findings = None
                    st.rerun()

    # Report Tab
    with tab_report:
        report_path = ROOT_DIR / "subagent_1" / "prior_art_report.md"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_md = f.read()
            st.markdown(report_md, unsafe_allow_html=True)
            st.download_button(
                "⬇️ Download Prior-Art Report (.md)",
                data=report_md,
                file_name="prior_art_report.md",
                mime="text/markdown",
            )
        else:
            st.info("Run Subagent 1 to generate the prior-art report.")

    # JSON Contract Tab
    with tab_json:
        json_path = ROOT_DIR / "subagent_1" / "prior_art_findings.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                json_str = f.read()
            st.json(json_str)
            st.download_button(
                "⬇️ Download JSON Contract (.json)",
                data=json_str,
                file_name="prior_art_findings.json",
                mime="application/json",
            )
        else:
            st.info("Run Subagent 1 to generate the JSON contract.")


# =========================================================================
# MODE 2: SUBAGENT 2 STANDALONE (ACADEMIC PAPER FINDER)
# =========================================================================
elif mode == "📚 Subagent 2 (Paper Finder Standalone)":
    st.markdown('<div class="main-header">📚 Subagent 2: Academic Paper Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consumes Subagent 1 findings, queries Firecrawl paper tools & Exa, explores citation graphs, and returns the top 5 academic papers resolving identified gaps.</div>', unsafe_allow_html=True)

    tab_finder, tab_list, tab_json2 = st.tabs(["🔍 Paper Discovery", "📖 Curated Reading List", "📦 JSON Contract"])

    with tab_finder:
        st.subheader("Input Contract Selection")
        source_option = st.radio(
            "Select findings source:",
            ["Load Existing Subagent 1 Findings (`prior_art_findings.json`)", "Upload Custom JSON File", "Enter Gaps & Statement Manually"],
            index=0,
        )

        input_findings = None
        input_statement = None

        if "Load Existing" in source_option:
            json_file = ROOT_DIR / "subagent_1" / "prior_art_findings.json"
            if not json_file.exists():
                json_file = ROOT_DIR / "prior_art_findings.json"
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    input_findings = json.load(f)
                st.success(f"✓ Found existing contract from: `{json_file.name}`")
                st.markdown(f"**Problem Statement:** {input_findings.get('confirmed_problem_statement')}")
                st.markdown(f"**Target Gaps:** {input_findings.get('gaps_identified')}")
                st.markdown(f"**Keywords:** {', '.join(input_findings.get('domain_keywords', []))}")
            else:
                st.warning("No prior_art_findings.json found. Run Subagent 1 first or upload a JSON.")

        elif "Upload" in source_option:
            uploaded_file = st.file_uploader("Upload prior_art_findings.json", type=["json"])
            if uploaded_file:
                try:
                    input_findings = json.load(uploaded_file)
                    st.success("✓ Custom findings loaded successfully!")
                    st.markdown(f"**Problem Statement:** {input_findings.get('confirmed_problem_statement')}")
                    st.markdown(f"**Target Gaps:** {input_findings.get('gaps_identified')}")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

        elif "Enter Gaps" in source_option:
            input_statement = st.text_area(
                "Problem Statement:",
                value="A local-first biometric earbud tracker that maps focus states to Spotify playlists.",
                height=80,
            )
            input_gaps = st.text_area(
                "Identified Gaps / Missing Techniques:",
                value="No open-source implementation provides real-time on-device EEG processing in earbuds for music playlists.",
                height=80,
            )
            input_keywords = st.text_input(
                "Domain Keywords (comma-separated):",
                value="EEG, focus detection, music recommendation, edge inference, earbuds",
            )
            input_findings = {
                "confirmed_problem_statement": input_statement,
                "gaps_identified": input_gaps,
                "domain_keywords": [k.strip() for k in input_keywords.split(",") if k.strip()],
                "closest_match_summary": "",
            }

        st.markdown("---")
        if st.button("🔬 Search Academic Papers", type="primary"):
            if input_findings:
                progress_box = st.empty()
                progress_bar = st.progress(0)

                def update_s2_progress(msg: str):
                    progress_box.info(f"⏳ {msg}")

                agent2 = get_s2_agent()
                progress_bar.progress(25)
                with st.spinner("Searching PubMed, arXiv, and citation graphs via Firecrawl MCP..."):
                    results = agent2.execute_literature_discovery(
                        findings_data=input_findings,
                        progress_callback=update_s2_progress,
                    )
                    st.session_state.s2_findings = results
                    progress_bar.progress(100)
                    st.success("✓ Literature discovery complete! Top 5 papers ranked.")
            else:
                st.error("Please load or enter prior-art findings before searching.")

        # Display Top 5 Ranked Papers
        if st.session_state.s2_findings:
            st.markdown("### 🏆 Top Ranked Academic Papers")
            papers = st.session_state.s2_findings.get("papers", [])
            for p in papers:
                rank = p.get("relevance_rank", 1)
                title = p.get("title", "Untitled")
                authors = p.get("authors", "Unknown")
                year = p.get("year", "Unknown")
                url = p.get("url_or_doi", "#")
                why = p.get("why_relevant", "")

                st.markdown(f"""
                <div class="paper-card">
                    <span class="badge badge-purple">RANK #{rank}</span>
                    <span class="badge badge-blue">{year}</span>
                    <h4 style="margin: 0.5rem 0;"><a href="{url}" target="_blank" style="text-decoration: none; color: #1e3a8a;">{title} 🔗</a></h4>
                    <p style="color: #4b5563; font-size: 0.9rem; margin-bottom: 0.5rem;"><b>Authors:</b> {authors}</p>
                    <div style="background-color: #f1f5f9; border-radius: 6px; padding: 0.8rem; font-size: 0.9rem;">
                        <b>💡 Relevance to Identified Gaps:</b><br/>{why}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab_list:
        reading_list_path = ROOT_DIR / "subagent_2" / "paper_reading_list.md"
        if reading_list_path.exists():
            with open(reading_list_path, "r", encoding="utf-8") as f:
                reading_md = f.read()
            st.markdown(reading_md, unsafe_allow_html=True)
            st.download_button(
                "⬇️ Download Reading List (.md)",
                data=reading_md,
                file_name="paper_reading_list.md",
                mime="text/markdown",
            )
        else:
            st.info("Run Subagent 2 to generate the curated reading list.")

    with tab_json2:
        paper_json_path = ROOT_DIR / "subagent_2" / "paper_findings.json"
        if paper_json_path.exists():
            with open(paper_json_path, "r", encoding="utf-8") as f:
                p_json_str = f.read()
            st.json(p_json_str)
            st.download_button(
                "⬇️ Download Paper Findings (.json)",
                data=p_json_str,
                file_name="paper_findings.json",
                mime="application/json",
            )
        else:
            st.info("Run Subagent 2 to generate paper_findings.json.")


# =========================================================================
# MODE 3: BOTH SUB-AGENTS AT ONCE (2-STAGE PIPELINE)
# =========================================================================
elif mode == "🚀 Full Pipeline (Both Agents)":
    st.markdown('<div class="main-header">🚀 2-Stage Literature Discovery Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Continuous workflow: Subagent 1 (Plan-Mode interview & Prior-Art search) seamlessly feeds findings into Subagent 2 (Academic Paper search & ranking).</div>', unsafe_allow_html=True)

    pipeline_tabs = st.tabs(["🔄 Interactive Pipeline", "📊 Unified Executive Dossier", "📦 Export All"])

    with pipeline_tabs[0]:
        st.subheader("Stage 1: Context Clarification & Prior-Art Discovery")

        # Display interview chat history
        for msg in st.session_state.s1_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.write(msg["content"])

        if st.session_state.pipeline_stage == "stage1_interview":
            if not st.session_state.s1_history:
                init_idea = st.text_area(
                    "What research or product idea would you like to validate end-to-end?",
                    placeholder="e.g. A privacy-preserving local price-comparison agent using Ollama and Playwright scraping fallback.",
                    height=100,
                )
                if st.button("Begin Pipeline", type="primary"):
                    if init_idea.strip():
                        st.session_state.s1_idea = init_idea.strip()
                        agent1 = get_s1_agent()
                        history = [
                            {"role": "system", "content": "You are Prior-Art Discovery Agent running a plan-mode interview across 6 dimensions. Ask only ONE single focused question at a time. When clear, output [INTERVIEW_COMPLETE] and a 1-paragraph plain-language problem statement."},
                            {"role": "user", "content": f"Here is my project idea: {st.session_state.s1_idea}"},
                        ]
                        with st.spinner("Analyzing project idea..."):
                            turn = agent1.get_interview_turn(history)
                        if turn["is_complete"]:
                            st.session_state.s1_statement = turn["statement"]
                            st.session_state.pipeline_stage = "stage1_confirm"
                        else:
                            history.append({"role": "assistant", "content": turn["question"]})
                        st.session_state.s1_history = history
                        st.rerun()
            else:
                user_msg = st.chat_input("Answer agent question...")
                if user_msg:
                    st.session_state.s1_history.append({"role": "user", "content": user_msg})
                    agent1 = get_s1_agent()
                    with st.spinner("Evaluating response..."):
                        turn = agent1.get_interview_turn(st.session_state.s1_history)
                    if turn["is_complete"]:
                        st.session_state.s1_statement = turn["statement"]
                        st.session_state.pipeline_stage = "stage1_confirm"
                    else:
                        st.session_state.s1_history.append({"role": "assistant", "content": turn["question"]})
                    st.rerun()

                if st.button("Synthesize Statement & Advance"):
                    agent1 = get_s1_agent()
                    with st.spinner("Synthesizing problem statement..."):
                        st.session_state.s1_statement = agent1.synthesize_problem_statement(st.session_state.s1_history)
                    st.session_state.pipeline_stage = "stage1_confirm"
                    st.rerun()

        elif st.session_state.pipeline_stage == "stage1_confirm":
            st.subheader("Confirm Problem Statement")
            confirmed_stmt = st.text_area(
                "Synthesized Problem Statement:",
                value=st.session_state.s1_statement,
                height=150,
            )
            col_g1, col_g2 = st.columns([2, 5])
            with col_g1:
                if st.button("🚀 Run Full Pipeline End-to-End", type="primary"):
                    st.session_state.s1_statement = confirmed_stmt
                    st.session_state.pipeline_stage = "running_full"
                    st.rerun()

        elif st.session_state.pipeline_stage == "running_full":
            st.subheader("Executing 2-Stage Pipeline")
            p_box1 = st.empty()
            p_bar = st.progress(10)

            # Stage 1 Execution
            agent1 = get_s1_agent()
            p_box1.info("⏳ Stage 1: Searching Exa, Firecrawl, Hugging Face Hub, and Playwright...")
            s1_res = agent1.execute_prior_art_discovery(st.session_state.s1_statement, headless_playwright=headless_mode)
            st.session_state.s1_findings = s1_res
            p_bar.progress(50)
            st.success("✓ Stage 1 Complete: Prior-art findings synthesized!")

            # Stage 2 Execution
            agent2 = get_s2_agent()
            p_box1.info("⏳ Stage 2: Searching academic literature & citation graphs with Firecrawl Paper tools...")
            s2_res = agent2.execute_literature_discovery(findings_data=s1_res)
            st.session_state.s2_findings = s2_res
            p_bar.progress(100)
            st.success("✓ Stage 2 Complete: Top 5 academic papers ranked!")

            st.session_state.pipeline_stage = "pipeline_complete"
            time.sleep(1)
            st.rerun()

        elif st.session_state.pipeline_stage == "pipeline_complete":
            st.success("🎉 Full 2-Stage Research Pipeline Successfully Executed!")
            col_sum1, col_sum2 = st.columns(2)
            with col_sum1:
                st.markdown("### 🎯 Prior Art (Stage 1)")
                if st.session_state.s1_findings:
                    st.write(f"**Status:** {'Prior art detected' if st.session_state.s1_findings.get('prior_art_found') else 'No direct prior art'}")
                    st.write(f"**Closest Match:** {st.session_state.s1_findings.get('closest_match_summary')[:200]}...")
            with col_sum2:
                st.markdown("### 📚 Academic Literature (Stage 2)")
                if st.session_state.s2_findings:
                    papers = st.session_state.s2_findings.get("papers", [])
                    st.write(f"**Total Papers Ranked:** {len(papers)}")
                    if papers:
                        st.write(f"**#1 Paper:** [{papers[0].get('title')}]({papers[0].get('url_or_doi')}) ({papers[0].get('year')})")

            st.markdown("👉 Check the **'Unified Executive Dossier'** tab to inspect full details.")

            if st.button("🔄 Restart Full Pipeline"):
                st.session_state.pipeline_stage = "stage1_interview"
                st.session_state.s1_history = []
                st.session_state.s1_findings = None
                st.session_state.s2_findings = None
                st.rerun()

    # Unified Executive Dossier Tab
    with pipeline_tabs[1]:
        st.subheader("📊 Complete Executive Research Dossier")
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown("#### 1. Prior-Art Implementations")
            s1_path = ROOT_DIR / "subagent_1" / "prior_art_report.md"
            if s1_path.exists():
                with open(s1_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read(), unsafe_allow_html=True)
            else:
                st.info("No prior-art report available yet.")

        with col_d2:
            st.markdown("#### 2. Academic Literature & Readings")
            s2_path = ROOT_DIR / "subagent_2" / "paper_reading_list.md"
            if s2_path.exists():
                with open(s2_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read(), unsafe_allow_html=True)
            else:
                st.info("No paper reading list available yet.")

    # Export Tab
    with pipeline_tabs[2]:
        st.subheader("📦 Download Complete Research Artifacts")
        col_ex1, col_ex2 = st.columns(2)

        with col_ex1:
            st.markdown("##### Subagent 1 Artifacts")
            s1_json = ROOT_DIR / "subagent_1" / "prior_art_findings.json"
            if s1_json.exists():
                with open(s1_json, "r", encoding="utf-8") as f:
                    st.download_button("⬇️ prior_art_findings.json", f.read(), file_name="prior_art_findings.json", mime="application/json")
            s1_md = ROOT_DIR / "subagent_1" / "prior_art_report.md"
            if s1_md.exists():
                with open(s1_md, "r", encoding="utf-8") as f:
                    st.download_button("⬇️ prior_art_report.md", f.read(), file_name="prior_art_report.md", mime="text/markdown")

        with col_ex2:
            st.markdown("##### Subagent 2 Artifacts")
            s2_json = ROOT_DIR / "subagent_2" / "paper_findings.json"
            if s2_json.exists():
                with open(s2_json, "r", encoding="utf-8") as f:
                    st.download_button("⬇️ paper_findings.json", f.read(), file_name="paper_findings.json", mime="application/json")
            s2_md = ROOT_DIR / "subagent_2" / "paper_reading_list.md"
            if s2_md.exists():
                with open(s2_md, "r", encoding="utf-8") as f:
                    st.download_button("⬇️ paper_reading_list.md", f.read(), file_name="paper_reading_list.md", mime="text/markdown")
