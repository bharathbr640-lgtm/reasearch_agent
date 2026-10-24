"""Comprehensive test suite for the Evaluation Agent (Agent 3).

Covers all 8 mandatory verification tests:
- Test A: Relevant project
- Test B: Superficially relevant project
- Test C: Relevant paper with incomplete evidence
- Test D: Contradictory evidence (internal & cross-finding)
- Test E: Unsupported extraction (missing source / quote)
- Test F: Input-boundary enforcement (rejecting outside files & traversal)
- Test G: Both source types (project + paper) evaluated under common 9 criteria
- Test H: Missing or malformed input
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
import pytest

from evaluator.boundary import (
    BoundaryValidationError,
    MalformedInputError,
    MissingInputError,
    load_session_inputs,
    load_session_inputs_strict,
    resolve_and_validate_session_dir,
    validate_file_boundary,
    validate_session_id,
)
from evaluator.criteria import (
    CRITERIA_IDS,
    CRITERIA_TITLES,
    evaluate_criterion_deterministic,
)
from evaluator.engine import EvaluationEngine
from evaluator.run import execute_evaluation
from evaluator.schema import (
    CriterionEvaluation,
    EvaluatedItem,
    EvaluationFindings,
    EvaluationVerdict,
)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary outputs base directory for isolated evaluation testing."""
    base = tmp_path / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _create_session_dir(base: Path, session_id: str) -> Path:
    s_dir = base / session_id
    s_dir.mkdir(parents=True, exist_ok=True)
    return s_dir


def _sample_spec() -> dict:
    return {
        "original_problem_statement": "Detect coffee leaf diseases with phone camera and give treatment guide.",
        "clarified_problem_statement": "Build an Android-only offline mobile app that lets a coffee farmer photograph a leaf, then instantly shows the diagnosed disease name and short agronomic treatment steps.",
        "expected_input": "A photo of a coffee leaf captured with the phone camera.",
        "expected_output": "The disease label plus a placeholder for short treatment guide.",
        "constraints": "- Platform: Android only, offline-first.\n- Accuracy: >= 90% correct diagnosis.\n- Latency: <= 3 seconds per inference.\n- Model size: <= 50 MB.",
        "datasets_and_technologies": "Public coffee leaf disease datasets (Arabica and Robusta). TensorFlow Lite or ONNX edge models.",
        "research_focus": "Offline Android deployment for coffee leaf disease diagnosis meeting size and latency budgets.",
    }


