"""
Subagent 2: Academic Paper Finder Agent.
Code has been organized into the 'subagent_2' directory.
This module re-exports PaperFinderAgent for backward compatibility.
"""

from subagent_2.agent import PaperFinderAgent

__all__ = ["PaperFinderAgent"]

if __name__ == "__main__":
    agent = PaperFinderAgent()
    agent.run()
