"""Input boundary enforcement and path validation for the Evaluation Agent (Agent 3).

Strict constraints:
1. The evaluator reads its inputs EXCLUSIVELY from outputs/{session_id}/
   (specifically research_spec.json, project_findings.json, and paper_findings.json).
2. It MUST NOT search GitHub, search papers, read external files, or access
   any directory outside outputs/{session_id}/.
3. Strict path validation: any attempt to load findings from outside the session
   directory is immediately rejected.
4. If files are missing or malformed, report errors explicitly — never fabricate results.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

ALLOWED_INPUT_FILENAMES = frozenset({
    "research_spec.json",
    "project_findings.json",
    "paper_findings.json",
})


class BoundaryValidationError(ValueError):
    """Raised when an input path, session ID, or file violates strict boundary isolation."""


class MalformedInputError(ValueError):
    """Raised when an input JSON file exists but contains invalid or corrupted JSON."""


class MissingInputError(FileNotFoundError):
    """Raised when an essential input file is missing."""


def validate_session_id(session_id: str) -> str:
    """Validate that session_id conforms strictly to safe alphanumeric/hyphen/underscore format.
    
    Rejects path traversal, slashes, null bytes, and non-conforming characters.
    """
    if not isinstance(session_id, str):
        raise BoundaryValidationError(f"session_id must be a string, got {type(session_id).__name__}")
    clean_id = session_id.strip()
    if not clean_id or not SESSION_ID_PATTERN.match(clean_id):
        raise BoundaryValidationError(
            f"session_id '{session_id}' is invalid. Must be 1-64 alphanumeric characters, "
            "underscores, or hyphens with no traversal sequences."
        )
    return clean_id


def resolve_and_validate_session_dir(session_id: str, output_base: Path | str | None = None) -> Path:
    """Resolve and strictly validate the session directory under output_base.
    
    Ensures:
    1. session_id is syntactically valid (no traversal).
    2. Resolved path is strictly a direct child of output_base.
    3. No symlinks or parent references escape output_base.
    """
    clean_id = validate_session_id(session_id)

    if output_base is None:
        base_dir = (Path(__file__).resolve().parent.parent / "outputs").resolve()
    else:
        base_dir = Path(output_base).resolve()

    target_dir = (base_dir / clean_id).resolve()

    # Boundary check: target must be inside base_dir and not base_dir itself
    try:
        if not target_dir.is_relative_to(base_dir) or target_dir == base_dir:
            raise BoundaryValidationError(
                f"Boundary violation: session path '{target_dir}' escapes base directory '{base_dir}'"
            )
    except AttributeError:
        # Fallback for Python < 3.9 if ever used
        if base_dir not in target_dir.parents:
            raise BoundaryValidationError(
                f"Boundary violation: session path '{target_dir}' escapes base directory '{base_dir}'"
            )

    return target_dir


def validate_file_boundary(session_dir: Path, filename: str) -> Path:
    """Validate that a filename is in the allowed set and resolves strictly within session_dir."""
    if not isinstance(filename, str) or filename not in ALLOWED_INPUT_FILENAMES:
        raise BoundaryValidationError(
            f"File '{filename}' is not an authorized evaluation input. Allowed: {sorted(ALLOWED_INPUT_FILENAMES)}"
        )
    if "/" in filename or "\\" in filename or ".." in filename:
        raise BoundaryValidationError(f"Path traversal detected in filename: '{filename}'")

    file_path = (session_dir / filename).resolve()
    if not file_path.is_relative_to(session_dir) or file_path.parent != session_dir:
        raise BoundaryValidationError(
            f"File '{file_path}' resolves outside target session directory '{session_dir}'"
        )
    return file_path


def load_session_inputs(
    session_id: str,
    output_base: Path | str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    """Load research_spec.json, project_findings.json, and paper_findings.json for a session.
    
    Returns:
        (spec_data, project_data, paper_data, validation_errors)
    
    Strictly verifies boundary constraints. Missing or malformed files are recorded in
    validation_errors without fabricating data.
    """
    validation_errors: list[str] = []

    try:
        session_dir = resolve_and_validate_session_dir(session_id, output_base)
    except BoundaryValidationError as err:
        return {}, {}, {}, [f"Boundary validation failed: {err}"]

    if not session_dir.exists():
        return {}, {}, {}, [f"Session directory does not exist: {session_dir}"]

    # 1. research_spec.json
    spec_data: dict[str, Any] = {}
    spec_path = session_dir / "research_spec.json"
    if not spec_path.exists():
        validation_errors.append(f"Missing required input file: {spec_path.name}")
    else:
        try:
            validate_file_boundary(session_dir, "research_spec.json")
            raw_text = spec_path.read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            if not isinstance(parsed, dict):
                validation_errors.append("research_spec.json must be a JSON object")
            else:
                spec_data = parsed
        except json.JSONDecodeError as jde:
            validation_errors.append(f"Malformed JSON in research_spec.json: {jde}")
        except Exception as exc:
            validation_errors.append(f"Error reading research_spec.json: {exc}")

    # 2. project_findings.json
    project_data: dict[str, Any] = {}
    proj_path = session_dir / "project_findings.json"
    if not proj_path.exists():
        validation_errors.append(f"Missing input file: {proj_path.name}")
    else:
        try:
            validate_file_boundary(session_dir, "project_findings.json")
            raw_text = proj_path.read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            if not isinstance(parsed, dict):
                validation_errors.append("project_findings.json must be a JSON object")
            else:
                project_data = parsed
        except json.JSONDecodeError as jde:
            validation_errors.append(f"Malformed JSON in project_findings.json: {jde}")
        except Exception as exc:
            validation_errors.append(f"Error reading project_findings.json: {exc}")

    # 3. paper_findings.json
    paper_data: dict[str, Any] = {}
    paper_path = session_dir / "paper_findings.json"
    if not paper_path.exists():
        validation_errors.append(f"Missing input file: {paper_path.name}")
    else:
        try:
            validate_file_boundary(session_dir, "paper_findings.json")
            raw_text = paper_path.read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            if not isinstance(parsed, dict):
                validation_errors.append("paper_findings.json must be a JSON object")
            else:
                paper_data = parsed
        except json.JSONDecodeError as jde:
            validation_errors.append(f"Malformed JSON in paper_findings.json: {jde}")
        except Exception as exc:
            validation_errors.append(f"Error reading paper_findings.json: {exc}")

    return spec_data, project_data, paper_data, validation_errors


def load_session_inputs_strict(
    session_id: str,
    output_base: Path | str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Strict variant that raises specific exceptions on any boundary, missing, or malformed issue."""
    session_dir = resolve_and_validate_session_dir(session_id, output_base)
    if not session_dir.exists():
        raise MissingInputError(f"Session directory does not exist: {session_dir}")

    spec_path = validate_file_boundary(session_dir, "research_spec.json")
    if not spec_path.exists():
        raise MissingInputError(f"Required file {spec_path} not found")
    try:
        spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise MalformedInputError(f"Malformed JSON in {spec_path}: {err}") from err

    proj_path = validate_file_boundary(session_dir, "project_findings.json")
    project_data = {}
    if proj_path.exists():
        try:
            project_data = json.loads(proj_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise MalformedInputError(f"Malformed JSON in {proj_path}: {err}") from err

    paper_path = validate_file_boundary(session_dir, "paper_findings.json")
    paper_data = {}
    if paper_path.exists():
        try:
            paper_data = json.loads(paper_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise MalformedInputError(f"Malformed JSON in {paper_path}: {err}") from err

    return spec_data, project_data, paper_data
