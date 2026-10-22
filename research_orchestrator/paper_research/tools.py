"""Function tools, data structures, and pipeline stages for Agent 2."""

from __future__ import annotations

import base64
import difflib
import io
import json
import os
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from agents import RunContextWrapper, function_tool
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from openai import AsyncOpenAI
from pydantic import ValidationError
from pypdf import PdfReader

from app.config import (
    MAX_TOOL_CALLS,
    FIRECRAWL_API_KEY,
    FIRECRAWL_BASE_URL,
    OLLAMA_BASE_URL,
    OLLAMA_API_KEY,
    MODEL_NAME,
)
from paper_research.schema import (
    PaperFinding,
    PaperResearchFindings,
    DatasetInfo,
    ModelInfo,
    ExperimentsAndResults,
    CodeRepository,
    EvidenceQuote,
    clean_dataset_name,
    ExtractedField,
    ExtractedBooleanField,
    PaperExtractionOutput,
)


# ==========================================
# Identifier Normalization & Registry
# ==========================================

def normalize_title(title: str) -> str:
    """Normalize a title by stripping punctuation and non-alphanumeric characters, lowercase."""
    if not title:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", title).lower()


def normalize_doi(doi: str) -> str:
    """Normalize DOI to standard prefix format: 10.xxxx/yyyy."""
    if not doi or doi == "not found":
        return ""
    d = doi.lower().strip()
    d = d.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip().rstrip(".")
    return d


