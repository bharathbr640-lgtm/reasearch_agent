import streamlit as st
from agent_manager import ResearchAgentManager

st.set_page_config(page_title="Research Agent", page_icon="🔍")

# Initialize agent manager in session state
if "agent" not in st.session_state:
    st.session_state.agent = ResearchAgentManager()
    st.session_state.step = "initial" # initial, gathering, confirming, researching, finished
    st.session_state.history = []
    st.session_state.user_idea = ""
    st.session_state.problem_statement = ""
    st.session_state.final_report = ""

st.title("🔍 Research Agent")
st.markdown("Validate your project ideas with AI-powered context gathering and web research.")

# Step 1: Initial Idea
if st.session_state.step == "initial":
    idea = st.text_area("What project idea are you thinking about?", placeholder="e.g., I want to build an AI agent that helps with my shopping")
    if st.button("Start Research"):
        if idea:
            st.session_state.user_idea = idea
            st.session_state.step = "gathering"
            st.rerun()
        else:
            st.warning("Please enter an idea first!")

# Step 2: Context Gathering
elif st.session_state.step == "gathering":
    st.subheader("Gathering Context")

    # Get follow-ups from the agent
    is_ready, follow_ups = st.session_state.agent.get_follow_ups(st.session_state.user_idea, st.session_state.history)

    if is_ready:
        st.session_state.step = "confirming"
        st.rerun()

    st.info(follow_ups)

    with st.form(key="follow_up_form"):
        user_answer = st.text_input("Your response:")
        submit = st.form_submit_button("Send")
        if submit and user_answer:
            st.session_state.history.append({"role": "user", "content": user_answer})
            st.rerun()

# Step 3: Problem Confirmation
elif st.session_state.step == "confirming":
    st.subheader("Confirm Problem Statement")

    if not st.session_state.problem_statement:
        with st.spinner("Synthesizing problem statement..."):
            st.session_state.problem_statement = st.session_state.agent.synthesize_problem(st.session_state.history)

    st.markdown(f"**Proposed Problem Statement:**\n\n{st.session_state.problem_statement}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm"):
            st.session_state.step = "researching"
            st.rerun()
    with col2:
        if st.button("🔄 Refine"):
            st.session_state.step = "gathering"
            st.rerun()

# Step 4: Researching
elif st.session_state.step == "researching":
    st.subheader("Conducting Web Research")
    with st.spinner("Searching and scraping the web via Firecrawl..."):
        report = st.session_state.agent.run_research(st.session_state.problem_statement)
        st.session_state.final_report = report
        st.session_state.step = "finished"
        st.rerun()

# Step 5: Final Report
elif st.session_state.step == "finished":
    st.subheader("Final Research Report")
    st.markdown(st.session_state.final_report)

    st.download_button(
        label="Download Report as Markdown",
        data=f"# Research Report\n\n## Problem Statement\n{st.session_state.problem_statement}\n\n## Analysis\n{st.session_state.final_report}",
        file_name="research_report.md",
        mime="text/markdown"
    )

    if st.button("Start New Research"):
        # Reset session state
        for key in list(st.session_state.keys()):
            if key != "agent":
                del st.session_state[key]
        st.session_state.step = "initial"
        st.rerun()
