# Clarified Problem Statement

Build a real‑time system that ingests a stream of English‑language comments from the Twitter/X and Reddit APIs, uses a transformer‑based model (e.g., fine‑tuned BERT) to assess each comment for hate speech, and returns a JSON record containing the original text, a toxicity score (0–1), a categorical label (hate_speech, offensive, clean), a confidence score, and an explanation of why the comment was flagged. The system must handle ≥ 500 comments per second with ≤ 50 ms latency per comment on a single A100‑class GPU.
