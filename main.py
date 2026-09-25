#!/usr/bin/env python3
"""
CLI Entry point for the 2-Stage Literature Discovery Pipeline:
Stage 1: Subagent 1 - Prior-Art Discovery Agent (Plan-mode interview + 4-MCP search)
Stage 2: Subagent 2 - Paper Finder Agent (Literature search & Top 5 papers)
"""

import sys
import argparse
from utils import load_env_vars
from subagent_1.agent import PriorArtDiscoveryAgent
from subagent_2.agent import PaperFinderAgent

def run_stage_1(env, auto_prompt=None):
    """Executes Subagent 1 (Prior-Art Discovery)."""
    print("\n" + "=" * 65)
    print("   STAGE 1: PRIOR-ART DISCOVERY (SUBAGENT 1)")
    print("=" * 65)
    agent1 = PriorArtDiscoveryAgent(
        model="gpt-oss:120b",
        api_key=env.get("OLLAMA_API_KEY"),
        headless_playwright=False,
    )
    return agent1.run(initial_idea=auto_prompt)

def run_stage_2(env, findings_json_path="prior_art_findings.json"):
    """Executes Subagent 2 (Paper Finder)."""
    print("\n" + "=" * 65)
    print("   STAGE 2: ACADEMIC LITERATURE DISCOVERY (SUBAGENT 2)")
    print("=" * 65)
    agent2 = PaperFinderAgent(
        model="gpt-oss:120b",
        api_key=env.get("OLLAMA_API_KEY"),
    )
    return agent2.run(findings_json_path=findings_json_path)

def main():
    parser = argparse.ArgumentParser(description="2-Stage Literature Discovery Pipeline")
    parser.add_argument("--stage", choices=["1", "2", "all"], default="interactive",
                        help="Run Stage 1 only, Stage 2 only, or all automatically")
    parser.add_argument("--prompt", type=str, default=None,
                        help="Optional initial idea to seed Stage 1")
    args, _ = parser.parse_known_args()

    env = load_env_vars()
    if not env.get("OLLAMA_API_KEY"):
        print("Error: Missing OLLAMA_API_KEY in .env file.")
        sys.exit(1)

    print("=" * 65)
    print("       2-STAGE RESEARCH LITERATURE PIPELINE")
    print("=" * 65)
    print("Model: gpt-oss:120b via Ollama Cloud")
    print("Subagent 1: Prior-Art Discovery (Exa, Firecrawl, Hugging Face, Playwright)")
    print("Subagent 2: Academic Paper Finder (Firecrawl Paper Research Tools + Exa)")
    print("=" * 65)

    try:
        if args.stage == "1":
            run_stage_1(env, auto_prompt=args.prompt)
        elif args.stage == "2":
            run_stage_2(env)
        elif args.stage == "all":
            run_stage_1(env, auto_prompt=args.prompt)
            run_stage_2(env)
        else:
            # Interactive chained pipeline
            findings = run_stage_1(env, auto_prompt=args.prompt)

            print("\n" + "-" * 65)
            print("✓ Stage 1 Complete: Prior-art findings saved to prior_art_findings.json")
            print("-" * 65)
            
            proceed = input("\nWould you like to proceed to Stage 2: Academic Paper Discovery? (yes/no)\n> ").strip().lower()
            if proceed in ["yes", "y", "proceed", "sure"]:
                run_stage_2(env)
            else:
                print("\nPipeline finished after Stage 1. You can run Stage 2 anytime with: python main.py --stage 2\n")

    except KeyboardInterrupt:
        print("\n\nSession terminated by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
