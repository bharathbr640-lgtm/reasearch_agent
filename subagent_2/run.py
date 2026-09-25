#!/usr/bin/env python3
"""
Standalone runner for Subagent 2: Academic Paper Finder Agent.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from subagent_2.agent import PaperFinderAgent
from utils import load_env_vars

def main():
    env = load_env_vars()
    agent = PaperFinderAgent(
        model="gpt-oss:120b",
        api_key=env.get("OLLAMA_API_KEY"),
    )
    agent.run()

if __name__ == "__main__":
    main()
