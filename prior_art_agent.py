"""
Subagent 1: Prior-Art Discovery Agent.
Code has been organized into the 'subagent_1' directory.
This module re-exports PriorArtDiscoveryAgent for backward compatibility.
"""

from subagent_1.agent import PriorArtDiscoveryAgent

__all__ = ["PriorArtDiscoveryAgent"]

if __name__ == "__main__":
    agent = PriorArtDiscoveryAgent()
    agent.run()
