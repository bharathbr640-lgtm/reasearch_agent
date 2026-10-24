"""End-to-end scripted conversation test for the Research Orchestrator."""

import asyncio
import json
import uuid
import httpx

BASE = "http://127.0.0.1:8000"
SESSION_ID = str(uuid.uuid4())

SCRIPT = [
    # 1. Rough problem statement
    "I want to build a system that automatically detects hate speech in social media comments using NLP. "
    "It should work in real time on a stream of comments and flag the toxic ones.",

    # 2. Answer follow-up questions (we'll read the agent's questions first, then respond)
    "The input is a stream of text comments from Twitter/X and Reddit APIs. "
    "The output should be a JSON object per comment with the original text, a toxicity score 0-1, "
    "a label (hate_speech, offensive, clean), and a confidence score. "
    "It needs to handle at least 500 comments per second. "
    "I want to use transformer-based models, maybe fine-tuned BERT or similar. "
    "The main dataset I have in mind is the Jigsaw Toxic Comment dataset from Kaggle. "
    "I'm interested in both existing open-source projects and recent papers.",

    # 3. Provide any remaining clarifications
    "No specific language constraints for now, English only is fine to start. "
    "No budget constraints. It should run on a single GPU (A100 or similar). "
    "I'd like the system to also explain why a comment was flagged, not just give a score. "
    "Latency should be under 50ms per comment.",

    # 4. Confirm the read-back
    "Yes, that looks correct. Please finalize.",
]


async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        for i, msg in enumerate(SCRIPT):
            print(f"\n{'='*60}")
            print(f"USER [{i+1}/{len(SCRIPT)}]: {msg[:80]}...")
            print(f"{'='*60}")

            resp = await client.post(
                f"{BASE}/chat",
                json={"session_id": SESSION_ID, "message": msg},
            )
            resp.raise_for_status()
            data = resp.json()

            print(f"\nASSISTANT: {data['reply'][:500]}")
            print(f"\nFinalized: {data['finalized']}")
            if data.get("output_dir"):
                print(f"Output dir: {data['output_dir']}")

            if data["finalized"]:
                print("\n✅ FINALIZED! Checking output files...")
                break

        # Check output files
        import os
        output_dir = f"outputs/{SESSION_ID}"
        if os.path.isdir(output_dir):
            for fname in os.listdir(output_dir):
                fpath = os.path.join(output_dir, fname)
                print(f"\n--- {fname} ---")
                with open(fpath) as f:
                    print(f.read()[:1000])
        else:
            print(f"\n⚠️  Output directory not found: {output_dir}")
            print("   (Agent may not have called finalize tool yet)")

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