# =====================================================================
# Test A: Relevant Project
# =====================================================================
def test_evaluation_test_a_relevant_project(temp_output_dir: Path):
    """Test A: Verifies a genuinely relevant open-source project matching the spec."""
    session_id = "test-a-relevant-proj"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    project_findings = {
        "session_id": session_id,
        "findings": [
            {
                "name": "CoffeeLeaf-TFLite",
                "url": "https://github.com/agri-ai/CoffeeLeaf-TFLite",
                "platform": "github",
                "kind": "repository",
                "problem_solved": "Detect coffee leaf diseases (Rust, Cercospora, Miner) from camera photos",
                "input_output": "Input: camera photo of coffee leaf; Output: disease label",
                "dataset": "Arabica and Robusta field coffee leaf images",
                "model_and_architecture": "MobileNetV2 quantized for TFLite on Android (model size 14 MB)",
                "method": "Convolutional Neural Network transfer learning with TFLite INT8 quantization",
                "evaluation_and_results": "93.5% test accuracy on field images, latency 45ms on Android",
                "repository_details": {
                    "stars": 42,
                    "license": "Apache-2.0",
                    "language": "Python",
                },
                "reproducibility": "Complete repository with installation guide, Dockerfile, and export scripts",
                "known_limitations": "Guide text is currently placeholder; user must supply localized text",
                "field_sources": {
                    "problem_solved": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "input_output": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "dataset": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "model_and_architecture": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "method": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "evaluation_and_results": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "repository_details": "[github_get_repository | https://api.github.com/repos/agri-ai/CoffeeLeaf-TFLite]",
                    "reproducibility": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                    "known_limitations": "[github_get_readme | https://github.com/agri-ai/CoffeeLeaf-TFLite/readme]",
                },
            }
        ],
    }
    (s_dir / "project_findings.json").write_text(json.dumps(project_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    assert findings.total_items_evaluated == 1
    item = findings.evaluated_projects[0]
    assert item.name == "CoffeeLeaf-TFLite"
    assert item.overall_verdict == "verified"
    assert len(item.criteria_results) == 9

    # Specific criteria checks
    prob_res = next(c for c in item.criteria_results if c.criterion_id == "problem_relevance")
    assert prob_res.verdict == "verified"
    assert prob_res.source_identifier == "https://github.com/agri-ai/CoffeeLeaf-TFLite"
    assert "coffee leaf" in prob_res.supporting_evidence.lower()

    input_res = next(c for c in item.criteria_results if c.criterion_id == "input_compatibility")
    assert input_res.verdict == "verified"

    repr_res = next(c for c in item.criteria_results if c.criterion_id == "reproducibility")
    assert repr_res.verdict == "verified"

    # Static inspection confirmed; no code execution occurred
    assert not item.contradictions_detected
    assert not item.unsupported_claims


# =====================================================================
# Test B: Superficially Relevant Project
# =====================================================================
def test_evaluation_test_b_superficially_relevant_project(temp_output_dir: Path):
    """Test B: Project matches keywords ('coffee') but addresses an unrelated task (roasting/IoT)."""
    session_id = "test-b-superficial-proj"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    project_findings = {
        "session_id": session_id,
        "findings": [
            {
                "name": "Coffee-Roaster-IoT",
                "url": "https://github.com/brew/Coffee-Roaster-IoT",
                "platform": "github",
                "kind": "repository",
                "problem_solved": "Predict coffee bean roasting temperature curve using IoT sensor logs",
                "input_output": "Input: temperature time series; Output: predicted roast level",
                "dataset": "Roast temperature sensor logs",
                "model_and_architecture": "LSTM regression model",
                "method": "Time series recurrent neural network",
                "evaluation_and_results": "RMSE 1.2 degrees Celsius",
                "repository_details": {"stars": 5, "license": "MIT", "language": "Python"},
                "reproducibility": "Code and notebooks in repo",
                "known_limitations": "Only for industrial drum roasters",
                "field_sources": {
                    "problem_solved": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "input_output": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "dataset": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "method": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "model_and_architecture": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "evaluation_and_results": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "repository_details": "[github_get_repository | https://api.github.com/repos/brew/Coffee-Roaster-IoT]",
                    "reproducibility": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                    "known_limitations": "[github_get_readme | https://github.com/brew/Coffee-Roaster-IoT/readme]",
                },
            }
        ],
    }
    (s_dir / "project_findings.json").write_text(json.dumps(project_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    assert findings.total_items_evaluated == 1
    item = findings.evaluated_projects[0]
    # Overall verdict must be not verified due to core problem mismatch
    assert item.overall_verdict == "not verified"

    prob_res = next(c for c in item.criteria_results if c.criterion_id == "problem_relevance")
    assert prob_res.verdict == "not verified"
    assert prob_res.missing_evidence is not None
    assert "roasting" in prob_res.supporting_evidence.lower()

    input_res = next(c for c in item.criteria_results if c.criterion_id == "input_compatibility")
    assert input_res.verdict == "not verified"


# =====================================================================
# Test C: Relevant Paper with Incomplete Evidence
# =====================================================================
def test_evaluation_test_c_relevant_paper_incomplete_evidence(temp_output_dir: Path):
    """Test C: Relevant academic preprint addressing the problem but omitting code and mobile benchmarks."""
    session_id = "test-c-paper-incomplete"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    paper_findings = {
        "session_id": session_id,
        "findings": [
            {
                "title": "Deep Classification of Coffee Foliar Rust Under Natural Illumination",
                "paper_url": "https://arxiv.org/abs/2105.12345",
                "year": "2021",
                "problem_addressed": "Diagnosis of coffee leaf rust in Brazilian plantations",
                "research_objective": "Classify coffee rust damage from smartphone camera leaf imagery",
                "domain": "plant disease identification",
                "input_type": "smartphone image of coffee leaf",
                "output_type": "disease classification label",
                "dataset": {
                    "name": "Field Coffee Dataset",
                    "description": "690 smartphone images of Arabica coffee leaves",
                    "size": "690",
                },
                "model": {
                    "model_name": "ResNet-50",
                    "architecture": "Standard 50-layer deep residual network",
                },
                "method": "Transfer learning using ImageNet pretrained weights and fine-tuning",
                "experiments_and_results": {
                    "evaluation_metrics": "classification accuracy",
                    "reported_results": "96.4%",
                },
                "limitations": "High computational complexity; not tested on mobile hardware",
                "research_gap": "Need for lightweight edge quantization and mobile runtime profiling",
                "code_repository": {
                    "url": "not found",
                    "is_official": "not found",
                    "framework": "not found",
                },
                "key_evidence": [
                    {
                        "quote": "Diagnosis of coffee leaf rust in Brazilian plantations using smartphone photography.",
                        "section": "abstract",
                        "field": "problem_addressed",
                    },
                    {
                        "quote": "The input to our network consists of RGB images captured with a handheld smartphone.",
                        "section": "methodology",
                        "field": "input_type",
                    },
                ],
            }
        ],
    }
    (s_dir / "paper_findings.json").write_text(json.dumps(paper_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    assert findings.total_items_evaluated == 1
    item = findings.evaluated_papers[0]
    # Partially verified because code is missing and mobile latency unverified
    assert item.overall_verdict == "partially verified"

    prob_res = next(c for c in item.criteria_results if c.criterion_id == "problem_relevance")
    assert prob_res.verdict == "verified"

    repr_res = next(c for c in item.criteria_results if c.criterion_id == "reproducibility")
    assert repr_res.verdict == "not verified"
    assert "not found" in repr_res.missing_evidence.lower()

    model_res = next(c for c in item.criteria_results if c.criterion_id == "model_relevance")
    assert model_res.verdict == "partially verified"
    assert "mobile" in model_res.missing_evidence.lower()


# =====================================================================
# Test D: Contradictory Evidence
# =====================================================================
def test_evaluation_test_d_contradictory_evidence(temp_output_dir: Path):
    """Test D: Detects internal contradiction within a finding and cross-finding contradiction across artifacts."""
    session_id = "test-d-contradictions"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    # Project internally claims offline mobile inference, but limitations state it requires a cloud server
    project_findings = {
        "session_id": session_id,
        "findings": [
            {
                "name": "Coffee-Offline-App",
                "url": "https://github.com/demo/Coffee-Offline-App",
                "platform": "github",
                "problem_solved": "Offline mobile coffee leaf disease diagnosis on Android",
                "input_output": "Input: photo; Output: label",
                "dataset": "ROCOLE dataset with 10000 images",
                "model_and_architecture": "Heavy Transformer Server Backbone",
                "method": "Vision Transformer",
                "evaluation_and_results": "98% accuracy",
                "repository_details": {"stars": 12, "license": "MIT", "language": "Python"},
                "reproducibility": "Code available",
                "known_limitations": "Requires server GPU backend; API connection required; not compatible with mobile offline inference",
                "field_sources": {
                    "problem_solved": "[readme | url]",
                    "input_output": "[readme | url]",
                    "dataset": "[readme | url]",
                    "model_and_architecture": "[readme | url]",
                    "method": "[readme | url]",
                    "evaluation_and_results": "[readme | url]",
                    "reproducibility": "[readme | url]",
                    "known_limitations": "[readme | url]",
                },
            }
        ],
    }
    (s_dir / "project_findings.json").write_text(json.dumps(project_findings), encoding="utf-8")

    # Paper studying the same ROCOLE dataset says it only has 690 images
    paper_findings = {
        "session_id": session_id,
        "findings": [
            {
                "title": "Benchmarking ROCOLE Coffee Leaf Pathology",
                "paper_url": "https://arxiv.org/abs/2005.99999",
                "problem_addressed": "Pathology evaluation on ROCOLE",
                "input_type": "leaf photo",
                "output_type": "disease label",
                "dataset": {
                    "name": "ROCOLE",
                    "description": "Benchmark dataset consisting strictly of 690 images",
                    "size": "690",
                },
                "model": {"model_name": "CNN", "architecture": "CNN"},
                "method": "CNN",
                "experiments_and_results": {"reported_results": "88%"},
                "limitations": "Small sample count (690 items)",
                "research_gap": "Dataset expansion",
                "code_repository": {"url": "https://github.com/bench/rocole"},
                "key_evidence": [
                    {
                        "quote": "The database consists of 690 images in total.",
                        "section": "3.1 dataset",
                        "field": "dataset",
                    }
                ],
            }
        ],
    }
    (s_dir / "paper_findings.json").write_text(json.dumps(paper_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    proj_item = findings.evaluated_projects[0]
    # Internal contradiction detected
    assert len(proj_item.contradictions_detected) > 0
    assert "mobile" in proj_item.contradictions_detected[0].lower()

    # Cross-finding contradiction detected for ROCOLE dataset dimensions
    assert len(findings.cross_finding_contradictions) > 0
    conflict = findings.cross_finding_contradictions[0]
    assert conflict.conflict_type == "dataset_size_conflict"
    assert "10000" in conflict.evidence_a or "10000" in conflict.evidence_b
    assert "690" in conflict.evidence_a or "690" in conflict.evidence_b


# =====================================================================
# Test E: Unsupported Extraction
# =====================================================================
def test_evaluation_test_e_unsupported_extraction(temp_output_dir: Path):
    """Test E: Detects extracted claims that lack supporting documentation or quotes."""
    session_id = "test-e-unsupported"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    # Project claiming 99.8% accuracy on Android, but field_sources marks evaluation as "not found"
    project_findings = {
        "session_id": session_id,
        "findings": [
            {
                "name": "Unverified-Repo",
                "url": "https://github.com/fake/Unverified-Repo",
                "platform": "github",
                "problem_solved": "Detect coffee disease",
                "input_output": "photo -> label",
                "dataset": "coffee images",
                "model_and_architecture": "MobileNet",
                "method": "CNN",
                "evaluation_and_results": "Achieves 99.8% real-time diagnostic accuracy on Android hardware",
                "repository_details": {"stars": 0, "license": "not found", "language": "Python"},
                "reproducibility": "not found",
                "known_limitations": "not found",
                "field_sources": {
                    "problem_solved": "[readme | url]",
                    "input_output": "[readme | url]",
                    "dataset": "[readme | url]",
                    "model_and_architecture": "[readme | url]",
                    "method": "[readme | url]",
                    "evaluation_and_results": "not found",  # Unsupported extraction!
                    "reproducibility": "not found",
                    "known_limitations": "not found",
                },
            }
        ],
    }
    (s_dir / "project_findings.json").write_text(json.dumps(project_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    item = findings.evaluated_projects[0]
    # Unsupported claim flagged
    assert len(item.unsupported_claims) > 0
    assert "evaluation_and_results" in item.unsupported_claims[0]

    # Verification status on experimental_evidence reflects unsupported/missing
    exp_res = next(c for c in item.criteria_results if c.criterion_id == "experimental_evidence")
    assert exp_res.verification_status in {"unsupported", "missing_claim"}


# =====================================================================
# Test F: Input-Boundary Enforcement
# =====================================================================
def test_evaluation_test_f_input_boundary_enforcement(temp_output_dir: Path):
    """Test F: Strictly enforces that files outside outputs/{session_id}/ cannot be accessed."""
    # 1. Invalid session_id with traversal attempts must raise BoundaryValidationError
    malicious_ids = [
        "../../etc/passwd",
        "../outputs/other_session",
        "session/with/slashes",
        "session\\backslashes",
        "session\x00nullbyte",
        "",
        "   ",
        "session with spaces",
    ]
    for bad_id in malicious_ids:
        with pytest.raises(BoundaryValidationError):
            validate_session_id(bad_id)

    # 2. Path escaping output_base must be rejected
    with pytest.raises(BoundaryValidationError):
        resolve_and_validate_session_dir("../outside_session", temp_output_dir)

    valid_id = "safe-session-123"
    s_dir = _create_session_dir(temp_output_dir, valid_id)

    # 3. Only authorized evaluation files allowed
    with pytest.raises(BoundaryValidationError):
        validate_file_boundary(s_dir, "passwords.txt")

    with pytest.raises(BoundaryValidationError):
        validate_file_boundary(s_dir, "../parent_file.json")

    # Authorized files succeed
    p = validate_file_boundary(s_dir, "research_spec.json")
    assert p.name == "research_spec.json"


# =====================================================================
# Test G: Both Source Types Evaluated Under Common 9 Criteria
# =====================================================================
def test_evaluation_test_g_common_9_criteria_both_sources(temp_output_dir: Path):
    """Test G: Confirms both projects and papers are evaluated against the EXACT same 9 criteria."""
    session_id = "test-g-common-9-criteria"
    s_dir = _create_session_dir(temp_output_dir, session_id)

    spec = _sample_spec()
    (s_dir / "research_spec.json").write_text(json.dumps(spec), encoding="utf-8")

    project_findings = {
        "session_id": session_id,
        "findings": [
            {
                "name": "Project-A",
                "url": "https://github.com/test/Project-A",
                "platform": "github",
                "problem_solved": "Coffee leaf pathology",
                "input_output": "photo -> label",
                "dataset": "Arabica dataset",
                "model_and_architecture": "CNN",
                "method": "CNN",
                "evaluation_and_results": "85% accuracy",
                "repository_details": {"stars": 2, "language": "Python"},
                "reproducibility": "github repo",
                "known_limitations": "none",
                "field_sources": {"problem_solved": "[readme | url]"},
            },
            # Pure dataset repository (model_relevance should be marked applicable=False)
            {
                "name": "Coffee-Leaf-Dataset-Only",
                "url": "https://github.com/data/Coffee-Leaf-Dataset-Only",
                "platform": "github",
                "kind": "dataset",
                "problem_solved": "Dataset of coffee leaves without models",
                "input_output": "photo",
                "dataset": "Arabica coffee images",
                "model_and_architecture": "not found",
                "method": "photography",
                "evaluation_and_results": "not found",
                "repository_details": {"stars": 10, "language": ""},
                "reproducibility": "data download link",
                "known_limitations": "no neural network models provided",
                "field_sources": {"problem_solved": "[readme | url]"},
            },
        ],
    }
    (s_dir / "project_findings.json").write_text(json.dumps(project_findings), encoding="utf-8")

    paper_findings = {
        "session_id": session_id,
        "findings": [
            {
                "title": "Paper-A",
                "paper_url": "https://arxiv.org/abs/2201.00001",
                "problem_addressed": "Coffee leaf pathology classification",
                "input_type": "smartphone photo",
                "output_type": "disease label",
                "dataset": "Coffee leaf dataset",
                "model": "ViT",
                "method": "Attention vision transformer",
                "experiments_and_results": "89% precision",
                "limitations": "none",
                "code_repository": "https://github.com/paper/code",
                "key_evidence": [{"quote": "coffee leaf pathology", "section": "abstract", "field": "problem_addressed"}],
            }
        ],
    }
    (s_dir / "paper_findings.json").write_text(json.dumps(paper_findings), encoding="utf-8")

    findings = execute_evaluation(session_id, output_base=temp_output_dir)

    assert findings.total_items_evaluated == 3
    assert len(findings.evaluated_projects) == 2
    assert len(findings.evaluated_papers) == 1

    # Every single evaluated item must have exactly the 9 criteria in identical order
    for item in findings.evaluated_projects + findings.evaluated_papers:
        assert len(item.criteria_results) == 9
        item_cids = [c.criterion_id for c in item.criteria_results]
        assert item_cids == CRITERIA_IDS
        for c in item.criteria_results:
            assert c.verdict in {"verified", "partially verified", "not verified", "unknown"}

    # Pure dataset item must have model_relevance applicable=False with an explicit reason
    ds_item = next(p for p in findings.evaluated_projects if p.name == "Coffee-Leaf-Dataset-Only")
    ds_model_crit = next(c for c in ds_item.criteria_results if c.criterion_id == "model_relevance")
    assert ds_model_crit.applicable is False
    assert ds_model_crit.applicability_reason is not None
    assert "dataset" in ds_model_crit.applicability_reason.lower()


# =====================================================================
# Test H: Missing or Malformed Input
# =====================================================================
def test_evaluation_test_h_missing_or_malformed_input(temp_output_dir: Path):
    """Test H: Handles missing files and malformed JSON explicitly without fabrication."""
    # Case 1: Missing research_spec.json
    session_id_missing = "test-h-missing-spec"
    s_dir1 = _create_session_dir(temp_output_dir, session_id_missing)
    (s_dir1 / "project_findings.json").write_text("{\"findings\": []}", encoding="utf-8")

    findings1 = execute_evaluation(session_id_missing, output_base=temp_output_dir)
    assert any("Missing required input file: research_spec.json" in err for err in findings1.validation_errors)

    # Case 2: Malformed JSON syntax
    session_id_malformed = "test-h-malformed-json"
    s_dir2 = _create_session_dir(temp_output_dir, session_id_malformed)
    (s_dir2 / "research_spec.json").write_text("{ broken json syntax : [", encoding="utf-8")

    findings2 = execute_evaluation(session_id_malformed, output_base=temp_output_dir)
    assert any("Malformed JSON in research_spec.json" in err for err in findings2.validation_errors)

    # Case 3: Strict loader raises explicit exceptions
    with pytest.raises(MalformedInputError):
        load_session_inputs_strict(session_id_malformed, output_base=temp_output_dir)

    with pytest.raises(MissingInputError):
        load_session_inputs_strict(session_id_missing, output_base=temp_output_dir)