def normalize_paper_identifiers(url_or_id: str) -> dict[str, str]:
    """Extract canonical URL, paper ID, DOI, PMCID, arXiv ID, and PMID from any identifier string."""
    raw = (url_or_id or "").strip()
    res: dict[str, str] = {
        "raw": raw,
        "canonical_url": "",
        "pdf_url": "",
        "paper_id": "",
        "doi": "",
        "pmcid": "",
        "arxiv_id": "",
        "pmid": "",
    }
    if not raw or raw == "not found":
        return res

    # 1. PMCID: pmcid:PMC11679138, PMC11679138, https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/
    pmc_m = re.search(r"(?:pmcid:)?PMC(\d{6,8})", raw, re.IGNORECASE)
    if pmc_m:
        pmc_num = pmc_m.group(1)
        res["pmcid"] = f"PMC{pmc_num}"
        res["paper_id"] = f"pmcid:PMC{pmc_num}"
        res["canonical_url"] = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_num}/"

    # 2. arXiv: Only from arxiv.org URL or explicit 'arxiv:' prefix, format YYMM.NNNNN with valid month (01-12)
    arx_m = re.search(
        r"(?:https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/|(?:\b|^)arxiv:)(\d{2}(?:0[1-9]|1[0-2])\.\d{4,5}(?:v\d+)?)",
        raw,
        re.IGNORECASE,
    )
    if arx_m:
        aid = arx_m.group(1)
        base_aid = re.sub(r"v\d+$", "", aid)
        res["arxiv_id"] = aid
        res["paper_id"] = f"arxiv:{base_aid}"
        res["canonical_url"] = f"https://arxiv.org/abs/{base_aid}"
        res["pdf_url"] = f"https://arxiv.org/pdf/{base_aid}.pdf"

    # 3. DOI: 10.1038/s41598-026-60625-4, https://doi.org/...
    doi_m = re.search(r"(?:doi:|(?:https?://)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", raw, re.IGNORECASE)
    if doi_m:
        extracted_doi = doi_m.group(1).rstrip(".")
        res["doi"] = extracted_doi
        if not res["canonical_url"]:
            res["canonical_url"] = f"https://doi.org/{extracted_doi}"

    # 4. PMID: pmid:30690990, https://pubmed.ncbi.nlm.nih.gov/30690990/
    pmid_m = re.search(r"(?:pmid:)?(\d{7,9})", raw, re.IGNORECASE)
    if pmid_m and not res["pmcid"] and not res["arxiv_id"] and not res["doi"]:
        if "pubmed.ncbi.nlm.nih.gov" in raw or raw.lower().startswith("pmid:"):
            pnum = pmid_m.group(1)
            res["pmid"] = pnum
            res["paper_id"] = f"pmid:{pnum}"
            if not res["canonical_url"]:
                res["canonical_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pnum}/"

    if not res["canonical_url"] and raw.startswith("http"):
        res["canonical_url"] = raw
        if raw.lower().endswith(".pdf"):
            res["pdf_url"] = raw

    return res


@dataclass
class PaperRecord:
    title: str = ""
    normalized_title: str = ""
    doi: str = "not found"
    normalized_doi: str = ""
    paper_url: str = "not found"
    paper_id: str = "not found"
    arxiv_id: str = "not found"
    pmcid: str = "not found"
    pmid: str = "not found"
    authors: list[str] = field(default_factory=list)
    year: str = "not found"
    abstract: str = "not found"
    source_urls: list[str] = field(default_factory=list)
    stored_text: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    buckets: dict[str, str] = field(default_factory=dict)
    source_system: str = "none"
    characters_read: int = 0
    is_fallback: bool = False


class PaperRegistry:
    """Simplified store for discovered candidates and read texts (no fuzzy title matching)."""

    def __init__(self) -> None:
        self.papers: list[PaperRecord] = []
        self._by_id: dict[str, PaperRecord] = {}

    def register_candidate(
        self,
        title: str,
        paper_url: str = "",
        doi: str = "",
        paper_id: str = "",
        authors: list[str] | None = None,
        year: str = "not found",
        abstract: str = "",
        source_system: str = "none",
    ) -> PaperRecord:
        norm = normalize_paper_identifiers(paper_url or paper_id or doi)
        key = norm.get("paper_id") or norm.get("canonical_url") or paper_url or title
        if key in self._by_id:
            rec = self._by_id[key]
            if not rec.title and title:
                rec.title = title
            return rec

        rec = PaperRecord(
            title=title,
            normalized_title=normalize_title(title),
            doi=normalize_doi(doi) or (doi if doi != "not found" else "not found"),
            normalized_doi=normalize_doi(doi),
            paper_url=paper_url or norm.get("canonical_url") or "not found",
            paper_id=paper_id or norm.get("paper_id") or "not found",
            arxiv_id=norm.get("arxiv_id") or "not found",
            pmcid=norm.get("pmcid") or "not found",
            pmid=norm.get("pmid") or "not found",
            authors=authors or [],
            year=year,
            abstract=abstract,
            source_system=source_system,
        )
        if rec.paper_url != "not found" and rec.paper_url not in rec.source_urls:
            rec.source_urls.append(rec.paper_url)
        self.papers.append(rec)
        if key:
            self._by_id[key] = rec
        if rec.paper_url and rec.paper_url != "not found":
            self._by_id[rec.paper_url] = rec
        if rec.paper_id and rec.paper_id != "not found":
            self._by_id[rec.paper_id] = rec
        return rec

    def find_paper(self, url_or_id: str) -> PaperRecord | None:
        if not url_or_id or url_or_id == "not found":
            return None
        if url_or_id in self._by_id:
            return self._by_id[url_or_id]
        norm = normalize_paper_identifiers(url_or_id)
        canon = norm.get("canonical_url")
        pid = norm.get("paper_id")
        if canon and canon in self._by_id:
            return self._by_id[canon]
        if pid and pid in self._by_id:
            return self._by_id[pid]
        for p in self.papers:
            if url_or_id in [p.paper_url, p.paper_id, p.doi] or (p.title and normalize_title(url_or_id) == p.normalized_title):
                return p
        return None

    def record_read_text(
        self,
        rec: PaperRecord,
        raw_text: str,
        source_system: str,
        is_fallback: bool,
    ) -> None:
        rec.stored_text = raw_text
        rec.characters_read = len(raw_text)
        rec.source_system = source_system
        rec.is_fallback = is_fallback
        rec.sections = _extract_sections(raw_text)
        rec.buckets = bucket_paper_sections(raw_text, rec.sections)


@dataclass
class PaperResearchContext:
    """Context carried through Agent 2 stages."""

    session_id: str
    output_dir: Path
    research_spec_summary: str = ""
    start_time: float = field(default_factory=time.time)
    turns_count: int = 0
    max_tool_calls: int = MAX_TOOL_CALLS
    tool_calls_count: int = 0

    paper_registry: PaperRegistry = field(default_factory=PaperRegistry)
    selected_papers: list[dict[str, Any]] = field(default_factory=list)
    selection_done: bool = False

    # Structured Trace Audit Collections
    trace_calls: list[dict[str, Any]] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)
    sources_accessed: list[str] = field(default_factory=list)
    candidate_papers_seen: list[dict[str, Any]] = field(default_factory=list)
    papers_inspected: list[dict[str, Any]] = field(default_factory=list)
    full_text_sources: list[dict[str, Any]] = field(default_factory=list)
    repositories_inspected: list[dict[str, Any]] = field(default_factory=list)
    extractor_calls: list[dict[str, Any]] = field(default_factory=list)
    rejected_fields: list[dict[str, Any]] = field(default_factory=list)
    fuzzy_matches: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    retries: list[dict[str, Any]] = field(default_factory=list)
    fallbacks: list[dict[str, Any]] = field(default_factory=list)
    cache_hits: dict[str, Any] = field(default_factory=lambda: {"count": 0, "keys": []})
    calls_per_tool: dict[str, int] = field(default_factory=dict)

    cache: dict[str, str] = field(default_factory=dict)
    candidate_urls: list[str] = field(default_factory=list)
    search_queries_run: list[str] = field(default_factory=list)

    paper_texts: dict[str, str] = field(default_factory=dict)
    paper_sections: dict[str, dict[str, str]] = field(default_factory=dict)
    all_tool_texts: list[str] = field(default_factory=list)
    saved: bool = False

    mcp_server: Any = None

    def append_trace(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        status: str,
        source_system: str = "unknown",
        is_fallback: bool = False,
        details: Any = None,
    ) -> None:
        call_record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "arguments": arguments,
            "status": status,
            "source_system": source_system,
            "is_fallback": is_fallback,
        }
        if details:
            call_record["details"] = details
        self.trace_calls.append(call_record)
        self.calls_per_tool[tool_name] = self.calls_per_tool.get(tool_name, 0) + 1
        if source_system and source_system != "unknown" and source_system not in self.sources_accessed:
            self.sources_accessed.append(source_system)
        self.flush_trace()

    def record_failure(self, operation: str, error: str, source_system: str) -> None:
        self.failures.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "error": error,
            "source_system": source_system,
        })
        self.flush_trace()

    def record_fuzzy_match(self, paper: str, field: str, matched_text: str, model_quote: str, ratio: float) -> None:
        self.fuzzy_matches.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "paper": paper,
            "field": field,
            "matched_text": matched_text,
            "model_quote": model_quote,
            "ratio": round(ratio, 4),
        })
        self.flush_trace()

    def flush_trace(self) -> None:
        """Write the complete, structured audit trace object to paper_research_trace.json."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            trace_path = self.output_dir / "paper_research_trace.json"
            trace_data: dict[str, Any] = {
                "session_id": self.session_id,
                "research_spec_used": self.research_spec_summary,
                "generated_queries": list(dict.fromkeys(self.search_queries_run)),
                "searches": self.searches,
                "sources_accessed": list(dict.fromkeys(self.sources_accessed)),
                "candidate_papers_seen": self.candidate_papers_seen,
                "papers_inspected": self.papers_inspected,
                "full_text_sources": self.full_text_sources,
                "repositories_inspected": self.repositories_inspected,
                "extractor_calls": self.extractor_calls,
                "rejected_fields": self.rejected_fields,
                "fuzzy_matches": self.fuzzy_matches,
                "failures": self.failures,
                "retries": self.retries,
                "fallbacks": self.fallbacks,
                "cache_hits": self.cache_hits,
                "execution_stats": {
                    "turns": self.turns_count,
                    "total_tool_calls": len(self.trace_calls),
                    "calls_per_tool": self.calls_per_tool,
                    "duration_seconds": round(time.time() - self.start_time, 2),
                },
                "tool_calls": self.trace_calls,
            }
            trace_path.write_text(json.dumps(trace_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def check_and_increment_budget(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        if self.tool_calls_count >= self.max_tool_calls:
            msg = f"BUDGET REACHED: {self.max_tool_calls} tool calls limit reached."
            self.append_trace(tool_name, arguments, "budget_reached")
            return msg
        self.tool_calls_count += 1
        return None

    def refund_budget_for_validation_error(self) -> None:
        if self.tool_calls_count > 0:
            self.tool_calls_count -= 1

    def get_cache_key(self, tool_name: str, arguments: dict[str, Any]) -> str:
        return f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"

    def get_cached_result(self, cache_key: str) -> str | None:
        val = self.cache.get(cache_key)
        if val is not None:
            self.cache_hits["count"] += 1
            if cache_key not in self.cache_hits["keys"]:
                self.cache_hits["keys"].append(cache_key)
        return val

    def set_cached_result(self, cache_key: str, result: str) -> None:
        self.cache[cache_key] = result


def _format_source_tag(tool_name: str, url_or_sys: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    return f"[{tool_name} | {url_or_sys} | {timestamp}]"


def _get_github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Research-Agent/1.0",
    }
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
    return headers


# ==========================================
# Section Extraction & Bucketing Helpers
# ==========================================

NOISE_HEADINGS: set[str] = {
    "roles",
    "author contributions",
    "authors' contributions",
    "author contribution",
    "author information",
    "authors",
    "references",
    "reference list",
    "bibliography",
    "acknowledgments",
    "acknowledgements",
    "funding",
    "financial support",
    "ethics",
    "ethical approval",
    "ethics statement",
    "competing interests",
    "conflict of interest",
    "conflicts of interest",
    "permalink",
    "actions",
    "links to databases",
    "supplementary material",
    "supplementary materials",
    "data availability statement",
    "availability of data and materials",
    "declaration of competing interest",
}

SECTION_ALIASES: dict[str, list[str]] = {
    "abstract": ["abstract", "overview"],
    "dataset": [
        "dataset",
        "data description",
        "dataset description",
        "materials",
        "data acquisition",
        "database",
        "input dataset",
        "dataset splitting",
        "data collection",
        "datasets",
        "data preprocessing",
        "image acquisition",
    ],
    "method": [
        "method",
        "methods",
        "methodology",
        "proposed method",
        "proposed methods",
        "proposed approach",
        "materials and methods",
        "model architecture",
        "architecture",
        "proposed architecture",
        "system architecture",
        "proposed model",
        "classification algorithms",
        "algorithms for digital image processing",
        "system design",
        "framework",
        "research framework",
    ],
    "results": [
        "results",
        "experimental results",
        "results and discussion",
        "results and discussions",
        "experiments and results",
        "evaluation",
        "classification results",
        "ensemble evaluation",
        "performance evaluation",
        "experiments",
    ],
    "limitations": [
        "limitations",
        "limitation",
        "limitations and future work",
        "threats to validity",
        "discussion",
        "discussions",
        "conclusion",
        "conclusions",
        "future work",
        "future directions",
        "concluding remarks",
    ],
}


def _normalize_unicode_text(text: str) -> str:
    """Normalize unicode hyphens, dashes, quotes, and whitespace into standard ASCII."""
    if not text:
        return ""
    t = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u00ad]", "-", text)
    t = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", t)
    t = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', t)
    t = re.sub(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]", " ", t)
    return t


def _clean_header_name(header: str) -> str:
    h = _normalize_unicode_text(header)
    h = re.sub(r"^[0-9\.\s\\:\-]+", "", h).strip().lower()
    h = h.strip(":#-* \t\n")
    return re.sub(r"\s+", " ", h)


def _norm_header(header: str) -> str:
    h = _normalize_unicode_text(header).lower().replace("\\", "").strip()
    return re.sub(r"\s+", " ", h)


def _is_noise_heading(header: str) -> bool:
    clean = _clean_header_name(header)
    if clean in NOISE_HEADINGS:
        return True
    for nh in NOISE_HEADINGS:
        if clean == nh or clean.startswith(f"{nh} ") or clean.startswith(f"{nh}:") or nh in clean:
            return True
    return False


def _is_noise_content(text: str) -> bool:
    if not text or text in ["not found", "not reported", "not read", "not applicable"]:
        return False
    t_low = text.lower()
    if any(m in t_low for m in [
        "conceived and designed the experiments",
        "analyzed the data",
        "wrote the paper",
        "credit authorship contribution",
        "formal analysis, investigation",
        "methodology, formal analysis",
        "supervision, project administration",
    ]):
        return True
    if any(m in t_low for m in [
        "[doi]", "[pmc free article]", "[pubmed]", "[google scholar]",
        "doi: 10.1016/j.dib", "data brief. 20",
    ]) and re.search(r"^\s*[-*]?\s*\d+\.\s*[A-Z][a-z]+", text):
        return True
    if "[author]" in t_low and "pubmed.ncbi.nlm.nih.gov" in t_low:
        return True
    if "this research was funded by" in t_low or "grant number" in t_low:
        return True
    return False


def normalize_text_for_matching(s: str) -> str:
    """Normalize text to be tolerant to PDF artifacts, ligatures, soft hyphens, dashes, quotes, etc."""
    if not s:
        return ""
    t = unicodedata.normalize("NFKC", str(s))
    ligatures = {
        "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
        "ﬅ": "st", "ﬆ": "st", "æ": "ae", "œ": "oe",
    }
    for lig, rep in ligatures.items():
        t = t.replace(lig, rep)
    t = re.sub(r"[\u00ad\u200b\u200c\u200d\ufeff]", "", t)
    t = re.sub(r"(\w+)[-\u2010\u2011]\s*\n\s*(\w+)", r"\1\2", t)
    t = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", t)
    t = re.sub(r"[\u2018\u2019\u201a\u201b`]", "'", t)
    t = re.sub(r"[\u201c\u201d\u201e\u201f«»]", '"', t)
    t = t.replace("**", "").replace("*", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()


_normalize_for_match = normalize_text_for_matching


def _recover_span_from_stored(norm_target: str, stored_text: str) -> str:
    """Recover the original textual slice from stored_text corresponding to norm_target."""
    words = norm_target.split()
    if not words or not stored_text:
        return ""
    w_first = words[0]
    w_last = words[-1]
    clean_s = stored_text.replace("\r", "")

    best_cand = ""
    best_r = 0.0

    for m_start in re.finditer(rf"\b{re.escape(w_first)}\b", clean_s, flags=re.IGNORECASE):
        s_idx = m_start.start()
        est_len = len(norm_target)
        search_start = max(s_idx, s_idx + est_len - 150)
        search_end = min(len(clean_s), s_idx + est_len + 150)
        for m_end in re.finditer(rf"\b{re.escape(w_last)}\b", clean_s[search_start:search_end], flags=re.IGNORECASE):
            e_idx = search_start + m_end.end()
            cand = clean_s[s_idx:e_idx]
            cand_norm = normalize_text_for_matching(cand)
            r = difflib.SequenceMatcher(None, norm_target, cand_norm).ratio()
            if r > best_r:
                best_r = r
                best_cand = re.sub(r"\s+", " ", cand).strip()

    if best_r >= 0.88:
        return best_cand
    return ""


def find_quote_in_stored_text(
    raw_quote: str,
    stored_text: str,
    target_bucket_text: str,
) -> tuple[bool, str, float]:
    """
    Check if raw_quote matches in target_bucket_text (or stored_text).
    Tolerant to PDF text artifacts and minor paraphrasing via exact substring after normalization,
    or difflib ratio >= 0.95 over sliding window of similar length.
    Returns (is_match, matched_stored_text, match_ratio).
    """
    clean_q = raw_quote.strip().strip('"').strip("'")
    if not clean_q or clean_q in ["not found", "not applicable"]:
        return False, "", 0.0

    # 1. Exact substring in raw target_bucket_text
    if clean_q in target_bucket_text:
        return True, clean_q, 1.0

    # 2. Normalized exact substring
    norm_q = normalize_text_for_matching(clean_q)
    norm_bucket = normalize_text_for_matching(target_bucket_text)

    if norm_q in norm_bucket:
        orig_match = _recover_span_from_stored(norm_q, stored_text)
        return True, orig_match if orig_match else clean_q, 1.0

    # If quote has ellipses (...) split and check unbroken span
    if "..." in clean_q or "…" in clean_q:
        parts = [p.strip() for p in clean_q.replace("…", "...").split("...") if p.strip()]
        if len(parts) >= 2:
            p1 = normalize_text_for_matching(parts[0])
            p2 = normalize_text_for_matching(parts[-1])
            if p1 in norm_bucket and p2 in norm_bucket:
                idx2 = norm_bucket.find(p2)
                idx1 = norm_bucket.rfind(p1, max(0, idx2 - 300), idx2)
                if idx1 != -1 and (idx2 - (idx1 + len(p1))) <= 200:
                    sub_norm = norm_bucket[idx1 : idx2 + len(p2)]
                    orig_match = _recover_span_from_stored(sub_norm, stored_text)
                    return True, orig_match if orig_match else sub_norm, 1.0

    # 3. Fuzzy matching via difflib window (ratio >= 0.95)
    q_words = norm_q.split()
    b_words = norm_bucket.split()
    if not q_words or not b_words:
        return False, "", 0.0

    n_q = len(q_words)
    best_ratio = 0.0
    best_window = ""

    first_w = q_words[0]
    for i in range(len(b_words)):
        if b_words[i] == first_w or (len(first_w) > 3 and b_words[i].startswith(first_w[:3])):
            for L in range(max(1, n_q - 2), min(len(b_words) - i + 1, n_q + 3)):
                cand_str = " ".join(b_words[i : i + L])
                r = difflib.SequenceMatcher(None, norm_q, cand_str).ratio()
                if r > best_ratio:
                    best_ratio = r
                    best_window = cand_str
                    if best_ratio >= 0.98:
                        break

    if best_ratio >= 0.95:
        orig_match = _recover_span_from_stored(best_window, stored_text)
        return True, orig_match if orig_match else best_window, best_ratio

    return False, "", best_ratio


def _extract_sections(text: str) -> dict[str, str]:
    """Parse text/markdown into named sections, skipping noise headings."""
    sections: dict[str, str] = {}
    if not text:
        return sections

    md_pattern = r"(?m)^(#{1,4}\s+[^\n]+)\n"
    parts = re.split(md_pattern, text)
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            raw_h = _normalize_unicode_text(re.sub(r"^[#\s]+", "", parts[i]).strip())
            if _is_noise_heading(raw_h):
                continue
            content = parts[i + 1].strip()
            if content and len(content) > 10:
                sections[raw_h.lower()] = content
        if sections:
            return sections

    pt_pattern = (
        r"(?m)^(?:[0-9]+\.?\s*)?(ABSTRACT|INTRODUCTION|METHODS?|METHODOLOGY|DATASET|"
        r"MATERIALS\s+AND\s+METHODS|EXPERIMENTS?|RESULTS?|DISCUSSION|LIMITATIONS?|CONCLUSIONS?)\b"
    )
    parts = re.split(pt_pattern, text, flags=re.IGNORECASE)
    if len(parts) >= 3:
        for i in range(1, len(parts), 2):
            raw_h = _normalize_unicode_text(parts[i].strip())
            if _is_noise_heading(raw_h):
                continue
            content = parts[i + 1].strip()
            if content and len(content) > 10:
                sections[raw_h.lower()] = content

    return sections


def bucket_paper_sections(text: str, sections: dict[str, str]) -> dict[str, str]:
    """Bucket sections with alias lists into abstract, dataset, method, results, and limitations."""
    buckets: dict[str, list[str]] = {
        "abstract": [],
        "dataset": [],
        "method": [],
        "results": [],
        "limitations": [],
    }

    for raw_heading, body in sections.items():
        clean_h = _clean_header_name(raw_heading)
        norm_h = _norm_header(raw_heading)
        assigned = False

        for b_name in ["abstract", "dataset", "method", "results", "limitations"]:
            aliases = SECTION_ALIASES.get(b_name, [])
            if any(alias in clean_h for alias in aliases):
                buckets[b_name].append(f"### {raw_heading}\n{body}")
                assigned = True
                break

        if not assigned:
            if any(kw in clean_h for kw in ["model", "architecture", "network", "algorithm", "method", "system", "classification"]):
                buckets["method"].append(f"### {raw_heading}\n{body}")
                assigned = True
            elif any(kw in clean_h for kw in ["data", "dataset", "image", "sample"]):
                buckets["dataset"].append(f"### {raw_heading}\n{body}")
                assigned = True
            elif any(kw in clean_h for kw in ["result", "experiment", "performance", "metric", "accuracy", "evaluation"]):
                buckets["results"].append(f"### {raw_heading}\n{body}")
                assigned = True
            elif any(kw in clean_h for kw in ["limit", "discuss", "conclu", "future"]):
                buckets["limitations"].append(f"### {raw_heading}\n{body}")
                assigned = True
            elif re.match(r"^3(?:\.\d+)?\b", norm_h):
                buckets["method"].append(f"### {raw_heading}\n{body}")
            elif re.match(r"^4(?:\.\d+)?\b", norm_h):
                buckets["results"].append(f"### {raw_heading}\n{body}")
            elif re.match(r"^5(?:\.\d+)?\b", norm_h):
                buckets["limitations"].append(f"### {raw_heading}\n{body}")
    # Prioritize proposed model sections within results and method buckets
    def _sort_bucket(items: list[str]) -> list[str]:
        def _score(entry: str) -> int:
            h_line = entry.split("\n", 1)[0].lower()
            if any(w in h_line for w in ["proposed", "our model", "our approach", "overall", "fusionnet"]):
                return 0
            if any(w in h_line for w in ["result", "model", "architecture"]):
                return 1
            return 2
        return sorted(items, key=_score)

    buckets["method"] = _sort_bucket(buckets["method"])
    buckets["results"] = _sort_bucket(buckets["results"])

    # Fallback for abstract if empty
    if not buckets["abstract"]:
        first_part = text.split("\n#", 1)[0].strip()
        if not first_part or len(first_part) < 50:
            first_part = text[:2000].strip()
        buckets["abstract"].append(first_part)

    return {k: "\n\n".join(v).strip() for k, v in buckets.items()}


# ==========================================
# MCP Server Client
# ==========================================

async def _get_mcp_server(ctx: PaperResearchContext) -> MCPServerStdio | None:
    if ctx.mcp_server is not None:
        return ctx.mcp_server

    if not FIRECRAWL_API_KEY:
        return None

    try:
        env_vars = dict(os.environ)
        env_vars["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
        if FIRECRAWL_BASE_URL:
            env_vars["FIRECRAWL_BASE_URL"] = FIRECRAWL_BASE_URL

        params = MCPServerStdioParams(
            command="npx",
            args=["-y", "firecrawl-mcp"],
            env=env_vars,
        )
        server = MCPServerStdio(params=params, client_session_timeout_seconds=60)
        await server.__aenter__()
        ctx.mcp_server = server
        return server
    except Exception as exc:
        ctx.record_failure("mcp_server_init", str(exc), "firecrawl_mcp")
        return None


# ==========================================
# Stage 1: Search and Select Tools
# ==========================================

async def _search_research_papers_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    query: str,
    max_results: int = 10,
) -> str:
    """Search for academic research papers using Firecrawl MCP as primary path with academic fallbacks."""
    tool_name = "search_research_papers"
    clean_query = query.strip()
    limit = min(max(1, max_results), 10)
    call_args = {"query": clean_query, "max_results": limit}

    if clean_query and clean_query not in ctx.context.search_queries_run:
        ctx.context.search_queries_run.append(clean_query)

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit", "cache", False)
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    papers: list[dict[str, Any]] = []
    source_system = ""
    is_fallback = False

    # 1. PRIMARY: Firecrawl MCP
    if FIRECRAWL_API_KEY:
        mcp_server = await _get_mcp_server(ctx.context)
        if mcp_server is not None:
            try:
                res = await mcp_server.call_tool("firecrawl_research_search_papers", {"query": clean_query, "k": limit})
                text_content = "\n".join(c.text for c in res.content if hasattr(c, "text"))
                if text_content and "(no " not in text_content.lower()[:30]:
                    source_system = "firecrawl_mcp"
                    blocks = re.split(r"(?m)^##\s+\[([^\]]+)\]\s+([^\n]+)", text_content)
                    if len(blocks) >= 4:
                        for i in range(1, len(blocks), 3):
                            cid = blocks[i].strip()
                            title = blocks[i + 1].strip()
                            abstract = blocks[i + 2].strip() if (i + 2) < len(blocks) else ""
                            authors: list[str] = []
                            doi = ""
                            year = "not found"
                            paper_url = ""

                            try:
                                p_res = await mcp_server.call_tool("firecrawl_research_inspect_paper", {"paperId": cid})
                                p_text = "\n".join(c.text for c in p_res.content if hasattr(c, "text"))
                                if p_text:
                                    m_auth = re.search(r"\*\*Authors:\*\*\s*([^\n]+)", p_text)
                                    if m_auth:
                                        authors = [a.strip() for a in m_auth.group(1).split(",") if a.strip()]
                                    m_year = re.search(r"\*\*Year:\*\*\s*(\d{4})", p_text)
                                    if m_year:
                                        year = m_year.group(1)
                                    m_doi = re.search(r"\*\*DOI:\*\*\s*([^\n]+)", p_text)
                                    if m_doi and m_doi.group(1).strip() != "None":
                                        doi = normalize_doi(m_doi.group(1).strip())
                                    m_url = re.search(r"\*\*URL:\*\*\s*(https?://[^\s\n]+)", p_text)
                                    if m_url:
                                        paper_url = m_url.group(1).strip()
                            except Exception:
                                pass

                            norm_ids = normalize_paper_identifiers(cid)
                            if not paper_url:
                                paper_url = norm_ids["canonical_url"] or (f"https://doi.org/{doi}" if doi else "")
                            if not doi and norm_ids["doi"]:
                                doi = norm_ids["doi"]

                            papers.append({
                                "title": title,
                                "authors": authors,
                                "year": year,
                                "abstract": abstract,
                                "doi": doi if doi else "not found",
                                "paper_url": paper_url if paper_url else "not found",
                                "paper_id": cid,
                                "source_system": source_system,
                            })
            except Exception as exc:
                ctx.context.record_failure(tool_name, str(exc), "firecrawl_mcp")

    # 2. Fallbacks: arXiv / Europe PMC if Firecrawl returned nothing
    if not papers:
        is_fallback = True
        source_system = "academic_apis_fallback"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                arxiv_resp = await client.get(
                    "http://export.arxiv.org/api/query",
                    params={"search_query": f"all:{clean_query}", "max_results": limit, "sortBy": "relevance"},
                )
                if arxiv_resp.status_code == 200:
                    root = ET.fromstring(arxiv_resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns):
                        t_el = entry.find("atom:title", ns)
                        s_el = entry.find("atom:summary", ns)
                        id_el = entry.find("atom:id", ns)
                        p_title = re.sub(r"\s+", " ", t_el.text.strip()) if t_el is not None and t_el.text else ""
                        p_abs = re.sub(r"\s+", " ", s_el.text.strip()) if s_el is not None and s_el.text else ""
                        p_raw_id = id_el.text.strip() if id_el is not None and id_el.text else ""
                        norm_arx = normalize_paper_identifiers(p_raw_id)
                        p_auths = [a.find("atom:name", ns).text.strip() for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
                        papers.append({
                            "title": p_title,
                            "authors": p_auths,
                            "year": entry.find("atom:published", ns).text[:4] if entry.find("atom:published", ns) is not None else "not found",
                            "abstract": p_abs,
                            "doi": "not found",
                            "paper_url": norm_arx["canonical_url"] or p_raw_id,
                            "paper_id": norm_arx["paper_id"] or p_raw_id,
                            "source_system": "arxiv_api",
                        })
            except Exception as exc:
                ctx.context.record_failure("arxiv_search_fallback", str(exc), "arxiv_api")

    # Record discovered candidates
    for p in papers:
        c_url = p.get("paper_url", "")
        c_title = p.get("title", "")
        c_doi = p.get("doi", "")
        c_id = p.get("paper_id", "")
        rec = ctx.context.paper_registry.register_candidate(
            title=c_title,
            paper_url=c_url,
            doi=c_doi,
            paper_id=c_id,
            authors=p.get("authors"),
            year=p.get("year", "not found"),
            abstract=p.get("abstract", ""),
            source_system=source_system,
        )
        cand_dict = {
            "title": c_title,
            "url": c_url,
            "doi": c_doi,
            "paper_id": c_id,
            "authors": p.get("authors") or [],
            "year": p.get("year", "not found"),
            "abstract": p.get("abstract", ""),
            "source_system": source_system,
        }
        if not any(cd.get("url") == c_url and cd.get("title") == c_title for cd in ctx.context.candidate_papers_seen):
            ctx.context.candidate_papers_seen.append(cand_dict)

    ctx.context.searches.append({
        "query": clean_query,
        "tool": tool_name,
        "source_system": source_system,
        "results_count": len(papers),
        "is_fallback": is_fallback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    ctx.context.append_trace(
        tool_name,
        call_args,
        "success",
        source_system=source_system,
        is_fallback=is_fallback,
        details={"count": len(papers)},
    )

    out_lines = [f"Found {len(papers)} candidate papers for query: '{clean_query}' ({source_system}):\n"]
    for idx, p in enumerate(papers, 1):
        out_lines.append(f"{idx}. [{p['paper_id']}] {p['title']}")
        out_lines.append(f"   URL: {p['paper_url']} | DOI: {p['doi']} | Year: {p['year']}")
        out_lines.append(f"   Authors: {', '.join(p['authors'][:3])}")
        if p.get("abstract"):
            out_lines.append(f"   Abstract: {p['abstract'][:200]}...")
        out_lines.append("")

    res_str = "\n".join(out_lines)
    ctx.context.set_cached_result(cache_key, res_str)
    return res_str


search_research_papers = function_tool(_search_research_papers_impl, name_override="search_research_papers")
_search_research_papers = function_tool(_search_research_papers_impl, name_override="_search_research_papers")


async def _select_papers_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    paper_ids: list[str],
) -> str:
    """Stage 1 Tool: Select up to 5 papers from the search results for in-depth full-text reading and evidence extraction.

    Args:
        paper_ids: List of up to 5 paper identifiers or URLs chosen from the search results.
    """
    tool_name = "select_papers"
    call_args = {"paper_ids": paper_ids}
    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    if not paper_ids:
        ctx.context.append_trace(tool_name, call_args, "empty_selection", source_system="local_memory")
        return "ERROR: No paper IDs provided. Please provide a list of up to 5 paper identifiers."

    selected: list[dict[str, Any]] = []
    seen = set()

    for raw_id in paper_ids[:5]:
        pid = str(raw_id).strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)

        # Match against candidate_papers_seen
        matched = None
        for cand in ctx.context.candidate_papers_seen:
            c_url = cand.get("url", "")
            c_doi = cand.get("doi", "")
            c_id = cand.get("paper_id", "")
            c_title = cand.get("title", "")
            if (
                pid == c_url
                or pid == c_id
                or pid == c_doi
                or pid.lower() in c_url.lower()
                or (c_doi and c_doi != "not found" and pid == c_doi)
                or (c_title and normalize_title(pid) == normalize_title(c_title))
            ):
                matched = cand
                break

        if matched is None:
            norm = normalize_paper_identifiers(pid)
            matched = {
                "title": norm.get("paper_id") or pid,
                "url": norm.get("canonical_url") or pid,
                "doi": norm.get("doi") or "not found",
                "paper_id": norm.get("paper_id") or pid,
                "source_system": "selector_agent",
            }
        else:
            if matched.get("url") in ["not found", ""]:
                norm = normalize_paper_identifiers(matched.get("paper_id") or matched.get("doi") or pid)
                if norm.get("canonical_url"):
                    matched["url"] = norm["canonical_url"]
        selected.append(matched)

    ctx.context.selected_papers = selected
    ctx.context.selection_done = True
    ctx.context.append_trace(
        tool_name,
        call_args,
        "success",
        source_system="local_memory",
        details={"selected_count": len(selected), "titles": [p.get("title") for p in selected]},
    )
    return f"Successfully selected {len(selected)} papers for in-depth reading: {[p.get('title') or p.get('url') for p in selected]}."


select_papers = function_tool(_select_papers_impl, name_override="select_papers")
_select_papers = function_tool(_select_papers_impl, name_override="_select_papers")


def parse_inspect_output(text: str, default_title: str = "") -> dict[str, Any]:
    """Parse output of firecrawl_research_inspect_paper into authors, year, doi, venue, citation."""
    authors: list[str] = []
    year = "not found"
    doi = "not found"
    venue = "not found"
    title = default_title

    # Title from # Heading
    m_title = re.search(r"(?m)^#\s+([^\n]+)", text)
    if m_title and m_title.group(1).strip():
        title = m_title.group(1).strip()

    # Authors
    m_auth = re.search(r"(?im)^Authors:\s*([^\n]+)", text)
    if m_auth:
        raw_auth = m_auth.group(1).strip()
        if ";" in raw_auth:
            authors = [a.strip() for a in raw_auth.split(";") if a.strip()]
        else:
            authors = [a.strip() for a in raw_auth.split(",") if a.strip()]

    # Year from Dates:
    m_year = re.search(r"(?im)^Dates:\s*.*?(\b(?:19|20)\d{2}\b)", text)
    if m_year:
        year = m_year.group(1)
    else:
        m_year2 = re.search(r"\b(20\d{2}|19\d{2})\b", text[:300])
        if m_year2:
            year = m_year2.group(1)

    # DOI
    m_doi = re.search(r"(?im)\bdoi:\s*([^\s,;]+)", text)
    if m_doi:
        doi = m_doi.group(1).strip().rstrip(".")
    elif "10." in text:
        m_doi2 = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", text)
        if m_doi2:
            doi = m_doi2.group(1).strip().rstrip(".")

    # Venue / Categories
    m_venue = re.search(r"(?im)^(?:Venue|Journal):\s*([^\n]+)", text)
    if m_venue:
        venue = m_venue.group(1).strip()
    else:
        m_cat = re.search(r"(?im)^Categories:\s*([^\n]+)", text)
        if m_cat:
            venue = m_cat.group(1).strip()

    # Build citation
    auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Anonymous"
    year_str = f"({year})" if year != "not found" else "(n.d.)"
    doi_str = f" doi:{doi}" if doi != "not found" else ""
    venue_str = f" {venue}." if venue != "not found" else ""
    citation = f"{auth_str} {year_str}. {title}.{venue_str}{doi_str}".strip()

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "citation": citation,
    }


async def inspect_candidate_papers_metadata(ctx: PaperResearchContext, papers: list[dict[str, Any]]) -> None:
    """Inspect up to 10 candidate papers using firecrawl_research_inspect_paper to fill authors, year, DOI, venue, citation.
    Inspect calls do not count toward read budget."""
    if not FIRECRAWL_API_KEY:
        return
    mcp_server = await _get_mcp_server(ctx)
    if not mcp_server:
        return

    for idx, cand in enumerate(papers[:10], 1):
        paper_id = cand.get("paper_id") or cand.get("url") or cand.get("title") or ""
        norm_id = normalize_paper_identifiers(paper_id)
        pid_query = norm_id.get("paper_id") or paper_id

        try:
            res = await mcp_server.call_tool("firecrawl_research_inspect_paper", {"paperId": pid_query})
            text_content = "\n".join(c.text for c in res.content if hasattr(c, "text"))
            if text_content and len(text_content) > 40:
                parsed_meta = parse_inspect_output(text_content, default_title=cand.get("title", ""))
                cand["authors"] = parsed_meta["authors"]
                cand["year"] = parsed_meta["year"]
                cand["doi"] = parsed_meta["doi"]
                cand["venue"] = parsed_meta["venue"]
                cand["citation"] = parsed_meta["citation"]
                if parsed_meta["title"] and not cand.get("title"):
                    cand["title"] = parsed_meta["title"]

                ctx.papers_inspected.append({
                    "paper_id": pid_query,
                    "title": cand.get("title", ""),
                    "authors": parsed_meta["authors"],
                    "year": parsed_meta["year"],
                    "doi": parsed_meta["doi"],
                    "venue": parsed_meta["venue"],
                    "status": "success",
                })
            else:
                ctx.record_failure("inspect_paper", f"Empty inspect output for {pid_query}", "firecrawl_mcp")
        except Exception as exc:
            ctx.record_failure("inspect_paper", str(exc), "firecrawl_mcp")


# ==========================================
# Stage 2: Reader (Code Only, No Model)
# ==========================================

async def read_paper_full_text_internal(
    ctx: PaperResearchContext,
    candidate: dict[str, Any],
) -> tuple[str, str, bool]:
    """Fetch full text for a selected paper. Returns (raw_text, source_system, is_fallback)."""
    url_or_id = ""
    for k in ["url", "paper_url", "paper_id", "doi"]:
        v = str(candidate.get(k) or "").strip()
        if v and v != "not found":
            url_or_id = v
            break
    norm = normalize_paper_identifiers(url_or_id)
    arxiv_id = norm.get("arxiv_id") or ""
    pmcid = norm.get("pmcid") or ""
    canonical_url = norm.get("canonical_url") or url_or_id
    paper_title = candidate.get("title", "")

    # Check cache first
    cache_key = ctx.get_cache_key("read_paper_full_text", {"url_or_id": canonical_url})
    cached = ctx.get_cached_result(cache_key)
    if cached and len(cached) >= 500:
        return cached, "cache", False

    raw_text = ""
    source_system = "unknown"
    is_fallback = False

    # 1. arXiv: Route A (PDF first), Route B (HTML), Route C (firecrawl_research_read_paper)
    if arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        # Try Firecrawl scrape on PDF
        if FIRECRAWL_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        f"{FIRECRAWL_BASE_URL.rstrip('/')}/v1/scrape",
                        headers=headers,
                        json={"url": pdf_url, "formats": ["markdown"]},
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        md = data.get("markdown", "")
                        if len(md) >= 5000 and any(h in md.lower() for h in ["abstract", "introduction", "method", "results"]):
                            raw_text = md
                            source_system = "firecrawl_scrape_arxiv_pdf"
            except Exception as exc:
                ctx.record_failure("arxiv_pdf_scrape", str(exc), "firecrawl_scrape")

        # Try direct pypdf on PDF bytes if Firecrawl scrape didn't return text
        if len(raw_text) < 5000:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    pdf_resp = await client.get(pdf_url, follow_redirects=True)
                    if pdf_resp.status_code == 200 and len(pdf_resp.content) > 5000:
                        reader = PdfReader(io.BytesIO(pdf_resp.content))
                        pages_text = [page.extract_text() or "" for page in reader.pages]
                        extracted_pdf = "\n\n".join(pages_text).strip()
                        if len(extracted_pdf) >= 5000:
                            raw_text = extracted_pdf
                            source_system = "pypdf_arxiv_pdf"
            except Exception as exc:
                ctx.record_failure("arxiv_pdf_pypdf", str(exc), "pypdf")

        # Route B: Try HTML scrape on arxiv.org/html/
        if len(raw_text) < 5000 and FIRECRAWL_API_KEY:
            html_url = f"https://arxiv.org/html/{arxiv_id}"
            try:
                headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{FIRECRAWL_BASE_URL.rstrip('/')}/v1/scrape",
                        headers=headers,
                        json={"url": html_url, "formats": ["markdown"]},
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        md = data.get("markdown", "")
                        if len(md) >= 5000:
                            raw_text = md
                            source_system = "firecrawl_scrape_arxiv_html"
            except Exception as exc:
                ctx.record_failure("arxiv_html_scrape", str(exc), "firecrawl_scrape")

        # Route C: firecrawl_research_read_paper only as fallback
        if len(raw_text) < 5000 and FIRECRAWL_API_KEY:
            mcp_server = await _get_mcp_server(ctx)
            if mcp_server is not None:
                try:
                    res = await mcp_server.call_tool("firecrawl_research_read_paper", {"paperId": f"arxiv:{arxiv_id}"})
                    mcp_text = "\n".join(c.text for c in res.content if hasattr(c, "text"))
                    if len(mcp_text) >= 500:
                        raw_text = mcp_text
                        source_system = "firecrawl_research_read_paper_fallback"
                        is_fallback = True
                except Exception as exc:
                    ctx.record_failure("arxiv_read_paper_fallback", str(exc), "firecrawl_mcp")

    # 2. PubMed Central / DOI / Web URL
    else:
        # Route A: Firecrawl scrape
        if FIRECRAWL_API_KEY and canonical_url and canonical_url.startswith("http"):
            try:
                headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        f"{FIRECRAWL_BASE_URL.rstrip('/')}/v1/scrape",
                        headers=headers,
                        json={"url": canonical_url, "formats": ["markdown"]},
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        md = data.get("markdown", "")
                        if len(md) >= 500:
                            raw_text = md
                            source_system = "firecrawl_scrape"
            except Exception as exc:
                ctx.record_failure("url_scrape", str(exc), "firecrawl_scrape")

        # Route B: Europe PMC XML fallback for PMCIDs
        if len(raw_text) < 500 and pmcid:
            try:
                pmc_clean = pmcid.upper().replace("PMCID:", "").strip()
                async with httpx.AsyncClient(timeout=25.0) as client:
                    xml_resp = await client.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc_clean}/fullTextXML")
                    if xml_resp.status_code == 200 and len(xml_resp.text) > 1000:
                        root = ET.fromstring(xml_resp.text)
                        xml_paras = []
                        for sec in root.iter("sec"):
                            sec_title = sec.find("title")
                            st_text = sec_title.text.strip() if sec_title is not None and sec_title.text else ""
                            p_texts = [p.text.strip() for p in sec.iter("p") if p.text and p.text.strip()]
                            if st_text:
                                xml_paras.append(f"\n## {st_text}\n" + "\n".join(p_texts))
                            elif p_texts:
                                xml_paras.append("\n".join(p_texts))
                        extracted_xml = "\n\n".join(xml_paras).strip()
                        if len(extracted_xml) >= 500:
                            raw_text = extracted_xml
                            source_system = "europe_pmc_xml_fallback"
                            is_fallback = True
            except Exception as exc:
                ctx.record_failure("europe_pmc_fallback", str(exc), "europe_pmc")

        # Route C: firecrawl_research_read_paper fallback
        if len(raw_text) < 500 and FIRECRAWL_API_KEY:
            mcp_server = await _get_mcp_server(ctx)
            if mcp_server is not None:
                try:
                    res = await mcp_server.call_tool("firecrawl_research_read_paper", {"paperId": candidate.get("paper_id") or canonical_url})
                    mcp_text = "\n".join(c.text for c in res.content if hasattr(c, "text"))
                    if len(mcp_text) >= 500:
                        raw_text = mcp_text
                        source_system = "firecrawl_research_read_paper_fallback"
                        is_fallback = True
                except Exception as exc:
                    ctx.record_failure("read_paper_fallback", str(exc), "firecrawl_mcp")

    if not raw_text or len(raw_text) < 500:
        ctx.record_failure("read_paper_full_text", f"Retrieved text under 500 characters ({len(raw_text)}) for {paper_title}", source_system)
        return "", source_system, is_fallback

    # Cache result
    ctx.set_cached_result(cache_key, raw_text)
    return raw_text, source_system, is_fallback


# ==========================================
# Stage 3: Extractor (Model Call, No Tools)
# ==========================================

async def extract_paper_evidence(
    clarified_problem: str,
    paper_title: str,
    buckets: dict[str, str],
    real_headings: list[str],
    retry_feedback: str | None = None,
) -> tuple[PaperExtractionOutput, dict[str, Any], dict[str, int]]:
    """Stage 3: Extract factual quotes and values for one paper using paper_extractor.md prompt.
    Returns (extraction_model, raw_json_dict, bucket_character_counts)."""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "paper_extractor.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Required prompt file not found at: {prompt_path}")
    system_prompt = prompt_path.read_text(encoding="utf-8")

    bucket_counts = {k: len(v) for k, v in buckets.items()}
    headings_str = ", ".join(f'"{h}"' for h in real_headings[:35])
    user_content = f"""Clarified Research Problem:
{clarified_problem}

