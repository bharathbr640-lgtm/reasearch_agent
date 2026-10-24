# Evaluation Agent (Agent 3)

The **Evaluation Agent** is the third autonomous agent in the AI Research Agent system. It conducts rigorous, evidence-backed verification of candidate codebases (Agent 1) and academic preprints (Agent 2) against the clarified technical specification (Orchestrator).

---

## 1. Core Architecture

The Evaluation Agent is structured into modular components:

- **`schema.py`**: Pydantic v2 data models for verdicts, criterion results, evaluated items, cross-finding conflicts, and final evaluation findings.
- **`boundary.py`**: Strict input boundary isolation and path validation. Ensures all inputs are read exclusively from `outputs/{session_id}/` (`research_spec.json`, `project_findings.json`, `paper_findings.json`). Rejects directory traversal and outside access.
- **`verification.py`**: Equal architectural verification engine:
  - Agent 1 (Projects): Verifies documented claims against README/docs, detects unsupported extractions, and guarantees no runtime code execution is falsely claimed.
  - Agent 2 (Papers): Verifies quotes, numbers, and sections in `key_evidence`, and distinguishes author preprint claims from independent scientific verification.
  - Cross-finding conflict detection: Flags contradictory metrics or dataset scopes across multiple artifacts.
- **`criteria.py`**: Implements the 9 standard criteria definitions with both LLM evaluation (AsyncOpenAI) and deterministic rule-based evaluation.
- **`engine.py`**: Orchestrates boundary loading, verification, 9-criteria evaluation, conflict synthesis, comparative matrix building, research gap identification, and recommended next steps formulation.
- **`run.py`**: Primary interface exporting `execute_evaluation(session_id, output_base)` which writes `evaluation_findings.json` and `evaluation_findings.md`.

---

## 2. The 9 Criteria Framework

Both open-source projects and academic papers are evaluated against the exact same 9 criteria:

| # | Criterion ID | Key Question |
|---|:---|:---|
| 1 | `problem_relevance` | Does the work address the same core problem? |
| 2 | `input_compatibility` | Does it use compatible input data or information? |
| 3 | `output_compatibility` | Does it produce the type of output required? |
| 4 | `dataset_relevance` | Is the dataset relevant to the proposed problem? |
| 5 | `method_relevance` | Is the method applicable to the proposed approach? |
| 6 | `model_relevance` | Is the model/architecture relevant and feasible? |
| 7 | `experimental_evidence` | Does the work demonstrate the method experimentally? |
| 8 | `reproducibility` | Is there enough information/code/data to reproduce? |
| 9 | `research_gap` | What remains unresolved relative to user constraints? |

---

## 3. Strict Verdicts & Applicability

- **Only 4 verdicts allowed:**
  - `verified`: Clear, traceable evidence meeting the requirement.
  - `partially verified`: Partially fulfills requirements or lacks complete evidence.
  - `not verified`: Fails the requirement or contradicts the specification.
  - `unknown`: No data available to determine compliance.
- **No arbitrary numerical scores:** Floating-point scores (e.g. 0-10) and arbitrary weights are prohibited.
- **Explicit applicability:** If a criterion does not apply (e.g., `model_relevance` on a pure dataset repository), `applicable=False` is recorded with `applicability_reason` rather than mislabeling it `unknown`.

---

## 4. Input Boundary Isolation

The evaluator enforces strict path boundaries:
- Reads only from `outputs/{session_id}/`:
  - `research_spec.json`
  - `project_findings.json`
  - `paper_findings.json`
- Path traversal sequences (`../`, absolute paths, symlinks outside `outputs/`) raise `BoundaryValidationError`.
- Missing or malformed files are recorded explicitly in `validation_errors`. The system never fabricates results.

---

## 5. Usage

```python
from pathlib import Path
from evaluator.run import execute_evaluation

# Synchronous execution
findings = execute_evaluation("session-123", output_base=Path("outputs"))

print(f"Total items audited: {findings.total_items_evaluated}")
print(f"Verdicts summary: {findings.verdict_counts}")
```
