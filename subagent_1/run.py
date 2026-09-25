#!/usr/bin/env python3
"""
Standalone runner for Subagent 1: Prior-Art Discovery Agent.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from subagent_1.agent import PriorArtDiscoveryAgent
from utils import load_env_vars

def main():
    env = load_env_vars()
    agent = PriorArtDiscoveryAgent(
        model="gpt-oss:120b",
        api_key=env.get("OLLAMA_API_KEY"),
        headless_playwright=False,
    )
    agent.run()

if __name__ == "__main__":
    main()