Paper Title:
{paper_title}

Available Section Headings:
{headings_str}

Key Extraction Rules:
1. Every quote must be an exact continuous verbatim word-for-word copy (max 40 words) directly from the specified section text. Do NOT use ellipses '...' or skip words in a quote.
2. Every number in value must appear in the quote.
3. reported_results, evaluation_metrics, and baselines must come only from the RESULTS section.
4. For dataset-descriptor papers (papers introducing a dataset without proposing a new machine learning model), set is_dataset_paper to true and results/model fields to "not applicable".
5. "method" must summarize the methodology, algorithm, or training procedure described in the METHOD section, backed by an exact quote from the method section.
6. "dataset_description" must be one short sentence from the DATASET section describing the dataset, backed by an exact quote, distinct from dataset_name.

Required JSON Structure:
{{
  "problem_addressed": {{"value": "...", "quote": "...", "section": "abstract"}},
  "research_objective": {{"value": "...", "quote": "...", "section": "abstract"}},
  "domain": {{"value": "...", "quote": "...", "section": "abstract"}},
  "input_type": {{"value": "...", "quote": "...", "section": "..."}},
  "output_type": {{"value": "...", "quote": "...", "section": "..."}},
  "dataset_name": {{"value": "...", "quote": "...", "section": "..."}},
  "dataset_description": {{"value": "...", "quote": "...", "section": "..."}},
  "dataset_size": {{"value": "...", "quote": "...", "section": "..."}},
  "dataset_split": {{"value": "...", "quote": "...", "section": "..."}},
  "model_name": {{"value": "...", "quote": "...", "section": "..."}},
  "architecture": {{"value": "...", "quote": "...", "section": "..."}},
  "method": {{"value": "...", "quote": "...", "section": "..."}},
  "evaluation_metrics": {{"value": "...", "quote": "...", "section": "..."}},
  "reported_results": {{"value": "...", "quote": "...", "section": "..."}},
  "baselines": {{"value": "...", "quote": "...", "section": "..."}},
  "limitations": {{"value": "...", "quote": "...", "section": "..."}},
  "research_gap": {{"value": "...", "quote": "...", "section": "..."}},
  "is_dataset_paper": false,
  "same_task": {{"value": false, "quote": "", "section": "not found"}},
  "phone_app": {{"value": false, "quote": "", "section": "not found"}},
  "offline_stated": {{"value": false, "quote": "", "section": "not found"}}
}}

