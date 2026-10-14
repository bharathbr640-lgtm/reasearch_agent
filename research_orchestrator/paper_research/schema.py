"""Pydantic schemas for the Research Paper Discovery and Evidence Collection Agent (Agent 2)."""

from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


def _sanitize_dict_nones(d: dict[str, Any], default_str: str = "not found") -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            cleaned[k] = default_str
        elif isinstance(v, str) and v.strip() == "":
            cleaned[k] = default_str
        else:
            cleaned[k] = v
    return cleaned


class EvidenceQuote(BaseModel):
    quote: str = Field(description="Exact unstitched quote from paper text")
    section: str = Field(default="not found", description="Section heading from which the quote was extracted")
    field: str = Field(default="not found", description="Target field this evidence supports, e.g. reported_results, method, limitations")

    def __str__(self) -> str:
        sec = f"[{self.section}] " if self.section and self.section != "not found" else ""
        return f'{sec}"{self.quote}"'

    @model_validator(mode="before")
    @classmethod
    def _clean_evidence_quote(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            q = str(data.get("quote") or "").strip()
            sec = str(data.get("section") or "not found").strip()
            fld = str(data.get("field") or "not found").strip()
            return {"quote": q, "section": sec, "field": fld}
        if isinstance(data, str):
            raw = data.strip()
            dict_m = re.search(r"\{.*\}", raw)
            if dict_m:
                try:
                    import ast
                    parsed = ast.literal_eval(dict_m.group(0))
                    if isinstance(parsed, dict) and "quote" in parsed:
                        return {
                            "quote": str(parsed.get("quote", "")).strip(),
                            "section": str(parsed.get("section", "not found")).strip(),
                            "field": str(parsed.get("field", "not found")).strip(),
                        }
                except Exception:
                    pass
            sec_m = re.match(r"^\[(?:Section:\s*)?([^\]]+)\]\s*(.*)$", raw, flags=re.DOTALL)
            if sec_m:
                sec = sec_m.group(1).strip()
                q = sec_m.group(2).strip().strip('"').strip("'")
                return {"quote": q, "section": sec, "field": "not found"}
            return {"quote": raw.strip('"').strip("'"), "section": "not found", "field": "not found"}
        return {"quote": str(data or ""), "section": "not found", "field": "not found"}


def clean_dataset_name(raw_name: str, raw_desc: str = "") -> str:
    """Format dataset name as a short name (<= 60 chars, balanced parentheses, never cut at comma)."""
    if not raw_name or str(raw_name).strip() in ["", "not found", "None"]:
        return "not found"
    name = str(raw_name).strip()

    # Strip leading introductory phrases
    name = re.sub(
        r"^(?:a\s+dataset\s+of|the\s+dataset\s+of|this\s+article\s+introduces|dataset\s+named|public\s+dataset\s+named)\s+",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    # Strip trailing clauses like 'with 1,685 images...', 'consisting of...', 'containing...'
    name = re.split(
        r"\b(?:with\s+\d+|consisting\s+of|containing\s+\d+|which\s+contains)\b",
        name,
        flags=re.IGNORECASE,
    )[0].strip()

    # Strip clauses with size/splits in parentheses
    name = re.sub(
        r"\s*\([^)]*(?:images|leaf|leaves|split|fold|train|test|healthy|cercospora|miner|rust)[^)]*\)",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    # Avoid cutting at comma inside numbers (e.g. 1,685): split only on comma NOT followed by digit
    if "," in name:
        parts = re.split(r",(?!\d)", name)
        if len(parts[0].strip()) >= 3:
            name = parts[0].strip()

    # Balance parentheses
    open_p = name.count("(")
    close_p = name.count(")")
    if open_p > close_p:
        name = re.sub(r"\s*\([^)]*$", "", name).strip()
    elif close_p > open_p:
        name = re.sub(r"^[^(]*\)\s*", "", name).strip()

    # Strip trailing punctuation
    name = name.rstrip(" ,;:-.")

    # Ensure max 60 chars cleanly
    if len(name) > 60:
        for known in ["Arabica Coffee Leaves", "RoCoLe", "JMuBEN2", "JMuBEN", "CoLeaf-DB", "BRACOL", "Coffee Leaf Rust"]:
            if known.lower() in name.lower():
                return known
        truncated = name[:60].rsplit(" ", 1)[0].strip()
        if truncated.count("(") > truncated.count(")"):
            truncated = re.sub(r"\s*\([^)]*$", "", truncated).strip()
        name = truncated.rstrip(" ,;:-.")

    return name if name else "not found"


class DatasetInfo(BaseModel):
    name: str = "not found"
    description: str = "not found"
    source: str = "not found"
    size: str = "not found"
    split: str = "not found"

    @model_validator(mode="before")
    @classmethod
    def _clean_nones(cls, data: Any) -> Any:
        if isinstance(data, str):
            data = {"name": data, "description": data}
        if isinstance(data, dict):
            cleaned = _sanitize_dict_nones(data)
            raw_name = str(cleaned.get("name", "")).strip()
            raw_desc = str(cleaned.get("description", "")).strip()
            combined = f"{raw_name} {raw_desc}"

            # Extract size if not populated or "not found"
            if cleaned.get("size") in ["not found", "", None]:
                size_m = re.search(r"(\b\d{1,3}(?:,\d{3})+|\b\d+)\s*(?:images|leaf images|leaves|photos|samples|records)\b", combined, re.IGNORECASE)
                if size_m:
                    cleaned["size"] = size_m.group(0).strip()

            # Extract split if not populated or "not found"
            if cleaned.get("split") in ["not found", "", None]:
                split_m = re.search(r"(\b\d{1,2}/\d{1,2}(?:/\d{1,2})?(?:\s*(?:train/test\s+split|train/test|split))?|\b\d+-fold(?:\s+cross[- ]validation|\s+cv)?\b|\b\d{1,2}%\s*(?:train|training|test|testing|val|validation)\b)", combined, re.IGNORECASE)
                if split_m:
                    cleaned["split"] = split_m.group(0).strip()

            # Preserve full original text in description if not populated
            if cleaned.get("description") in ["not found", "", None] and len(raw_name) > 20:
                cleaned["description"] = raw_name

            # Format clean short dataset name
            cleaned["name"] = clean_dataset_name(raw_name, raw_desc)

            return cleaned
        return data or {}


class ModelInfo(BaseModel):
    model_name: str = "not found"
    architecture: str = "not found"
    backbone: str = "not found"
    components: str = "not found"

    @model_validator(mode="before")
    @classmethod
    def _clean_nones(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _sanitize_dict_nones(data)
        if isinstance(data, str):
            return {"model_name": data, "architecture": data}
        return data or {}


class ExperimentsAndResults(BaseModel):
    experimental_setup: str = "not found"
    evaluation_metrics: str = "not found"
    reported_results: str = "not found"
    baseline_comparisons: str = "not found"
    evidence_location: str = "not found"  # e.g., "Table 3, Section 4.2"

    @model_validator(mode="before")
    @classmethod
    def _clean_nones(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _sanitize_dict_nones(data)
        if isinstance(data, str):
            return {"reported_results": data}
        return data or {}


class CodeRepository(BaseModel):
    url: str = "not found"
    is_official: bool | str = "not found"
    framework: str = "not found"
    details: str = "not found"

    @model_validator(mode="before")
    @classmethod
    def _clean_nones(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return _sanitize_dict_nones(data)
        if isinstance(data, str):
            return {"url": data}
        return data or {}


class PaperFinding(BaseModel):
    title: str = "Research Paper"
    authors: list[str] = Field(default_factory=list)
    year: int | str = "not found"
    doi: str = "not found"
    paper_url: str = "not found"
    citation: str = "not found"
    match_type: Literal["exact", "closely_related"] = "closely_related"
    match_reason: str = "not found"

    problem_addressed: str = "not found"
    research_objective: str = "not found"
    domain: str = "not found"
    input_type: str = "not found"
    output_type: str = "not found"

    dataset: DatasetInfo = Field(default_factory=DatasetInfo)
    model: ModelInfo = Field(default_factory=ModelInfo)
    method: str = "not found"

    experiments_and_results: ExperimentsAndResults = Field(default_factory=ExperimentsAndResults)

    limitations: str = "not found"
    limitations_section: str = "not found"
    limitations_evidence: str = "not found"

    research_gap: str = "not found"
    research_gap_section: str = "not found"
    research_gap_evidence: str = "not found"
    code_repository: CodeRepository = Field(default_factory=CodeRepository)

    key_evidence: list[EvidenceQuote] = Field(
        default_factory=list,
        description="Direct quotes, metrics, or factual statements extracted from paper text as structured evidence objects",
    )
    source_urls: list[str] = Field(
        default_factory=list,
        description="Source URLs called or inspected for this paper (e.g. arXiv, PMC, PDF, GitHub)",
    )

    @model_validator(mode="before")
    @classmethod
    def _clean_paper_finding_nones(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned: dict[str, Any] = {}
        raw_title = str(data.get("title") or "").strip()
        if not raw_title or raw_title in ["not found", "None"] or raw_title.lower().startswith("http") or "://" in raw_title:
            cleaned["title"] = "Research Paper"
        else:
            cleaned["title"] = raw_title
        str_default_fields = {
            "doi", "paper_url", "citation", "problem_addressed", "research_objective",
            "domain", "input_type", "output_type", "method", "limitations",
            "limitations_section", "limitations_evidence", "research_gap",
            "research_gap_section", "research_gap_evidence", "year", "match_reason",
        }
        for k, v in data.items():
            if v is None or (isinstance(v, str) and v.strip() == "" and k in str_default_fields):
                if k in str_default_fields:
                    cleaned[k] = "not found"
                elif k in {"authors", "key_evidence", "source_urls"}:
                    cleaned[k] = []
                elif k == "match_type":
                    cleaned[k] = "closely_related"
                else:
                    cleaned[k] = "not found"
            else:
                cleaned[k] = v
        return cleaned

    @field_validator("dataset", mode="before")
    @classmethod
    def _coerce_dataset(cls, v: Any) -> Any:
        if isinstance(v, str):
            return DatasetInfo(name=v, description=v)
        if isinstance(v, dict):
            return DatasetInfo.model_validate(v)
        return v or DatasetInfo()

    @field_validator("model", mode="before")
    @classmethod
    def _coerce_model(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v.strip().lower() in ["not applicable", "n/a", "none"]:
                return ModelInfo(
                    model_name="not applicable",
                    architecture="not applicable",
                    backbone="not applicable",
                    components="not applicable",
                )
            return ModelInfo(model_name=v, architecture=v)
        if isinstance(v, dict):
            return ModelInfo.model_validate(v)
        return v or ModelInfo()

    @field_validator("experiments_and_results", mode="before")
    @classmethod
    def _coerce_experiments(cls, v: Any) -> Any:
        if isinstance(v, str):
            return ExperimentsAndResults(reported_results=v)
        if isinstance(v, dict):
            return ExperimentsAndResults.model_validate(v)
        return v or ExperimentsAndResults()

    @field_validator("code_repository", mode="before")
    @classmethod
    def _coerce_code_repo(cls, v: Any) -> Any:
        if isinstance(v, str):
            return CodeRepository(url=v)
        if isinstance(v, dict):
            return CodeRepository.model_validate(v)
        return v or CodeRepository()

    @field_validator("authors", "source_urls", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip() or v.strip() == "not found":
                return []
            return [v.strip()]
        if isinstance(v, list):
            res = []
            for x in v:
                if x is not None:
                    sx = str(x).strip()
                    if sx and sx != "not found":
                        res.append(sx)
            return res
        return []

    @field_validator("key_evidence", mode="before")
    @classmethod
    def _coerce_evidence(cls, v: Any) -> list[EvidenceQuote]:
        if v is None:
            return []
        if isinstance(v, (str, dict, EvidenceQuote)):
            v = [v]
        if isinstance(v, list):
            res: list[EvidenceQuote] = []
            for item in v:
                if item is None:
                    continue
                if isinstance(item, EvidenceQuote):
                    res.append(item)
                elif isinstance(item, (dict, str)):
                    try:
                        eq = EvidenceQuote.model_validate(item)
                        if eq.quote and eq.quote not in ["not found", "not reported"]:
                            res.append(eq)
                    except Exception:
                        pass
            return res
        return []


class PaperResearchFindings(BaseModel):
    session_id: str
    search_queries_run: list[str]
    exact_research_found: bool = False
    findings: list[PaperFinding] = Field(..., max_length=10)
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def _clean_findings_container(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("notes") is None:
                data["notes"] = ""
            if data.get("search_queries_run") is None:
                data["search_queries_run"] = []
            if data.get("findings") is None:
                data["findings"] = []
            findings_list = data.get("findings") or []
            data["exact_research_found"] = any(
                (f.get("match_type") == "exact" if isinstance(f, dict) else getattr(f, "match_type", None) == "exact")
                for f in findings_list
            )
        return data