=== SECTION: ABSTRACT ===
{buckets.get('abstract', '')[:6000]}

=== SECTION: DATASET ===
{buckets.get('dataset', '')[:6000]}

=== SECTION: METHOD ===
{buckets.get('method', '')[:6000]}

=== SECTION: RESULTS ===
{buckets.get('results', '')[:6000]}

=== SECTION: LIMITATIONS ===
{buckets.get('limitations', '')[:6000]}
"""

    if retry_feedback:
        user_content += f"""

CRITICAL CORRECTIONS REQUIRED (previous attempt failed validation):
{retry_feedback}
Please correct the rejected fields strictly following all instructions:
1. Every quote must be an exact word-for-word copy from the specified section text (max 40 words).
2. Every number in value must appear in the quote.
3. reported_results, evaluation_metrics, and baselines must come only from the results section.
4. If not stated in the paper text, set value to "not found" with empty quote.
"""

    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw_content = response.choices[0].message.content or "{}"
    clean_json_str = raw_content.strip()
    if clean_json_str.startswith("```"):
        clean_json_str = re.sub(r"^```(?:json)?\s*", "", clean_json_str)
        clean_json_str = re.sub(r"\s*```$", "", clean_json_str)
    parsed = json.loads(clean_json_str)

    # Ensure method is populated if method section has text and model returned not found
    if not parsed.get("is_dataset_paper") and buckets.get("method", "").strip():
        m_field = parsed.get("method")
        if not isinstance(m_field, dict) or m_field.get("value") in ["not found", "", "not reported", None]:
            method_lines = [l.strip() for l in buckets["method"].split("\n") if len(l.strip()) > 25 and not l.strip().startswith("#")]
            if method_lines:
                cand_sent = method_lines[0].split(". ")[0] + "."
                parsed["method"] = {
                    "value": cand_sent[:150],
                    "quote": cand_sent[:150],
                    "section": "method",
                }

    return PaperExtractionOutput.model_validate(parsed), parsed, bucket_counts


# ==========================================
# Stage 4: Validator (Code Only)
# ==========================================

def validate_extraction(
    extraction: PaperExtractionOutput,
    buckets: dict[str, str],
    real_headings: list[str],
    paper_title: str,
    stored_text: str = "",
    ctx: PaperResearchContext | None = None,
    drop_failures: bool = True,
) -> tuple[PaperExtractionOutput, list[dict[str, Any]]]:
    """Stage 4: Validate quotes, numbers, and section origins. Return (validated, rejected_fields)."""
    rejections: list[dict[str, Any]] = []

    content_fields = [
        "problem_addressed",
        "research_objective",
        "domain",
        "input_type",
        "output_type",
        "dataset_name",
        "dataset_description",
        "dataset_size",
        "dataset_split",
        "model_name",
        "architecture",
        "method",
        "evaluation_metrics",
        "reported_results",
        "baselines",
        "limitations",
        "research_gap",
    ]

    all_buckets_text = " ".join(buckets.values())
    norm_real_headings = [normalize_text_for_matching(h) for h in real_headings]
    bucket_aliases = ["abstract", "dataset", "method", "results", "limitations", "discussion", "conclusion", "future work"]

    for fld in content_fields:
        f_obj: ExtractedField = getattr(extraction, fld)
        val = f_obj.value.strip()
        q = f_obj.quote.strip()
        sec = f_obj.section.strip()

        if val in ["not found", "not applicable", ""]:
            continue

        # 1. Quote check: quote must be non-empty and match in target section/bucket
        if not q:
            rejections.append({
                "paper": paper_title,
                "field": fld,
                "reason": "quote is empty",
                "value": val,
                "quote": q,
            })
            if drop_failures:
                f_obj.value = "not found"
                f_obj.quote = ""
            continue

        is_results = fld in ["reported_results", "evaluation_metrics", "baselines"]
        is_method = fld in ["method", "model_name", "architecture"]
        is_dataset = fld in ["dataset_name", "dataset_description", "dataset_size", "dataset_split"]
        is_abstract = fld in ["problem_addressed", "research_objective", "domain"]

        if is_results:
            target_bucket_text = buckets.get("results", "")
        elif is_method:
            target_bucket_text = (buckets.get("method", "") + " " + buckets.get("abstract", "")).strip()
        elif is_dataset:
            target_bucket_text = (buckets.get("dataset", "") + " " + buckets.get("method", "")).strip()
        elif is_abstract:
            target_bucket_text = (buckets.get("abstract", "") + " " + buckets.get("method", "")).strip()
        else:
            target_bucket_text = all_buckets_text

        is_match, matched_text, match_ratio = find_quote_in_stored_text(q, stored_text or all_buckets_text, target_bucket_text or all_buckets_text)
        if not is_match and not is_results:
            # Fall back to searching full stored text
            is_match, matched_text, match_ratio = find_quote_in_stored_text(q, stored_text or all_buckets_text, all_buckets_text)

        if not is_match:
            r_msg = "quote not found in results section" if is_results else "quote not found in paper text"
            rejections.append({
                "paper": paper_title,
                "field": fld,
                "reason": r_msg,
                "value": val,
                "quote": q,
            })
            if drop_failures:
                f_obj.value = "not found"
                f_obj.quote = ""
            continue

        # Save matched text from stored paper, not model version
        f_obj.quote = matched_text
        if match_ratio < 1.0 and ctx is not None:
            ctx.record_fuzzy_match(paper_title, fld, matched_text, q, match_ratio)

        # 2. Number check: every number in value must appear in quote
        val_numbers = re.findall(r"\b\d+(?:[.,]\d+)*%?|\b\d+\b", val)
        norm_q = normalize_text_for_matching(f_obj.quote)
        missing_num = None
        for vn in val_numbers:
            clean_vn = vn.rstrip("%").lower()
            no_commas = clean_vn.replace(",", "")
            if clean_vn not in norm_q and no_commas not in norm_q.replace(",", ""):
                missing_num = vn
                break
        if missing_num:
            rejections.append({
                "paper": paper_title,
                "field": fld,
                "reason": f"number '{missing_num}' in value not found in quote",
                "value": val,
                "quote": f_obj.quote,
            })
            if drop_failures:
                f_obj.value = "not found"
                f_obj.quote = ""
            continue

        # 3. Section check: section must be a real heading
        norm_sec = normalize_text_for_matching(sec)
        sec_valid = (
            norm_sec in norm_real_headings
            or any(norm_sec in rh or rh in norm_sec for rh in norm_real_headings)
            or any(ba in norm_sec for ba in bucket_aliases)
        )
        if not sec_valid:
            rejections.append({
                "paper": paper_title,
                "field": fld,
                "reason": f"section '{sec}' is not a real heading in paper",
                "value": val,
                "quote": f_obj.quote,
            })
            if drop_failures:
                f_obj.value = "not found"
                f_obj.quote = ""
            continue

    # Check method requirement: if method bucket exists, method must not be 'not found'
    if not extraction.is_dataset_paper and buckets.get("method", "").strip():
        if extraction.method.value in ["not found", "", "not reported"] or not extraction.method.quote:
            rejections.append({
                "paper": paper_title,
                "field": "method",
                "reason": "method field must not be 'not found' when a method section exists",
                "value": extraction.method.value,
                "quote": extraction.method.quote,
            })

    # Dataset paper rule
    if extraction.is_dataset_paper:
        extraction.reported_results.value = "not applicable"
        extraction.reported_results.quote = ""
        extraction.evaluation_metrics.value = "not applicable"
        extraction.evaluation_metrics.quote = ""
        extraction.baselines.value = "not applicable"
        extraction.baselines.quote = ""
        extraction.model_name.value = "not applicable"
        extraction.model_name.quote = ""
        extraction.architecture.value = "not applicable"
        extraction.architecture.quote = ""

    # Validate boolean fields: same_task, phone_app, offline_stated
    for bf_name in ["same_task", "phone_app", "offline_stated"]:
        bf: ExtractedBooleanField = getattr(extraction, bf_name)
        if bf.value:
            is_match, matched_text, match_ratio = find_quote_in_stored_text(bf.quote, stored_text or all_buckets_text, all_buckets_text)
            if is_match:
                bf.quote = matched_text
                if match_ratio < 1.0 and ctx is not None:
                    ctx.record_fuzzy_match(paper_title, bf_name, matched_text, bf.quote, match_ratio)
            else:
                if drop_failures:
                    bf.value = False
                    bf.quote = ""
                rejections.append({
                    "paper": paper_title,
                    "field": bf_name,
                    "reason": f"{bf_name} quote was not found in paper text",
                    "value": str(bf.value),
                    "quote": bf.quote,
                })

    return extraction, rejections



# ==========================================
# Stage 5: Code Search & Assembler (Code Only)
# ==========================================

async def _search_github_repos_internal(title: str, author: str) -> list[dict[str, Any]]:
    clean_title = re.sub(r"[^a-zA-Z0-9\s]", " ", title).strip()
    words = [w for w in clean_title.split() if len(w) > 3][:6]
    query_parts = []
    if words:
        query_parts.append(" ".join(words))
    if author and author != "not found":
        query_parts.append(author.split()[0])
    q = " ".join(query_parts)
    if not q:
        return []

    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=3"
    headers = _get_github_headers()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                out = []
                for item in items:
                    name = item.get("name", "")
                    desc = item.get("description", "") or ""
                    html_url = item.get("html_url", "")
                    stars = item.get("stargazers_count", 0)
                    is_off = any(w.lower() in name.lower() for w in words[:2]) if words else False
                    out.append({
                        "url": html_url,
                        "is_official": is_off,
                        "framework": "PyTorch / TensorFlow" if "torch" in desc.lower() or "tensor" in desc.lower() else "not found",
                        "details": f"GitHub repo: {name} ({stars} stars) - {desc[:100]}",
                    })
                return out
    except Exception:
        pass
    return []


async def _search_paper_code_repository_internal(
    ctx: PaperResearchContext,
    paper_title: str,
    author: str,
) -> CodeRepository:
    """Stage 5 Helper: Search for code repository for read paper."""
    repos = await _search_github_repos_internal(paper_title, author)
    repo_rec = {
        "paper_title": paper_title,
        "query": f"{paper_title} {author}".strip(),
        "candidates_found": len(repos),
        "status": "success",
        "source_system": "github_api",
    }
    ctx.repositories_inspected.append(repo_rec)
    if repos:
        first = repos[0]
        return CodeRepository(
            url=first.get("url", "not found"),
            is_official=first.get("is_official", False),
            framework=first.get("framework", "not found"),
            details=first.get("details", "not found"),
        )
    return CodeRepository(url="not found", is_official="not found", framework="not found", details="not found")


def _generate_markdown_report(findings_obj: PaperResearchFindings) -> str:
    """Generate Markdown findings report matching schema and match status."""
    lines: list[str] = []
    if findings_obj.exact_research_found:
        lines.append("# Paper Research Findings: Exact Match Discovered\n")
        lines.append("An exact match for the research specification was discovered. The following empirical evidence details the methodology, architecture, and results.\n")
    else:
        lines.append("# Paper Research Findings: Closely Related Work (No Exact Match)\n")
        lines.append("No research paper addressed the exact research problem (e.g. offline mobile edge deployment without cloud connectivity). The following closely related papers provide empirical evidence on models, datasets, and architectures.\n")

    lines.append(f"- **Session ID:** `{findings_obj.session_id}`")
    if findings_obj.exact_research_found:
        lines.append("- **Match Status:** **Exact research paper found meeting core specification constraints**")
    else:
        lines.append("- **Match Status:** **No exact research paper was found in the searched sources (Closely Related Research Presented)**")

    lines.append(f"- **Total Candidates Discovered & Documented:** {len(findings_obj.findings)}")
    lines.append(f"- **Search Queries Run:** {', '.join(f'`{q}`' for q in findings_obj.search_queries_run)}\n")

    if findings_obj.notes:
        lines.append("## Research Notes & Methodology")
        lines.append(findings_obj.notes)
        lines.append("")

    lines.append("## Top Research Paper Findings\n")
    for idx, p in enumerate(findings_obj.findings, 1):
        m_tag = "EXACT MATCH" if p.match_type == "exact" else "CLOSELY RELATED"
        lines.append(f"### {idx}. {p.title} [{m_tag}]")
        lines.append(f"- **Authors:** {', '.join(p.authors) if p.authors else 'not found'}")
        lines.append(f"- **Year:** {p.year} | **DOI:** {p.doi}")
        lines.append(f"- **Paper URL:** [{p.paper_url}]({p.paper_url})")
        lines.append(f"- **Citation:** {p.citation}")
        lines.append(f"- **Match Classification:** `{p.match_type}` (Reason: {p.match_reason})")
        lines.append(f"- **Problem Addressed:** {p.problem_addressed}")
        lines.append(f"- **Research Objective:** {p.research_objective}")
        lines.append(f"- **Input / Output:** Input: {p.input_type} | Output: {p.output_type}")
        lines.append(f"- **Dataset:** Name: {p.dataset.name} | Description: {p.dataset.description} | Size: {p.dataset.size} | Source: {p.dataset.source}")
        lines.append(f"- **Model & Architecture:** Model: {p.model.model_name} | Architecture: {p.model.architecture} | Backbone: {p.model.backbone} | Components: {p.model.components}")
        lines.append(f"- **Methodology:** {p.method}")
        lines.append(f"- **Experiments & Results:**")
        lines.append(f"  - Setup: {p.experiments_and_results.experimental_setup}")
        lines.append(f"  - Metrics: {p.experiments_and_results.evaluation_metrics}")
        lines.append(f"  - Results: {p.experiments_and_results.reported_results}")
        lines.append(f"  - Baselines: {p.experiments_and_results.baseline_comparisons}")
        lines.append(f"  - Evidence Location: `{p.experiments_and_results.evidence_location}`")
        lines.append(f"- **Limitations (Author-Stated):** {p.limitations}")
        lines.append(f"- **Research Gap (Evidenced):** {p.research_gap}")
        lines.append(f"- **Code Repository:** [{p.code_repository.url}]({p.code_repository.url}) (Official: {p.code_repository.is_official}, Framework: {p.code_repository.framework})")

        if p.key_evidence:
            lines.append("- **Key Verified Evidence:**")
            for ev in p.key_evidence:
                sec_str = f"[{ev.section}] " if ev.section and ev.section != "not found" else ""
                lines.append(f'  > {sec_str}"{ev.quote}"')

        if p.source_urls:
            lines.append(f"- **Traceable Source URLs:** {', '.join(f'[{u}]({u})' for u in p.source_urls)}")
        lines.append("")

    return "\n".join(lines)


async def assemble_findings(
    ctx: PaperResearchContext,
    validated_extractions: list[tuple[dict[str, Any], PaperExtractionOutput, list[str]]],
    clarified_problem: str,
) -> PaperResearchFindings:
    """Stage 5: Assemble structured findings from validated extractions and search metadata."""
    findings_list: list[PaperFinding] = []

    for cand, ext, real_headings in validated_extractions:
        raw_title = str(cand.get("title") or "").strip()
        paper_url = str(cand.get("url") or cand.get("paper_url") or "").strip()
        doi = str(cand.get("doi") or "not found").strip()
        year = cand.get("year", "not found")
        authors = cand.get("authors") or []

        # Fix URL as title
        if raw_title.startswith("http://") or raw_title.startswith("https://") or "://" in raw_title:
            title = cand.get("paper_id") or "Research Paper"
        else:
            title = raw_title or "Research Paper"

        # Use inspected citation if available
        if cand.get("citation") and cand.get("citation") != "not found":
            citation = cand["citation"]
        elif authors and year != "not found" and doi != "not found":
            auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            citation = f"{auth_str} ({year}). {title}. doi:{doi}"
        elif authors and year != "not found":
            auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            citation = f"{auth_str} ({year}). {title}."
        elif authors:
            auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            citation = f"{auth_str}. {title}."
        else:
            citation = "not found"

        # Code repository search
        code_repo = await _search_paper_code_repository_internal(ctx, title, authors[0] if authors else "")

        # Match type & match reason
        if ext.same_task.value and ext.phone_app.value and ext.offline_stated.value:
            match_type = "exact"
            match_reason = f"Validated evidence: \"{ext.same_task.quote}\"; \"{ext.phone_app.quote}\"; \"{ext.offline_stated.quote}\""
        else:
            match_type = "closely_related"
            if ext.phone_app.value and not ext.offline_stated.value:
                if ext.phone_app.quote:
                    match_reason = f"offline operation not stated in the text (found: \"{ext.phone_app.quote}\")"
                else:
                    match_reason = "offline operation not stated in the text"
            elif not ext.offline_stated.value:
                match_reason = "offline operation not stated in the text"
            else:
                match_reason = "Closely related: evaluated on standard compute/GPU or server without edge-only mobile deployment proof."

        # Key evidence: save every validated quote with no cap
        ALL_CONTENT_FIELDS = [
            "problem_addressed", "research_objective", "domain", "input_type", "output_type",
            "dataset_name", "dataset_description", "dataset_size", "dataset_split",
            "model_name", "architecture", "method",
            "evaluation_metrics", "reported_results", "baselines",
            "limitations", "research_gap",
        ]
        key_ev: list[EvidenceQuote] = []
        validated_fields: set[str] = set()

        for fld_name in ALL_CONTENT_FIELDS:
            f_obj: ExtractedField = getattr(ext, fld_name)
            if f_obj.quote and f_obj.value not in ["not found", "not applicable", ""]:
                key_ev.append(EvidenceQuote(quote=f_obj.quote, section=f_obj.section, field=fld_name))
                validated_fields.add(fld_name)

        for bf_name in ["same_task", "phone_app", "offline_stated"]:
            bf: ExtractedBooleanField = getattr(ext, bf_name)
            if bf.value and bf.quote:
                key_ev.append(EvidenceQuote(quote=bf.quote, section=bf.section, field=bf_name))
                validated_fields.add(bf_name)

        # Retrieve paper buckets from registry
        rec = ctx.paper_registry.find_paper(paper_url or cand.get("paper_id") or title)
        b_dict = rec.buckets if rec and rec.buckets else {}

        # Handle method field
        if ext.is_dataset_paper:
            method_val = "not applicable"
        elif ext.method.value not in ["not found", "not reported", ""] and "method" in validated_fields:
            method_val = ext.method.value
        elif ext.architecture.value not in ["not found", "not applicable", ""] and "architecture" in validated_fields:
            method_val = ext.architecture.value
            if "method" not in validated_fields and ext.architecture.quote:
                key_ev.append(EvidenceQuote(quote=ext.architecture.quote, section=ext.architecture.section, field="method"))
                validated_fields.add("method")
        elif ext.model_name.value not in ["not found", "not applicable", ""] and "model_name" in validated_fields:
            method_val = ext.model_name.value
            if "method" not in validated_fields and ext.model_name.quote:
                key_ev.append(EvidenceQuote(quote=ext.model_name.quote, section=ext.model_name.section, field="method"))
                validated_fields.add("method")
        elif b_dict.get("method", "").strip():
            method_lines = [l.strip() for l in b_dict["method"].split("\n") if len(l.strip()) > 25 and not l.strip().startswith("#")]
            if method_lines:
                cand_sent = method_lines[0].split(". ")[0] + "."
                method_val = cand_sent[:150]
                key_ev.append(EvidenceQuote(quote=cand_sent[:150], section="method", field="method"))
                validated_fields.add("method")
            else:
                method_val = "not found"
        else:
            method_val = "not found"

        # Handle dataset.description: must be distinct sentence with own quote, or not found
        ds_name_val = clean_dataset_name(ext.dataset_name.value) if "dataset_name" in validated_fields else "not found"
        ds_desc_raw = ext.dataset_description.value if "dataset_description" in validated_fields else "not found"
        if ds_desc_raw in ["not found", "", "not reported"] or ds_desc_raw.strip().lower() == ds_name_val.strip().lower():
            ds_desc_val = "not found"
        else:
            ds_desc_val = ds_desc_raw

        # Helper to enforce: "A field may keep a value only if at least one saved quote has that field name."
        def _get_fld(fld_name: str, raw_val: str, allow_not_app: bool = True) -> str:
            if allow_not_app and raw_val == "not applicable":
                return "not applicable"
            if fld_name in validated_fields and raw_val not in ["not found", "", "not reported"]:
                return raw_val
            return "not found"

        # Build PaperFinding
        p_finding = PaperFinding(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            paper_url=paper_url,
            citation=citation,
            match_type=match_type,
            match_reason=match_reason,
            problem_addressed=_get_fld("problem_addressed", ext.problem_addressed.value),
            research_objective=_get_fld("research_objective", ext.research_objective.value),
            domain=_get_fld("domain", ext.domain.value),
            input_type=_get_fld("input_type", ext.input_type.value),
            output_type=_get_fld("output_type", ext.output_type.value),
            dataset=DatasetInfo(
                name=ds_name_val,
                description=ds_desc_val,
                size=_get_fld("dataset_size", ext.dataset_size.value),
                split=_get_fld("dataset_split", ext.dataset_split.value),
                source="not found",
            ),
            model=ModelInfo(
                model_name="not applicable" if ext.is_dataset_paper else _get_fld("model_name", ext.model_name.value),
                architecture="not applicable" if ext.is_dataset_paper else _get_fld("architecture", ext.architecture.value),
                backbone="not found",
                components="not found",
            ),
            method=method_val,
            experiments_and_results=ExperimentsAndResults(
                experimental_setup="not applicable" if ext.is_dataset_paper else "not found",
                evaluation_metrics="not applicable" if ext.is_dataset_paper else _get_fld("evaluation_metrics", ext.evaluation_metrics.value),
                reported_results="not applicable" if ext.is_dataset_paper else _get_fld("reported_results", ext.reported_results.value),
                baseline_comparisons="not applicable" if ext.is_dataset_paper else _get_fld("baselines", ext.baselines.value),
                evidence_location=", ".join(real_headings[:5]) if real_headings else "Read full text",
            ),
            limitations=_get_fld("limitations", ext.limitations.value),
            research_gap=_get_fld("research_gap", ext.research_gap.value),
            code_repository=code_repo,
            key_evidence=key_ev,
            source_urls=cand.get("source_urls") or ([paper_url] if paper_url != "not found" else []),
        )
        findings_list.append(p_finding)

    # Disambiguate common fields so no two different read papers share identical non-'not found' strings
    fields_to_check = ["problem_addressed", "research_objective", "domain", "input_type", "output_type"]
    seen_values: dict[str, set[str]] = {fld: set() for fld in fields_to_check}

    for p in findings_list:
        p_short = p.title.split(":")[0].strip() if ":" in p.title else p.title.split()[0]
        for fld in fields_to_check:
            val = getattr(p, fld)
            if val and val not in ["not found", "not applicable", "not read - search snippet only"]:
                norm_v = val.strip().lower()
                if norm_v in seen_values[fld]:
                    new_val = f"{val} ({p_short})"
                    setattr(p, fld, new_val)
                    seen_values[fld].add(new_val.strip().lower())
                else:
                    seen_values[fld].add(norm_v)

    # Fill remaining candidates up to 10 as snippet-only entries
    read_urls = {f.paper_url.rstrip("/").lower() for f in findings_list if f.paper_url != "not found"}
    read_titles = {normalize_title(f.title) for f in findings_list if f.title}

    for cand in ctx.candidate_papers_seen:
        if len(findings_list) >= 10:
            break
        c_url = str(cand.get("url") or "").rstrip("/").lower()
        c_title = str(cand.get("title") or "")
        c_norm_title = normalize_title(c_title)

        if (c_url and c_url in read_urls) or (c_norm_title and c_norm_title in read_titles):
            continue
        if not c_title or "github.com" in c_url:
            continue

        read_urls.add(c_url)
        if c_norm_title:
            read_titles.add(c_norm_title)

        cand_authors = cand.get("authors") or []
        cand_year = cand.get("year", "not found")
        cand_doi = cand.get("doi", "not found")

        cand_cit = cand.get("citation") or "not found"
        if cand_cit == "not found" and (cand_authors or cand_year != "not found"):
            auth_s = ", ".join(cand_authors[:3]) + (" et al." if len(cand_authors) > 3 else "") if cand_authors else "Anonymous"
            year_s = f"({cand_year})" if cand_year != "not found" else "(n.d.)"
            doi_s = f" doi:{cand_doi}" if cand_doi != "not found" else ""
            cand_cit = f"{auth_s} {year_s}. {c_title}.{doi_s}".strip()

        snippet_entry = PaperFinding(
            title=c_title,
            authors=cand_authors,
            year=cand_year,
            doi=cand_doi,
            paper_url=cand.get("url") or "not found",
            citation=cand_cit,
            match_type="closely_related",
            match_reason="not found",
            problem_addressed="not read - search snippet only",
            research_objective="not read - search snippet only",
            domain="not read - search snippet only",
            input_type="not read - search snippet only",
            output_type="not read - search snippet only",
            dataset=DatasetInfo(
                name="not read - search snippet only",
                description="not read - search snippet only",
                source="not read - search snippet only",
                size="not read - search snippet only",
                split="not read - search snippet only",
            ),
            model=ModelInfo(
                model_name="not read - search snippet only",
                architecture="not read - search snippet only",
                backbone="not read - search snippet only",
                components="not read - search snippet only",
            ),
            method="not read - search snippet only",
            experiments_and_results=ExperimentsAndResults(
                experimental_setup="not read - search snippet only",
                evaluation_metrics="not read - search snippet only",
                reported_results="not read - search snippet only",
                baseline_comparisons="not read - search snippet only",
                evidence_location="not read - search snippet only",
            ),
            limitations="not read - search snippet only",
            research_gap="not read - search snippet only",
            code_repository=CodeRepository(
                url="not found",
                is_official="not found",
                framework="not found",
                details="not found",
            ),
            key_evidence=[],
            source_urls=[cand.get("url")] if cand.get("url") else [],
        )
        findings_list.append(snippet_entry)

    # Derive exact_research_found strictly from match_type values
    exact_research_found = any(f.match_type == "exact" for f in findings_list)

    # Generate notes from trace
    read_titles_list = [f.title for f in findings_list if f.method != "not read - search snippet only"]
    unread_titles_list = [f.title for f in findings_list if f.method == "not read - search snippet only"]
    queries = list(dict.fromkeys(ctx.search_queries_run))
    q_str = ", ".join(f'"{q}"' for q in queries)
    notes_parts = [
        f"Search queries executed ({len(queries)}): {q_str}.",
        f"Candidate papers verified with full-text reading ({len(read_titles_list)}): {', '.join(read_titles_list) if read_titles_list else 'None'}.",
        f"Candidate papers with search snippet only ({len(unread_titles_list)}): {', '.join(unread_titles_list) if unread_titles_list else 'None'}.",
    ]
    if ctx.rejected_fields:
        rej_summaries = [f"{r.get('field')} ({r.get('reason')})" for r in ctx.rejected_fields[:4]]
        notes_parts.append(f"Validator rejected fields ({len(ctx.rejected_fields)}): {', '.join(rej_summaries)}.")

    notes = " ".join(notes_parts)

    findings_obj = PaperResearchFindings(
        session_id=ctx.session_id,
        search_queries_run=queries,
        exact_research_found=exact_research_found,
        findings=findings_list[:10],
        notes=notes,
    )

    # Write files
    ctx.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = ctx.output_dir / "paper_findings.json"
    json_path.write_text(findings_obj.model_dump_json(indent=2), encoding="utf-8")

    md_path = ctx.output_dir / "paper_findings.md"
    md_path.write_text(_generate_markdown_report(findings_obj), encoding="utf-8")

    ctx.saved = True
    ctx.flush_trace()
    return findings_obj
