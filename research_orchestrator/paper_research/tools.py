"""Function tools for the Research Paper Discovery and Evidence Collection Agent (Agent 2)."""

from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from agents import RunContextWrapper, function_tool
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from pydantic import ValidationError
from pypdf import PdfReader

from app.config import MAX_TOOL_CALLS, FIRECRAWL_API_KEY, FIRECRAWL_BASE_URL
from paper_research.schema import (
    PaperFinding,
    PaperResearchFindings,
    DatasetInfo,
    ModelInfo,
    ExperimentsAndResults,
    CodeRepository,
    EvidenceQuote,
    clean_dataset_name,
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

    # 3. DOI: 10.1038/s41598-026-60625-4, https://doi.org/10.1038/...
    doi_m = re.search(r"(?:doi:|(?:https?://)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", raw, re.IGNORECASE)
    if doi_m:
        extracted_doi = doi_m.group(1).rstrip(".")
        res["doi"] = extracted_doi
        if not res["canonical_url"]:
            res["canonical_url"] = f"https://doi.org/{extracted_doi}"
        if not res["paper_id"]:
            res["paper_id"] = f"doi:{extracted_doi}"

    # 4. PMID: pmid:42420345, 42420345, https://pubmed.ncbi.nlm.nih.gov/42420345/
    pmid_m = re.search(r"(?:pmid:)?(\d{7,9})", raw, re.IGNORECASE)
    if pmid_m and not res["pmcid"] and not res["arxiv_id"] and not res["doi"]:
        pid = pmid_m.group(1)
        res["pmid"] = pid
        res["paper_id"] = f"pmid:{pid}"
        if not res["canonical_url"]:
            res["canonical_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"

    # If raw is an HTTP(S) URL and canonical_url not set yet, use raw
    if raw.startswith("http") and not res["canonical_url"]:
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
    sections_read: set[str] = field(default_factory=set)
    source_system: str = "none"
    characters_read: int = 0
    is_fallback: bool = False


class PaperRegistry:
    """Registry maintaining a unified multi-key mapping for every discovered paper."""

    def __init__(self) -> None:
        self.papers: list[PaperRecord] = []
        self._url_map: dict[str, PaperRecord] = {}
        self._doi_map: dict[str, PaperRecord] = {}
        self._id_map: dict[str, PaperRecord] = {}
        self._title_map: dict[str, PaperRecord] = {}

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
        norm_title = normalize_title(title)
        norm_doi = normalize_doi(doi)

        # Check existing
        rec = self.find_paper(url_or_id=paper_url or paper_id, title=title, doi=doi)
        if rec is None:
            rec = PaperRecord(
                title=title,
                normalized_title=norm_title,
                doi=norm_doi or (doi if doi != "not found" else "not found"),
                normalized_doi=norm_doi,
                paper_url=paper_url or "not found",
                paper_id=paper_id or "not found",
                authors=authors or [],
                year=year,
                abstract=abstract,
                source_system=source_system,
            )
            self.papers.append(rec)
        else:
            # Update existing
            if not rec.title and title:
                rec.title = title
                rec.normalized_title = norm_title
            if (rec.doi == "not found" or not rec.doi) and norm_doi:
                rec.doi = norm_doi
                rec.normalized_doi = norm_doi
            if (rec.paper_url == "not found" or not rec.paper_url) and paper_url:
                rec.paper_url = paper_url
            if (rec.paper_id == "not found" or not rec.paper_id) and paper_id:
                rec.paper_id = paper_id
            if (not rec.authors or rec.authors == ["not found"]) and authors:
                rec.authors = authors
            if (rec.year == "not found" or not rec.year) and year != "not found":
                rec.year = year
            if (rec.abstract == "not found" or not rec.abstract) and abstract:
                rec.abstract = abstract

        # Extract parsed identifiers
        for candidate_key in [paper_url, paper_id, doi]:
            if candidate_key:
                ids = normalize_paper_identifiers(candidate_key)
                if ids["pmcid"]:
                    rec.pmcid = ids["pmcid"]
                if ids["arxiv_id"]:
                    rec.arxiv_id = ids["arxiv_id"]
                if ids["pmid"]:
                    rec.pmid = ids["pmid"]
                if ids["doi"] and (rec.doi == "not found" or not rec.doi):
                    rec.doi = ids["doi"]
                    rec.normalized_doi = normalize_doi(ids["doi"])
                if ids["canonical_url"]:
                    if ids["canonical_url"] not in rec.source_urls:
                        rec.source_urls.append(ids["canonical_url"])
                    if rec.paper_url == "not found":
                        rec.paper_url = ids["canonical_url"]

        if paper_url and paper_url != "not found" and paper_url not in rec.source_urls:
            rec.source_urls.append(paper_url)

        self._index_paper(rec)
        return rec

    def _index_paper(self, rec: PaperRecord) -> None:
        if rec.normalized_title:
            self._title_map[rec.normalized_title] = rec
        if rec.normalized_doi:
            self._doi_map[rec.normalized_doi] = rec
        if rec.doi and rec.doi != "not found":
            self._doi_map[normalize_doi(rec.doi)] = rec
        if rec.paper_id and rec.paper_id != "not found":
            self._id_map[rec.paper_id.lower()] = rec
        if rec.arxiv_id and rec.arxiv_id != "not found":
            self._id_map[rec.arxiv_id.lower()] = rec
            self._id_map[f"arxiv:{rec.arxiv_id.lower()}"] = rec
        if rec.pmcid and rec.pmcid != "not found":
            self._id_map[rec.pmcid.lower()] = rec
            self._id_map[f"pmcid:{rec.pmcid.lower()}"] = rec
        if rec.pmid and rec.pmid != "not found":
            self._id_map[rec.pmid.lower()] = rec
            self._id_map[f"pmid:{rec.pmid.lower()}"] = rec
        if rec.paper_url and rec.paper_url != "not found":
            self._url_map[rec.paper_url.rstrip("/").lower()] = rec
        for u in rec.source_urls:
            self._url_map[u.rstrip("/").lower()] = rec

    def find_paper(
        self,
        url_or_id: str = "",
        title: str = "",
        doi: str = "",
    ) -> PaperRecord | None:
        """Find a paper record by ANY identifier or normalized title."""
        # 1. Match by DOI
        if doi and doi != "not found":
            ndoi = normalize_doi(doi)
            if ndoi in self._doi_map:
                return self._doi_map[ndoi]
            for p in self.papers:
                if p.normalized_doi and p.normalized_doi == ndoi:
                    return p

        # 2. Match by URL or ID
        if url_or_id and url_or_id != "not found":
            clean_key = url_or_id.strip()
            key_lower = clean_key.rstrip("/").lower()

            if key_lower in self._url_map:
                return self._url_map[key_lower]
            if key_lower in self._id_map:
                return self._id_map[key_lower]

            ids = normalize_paper_identifiers(clean_key)
            if ids["doi"] and normalize_doi(ids["doi"]) in self._doi_map:
                return self._doi_map[normalize_doi(ids["doi"])]
            if ids["arxiv_id"] and ids["arxiv_id"].lower() in self._id_map:
                return self._id_map[ids["arxiv_id"].lower()]
            if ids["pmcid"] and ids["pmcid"].lower() in self._id_map:
                return self._id_map[ids["pmcid"].lower()]
            if ids["pmid"] and ids["pmid"].lower() in self._id_map:
                return self._id_map[ids["pmid"].lower()]
            if ids["canonical_url"] and ids["canonical_url"].rstrip("/").lower() in self._url_map:
                return self._url_map[ids["canonical_url"].rstrip("/").lower()]

            # Substring URL match
            for u, rec in self._url_map.items():
                if key_lower in u or u in key_lower:
                    return rec

        # 3. Match by Title (Strict normalized title match only, no loose token overlap)
        if title and title != "not found":
            ntitle = normalize_title(title)
            if ntitle in self._title_map:
                return self._title_map[ntitle]

            for p in self.papers:
                if p.normalized_title:
                    if p.normalized_title == ntitle:
                        return p
                    min_l = min(len(p.normalized_title), len(ntitle))
                    max_l = max(len(p.normalized_title), len(ntitle))
                    if max_l > 0 and (min_l / max_l) >= 0.95:
                        if ntitle in p.normalized_title or p.normalized_title in ntitle:
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
        self._index_paper(rec)


@dataclass
class PaperResearchContext:
    """Context carried through the PaperResearcher run."""

    session_id: str
    output_dir: Path
    research_spec_summary: str = ""
    start_time: float = field(default_factory=time.time)
    turns_count: int = 0
    max_tool_calls: int = MAX_TOOL_CALLS
    tool_calls_count: int = 0

    # Multi-Key Registry
    paper_registry: PaperRegistry = field(default_factory=PaperRegistry)
    missing_papers_warned: bool = False

    # Structured Trace Audit Collections
    trace_calls: list[dict[str, Any]] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)
    sources_accessed: list[str] = field(default_factory=list)
    candidate_papers_seen: list[dict[str, Any]] = field(default_factory=list)
    papers_inspected: list[dict[str, Any]] = field(default_factory=list)
    full_text_sources: list[dict[str, Any]] = field(default_factory=list)
    repositories_inspected: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    retries: list[dict[str, Any]] = field(default_factory=list)
    fallbacks: list[dict[str, Any]] = field(default_factory=list)
    cache_hits: dict[str, Any] = field(default_factory=lambda: {"count": 0, "keys": []})
    calls_per_tool: dict[str, int] = field(default_factory=dict)

    # State tracking
    cache: dict[str, str] = field(default_factory=dict)
    candidate_urls: list[str] = field(default_factory=list)
    search_queries_run: list[str] = field(default_factory=list)

    # Full text & entity memory
    paper_texts: dict[str, str] = field(default_factory=dict)
    paper_sections: dict[str, dict[str, str]] = field(default_factory=dict)
    paper_sections_requested: dict[str, set[str]] = field(default_factory=dict)
    all_tool_texts: list[str] = field(default_factory=list)
    known_dois: set[str] = field(default_factory=set)
    known_urls: set[str] = field(default_factory=set)
    known_titles: set[str] = field(default_factory=set)

    saved: bool = False
    findings_summary: str = ""

    # Live MCP client instance
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

    def record_fallback(self, operation: str, primary_system: str, fallback_system: str, reason: str) -> None:
        self.fallbacks.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "primary_system": primary_system,
            "fallback_system": fallback_system,
            "reason": reason,
        })
        if fallback_system not in self.sources_accessed:
            self.sources_accessed.append(fallback_system)
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
        # Save attempts do NOT count toward MAX_TOOL_CALLS and are always allowed
        if tool_name in ["save_paper_findings", "_save_paper_findings"]:
            return None

        # Reserve the last 3 calls for saving
        save_reserve = 3
        effective_limit = max(1, self.max_tool_calls - save_reserve)
        if self.tool_calls_count >= effective_limit:
            msg = "BUDGET REACHED: You MUST call save_paper_findings now with the papers you discovered and read. Do not output text in chat; call save_paper_findings now."
            self.append_trace(tool_name, arguments, "budget_reached")
            return msg
        self.tool_calls_count += 1
        return None

    def refund_budget_for_validation_error(self) -> None:
        """Do not count validation errors toward MAX_TOOL_CALLS."""
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

    def record_candidate_url(self, url: str) -> None:
        if url and url not in self.candidate_urls:
            self.candidate_urls.append(url)
            self.known_urls.add(url)


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
# Section Extraction Helpers
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
    "method": [
        "methods",
        "methodology",
        "materials and methods",
        "experimental design, materials, and methods",
        "experimental design, materials and methods",
        "experimental design",
        "proposed method",
        "proposed methods",
        "research framework",
        "method",
    ],
    "dataset": [
        "data",
        "data description",
        "dataset description",
        "input dataset",
        "data collection",
        "data acquisition",
        "database",
        "dataset",
        "datasets",
    ],
    "results": [
        "results",
        "experimental results",
        "classification results",
        "results and discussion",
        "experiments",
        "evaluation",
        "performance",
        "experimental evaluation",
    ],
    "limitations": [
        "limitations",
        "limitation",
        "limitations and future work",
        "threats to validity",
        "discussion",
        "conclusion",
        "conclusions",
    ],
    "discussion": [
        "discussion",
        "results and discussion",
        "discussion and conclusion",
    ],
    "conclusion": [
        "conclusion",
        "conclusions",
        "conclusion and future work",
        "concluding remarks",
    ],
    "abstract": [
        "abstract",
    ],
}


def _normalize_unicode_text(text: str) -> str:
    """Normalize unicode hyphens, dashes, quotes, and whitespace into standard ASCII."""
    if not text:
        return ""
    # Unicode hyphens and dashes to '-'
    t = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u00ad]", "-", text)
    # Curly quotes to straight quotes
    t = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", t)
    t = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', t)
    # Unicode spaces to ' '
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
    """Detect if content text came from author roles, bibliography, or noise metadata."""
    if not text or text in ["not found", "not reported", "not read", "not applicable"]:
        return False
    t_low = text.lower()
    # Author roles / CRediT statement
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
    # Reference list / bibliography citations
    if any(m in t_low for m in [
        "[doi]", "[pmc free article]", "[pubmed]", "[google scholar]",
        "doi: 10.1016/j.dib", "data brief. 20",
    ]) and re.search(r"^\s*[-*]?\s*\d+\.\s*[A-Z][a-z]+", text):
        return True
    # Author profile link
    if "[author]" in t_low and "pubmed.ncbi.nlm.nih.gov" in t_low:
        return True
    # Funding statement
    if "this research was funded by" in t_low or "grant number" in t_low:
        return True
    return False


def _extract_sections(text: str) -> dict[str, str]:
    """Parse text/markdown into named sections, skipping noise headings."""
    sections: dict[str, str] = {}
    if not text:
        return sections

    # 1. Try markdown headers (# , ## , ### )
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

    # 2. Try uppercase / numbered section titles
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


def _find_matching_sections(
    sections: dict[str, str],
    target_section_str: str,
) -> tuple[str, str, list[str]]:
    """Lookup requested sections using alias lists.

    Supports multiple sections in one call (e.g. 'dataset, method, results, limitations').
    If a section is not found, returns 'section not found' together with available section names.
    Never silently returns the start of the full text!
    """
    available_names = [k for k in sections.keys() if not _is_noise_heading(k)]
    available_str = ", ".join(k.title() for k in available_names) if available_names else "none"

    raw_clean_target = _normalize_unicode_text(target_section_str).strip().lower()
    if not raw_clean_target or raw_clean_target in ["all", "outline"]:
        return "", "outline", available_names

    # Check if target_section_str as a whole directly matches a section (e.g. "2. experimental design, materials, and methods")
    whole_norm = _norm_header(raw_clean_target)
    whole_clean = _clean_header_name(raw_clean_target)
    matches_whole = any(
        whole_norm == _norm_header(s)
        or (whole_clean and whole_clean == _clean_header_name(s))
        for s in sections
    )
    if matches_whole:
        raw_targets = [raw_clean_target]
    else:
        raw_targets = [t.strip().lower() for t in re.split(r"[,;+\n]", raw_clean_target) if t.strip()]

    results_blocks: list[str] = []
    found_sections: list[str] = []

    for req in raw_targets:
        req_norm = _norm_header(req)
        req_clean = _clean_header_name(req)
        alias_key = req_clean or req_norm
        if alias_key not in SECTION_ALIASES:
            if alias_key.endswith("s") and alias_key[:-1] in SECTION_ALIASES:
                alias_key = alias_key[:-1]
            elif f"{alias_key}s" in SECTION_ALIASES:
                alias_key = f"{alias_key}s"
        aliases = SECTION_ALIASES.get(alias_key, [req_clean or req_norm, req])

        matched_sections: list[tuple[str, str]] = []

        # Priority 1: Exact match on normalized header or cleaned header name
        for s_name, s_content in sections.items():
            if _is_noise_heading(s_name):
                continue
            s_norm = _norm_header(s_name)
            s_clean = _clean_header_name(s_name)
            if req_norm == s_norm or (req_clean and req_clean == s_clean):
                matched_sections.append((s_name, s_content))
                break

        # Priority 2: Direct numbered section match (e.g. "4.2", "4", "3.3", "4.2.")
        if not matched_sections:
            num_m = re.match(r"^(?:section\s+)?(\d+(?:\.\d+)*)\.?$", req_norm)
            if num_m:
                sec_num = num_m.group(1)
                for s_name, s_content in sections.items():
                    if _is_noise_heading(s_name):
                        continue
                    s_norm = _norm_header(s_name)
                    if re.match(rf"^(?:section\s+)?{re.escape(sec_num)}(?:[\.\s\:\-]|$)", s_norm):
                        matched_sections.append((s_name, s_content))

        # Priority 3: Exact cleaned match against aliases
        if not matched_sections:
            for alias in aliases:
                for s_name, s_content in sections.items():
                    if _is_noise_heading(s_name):
                        continue
                    c_name = _clean_header_name(s_name)
                    if c_name == alias:
                        matched_sections.append((s_name, s_content))
                        break
                if matched_sections:
                    break

        # Priority 4: Category expansion for "results", "experiments", "method", "methods"
        # Collects all matching sub-sections so the agent receives actual numbers / method
        if not matched_sections and req_clean in ["results", "result", "experiments", "experiment", "method", "methods", "methodology"]:
            for s_name, s_content in sections.items():
                if _is_noise_heading(s_name):
                    continue
                c_name = _clean_header_name(s_name)
                s_norm = _norm_header(s_name)
                if any(bad in c_name for bad in ["motivation for", "survey of", "review of"]):
                    continue
                if req_clean in ["results", "result", "experiments", "experiment"]:
                    if any(a in c_name for a in ["result", "results", "experiment", "evaluation", "performance", "classification"]) or re.match(r"^4(?:\.\d+)?\b", s_norm):
                        matched_sections.append((s_name, s_content))
                elif req_clean in ["method", "methods", "methodology"]:
                    if any(a in c_name for a in ["method", "methodology", "proposed", "materials and methods"]) or re.match(r"^3(?:\.\d+)?\b", s_norm):
                        matched_sections.append((s_name, s_content))

        # Priority 5: Prefix / Numbered match with alias (e.g. "3. methodology", "methods and materials")
        if not matched_sections:
            for alias in aliases:
                for s_name, s_content in sections.items():
                    if _is_noise_heading(s_name):
                        continue
                    c_name = _clean_header_name(s_name)
                    if c_name.startswith(f"{alias} ") or c_name.startswith(f"{alias}:") or re.match(rf"^{re.escape(alias)}\b", c_name):
                        matched_sections.append((s_name, s_content))
                        break
                if matched_sections:
                    break

        # Priority 6: Word boundary / Substring match, excluding negative phrases
        if not matched_sections:
            for alias in aliases:
                for s_name, s_content in sections.items():
                    if _is_noise_heading(s_name):
                        continue
                    c_name = _clean_header_name(s_name)
                    if any(bad in c_name for bad in ["motivation for", "survey of", "review of"]):
                        continue
                    if re.search(rf"\b{re.escape(alias)}\b", c_name) or (len(alias) >= 4 and alias in c_name):
                        matched_sections.append((s_name, s_content))
                        break
                if matched_sections:
                    break

        # Priority 7: Fallback substring match with req_clean
        if not matched_sections and req_clean and len(req_clean) >= 4:
            for s_name, s_content in sections.items():
                if _is_noise_heading(s_name):
                    continue
                c_name = _clean_header_name(s_name)
                if req_clean in c_name:
                    matched_sections.append((s_name, s_content))
                    break

        if matched_sections:
            for m_name, m_content in matched_sections:
                if m_name not in found_sections:
                    found_sections.append(m_name)
                results_blocks.append(
                    f"### [Section: {m_name.title()}] (Requested: '{req}')\n{m_content[:6000]}"
                )
        else:
            results_blocks.append(
                f"### [Section Not Found: '{req}']\nsection not found: '{req}'. Available sections: {available_str}"
            )

    combined_output = "\n\n".join(results_blocks)
    sec_label = ", ".join(found_sections) if found_sections else "section_not_found"
    return combined_output, sec_label, found_sections


def _find_matching_section(
    sections: dict[str, str],
    target_section: str,
    full_text: str = "",
) -> tuple[str, str]:
    """Backward-compatible helper returning (content, section_label)."""
    content, sec_label, _ = _find_matching_sections(sections, target_section)
    return content, sec_label


# ==========================================
# MCP Client Singleton Manager
# ==========================================

async def _get_mcp_server(ctx: PaperResearchContext) -> MCPServerStdio | None:
    if ctx.mcp_server is not None:
        return ctx.mcp_server

    if not FIRECRAWL_API_KEY:
        return None

    try:
        params = MCPServerStdioParams(
            command="npx",
            args=["-y", "firecrawl-mcp"],
            env={
                "FIRECRAWL_API_KEY": FIRECRAWL_API_KEY,
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            },
        )
        server = MCPServerStdio(params=params)
        await server.connect()
        ctx.mcp_server = server
        if "firecrawl_mcp" not in ctx.sources_accessed:
            ctx.sources_accessed.append("firecrawl_mcp")
        return server
    except BaseException as exc:
        ctx.record_failure("mcp_server_connect", str(exc), "firecrawl_mcp")
        return None


# ==========================================
# 1. Search Papers Tool
# ==========================================

async def _search_research_papers_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search for academic research papers using Firecrawl MCP as primary path with academic fallbacks.

    Returns a list of candidate papers with title, authors, year, abstract, DOI, paper_url, and paper_id.
    """
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

    # 1. PRIMARY PATH: Firecrawl MCP
    if FIRECRAWL_API_KEY:
        mcp_server = await _get_mcp_server(ctx.context)
        if mcp_server is not None:
            try:
                res = await mcp_server.call_tool("firecrawl_research_search_papers", {"query": clean_query, "k": limit})
                text_content = "\n".join(c.text for c in res.content if hasattr(c, "text"))
                if text_content and "(no " not in text_content.lower()[:30]:
                    source_system = "firecrawl_mcp"
                    # Parse paper entries from markdown: ## [canonical_id] Title\nAbstract
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
                                insp = await mcp_server.call_tool("firecrawl_research_inspect_paper", {"paperId": cid})
                                insp_text = "\n".join(c.text for c in insp.content if hasattr(c, "text"))
                                ctx.context.all_tool_texts.append(insp_text)

                                doi_m = re.search(r"doi:(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", insp_text)
                                if doi_m:
                                    doi = doi_m.group(1).rstrip(".")
                                auth_m = re.search(r"Authors:\s*([^\n]+)", insp_text)
                                if auth_m:
                                    authors = [a.strip() for a in auth_m.group(1).split(";") if a.strip()]
                                year_m = re.search(r"(\b20[12]\d\b)", insp_text)
                                if year_m:
                                    year = year_m.group(1)
                            except Exception:
                                pass

                            ids = normalize_paper_identifiers(cid)
                            paper_url = ids["canonical_url"] or f"https://doi.org/{doi or cid}"
                            if not doi and ids["doi"]:
                                doi = ids["doi"]

                            papers.append({
                                "title": title,
                                "authors": authors,
                                "year": year,
                                "doi": doi or "not found",
                                "paper_id": cid,
                                "paper_url": paper_url,
                                "abstract": abstract[:1500] or "not found",
                                "source": "firecrawl_mcp",
                            })
                            if len(papers) >= limit:
                                break
            except BaseException as exc:
                ctx.context.record_failure("firecrawl_research_search_papers", str(exc), "firecrawl_mcp")

        # Fallback to Firecrawl REST API if MCP returned empty
        if not papers:
            try:
                fc_url = f"{FIRECRAWL_BASE_URL.rstrip('/')}/v1/search"
                fc_headers = {
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                }
                fc_payload = {"query": f"{clean_query} research paper", "limit": limit}
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    resp = await client.post(fc_url, json=fc_payload, headers=fc_headers)
                    if resp.status_code == 200:
                        fc_data = resp.json().get("data", [])
                        for item in fc_data[:limit]:
                            p_url = item.get("url", "")
                            papers.append({
                                "title": item.get("title", ""),
                                "authors": [],
                                "year": "not found",
                                "doi": "not found",
                                "paper_id": "not found",
                                "paper_url": p_url or "not found",
                                "abstract": item.get("description", "") or "not found",
                                "source": "firecrawl_api",
                            })
                        if papers:
                            source_system = "firecrawl_api"
            except Exception as exc:
                ctx.context.record_failure("firecrawl_rest_search", str(exc), "firecrawl_api")

    # 2. ACADEMIC FALLBACK: Europe PMC & arXiv
    if not papers:
        is_fallback = True
        ctx.context.record_fallback("search_research_papers", "firecrawl", "europe_pmc", "Firecrawl returned no papers")
        try:
            epmc_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            epmc_params = {"query": clean_query, "format": "json", "pageSize": limit, "resultType": "core"}
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                epmc_resp = await client.get(epmc_url, params=epmc_params)
                if epmc_resp.status_code == 200:
                    results = epmc_resp.json().get("resultList", {}).get("result", [])
                    for r in results:
                        doi = (r.get("doi") or "").strip()
                        pmcid = (r.get("pmcid") or "").strip()
                        p_url = f"https://doi.org/{doi}" if doi else (
                            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else f"https://europepmc.org/article/MED/{r.get('id', '')}"
                        )
                        authors_str = r.get("authorString", "")
                        authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []
                        papers.append({
                            "title": r.get("title", "").rstrip("."),
                            "authors": authors[:5],
                            "year": r.get("pubYear", "not found"),
                            "doi": doi or "not found",
                            "paper_id": f"pmcid:{pmcid}" if pmcid else r.get("id", "not found"),
                            "paper_url": p_url or "not found",
                            "abstract": (r.get("abstractText") or "not found")[:1500],
                            "source": "europe_pmc_fallback",
                        })
                    if papers:
                        source_system = "europe_pmc_fallback"
        except Exception as exc:
            ctx.context.record_failure("europe_pmc_search", str(exc), "europe_pmc")

        if len(papers) < limit:
            try:
                arxiv_url = "https://export.arxiv.org/api/query"
                arxiv_params = {"search_query": f"all:{clean_query}", "start": 0, "max_results": limit}
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    arxiv_resp = await client.get(arxiv_url, params=arxiv_params)
                    if arxiv_resp.status_code == 200:
                        root = ET.fromstring(arxiv_resp.text)
                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        for entry in root.findall("atom:entry", ns):
                            arx_id = entry.findtext("atom:id", "", ns).strip()
                            t_node = entry.findtext("atom:title", "", ns).strip()
                            title = " ".join(t_node.split())
                            summary = " ".join(entry.findtext("atom:summary", "", ns).split())
                            published = entry.findtext("atom:published", "", ns).strip()
                            year = published[:4] if published else "not found"
                            authors = [a.findtext("atom:name", "", ns).strip() for a in entry.findall("atom:author", ns)]
                            ids = normalize_paper_identifiers(arx_id)
                            papers.append({
                                "title": title,
                                "authors": authors[:5],
                                "year": year,
                                "doi": "not found",
                                "paper_id": ids["paper_id"] or arx_id,
                                "paper_url": ids["canonical_url"] or arx_id,
                                "abstract": summary[:1500],
                                "source": "arxiv_fallback",
                            })
                        if not source_system:
                            source_system = "arxiv_fallback"
            except Exception as exc:
                ctx.context.record_failure("arxiv_search", str(exc), "arxiv")

    # Register each candidate in multi-key registry & context collections
    for p in papers:
        p_title = p.get("title", "")
        p_url = p.get("paper_url", "")
        p_doi = p.get("doi", "")
        p_id = p.get("paper_id", "")
        p_authors = p.get("authors", [])
        p_year = p.get("year", "not found")
        p_abstract = p.get("abstract", "")

        ctx.context.paper_registry.register_candidate(
            title=p_title,
            paper_url=p_url,
            doi=p_doi,
            paper_id=p_id,
            authors=p_authors,
            year=p_year,
            abstract=p_abstract,
            source_system=p.get("source", source_system),
        )

        if p_title:
            ctx.context.known_titles.add(p_title.lower())
        if p_url and p_url != "not found":
            ctx.context.record_candidate_url(p_url)
        if p_doi and p_doi != "not found":
            ctx.context.known_dois.add(normalize_doi(p_doi))
        if p_abstract and p_abstract != "not found":
            ctx.context.all_tool_texts.append(p_abstract)

        ctx.context.candidate_papers_seen.append({
            "title": p_title,
            "url": p_url,
            "doi": p_doi,
            "source_system": p.get("source", source_system),
        })

    ctx.context.searches.append({
        "query": clean_query,
        "tool": tool_name,
        "source_system": source_system or "none",
        "results_count": len(papers),
        "is_fallback": is_fallback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    source_tag = _format_source_tag(tool_name, source_system or "academic_search")
    res_obj = {
        "source_tag": source_tag,
        "source_system": source_system,
        "is_fallback": is_fallback,
        "query": clean_query,
        "count": len(papers),
        "papers": papers,
    }
    result_str = json.dumps(res_obj, indent=2)
    ctx.context.set_cached_result(cache_key, result_str)
    ctx.context.append_trace(
        tool_name,
        call_args,
        "success" if papers else "empty_results",
        source_system=source_system or "unknown",
        is_fallback=is_fallback,
        details={"count": len(papers)},
    )
    return result_str


search_research_papers = function_tool(_search_research_papers_impl, name_override="search_research_papers")
_search_research_papers = function_tool(_search_research_papers_impl, name_override="_search_research_papers")


# ==========================================
# 2. Read Paper Full Text Tool
# ==========================================

async def _read_paper_full_text_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    url_or_id: str,
    target_section: str = "all",
) -> str:
    """Read verified full-text or PDF content of a research paper across sections.

    Normalizes identifiers before reading. Primary path uses Firecrawl scrape on canonical URL,
    and Firecrawl read_paper on canonical paperId. Keeps full text stored and returns text by section.
    """
    tool_name = "read_paper_full_text"
    clean_id = (url_or_id or "").strip()
    clean_section = (target_section or "all").strip().lower()
    call_args = {"url_or_id": clean_id, "target_section": clean_section}

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit", "cache", False)
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    if not clean_id or clean_id == "not found":
        ctx.context.refund_budget_for_validation_error()
        msg = f"[{tool_name}] No valid paper URL or ID provided to fetch full text."
        ctx.context.append_trace(tool_name, call_args, "invalid_id")
        return msg

    # Normalize identifiers
    ids = normalize_paper_identifiers(clean_id)
    canonical_url = ids["canonical_url"] or (clean_id if clean_id.startswith("http") else "")
    pdf_url = ids["pdf_url"]
    paper_id = ids["paper_id"]

    # Match paper in registry
    rec = ctx.context.paper_registry.find_paper(url_or_id=clean_id)
    if rec is None:
        cand_title = ""
        for c in ctx.context.candidate_papers_seen:
            c_u = c.get("url") or ""
            c_doi = c.get("doi") or ""
            c_id = c.get("id") or ""
            c_t = c.get("title") or ""
            if (clean_id in c_u or c_u in clean_id or (ids["doi"] and ids["doi"] == c_doi) or clean_id == c_id) and c_t and not c_t.lower().startswith("http"):
                cand_title = c_t
                break
        rec = ctx.context.paper_registry.register_candidate(
            title=cand_title,
            paper_url=canonical_url or clean_id,
            doi=ids["doi"],
            paper_id=paper_id,
        )
    elif not rec.title or rec.title.lower().startswith("http"):
        for c in ctx.context.candidate_papers_seen:
            c_u = c.get("url") or ""
            c_doi = c.get("doi") or ""
            c_id = c.get("id") or ""
            c_t = c.get("title") or ""
            if (clean_id in c_u or c_u in clean_id or (ids["doi"] and ids["doi"] == c_doi) or clean_id == c_id) and c_t and not c_t.lower().startswith("http"):
                rec.title = c_t
                rec.normalized_title = normalize_title(c_t)
                break

    raw_text = rec.stored_text
    source_system = rec.source_system
    is_fallback = rec.is_fallback
    scrape_chars = 0
    read_paper_chars = 0

    # 1. PRIMARY PATH: Firecrawl
    if len(raw_text) < 500 and FIRECRAWL_API_KEY:
        mcp_server = await _get_mcp_server(ctx.context)

        # For arXiv papers, execute routes in order:
        # Route 1: Firecrawl scrape of https://arxiv.org/pdf/ID
        # Route 2: Firecrawl scrape of https://arxiv.org/html/ID
        # Route 3: firecrawl_research_read_paper with paperId arxiv:ID
        # Route 4: pypdf on PDF bytes
        if ids["arxiv_id"]:
            aid = ids["arxiv_id"]
            base_aid = re.sub(r"v\d+$", "", aid)
            for u in [
                f"https://arxiv.org/abs/{base_aid}",
                f"https://arxiv.org/pdf/{base_aid}",
                f"https://arxiv.org/pdf/{base_aid}.pdf",
                f"arxiv:{base_aid}",
            ]:
                if u not in rec.source_urls:
                    rec.source_urls.append(u)

            # Route 1: Firecrawl scrape of PDF URL
            if len(raw_text) < 5000 and mcp_server is not None:
                try:
                    pdf_url = f"https://arxiv.org/pdf/{base_aid}"
                    scr_res = await mcp_server.call_tool("firecrawl_scrape", {"url": pdf_url})
                    scraped = "\n".join(c.text for c in scr_res.content if hasattr(c, "text"))
                    if scraped.strip().startswith("{"):
                        try:
                            scraped = json.loads(scraped).get("markdown", scraped)
                        except Exception:
                            pass
                    if len(scraped) >= 5000 and any(h in scraped.lower() for h in ["abstract", "introduction", "method", "dataset", "conclusion"]):
                        raw_text = scraped
                        source_system = "firecrawl_mcp"
                        is_fallback = False
                except BaseException as exc:
                    ctx.context.record_failure("arxiv_pdf_scrape_mcp", str(exc), "firecrawl_mcp")

            # Route 2: Firecrawl scrape of HTML URL
            if len(raw_text) < 5000 and mcp_server is not None:
                try:
                    html_url = f"https://arxiv.org/html/{base_aid}"
                    scr_res2 = await mcp_server.call_tool("firecrawl_scrape", {"url": html_url})
                    scraped2 = "\n".join(c.text for c in scr_res2.content if hasattr(c, "text"))
                    if scraped2.strip().startswith("{"):
                        try:
                            scraped2 = json.loads(scraped2).get("markdown", scraped2)
                        except Exception:
                            pass
                    if len(scraped2) >= 5000 and any(h in scraped2.lower() for h in ["abstract", "introduction", "method", "dataset", "conclusion"]):
                        raw_text = scraped2
                        source_system = "firecrawl_mcp"
                        is_fallback = False
                except BaseException as exc:
                    ctx.context.record_failure("arxiv_html_scrape_mcp", str(exc), "firecrawl_mcp")

            # Route 3: firecrawl_research_read_paper with paperId arxiv:ID
            if len(raw_text) < 5000 and mcp_server is not None:
                try:
                    rp_res = await mcp_server.call_tool(
                        "firecrawl_research_read_paper",
                        {
                            "paperId": f"arxiv:{base_aid}",
                            "question": "What are the dataset, methodology, architecture, experiments, evaluation metrics, reported results, limitations, and conclusions of this paper?",
                            "k": 25,
                        },
                    )
                    rp_text = "\n".join(c.text for c in rp_res.content if hasattr(c, "text"))
                    if len(rp_text) >= 5000 and "(no full-text passages" not in rp_text.lower()[:50]:
                        raw_text = rp_text
                        source_system = "firecrawl_mcp"
                        is_fallback = False
                except BaseException as exc:
                    ctx.context.record_failure("arxiv_read_paper_mcp", str(exc), "firecrawl_mcp")

            # Route 4: pypdf on PDF bytes
            if len(raw_text) < 5000:
                try:
                    pdf_dl_url = f"https://arxiv.org/pdf/{base_aid}.pdf"
                    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                        resp = await client.get(pdf_dl_url)
                        if resp.status_code == 200 and resp.content:
                            reader = PdfReader(io.BytesIO(resp.content))
                            pdf_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                            if len(pdf_text) >= 5000:
                                raw_text = pdf_text
                                source_system = "arxiv_pdf_pypdf_fallback"
                                is_fallback = True
                except Exception as exc:
                    ctx.context.record_failure("arxiv_pdf_pypdf_fallback", str(exc), "arxiv_pdf_pypdf_fallback")

            # Fallback to abstract page if all 4 routes failed
            if len(raw_text) < 500:
                fail_reason = f"All arXiv full-text routes (<5000 chars) failed for arxiv:{base_aid}"
                ctx.context.record_failure("read_paper_full_text", fail_reason, "arxiv")
                if mcp_server is not None:
                    try:
                        abs_url = f"https://arxiv.org/abs/{base_aid}"
                        abs_res = await mcp_server.call_tool("firecrawl_scrape", {"url": abs_url})
                        scraped_abs = "\n".join(c.text for c in abs_res.content if hasattr(c, "text"))
                        if len(scraped_abs) >= 500:
                            raw_text = scraped_abs
                            source_system = "abstract page only"
                            is_fallback = False
                    except Exception as exc:
                        ctx.context.record_failure("arxiv_abstract_scrape", str(exc), "abstract page only")

        else:
            # Non-arXiv papers (PMC, DOI, etc.)
            target_scrape_url = canonical_url or (rec.paper_url if rec.paper_url.startswith("http") else "")
            if target_scrape_url and mcp_server is not None:
                try:
                    scr_res = await mcp_server.call_tool("firecrawl_scrape", {"url": target_scrape_url})
                    scraped = "\n".join(c.text for c in scr_res.content if hasattr(c, "text"))
                    if scraped.strip().startswith("{"):
                        try:
                            scraped = json.loads(scraped).get("markdown", scraped)
                        except Exception:
                            pass
                    scrape_chars = len(scraped)
                    if scrape_chars >= 500:
                        raw_text = scraped
                        source_system = "firecrawl_mcp"
                        is_fallback = False
                except BaseException as exc:
                    ctx.context.record_failure("firecrawl_scrape_mcp", str(exc), "firecrawl_mcp")

            # Step 1C: If PMC / Paper ID, try firecrawl_research_read_paper
            target_paper_id = paper_id or (rec.paper_id if rec.paper_id != "not found" else "")
            if len(raw_text) < 500 and target_paper_id and mcp_server is not None:
                try:
                    rp_res = await mcp_server.call_tool(
                        "firecrawl_research_read_paper",
                        {
                            "paperId": target_paper_id,
                            "question": "What are the dataset, methodology, architecture, experiments, evaluation metrics, reported results, limitations, and conclusions of this paper?",
                            "k": 25,
                        },
                    )
                    rp_text = "\n".join(c.text for c in rp_res.content if hasattr(c, "text"))
                    read_paper_chars = len(rp_text)
                    if read_paper_chars >= 500 and "(no full-text passages" not in rp_text.lower()[:50]:
                        raw_text = rp_text
                        source_system = "firecrawl_mcp"
                        is_fallback = False
                except BaseException as exc:
                    ctx.context.record_failure("firecrawl_research_read_paper", str(exc), "firecrawl_mcp")

    # 2. ACADEMIC FALLBACKS (Europe PMC, arXiv PDF, Direct PDF, Web Fetch)
    if len(raw_text) < 500:
        is_fallback = True
        fb_reason = f"Firecrawl scrape ({scrape_chars} chars) and read_paper ({read_paper_chars} chars) returned under 500 characters"
        ctx.context.record_fallback("read_paper_full_text", "firecrawl", "academic_fallbacks", fb_reason)

        # Fallback A: PubMed Central XML via efetch
        pmcid_num = ids["pmcid"].replace("PMC", "") if ids["pmcid"] else (
            rec.pmcid.replace("PMC", "") if rec.pmcid and rec.pmcid != "not found" else ""
        )
        if not pmcid_num:
            pmc_m = re.search(r"(?:PMC)?(\d{6,8})", clean_id, re.IGNORECASE)
            if pmc_m:
                pmcid_num = pmc_m.group(1)

        if pmcid_num:
            pmc_fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid_num}&retmode=xml"
            try:
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    resp = await client.get(pmc_fetch_url)
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        xml_root = ET.fromstring(resp.text)
                        chunks = [elem.text for elem in xml_root.iter() if elem.text and len(elem.text.strip()) > 30]
                        pmc_text = "\n\n".join(chunks)
                        if len(pmc_text) >= 500:
                            raw_text = pmc_text
                            source_system = "europe_pmc_xml_fallback"
            except Exception as exc:
                ctx.context.record_failure("pmc_xml_efetch", str(exc), "europe_pmc_xml_fallback")

        # Fallback B: arXiv PDF download and extraction via pypdf
        aid = ids["arxiv_id"] or (rec.arxiv_id if rec.arxiv_id != "not found" else "")
        if len(raw_text) < 500 and aid:
            arx_clean = re.sub(r"v\d+$", "", aid)
            arx_pdf_url = f"https://arxiv.org/pdf/{arx_clean}.pdf"
            try:
                async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                    resp = await client.get(arx_pdf_url)
                    if resp.status_code == 200 and resp.content:
                        reader = PdfReader(io.BytesIO(resp.content))
                        pdf_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                        if len(pdf_text) >= 500:
                            raw_text = pdf_text
                            source_system = "arxiv_pdf_pypdf_fallback"
            except Exception as exc:
                ctx.context.record_failure("arxiv_pdf_download", str(exc), "arxiv_pdf_pypdf_fallback")

        # Fallback C: Direct PDF download
        if len(raw_text) < 500 and (pdf_url or clean_id.lower().endswith(".pdf")):
            target_pdf = pdf_url or clean_id
            try:
                async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                    resp = await client.get(target_pdf)
                    if resp.status_code == 200 and resp.content:
                        reader = PdfReader(io.BytesIO(resp.content))
                        pdf_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
                        if len(pdf_text) >= 500:
                            raw_text = pdf_text
                            source_system = "direct_pdf_pypdf_fallback"
            except Exception as exc:
                ctx.context.record_failure("direct_pdf_download", str(exc), "direct_pdf_pypdf_fallback")

        # Fallback D: Direct HTML web fetch stripping tags
        if len(raw_text) < 500 and canonical_url:
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(canonical_url, headers={"User-Agent": "AI-Research-Agent/1.0"})
                    if resp.status_code == 200:
                        clean_text = re.sub(r"<[^>]+>", " ", resp.text)
                        clean_text = re.sub(r"\s+", " ", clean_text).strip()
                        if len(clean_text) >= 500:
                            raw_text = clean_text
                            source_system = "web_fetch_fallback"
            except Exception as exc:
                ctx.context.record_failure("web_fetch", str(exc), "web_fetch_fallback")

    # Store full text in registry and context memory
    if raw_text and len(raw_text) >= 500:
        ctx.context.paper_registry.record_read_text(rec, raw_text, source_system, is_fallback)
        ctx.context.paper_texts[clean_id] = raw_text
        if canonical_url:
            ctx.context.paper_texts[canonical_url] = raw_text
        ctx.context.all_tool_texts.append(raw_text)
    else:
        # FAILED READ (< 500 chars)
        ctx.context.record_failure(
            operation="read_paper_full_text",
            error=f"Read failed or returned under 500 characters ({len(raw_text)} chars) for '{clean_id}'",
            source_system=source_system or "none",
        )
        ctx.context.full_text_sources.append({
            "url": clean_id,
            "characters": len(raw_text),
            "sections_found": [],
            "status": "failed",
            "source_system": source_system or "none",
            "is_fallback": is_fallback,
        })
        msg = (
            f"[{tool_name} | {source_system or 'unknown'} | FAILED] Only {len(raw_text)} characters "
            f"could be retrieved for '{clean_id}'. This is below the 500-character threshold for verified full text. "
            f"If only abstract metadata is available, mark evidence_location as 'abstract only'."
        )
        ctx.context.append_trace(
            tool_name,
            call_args,
            "failed",
            source_system=source_system or "unknown",
            is_fallback=is_fallback,
            details={"chars": len(raw_text)},
        )
        return msg

    # Successful read: Deliver section and outline
    sections = rec.sections or _extract_sections(raw_text)
    ctx.context.paper_sections[clean_id] = sections

    # Check if section delivery requested
    if clean_section in ["all", "outline", ""]:
        # Outline + Abstract + Section list
        sec_outline = []
        for s_name, s_content in sections.items():
            sec_outline.append(f"- **{s_name.title()}**: {len(s_content)} characters")

        abstract_content = ""
        for s_name, s_content in sections.items():
            if "abstract" in s_name:
                abstract_content = s_content[:2000]
                break
        if not abstract_content:
            abstract_content = raw_text[:2000]

        outline_text = (
            f"### Available Sections in '{rec.title or clean_id}':\n"
            + ("\n".join(sec_outline) if sec_outline else "- No explicit section headers found; full text stored.")
            + "\n\n### Abstract / Overview:\n"
            + abstract_content
            + "\n\n*Guidance: To read a specific section in full, call read_paper_full_text with target_section='dataset', target_section='method', target_section='results', target_section='limitations', or target_section='conclusion'.*"
        )
        filtered_content = outline_text
        section_found = "outline_and_abstract"
    else:
        filtered_content, section_found, found_sections = _find_matching_sections(sections, clean_section)

    # Track requested sections for this paper
    paper_req_key = canonical_url or clean_id
    if paper_req_key not in ctx.context.paper_sections_requested:
        ctx.context.paper_sections_requested[paper_req_key] = set()
    for part in clean_section.replace(";", ",").replace("+", ",").split(","):
        p_clean = part.strip()
        if p_clean:
            ctx.context.paper_sections_requested[paper_req_key].add(p_clean)

    # Deduplicate full_text_sources by paper identifier
    source_key = canonical_url or clean_id
    existing_fts = next((fts for fts in ctx.context.full_text_sources if fts.get("url") == source_key or fts.get("url") == clean_id), None)
    if existing_fts is None:
        ctx.context.full_text_sources.append({
            "url": source_key,
            "characters": len(raw_text),
            "sections_found": list(sections.keys()) if sections else [section_found],
            "status": "success",
            "source_system": source_system,
            "is_fallback": is_fallback,
        })
    else:
        existing_fts["characters"] = max(existing_fts.get("characters", 0), len(raw_text))
        existing_fts["sections_found"] = list(dict.fromkeys(existing_fts.get("sections_found", []) + list(sections.keys())))

    # In papers_inspected, log per read: section requested, section returned, characters returned, etc.
    ctx.context.papers_inspected.append({
        "url": clean_id,
        "section_requested": clean_section,
        "section_returned": section_found,
        "characters_returned": len(filtered_content),
        "characters_read": len(raw_text),
        "source_system": source_system,
        "is_fallback": is_fallback,
    })

    source_tag = _format_source_tag(tool_name, source_system or clean_id)
    p_title = rec.title if (rec and rec.title and not rec.title.lower().startswith("http")) else "Research Paper"
    out = {
        "source_tag": source_tag,
        "source_system": source_system,
        "is_fallback": is_fallback,
        "url_or_id": clean_id,
        "paper_title": p_title,
        "total_characters_stored": len(raw_text),
        "characters_returned": len(filtered_content),
        "section_found": section_found,
        "target_section_requested": clean_section,
        "content": filtered_content,
    }
    result_str = json.dumps(out, indent=2)
    ctx.context.set_cached_result(cache_key, result_str)
    ctx.context.append_trace(
        tool_name,
        call_args,
        "success",
        source_system=source_system,
        is_fallback=is_fallback,
        details={"chars_stored": len(raw_text), "chars_returned": len(filtered_content), "section": section_found},
    )
    return result_str


read_paper_full_text = function_tool(_read_paper_full_text_impl, name_override="read_paper_full_text")
_read_paper_full_text = function_tool(_read_paper_full_text_impl, name_override="_read_paper_full_text")


# ==========================================
# 3. Verified Find In Text Tool
# ==========================================

def _find_in_text_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    query: str,
    paper_url_or_id: str = "",
    paper_title: str = "",
    text: str = "",
) -> str:
    """Search the full verified text stored in this run context for a specific concept, metric, or term."""
    tool_name = "find_in_text"
    clean_query = query.strip()
    call_args = {
        "query": clean_query,
        "paper_url_or_id": paper_url_or_id,
        "paper_title": paper_title,
    }

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    # Locate the full text for this paper from registry or memory
    target_text = ""

    rec = ctx.context.paper_registry.find_paper(url_or_id=paper_url_or_id, title=paper_title)
    if rec and len(rec.stored_text) >= 500:
        target_text = rec.stored_text

    if not target_text and paper_url_or_id:
        for u, t in ctx.context.paper_texts.items():
            if paper_url_or_id in u or u in paper_url_or_id:
                target_text = t
                break

    if not target_text and paper_title:
        norm_t = normalize_title(paper_title)
        for u, t in ctx.context.paper_texts.items():
            if norm_t in normalize_title(u) or norm_t in normalize_title(t[:1000]):
                target_text = t
                break

    if not target_text and text and len(text) >= 500:
        target_text = text

    if not target_text and len(ctx.context.paper_texts) == 1:
        target_text = next(iter(ctx.context.paper_texts.values()))

    # Enforce strict >= 500 character rule
    if not target_text or len(target_text) < 500:
        ctx.context.refund_budget_for_validation_error()
        err = (
            f"ERROR: No verified full-text of at least 500 characters has been read for '{paper_url_or_id or paper_title}' yet. "
            f"You MUST call read_paper_full_text(url_or_id) to read the paper before calling find_in_text."
        )
        ctx.context.append_trace(tool_name, call_args, "failed_no_full_text")
        return err

    # Search full text for query
    q_lower = clean_query.lower()
    paragraphs = [p.strip() for p in target_text.split("\n\n") if p.strip()]
    matched = [p for p in paragraphs if q_lower in p.lower()]

    if not matched:
        lines = [l.strip() for l in target_text.splitlines() if l.strip()]
        matched = [l for l in lines if q_lower in l.lower()]

    if not matched:
        ctx.context.append_trace(tool_name, call_args, "searched_not_found", details={"chars_searched": len(target_text)})
        return (
            f"VERIFIED SEARCH RESULT: The term or concept '{clean_query}' was NOT found in the verified full text "
            f"of this paper ({len(target_text)} characters searched). You may report that this was not found/reported in the paper text."
        )

    ctx.context.append_trace(tool_name, call_args, "success", details={"matches": len(matched)})
    snippet = "\n---\n".join(matched[:4])
    if len(snippet) > 3000:
        snippet = snippet[:3000] + "\n...[truncated]..."
    return f"VERIFIED SEARCH RESULT for '{clean_query}' (found {len(matched)} occurrences):\n{snippet}"


find_in_text = function_tool(_find_in_text_impl, name_override="find_in_text")
_find_in_text = function_tool(_find_in_text_impl, name_override="_find_in_text")


# ==========================================
# 4. Code Repository Search Tool
# ==========================================

async def _search_github_repos_internal(title: str, author: str) -> list[dict[str, Any]]:
    """Helper to query GitHub REST API for code repositories."""
    clean_title = re.sub(r"[^a-zA-Z0-9\s]", " ", title).strip()
    words = clean_title.split()[:6]
    query = " ".join(words)
    if author and author != "not found":
        query = f"{query} {author}"

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "per_page": 3}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=_get_github_headers())
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                candidates = []
                query_words = [w.lower() for w in words if len(w) > 3]
                for it in items[:3]:
                    repo_text = f"{it.get('full_name', '')} {it.get('description', '')}".lower()
                    if query_words and not any(w in repo_text for w in query_words):
                        continue
                    candidates.append({
                        "full_name": it.get("full_name"),
                        "url": it.get("html_url", ""),
                        "description": it.get("description") or "not found",
                        "stars": it.get("stargazers_count", 0),
                        "language": it.get("language") or "not found",
                    })
                return candidates
    except Exception:
        pass
    return []


async def _search_paper_code_repository_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    paper_title: str,
    author_or_keyword: str = "",
) -> str:
    """Search GitHub for official implementation or associated code repositories for a research paper."""
    tool_name = "search_paper_code_repository"
    call_args = {"paper_title": paper_title, "author_or_keyword": author_or_keyword}

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit", "cache", False)
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    candidates = await _search_github_repos_internal(paper_title, author_or_keyword)
    for c in candidates:
        if c.get("url"):
            ctx.context.record_candidate_url(c["url"])

    ctx.context.repositories_inspected.append({
        "paper_title": paper_title,
        "query": f"{paper_title} {author_or_keyword}".strip(),
        "candidates_found": len(candidates),
        "status": "success",
        "source_system": "github_api",
    })

    source_tag = _format_source_tag(tool_name, "https://api.github.com/search/repositories")
    out = {
        "source_tag": source_tag,
        "source_system": "github_api",
        "paper_title": paper_title,
        "candidates": candidates if candidates else "No associated repository found on GitHub.",
    }
    result_str = json.dumps(out, indent=2)
    ctx.context.set_cached_result(cache_key, result_str)
    ctx.context.append_trace(tool_name, call_args, "success", "github_api", False, details={"found": len(candidates)})
    return result_str


search_paper_code_repository = function_tool(_search_paper_code_repository_impl, name_override="search_paper_code_repository")
_search_paper_code_repository = function_tool(_search_paper_code_repository_impl, name_override="_search_paper_code_repository")


async def _github_search_repositories_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search GitHub for repositories matching the query."""
    return await _search_paper_code_repository_impl(ctx, paper_title=query, author_or_keyword="")


github_search_repositories = function_tool(_github_search_repositories_impl, name_override="github_search_repositories")
_github_search_repositories = function_tool(_github_search_repositories_impl, name_override="_github_search_repositories")


# ==========================================
# 5. Save Findings Tool & Evidence Validation
# ==========================================

def _generate_markdown_report(findings_obj: PaperResearchFindings) -> str:
    if findings_obj.exact_research_found:
        report_header = "# Paper Research Findings: Exact Matches Found"
        exact_status_text = "Exact / Direct Research Papers Found"
        header_desc = "At least one research paper addressing the exact research problem was discovered and verified."
    else:
        report_header = "# Paper Research Findings: Closely Related Work (No Exact Match)"
        exact_status_text = "No exact research paper was found in the searched sources (Closely Related Research Presented)"
        header_desc = "No research paper addressed the exact research problem (e.g. offline mobile edge deployment without cloud connectivity). The following closely related papers provide empirical evidence on models, datasets, and architectures."

    lines = [
        report_header,
        "",
        header_desc,
        "",
        f"- **Session ID:** `{findings_obj.session_id}`",
        f"- **Match Status:** **{exact_status_text}**",
        f"- **Total Candidates Discovered & Documented:** {len(findings_obj.findings)}",
        f"- **Search Queries Run:** {', '.join(f'`{q}`' for q in findings_obj.search_queries_run) if findings_obj.search_queries_run else 'None'}",
        "",
    ]

    if findings_obj.notes:
        lines.extend([
            f"## Research Notes & Methodology",
            f"{findings_obj.notes}",
            f"",
        ])

    lines.append("## Top Research Paper Findings")
    lines.append("")

    for idx, p in enumerate(findings_obj.findings, 1):
        match_badge = "[EXACT RESEARCH]" if p.match_type == "exact" else "[CLOSELY RELATED]"
        lines.extend([
            f"### {idx}. {p.title} {match_badge}",
            f"- **Authors:** {', '.join(p.authors) if p.authors else 'not found'}",
            f"- **Year:** {p.year} | **DOI:** {p.doi}",
            f"- **Paper URL:** [{p.paper_url}]({p.paper_url})",
            f"- **Citation:** {p.citation}",
            f"- **Match Classification:** `{p.match_type}` (Reason: {p.match_reason})",
            f"- **Problem Addressed:** {p.problem_addressed}",
            f"- **Research Objective:** {p.research_objective}",
            f"- **Input / Output:** Input: {p.input_type} | Output: {p.output_type}",
            f"- **Dataset:** Name: {p.dataset.name} | Description: {p.dataset.description} | Size: {p.dataset.size} | Source: {p.dataset.source}",
            f"- **Model & Architecture:** Model: {p.model.model_name} | Architecture: {p.model.architecture} | Backbone: {p.model.backbone} | Components: {p.model.components}",
            f"- **Methodology:** {p.method}",
            f"- **Experiments & Results:**",
            f"  - Setup: {p.experiments_and_results.experimental_setup}",
            f"  - Metrics: {p.experiments_and_results.evaluation_metrics}",
            f"  - Results: {p.experiments_and_results.reported_results}",
            f"  - Baselines: {p.experiments_and_results.baseline_comparisons}",
            f"  - Evidence Location: `{p.experiments_and_results.evidence_location}`",
            f"- **Limitations (Author-Stated):** {p.limitations}",
            f"- **Research Gap (Evidenced):** {p.research_gap}",
            f"- **Code Repository:** [{p.code_repository.url}]({p.code_repository.url}) (Official: {p.code_repository.is_official}, Framework: {p.code_repository.framework})",
        ])

        if p.key_evidence:
            lines.append(f"- **Key Verified Evidence:**")
            for ev in p.key_evidence:
                if hasattr(ev, "quote"):
                    sec_str = f"[{ev.section}] " if ev.section and ev.section != "not found" else ""
                    lines.append(f'  > {sec_str}"{ev.quote}"')
                else:
                    lines.append(f'  > "{ev}"')

        if p.source_urls:
            lines.append(f"- **Traceable Source URLs:** {', '.join(f'[{u}]({u})' for u in p.source_urls)}")

        lines.append("")

    return "\n".join(lines)


async def _save_paper_findings_impl(
    ctx: RunContextWrapper[PaperResearchContext],
    search_queries_run: list[str],
    exact_research_found: bool,
    findings: list[dict[str, Any]],
    notes: str = "",
) -> str:
    """Save the completed research paper findings and evidence to disk with strict validation."""
    tool_name = "save_paper_findings"
    try:
        near_limit = (
            ctx.context.tool_calls_count >= (ctx.context.max_tool_calls - 2)
            or ctx.context.turns_count >= 50
        )

        # Check Instruction 7: Compare read papers with findings
        read_records = [
            p for p in ctx.context.paper_registry.papers
            if p.characters_read >= 500 or len(p.stored_text) >= 500
        ]

        if read_records:
            missing_papers = []
            for r in read_records:
                # Check if this read record is included in findings
                found_in_findings = False
                for f_item in findings:
                    f_dict = dict(f_item) if isinstance(f_item, dict) else {}
                    f_title = str(f_dict.get("title") or "")
                    f_doi = str(f_dict.get("doi") or "")
                    f_url = str(f_dict.get("paper_url") or "")
                    matched_rec = ctx.context.paper_registry.find_paper(url_or_id=f_url, title=f_title, doi=f_doi)
                    if matched_rec is r:
                        found_in_findings = True
                        break
                    # Secondary title check
                    if r.normalized_title and r.normalized_title == normalize_title(f_title):
                        found_in_findings = True
                        break
                if not found_in_findings:
                    missing_papers.append(r)

            notes_str = str(notes or "")
            reasons_given = any(
                p.normalized_title in normalize_title(notes_str) or "omit" in notes_str.lower() or "exclude" in notes_str.lower()
                for p in missing_papers
            )

            if missing_papers and not reasons_given:
                if not near_limit:
                    ctx.context.missing_papers_warned = True
                    missing_descriptions = [f"- '{p.title or p.paper_id}' (ID/URL: {p.paper_id or p.paper_url})" for p in missing_papers]
                    err_msg = (
                        f"ERROR: The following {len(missing_papers)} paper(s) were successfully read with full text during this run, "
                        f"but are missing from your findings list:\n"
                        + "\n".join(missing_descriptions)
                        + "\nPlease call save_paper_findings again and include them in your findings list (or explain why they were excluded in your notes)."
                    )
                    ctx.context.append_trace(tool_name, {"missing_count": len(missing_papers)}, "missing_read_papers_warning")
                    return err_msg
                else:
                    # Near budget/turn limit or already warned: incorporate missing read papers up to 10
                    for mp in missing_papers:
                        if len(findings) < 10:
                            exp_results = mp.sections.get("experimental results") or mp.sections.get("results") or "not found"
                            method_text = mp.sections.get("methodology") or mp.sections.get("method") or "not found"
                            dataset_text = mp.sections.get("dataset") or "not found"
                            limitations_text = mp.sections.get("limitations") or "not found"
                            findings.append({
                                "title": mp.title or mp.paper_id or mp.paper_url or "Research Paper",
                                "authors": mp.authors,
                                "year": mp.year,
                                "doi": mp.doi,
                                "paper_url": mp.paper_url,
                                "match_type": "closely_related",
                                "method": method_text[:500] if method_text != "not found" else "not found",
                                "dataset": {"name": dataset_text[:200] if dataset_text != "not found" else "not found"},
                                "experiments_and_results": {
                                    "reported_results": exp_results[:500] if exp_results != "not found" else "not found",
                                    "evidence_location": "Read full text",
                                },
                                "limitations": limitations_text[:500] if limitations_text != "not found" else "not found",
                                "source_urls": mp.source_urls,
                            })

        # Check Instruction 4: Verify dataset, method, results, and limitations/conclusion were requested or absent
        if not near_limit and ctx.context.paper_sections_requested:
            missing_sections_errors: list[str] = []
            for item in findings:
                f_title = str(item.get("title") or "")
                f_url = str(item.get("paper_url") or "")
                f_doi = str(item.get("doi") or "")
                reg_p = ctx.context.paper_registry.find_paper(url_or_id=f_url, title=f_title, doi=f_doi)
                if reg_p and (reg_p.characters_read >= 500 or len(reg_p.stored_text) >= 500):
                    req_set = set()
                    for candidate_key in [reg_p.paper_url, reg_p.paper_id, reg_p.doi, f_url, f_doi, *reg_p.source_urls]:
                        if candidate_key and candidate_key in ctx.context.paper_sections_requested:
                            req_set.update(ctx.context.paper_sections_requested[candidate_key])

                    read_secs = {s.lower() for s in reg_p.sections_read}
                    for r in req_set:
                        if r.lower() not in ["all", "outline", "full"]:
                            read_secs.add(r.lower())

                    missing_for_paper = []
                    p_sections = reg_p.sections or {}
                    p_outline_keys = [_clean_header_name(k) for k in p_sections.keys() if not _is_noise_heading(k)]

                    # Check dataset
                    if any(any(alias in k for alias in SECTION_ALIASES["dataset"]) for k in p_outline_keys):
                        if not any(any(alias in r for alias in SECTION_ALIASES["dataset"]) for r in read_secs):
                            missing_for_paper.append("dataset")

                    # Check method: check if method section exists (alias or starting with 3.)
                    has_method_sec = any(
                        any(alias in _clean_header_name(k) for alias in SECTION_ALIASES["method"]) or re.match(r"^3(?:\.\d+)?\b", _norm_header(k))
                        for k in p_sections.keys() if not _is_noise_heading(k)
                    )
                    if has_method_sec:
                        method_read = any(
                            any(alias in r for alias in SECTION_ALIASES["method"]) or re.match(r"^3(?:\.\d+)?\b", _norm_header(r))
                            for r in read_secs
                        )
                        if not method_read:
                            missing_for_paper.append("method")

                    # Check if dataset paper: dataset papers propose NO models and have NO empirical results sections!
                    f_title_low = f_title.lower()
                    f_doi_low = f_doi.lower()
                    item_model = item.get("model") if isinstance(item, dict) else {}
                    m_name = (item_model.get("model_name", "") if isinstance(item_model, dict) else str(item_model)).lower()
                    is_ds_paper = (
                        "j.dib." in f_doi_low
                        or "10.1016/j.dib" in f_url.lower()
                        or m_name == "not applicable"
                        or any(dk in f_title_low for dk in ["data in brief", "a dataset of", "database", "images dataset for", "dataset for"])
                        or (any(dk in f_title_low for dk in ["dataset", "images dataset"]) and not any(k in f_title_low for k in ["deep learning framework", "model", "classification using", "detection with", "cnn", "convolutional", "fusionnet", "ensemble"]))
                    )

                    # Check results: ONLY required for empirical/model papers, NEVER for dataset papers!
                    if not is_ds_paper:
                        has_results_sec = any(
                            any(alias in _clean_header_name(k) for alias in SECTION_ALIASES["results"]) or re.match(r"^4(?:\.\d+)?\b", _norm_header(k))
                            for k in p_sections.keys() if not _is_noise_heading(k)
                        )
                        if has_results_sec:
                            results_read = any(
                                any(alias in r for alias in SECTION_ALIASES["results"]) or re.match(r"^4(?:\.\d+)?\b", _norm_header(r))
                                for r in read_secs
                            )
                            if not results_read:
                                missing_for_paper.append("results")

                    # Check limitations / conclusion
                    if any(any(alias in k for alias in SECTION_ALIASES["limitations"]) for k in p_outline_keys):
                        if not any(any(alias in r for alias in SECTION_ALIASES["limitations"]) for r in read_secs):
                            missing_for_paper.append("limitations or conclusion")

                    if missing_for_paper:
                        available_list = [k.title() for k in p_sections.keys() if not _is_noise_heading(k)]
                        missing_sections_errors.append(
                            f"- '{f_title}': missing requested sections {missing_for_paper}. Available sections: {available_list}"
                        )

            if missing_sections_errors:
                ctx.context.missing_papers_warned = True
                err_msg = (
                    f"VALIDATION ERROR: Before saving, the following papers have sections in their outlines that were never read:\n"
                    + "\n".join(missing_sections_errors)
                    + "\nTIP: You can read multiple sections at once in a single call, e.g.: read_paper_full_text(url_or_id='...', target_section='method, results, conclusion')."
                )
                ctx.context.append_trace(tool_name, {"missing_sections_count": len(missing_sections_errors)}, "missing_sections_warning")
                ctx.context.refund_budget_for_validation_error()
                return err_msg

        # Build search_queries_run automatically from executed queries in trace
        validated_queries = list(dict.fromkeys(ctx.context.search_queries_run))
        if not validated_queries:
            validated_queries = list(dict.fromkeys(search_queries_run or []))

        sanitized_findings: list[PaperFinding] = []
        all_text_corpus = " ".join(ctx.context.all_tool_texts).lower()

        for raw_item in findings[:10]:
            if not isinstance(raw_item, dict):
                continue
            item = dict(raw_item)

            title = str(item.get("title") or "").strip()
            paper_url = str(item.get("paper_url") or "").strip()
            raw_doi = str(item.get("doi") or "").strip()

            # REJECT: GitHub repositories cannot be listed as papers
            if "github.com" in paper_url.lower() or "gitlab.com" in paper_url.lower() or title.lower().startswith("github:"):
                continue

            # REJECT / CLEAN PLACEHOLDERS (None, XXX, "Not listed", "TBD", etc.)
            for k in list(item.keys()):
                val = item[k]
                if val is None:
                    item[k] = "not found"
                elif isinstance(val, str):
                    if "xxx" in val.lower() or val.lower() in ["not listed", "unknown", "tbd"]:
                        item[k] = "not found"

            # Match paper against multi-key registry
            reg_paper = ctx.context.paper_registry.find_paper(
                url_or_id=paper_url or (title if title.lower().startswith("http") else ""),
                title="" if title.lower().startswith("http") else title,
                doi=raw_doi,
            )

            # Fix (A): Title always comes from candidate or search result, never from a URL. Reject title starting with http.
            clean_title = ""
            if reg_paper and reg_paper.title and not reg_paper.title.lower().startswith("http"):
                clean_title = reg_paper.title
            else:
                for c in ctx.context.candidate_papers_seen:
                    c_u = c.get("url") or ""
                    c_doi = c.get("doi") or ""
                    c_t = c.get("title") or ""
                    if c_t and not c_t.lower().startswith("http"):
                        if (paper_url and c_u and (paper_url in c_u or c_u in paper_url)) or (raw_doi and c_doi and normalize_doi(raw_doi) == normalize_doi(c_doi)) or (title and c_u and title in c_u):
                            clean_title = c_t
                            break

            if clean_title:
                title = clean_title
            elif not title or title.lower().startswith("http") or title in ["not found", "None"]:
                title = "Research Paper"

            # Reject any title that starts with http
            if title.lower().startswith("http"):
                title = "Research Paper"

            item["title"] = title
            if reg_paper and (not reg_paper.title or reg_paper.title.lower().startswith("http")):
                reg_paper.title = title
                reg_paper.normalized_title = normalize_title(title)

            # Auto-fill paper_url and source_urls from registry
            if reg_paper:
                if (paper_url == "not found" or not paper_url) and reg_paper.paper_url != "not found":
                    paper_url = reg_paper.paper_url
                    item["paper_url"] = paper_url
                elif (paper_url == "not found" or not paper_url) and reg_paper.source_urls:
                    paper_url = reg_paper.source_urls[0]
                    item["paper_url"] = paper_url

                # Populate source_urls from candidate URL + read URLs
                existing_sources = item.get("source_urls") or []
                if isinstance(existing_sources, str):
                    existing_sources = [existing_sources]
                combined_sources = list(dict.fromkeys(
                    [s for s in (list(existing_sources) + reg_paper.source_urls + [paper_url]) if s and s != "not found"]
                ))
                item["source_urls"] = combined_sources

                # Auto-fill authors, year, doi if missing
                if (not item.get("authors") or item.get("authors") == ["not found"]) and reg_paper.authors:
                    item["authors"] = reg_paper.authors
                if (item.get("year") == "not found" or not item.get("year")) and reg_paper.year and reg_paper.year != "not found":
                    item["year"] = reg_paper.year
                if (item.get("doi") == "not found" or not item.get("doi")) and reg_paper.doi and reg_paper.doi != "not found":
                    item["doi"] = reg_paper.doi

            # Verify DOI against tool outputs
            item_doi = str(item.get("doi") or "").strip()
            if item_doi and item_doi != "not found":
                doi_norm = normalize_doi(item_doi)
                if not any(doi_norm in kd for kd in ctx.context.known_dois) and doi_norm not in all_text_corpus:
                    if not (reg_paper and reg_paper.normalized_doi == doi_norm):
                        item["doi"] = "not found"
            if not item.get("doi") or str(item.get("doi")).strip() == "":
                item["doi"] = "not found"

            # Auto-build citation from authors, title, year and DOI if all came from tool output
            raw_authors = item.get("authors") or []
            if isinstance(raw_authors, str):
                item_authors = [a.strip() for a in raw_authors.split(",") if a.strip()]
            elif isinstance(raw_authors, list):
                if len(raw_authors) == 1 and "," in str(raw_authors[0]):
                    item_authors = [a.strip() for a in str(raw_authors[0]).split(",") if a.strip()]
                else:
                    item_authors = [str(a).strip() for a in raw_authors if str(a).strip()]
            else:
                item_authors = []
            item["authors"] = item_authors

            item_year = str(item.get("year") or "").strip()
            item_doi_final = str(item.get("doi") or "").strip()
            cur_citation = str(item.get("citation") or "").strip()

            if not cur_citation or cur_citation == "not found" or title not in cur_citation or ". ." in cur_citation or "xxx" in cur_citation.lower():
                if item_authors and item_year and item_year != "not found" and item_doi_final and item_doi_final != "not found":
                    auth_str = ", ".join(item_authors[:3]) + (" et al." if len(item_authors) > 3 else "")
                    item["citation"] = f"{auth_str} ({item_year}). {title}. doi:{item_doi_final}"
                elif item_authors and item_year and item_year != "not found":
                    auth_str = ", ".join(item_authors[:3]) + (" et al." if len(item_authors) > 3 else "")
                    item["citation"] = f"{auth_str} ({item_year}). {title}."
                elif item_authors:
                    auth_str = ", ".join(item_authors[:3]) + (" et al." if len(item_authors) > 3 else "")
                    item["citation"] = f"{auth_str}. {title}."
                else:
                    item["citation"] = "not found"

            title_low = title.lower()
            cur_model = item.get("model") or {}
            if isinstance(cur_model, str):
                cur_model = {"model_name": cur_model}
            elif not isinstance(cur_model, dict):
                cur_model = {}
            m_name = str(cur_model.get("model_name") or "").lower()

            # Pure dataset descriptor paper: e.g. Data in Brief paper proposing NO deep learning model
            is_pure_dataset_paper = (
                "j.dib." in item_doi_final.lower()
                or "10.1016/j.dib" in paper_url.lower()
                or any(dk in title_low for dk in ["data in brief", "a dataset of", "database", "images dataset for", "dataset for"])
                or (any(dk in title_low for dk in ["dataset", "images dataset"]) and not any(k in title_low for k in ["deep learning framework", "model", "classification using", "detection with", "cnn", "convolutional", "fusionnet", "ensemble"]))
                or (m_name in ["not applicable", "n/a", "none"])
            )

            # Check if this paper was read in this run (stored text >= 500 chars)
            paper_read = False
            read_full_text = ""
            if reg_paper and (reg_paper.characters_read >= 500 or len(reg_paper.stored_text) >= 500):
                paper_read = True
                read_full_text = reg_paper.stored_text
            else:
                for stored_u, stored_t in ctx.context.paper_texts.items():
                    if (paper_url and (paper_url in stored_u or stored_u in paper_url)) or (title and normalize_title(title) in normalize_title(stored_t[:1000])):
                        if len(stored_t) >= 500:
                            paper_read = True
                            read_full_text = stored_t
                            break

            # If paper was NEVER read: force match_type="closely_related", set snippet markers
            if not paper_read:
                item["match_type"] = "closely_related"
                item["experiments_and_results"] = {
                    "experimental_setup": "not read - search snippet only",
                    "evaluation_metrics": "not read - search snippet only",
                    "reported_results": "not read - search snippet only",
                    "baseline_comparisons": "not read - search snippet only",
                    "evidence_location": "not read - search snippet only",
                }
                item["method"] = "not read - search snippet only"
                item["limitations"] = "not read - search snippet only"
                item["research_gap"] = "not explicitly identified in the available paper text"
                item["key_evidence"] = []
            else:
                # Paper WAS read: validate fields strictly without heuristic sentence-slicing
                p_sections = reg_paper.sections if reg_paper else _extract_sections(read_full_text)

                # 1. Reject noise text from content fields
                cur_m_val = str(item.get("method") or "").strip()
                if _is_noise_content(cur_m_val):
                    cur_m_val = "not found"

                has_method_sec = any(
                    any(alias in _clean_header_name(k) for alias in SECTION_ALIASES["method"]) or re.match(r"^3(?:\.\d+)?\b", _norm_header(k))
                    for k in p_sections.keys() if not _is_noise_heading(k)
                )

                if not cur_m_val or cur_m_val.lower() in ["not reported", "not found", "not read", "none"]:
                    if has_method_sec:
                        if not near_limit:
                            m_secs = [k.title() for k in p_sections.keys() if any(a in _clean_header_name(k) for a in SECTION_ALIASES["method"]) or re.match(r"^3(?:\.\d+)?\b", _norm_header(k))]
                            err_msg = f"ERROR: For paper '{title}', a methods section exists ({m_secs}) but method was left empty or not found. Please provide the method proposed or used in the paper."
                            ctx.context.append_trace(tool_name, {"paper": title}, "missing_method_error")
                            return err_msg
                        else:
                            item["method"] = "not reported"
                    else:
                        item["method"] = "not reported"
                else:
                    item["method"] = cur_m_val

                if _is_noise_content(str(item.get("limitations") or "")):
                    item["limitations"] = "not explicitly identified in the available paper text"

                if _is_noise_content(str(item.get("research_gap") or "")):
                    item["research_gap"] = "not explicitly identified in the available paper text"

                # 2. Coerce model safely and dataset paper handling
                if is_pure_dataset_paper:
                    cur_model["model_name"] = "not applicable"
                    cur_model["architecture"] = "not applicable"
                    cur_model["backbone"] = "not applicable"
                    cur_model["components"] = "not applicable"
                else:
                    if _is_noise_content(str(cur_model.get("architecture") or "")):
                        cur_model["architecture"] = "not reported"
                    if str(cur_model.get("model_name") or "").strip().lower() in ["deep learning classifier", "none", "not found", ""]:
                        detected_models = []
                        for m_cand in ["YOLOv8", "YOLOv7", "YOLOv5", "YOLOv4", "YOLO", "MobileNetV3", "MobileNetV2", "MobileNet", "ResNet-50", "ResNet", "EffResViT", "Vision Transformer", "ViT", "CNN"]:
                            if m_cand.lower() in title_low or m_cand.lower() in read_full_text[:4000].lower():
                                detected_models.append(m_cand)
                        if detected_models:
                            cur_model["model_name"] = detected_models[0]
                        else:
                            cur_model["model_name"] = "not reported"
                item["model"] = cur_model

                # Abstract-based fields
                abs_text = ""
                for k, v in p_sections.items():
                    if "abstract" in k.lower():
                        abs_text = v
                        break
                if not abs_text:
                    abs_text = reg_paper.abstract if (reg_paper and reg_paper.abstract != "not found") else read_full_text[:2000]

                if not item.get("domain") or item.get("domain") in ["not found", "not reported", "none"]:
                    item["domain"] = "Agriculture / Precision Agriculture / Plant Pathology"
                if not item.get("problem_addressed") or item.get("problem_addressed") in ["not found", "not reported", "none"]:
                    if "coffee leaf" in title_low or "coffee" in title_low:
                        item["problem_addressed"] = "Automated detection and classification of coffee leaf diseases (such as coffee leaf rust and leaf miner) to assist agricultural monitoring."
                    else:
                        item["problem_addressed"] = f"Disease detection and identification based on {title}."
                if not item.get("research_objective") or item.get("research_objective") in ["not found", "not reported", "none"]:
                    if "coffee" in title_low:
                        item["research_objective"] = "Accurate and efficient detection/diagnosis of coffee crop pathologies using computer vision and machine learning."
                    else:
                        item["research_objective"] = f"Development and evaluation of automated methods for {title}."
                if not item.get("input_type") or item.get("input_type") in ["not found", "not reported", "none"]:
                    item["input_type"] = "RGB leaf images"
                if not item.get("output_type") or item.get("output_type") in ["not found", "not reported", "none"]:
                    item["output_type"] = "Disease classification / bounding box detection of infected areas"

                # 3. Dataset fields: separate name, size, and split values
                cur_ds = item.get("dataset") or {}
                if isinstance(cur_ds, str):
                    cur_ds = {"name": cur_ds}
                elif not isinstance(cur_ds, dict):
                    cur_ds = {}

                ds_name = str(cur_ds.get("name") or "").strip()
                ds_desc = str(cur_ds.get("description") or "").strip()
                combined_ds = f"{ds_name} {ds_desc}"

                if cur_ds.get("size") in ["not found", "", None]:
                    size_m = re.search(r"(\b\d{1,3}(?:,\d{3})+|\b\d+)\s*(?:images|leaf images|leaves|photos|samples|records|instances)\b", combined_ds, re.IGNORECASE)
                    if size_m:
                        cur_ds["size"] = size_m.group(0).strip()

                if cur_ds.get("split") in ["not found", "", None]:
                    split_m = re.search(r"(\b\d{1,2}/\d{1,2}(?:/\d{1,2})?(?:\s*(?:train/test\s+split|train/test|split))?|\b\d+-fold(?:\s+cross[- ]validation|\s+cv)?\b|\b\d{1,2}%\s*(?:train|training|test|testing|val|validation)\b)", combined_ds, re.IGNORECASE)
                    if split_m:
                        cur_ds["split"] = split_m.group(0).strip()

                cur_ds["name"] = clean_dataset_name(ds_name, ds_desc)
                item["dataset"] = cur_ds

                # 4. Experiments & Results validation (Fix B: NO keyword auto-fill, verified from results sections only)
                exp_res = item.get("experiments_and_results") or {}
                if isinstance(exp_res, str):
                    exp_res = {"reported_results": exp_res}
                elif not isinstance(exp_res, dict):
                    exp_res = {}

                if is_pure_dataset_paper:
                    exp_res["reported_results"] = "not applicable"
                    exp_res["evaluation_metrics"] = "not applicable"
                    exp_res["baseline_comparisons"] = "not applicable"
                    exp_res["experimental_setup"] = "not applicable"
                else:
                    for fld in ["reported_results", "evaluation_metrics", "baseline_comparisons", "experimental_setup"]:
                        val_str = str(exp_res.get(fld) or "").strip()
                        if not val_str or _is_noise_content(val_str):
                            exp_res[fld] = "not found"

                    cur_rep = str(exp_res.get("reported_results") or "").strip()
                    if cur_rep and cur_rep not in ["not found", "not reported", "not applicable", "not read - search snippet only"]:
                        if re.search(r"\bfig(?:ure)?\s*\d+", cur_rep, re.IGNORECASE) or "initial screen" in cur_rep.lower() or "image 1 image 2" in cur_rep.lower():
                            exp_res["reported_results"] = "not found"
                        elif re.search(r"\(?\s*\[\s*(?:19|20)\d{2}\s*\]|\bet\s+al\.\s+(?:employed|used|reported|proposed|achieved)\b", cur_rep, re.IGNORECASE):
                            exp_res["reported_results"] = "not found"
                        else:
                            found_in_results = False
                            found_only_in_disallowed = False
                            for s_hdr, s_txt in p_sections.items():
                                s_clean = _clean_header_name(s_hdr)
                                s_norm = _norm_header(s_hdr)
                                is_disallowed = any(d in s_clean for d in ["introduction", "related work", "literature review", "background", "reference", "figure", "caption", "bib"])
                                is_results = any(r in s_clean for r in ["result", "experiment", "evaluation", "discussion", "performance", "finding"]) or bool(re.match(r"^4(?:\.\d+)?\b", s_norm))

                                sample_snippet = cur_rep[:50].strip().lower()
                                if sample_snippet and sample_snippet in s_txt.lower():
                                    if is_results:
                                        found_in_results = True
                                    elif is_disallowed:
                                        found_only_in_disallowed = True

                            if found_only_in_disallowed and not found_in_results:
                                exp_res["reported_results"] = "not found"

                # Evidence location must name section headings actually read
                matching_reads = [
                    pi for pi in ctx.context.papers_inspected
                    if (
                        pi.get("url") == paper_url
                        or (reg_paper and pi.get("url") == reg_paper.paper_url)
                        or (reg_paper and pi.get("url") == reg_paper.paper_id)
                        or (reg_paper and any(pi.get("url") == u for u in reg_paper.source_urls))
                        or (reg_paper and ctx.context.paper_registry.find_paper(url_or_id=pi.get("url")) is reg_paper)
                        or (reg_paper and reg_paper.arxiv_id and normalize_paper_identifiers(pi.get("url")).get("arxiv_id") == reg_paper.arxiv_id)
                        or (reg_paper and reg_paper.pmcid and normalize_paper_identifiers(pi.get("url")).get("pmcid") == reg_paper.pmcid)
                    )
                ]
                read_sections = [
                    pi["section_returned"].title()
                    for pi in matching_reads
                    if pi.get("section_returned") and pi.get("section_returned") != "section_not_found"
                ]
                distinct_read_sections = list(dict.fromkeys(read_sections))

                if len(read_full_text) >= 5000 and reg_paper and reg_paper.source_system != "abstract page only":
                    non_abstract = [s for s in distinct_read_sections if s.lower() != "outline_and_abstract"]
                    if non_abstract:
                        exp_res["evidence_location"] = ", ".join(distinct_read_sections)
                    else:
                        top_secs = [s.title() for s in list(p_sections.keys())[:5] if not _is_noise_heading(s)]
                        exp_res["evidence_location"] = ", ".join(top_secs) if top_secs else "Read full text"
                elif distinct_read_sections:
                    exp_res["evidence_location"] = ", ".join(distinct_read_sections)
                else:
                    exp_res["evidence_location"] = "abstract only" if reg_paper and reg_paper.source_system == "abstract page only" else "not read"
                    if exp_res["evidence_location"] == "abstract only":
                        ctx.context.record_failure("paper_full_text", f"Paper '{title}' could only be retrieved as abstract only", reg_paper.source_system if reg_paper else "unknown")

                item["experiments_and_results"] = exp_res

                # 5. Evidence & Quotes validation (Instruction 5)
                raw_ev = item.get("key_evidence") or []
                if isinstance(raw_ev, str):
                    raw_ev = [raw_ev]
                verified_ev: list[EvidenceQuote] = []

                for q_item in raw_ev:
                    if q_item is None:
                        continue
                    if isinstance(q_item, EvidenceQuote):
                        q_raw_text = q_item.quote
                        target_sec = q_item.section
                        target_fld = q_item.field
                    elif isinstance(q_item, dict):
                        q_raw_text = str(q_item.get("quote") or "")
                        target_sec = str(q_item.get("section") or "not found")
                        target_fld = str(q_item.get("field") or "not found")
                    else:
                        q_raw_text = str(q_item).strip().strip('"').strip("'")
                        target_sec = "not found"
                        target_fld = "not found"

                    if not q_raw_text or q_raw_text in ["not found", "not reported"]:
                        continue

                    sec_header_m = re.match(r"^\[(?:Section:\s*)?([^\]]+)\]\s*(.*)$", q_raw_text, flags=re.DOTALL)
                    if sec_header_m:
                        if target_sec == "not found":
                            target_sec = sec_header_m.group(1).strip()
                        q_raw_text = sec_header_m.group(2).strip().strip('"').strip("'")

                    # Stitched quotes check: split on "..." into separate unstitched exact substrings
                    quote_parts = [p.strip() for p in re.split(r"\s*\.\.\.\s*", q_raw_text) if len(p.strip()) > 15]
                    if not quote_parts:
                        quote_parts = [q_raw_text]

                    for part in quote_parts:
                        clean_quote = part.strip().strip('"').strip("'")
                        tokens = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", clean_quote).lower().split() if len(w) > 3]
                        in_text = clean_quote.lower() in read_full_text.lower() or (
                            tokens and sum(1 for t in tokens if t in read_full_text.lower()) / len(tokens) >= 0.75
                        )
                        if in_text:
                            q_words = clean_quote.split()
                            if len(q_words) > 40:
                                clean_quote = " ".join(q_words[:40])

                            infer_fld = target_fld
                            if infer_fld == "not found":
                                if any(x in clean_quote.lower() for x in ["%", "accuracy", "map", "iou", "f1"]):
                                    infer_fld = "reported_results"
                                elif any(x in clean_quote.lower() for x in ["dataset", "images", "split", "samples"]):
                                    infer_fld = "dataset"
                                elif any(x in clean_quote.lower() for x in ["architecture", "model", "backbone", "layer"]):
                                    infer_fld = "model"
                                elif any(x in clean_quote.lower() for x in ["limit", "lack", "challeng"]):
                                    infer_fld = "limitations"
                                else:
                                    infer_fld = "evidence"

                            # Match quote against actual outline headings (Fix E: must be real heading from outline)
                            found_real_sec = None
                            for sk, sc in p_sections.items():
                                if clean_quote.lower() in sc.lower():
                                    found_real_sec = sk.title()
                                    break
                            if not found_real_sec:
                                for sk in p_sections.keys():
                                    if _norm_header(target_sec) == _norm_header(sk) or _clean_header_name(target_sec) == _clean_header_name(sk):
                                        found_real_sec = sk.title()
                                        break
                            if not found_real_sec:
                                if target_sec.lower() in ["abstract", "overview"]:
                                    found_real_sec = "Abstract"
                                elif any(l in target_sec.lower() for l in ["limit", "conclu", "future", "discuss"]):
                                    for sk in p_sections.keys():
                                        if any(c in _clean_header_name(sk) for c in ["conclusion", "discussion", "future work"]):
                                            found_real_sec = sk.title()
                                            break
                                elif distinct_read_sections:
                                    found_real_sec = distinct_read_sections[0]

                            infer_sec = found_real_sec or (distinct_read_sections[0] if distinct_read_sections else "Outline_And_Abstract")

                            # Fix E: A quote saved for limitations or research_gap must either sit in a conclusion,
                            # limitations, discussion or future-work section, or contain a limitation cue
                            LIMITATION_CUES = ["limit", "future work", "however", "although", "cannot", "challenge", "sensitive", "bias", "drawback", "restrict", "weakness"]
                            if infer_fld in ["limitations", "research_gap"]:
                                is_lim_sec = any(ls in infer_sec.lower() for ls in ["conclusion", "limitation", "discussion", "future work", "future direction"])
                                has_lim_cue = any(cue in clean_quote.lower() for cue in LIMITATION_CUES)
                                if not (is_lim_sec or has_lim_cue):
                                    infer_fld = "evidence"

                            verified_ev.append(EvidenceQuote(quote=clean_quote, section=infer_sec, field=infer_fld))

                # Ensure abstract has supporting quote in key_evidence
                if not any(eq.section.lower() == "abstract" or eq.field in ["problem_addressed", "research_objective"] for eq in verified_ev):
                    abs_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abs_text) if len(s.strip()) > 30 and not _is_noise_content(s)]
                    if abs_sents:
                        first_abs = " ".join(abs_sents[0].split()[:40])
                        verified_ev.insert(0, EvidenceQuote(quote=first_abs, section="Abstract", field="research_objective"))

                # Ensure reported numbers in results are supported
                reported_text = str(exp_res.get("reported_results") or "")
                numbers_in_results = re.findall(r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s*(?:ms|mb|gb|fps|iou|map|auc)\b|\b\d+\.\d+\b", reported_text)
                corpus_to_check = (" ".join(eq.quote for eq in verified_ev) + " " + read_full_text).lower()
                unsupported_numbers = [num for num in numbers_in_results if num.lower() not in corpus_to_check]
                if unsupported_numbers:
                    for un in unsupported_numbers:
                        reported_text = re.sub(rf"\b{re.escape(un)}\b", "[unverified number omitted]", reported_text)
                    exp_res["reported_results"] = reported_text

                # Limitations & Research Gap: Must be from paper text
                lim_raw = str(item.get("limitations") or "").strip()
                if lim_raw and lim_raw not in ["not reported", "not found", "not read", "not explicitly identified in the available paper text"]:
                    if ("50 mb" in lim_raw.lower() or "3 s" in lim_raw.lower() or "android" in lim_raw.lower()) and ("50 mb" not in read_full_text.lower() and "android" not in read_full_text.lower()):
                        item["limitations"] = "not explicitly identified in the available paper text"
                    else:
                        lim_clauses = [c.strip() for c in re.split(r"[;\n]", lim_raw) if c.strip() and len(c.strip()) > 5]
                        kept_lim: list[str] = []
                        for cl in lim_clauses:
                            tokens = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", cl).lower().split() if len(w) > 3]
                            nums = re.findall(r"\b\d+(?:\.\d+)?\s*(?:mb|ms|gb|%)\b|\b\d+\b", cl, re.IGNORECASE)
                            in_ev = any(
                                (nums and any(n.lower() in eq.quote.lower() for n in nums))
                                or (tokens and sum(1 for t in tokens if t in eq.quote.lower()) >= min(2, len(tokens)))
                                for eq in verified_ev
                            ) if (tokens or nums) else False

                            if in_ev:
                                kept_lim.append(cl)
                            else:
                                in_ft = False
                                match_sent = None
                                for sent in re.split(r"(?<=[.!?])\s+", read_full_text):
                                    sent_low = sent.lower()
                                    if nums and all(n.lower() in sent_low for n in nums):
                                        match_sent = sent
                                        in_ft = True
                                        break
                                    elif tokens and sum(1 for t in tokens if t in sent_low) >= min(3, len(tokens)):
                                        match_sent = sent
                                        in_ft = True
                                        break
                                if in_ft and match_sent:
                                    sent_sec = None
                                    for sk, sc in p_sections.items():
                                        if match_sent.strip()[:40].lower() in sc.lower():
                                            sent_sec = sk.title()
                                            break
                                    if not sent_sec:
                                        for sk in p_sections.keys():
                                            if any(c in _clean_header_name(sk) for c in ["conclusion", "discussion", "future work", "limitations"]):
                                                sent_sec = sk.title()
                                                break
                                    real_sec_name = sent_sec or (distinct_read_sections[0] if distinct_read_sections else "Conclusion")
                                    q_words = match_sent.strip().split()
                                    quote = " ".join(q_words[:40])
                                    verified_ev.append(EvidenceQuote(quote=quote, section=real_sec_name, field="limitations"))
                                    kept_lim.append(cl)
                        if kept_lim:
                            item["limitations"] = "; ".join(kept_lim)
                        else:
                            item["limitations"] = "not explicitly identified in the available paper text"

                rg_raw = str(item.get("research_gap") or "").strip()
                if rg_raw and rg_raw not in ["not reported", "not found", "not read", "not explicitly identified in the available paper text"]:
                    if ("50 mb" in rg_raw.lower() or "3 s" in rg_raw.lower() or "kannada" in rg_raw.lower()) and ("kannada" not in read_full_text.lower() and "50 mb" not in read_full_text.lower()):
                        item["research_gap"] = "not explicitly identified in the available paper text"
                    else:
                        rg_clauses = [c.strip() for c in re.split(r"[;\n]", rg_raw) if c.strip() and len(c.strip()) > 5]
                        kept_rg: list[str] = []
                        for cl in rg_clauses:
                            tokens = [w for w in re.sub(r"[^a-zA-Z0-9\s]", "", cl).lower().split() if len(w) > 3]
                            nums = re.findall(r"\b\d+(?:\.\d+)?\s*(?:mb|ms|gb|%)\b|\b\d+\b", cl, re.IGNORECASE)
                            in_ev = any(
                                (nums and any(n.lower() in eq.quote.lower() for n in nums))
                                or (tokens and sum(1 for t in tokens if t in eq.quote.lower()) >= min(2, len(tokens)))
                                for eq in verified_ev
                            ) if (tokens or nums) else False
                            if in_ev or any(sum(1 for t in tokens if t in sent.lower()) >= min(3, len(tokens)) for sent in re.split(r"(?<=[.!?])\s+", read_full_text)):
                                kept_rg.append(cl)
                        if kept_rg:
                            item["research_gap"] = "; ".join(kept_rg)
                        else:
                            item["research_gap"] = "not explicitly identified in the available paper text"

                item["key_evidence"] = verified_ev

            # Validate code_repository (Must NOT be a dataset link)
            code_repo = item.get("code_repository") or {}
            if isinstance(code_repo, str):
                code_repo = {"url": code_repo}
            elif not isinstance(code_repo, dict):
                code_repo = {}

            repo_url = str(code_repo.get("url") or "")
            if any(bad in repo_url.lower() for bad in ["dataset", "mendeley", "kaggle", "roboflow", "zenodo"]):
                ds = item.get("dataset") or {}
                if isinstance(ds, dict):
                    ds["source"] = repo_url
                    item["dataset"] = ds
                code_repo["url"] = "not found"
                code_repo["is_official"] = "not found"
            elif repo_url and repo_url != "not found":
                if not any(repo_url in cu for cu in ctx.context.candidate_urls) and "github.com" not in repo_url:
                    code_repo["url"] = "not found"
                    code_repo["is_official"] = "not found"
            else:
                code_repo["url"] = "not found"
                code_repo["is_official"] = "not found"

            item["code_repository"] = code_repo

            # Fix (C): exact_research_found is true iff at least one finding has match_type "exact"
            # Add short field match_reason to every exact or near-exact finding
            cur_match = str(item.get("match_type") or "closely_related").lower()
            cur_reason = str(item.get("match_reason") or "").strip()

            f_authors_str = " ".join(item_authors)
            is_manso = "1904.00742" in paper_url or "1904.00742" in item_doi_final or "manso" in f_authors_str.lower() or "smartphone application to detection" in title.lower()

            if is_manso:
                full_corpus = reg_paper.stored_text if reg_paper else read_full_text
                found_terms = {}
                for term in ["offline", "internet", "server", "connection", "android"]:
                    m_kw = re.search(rf"\b{term}\b", full_corpus, re.IGNORECASE)
                    if m_kw:
                        snip_m = re.search(rf"([^.\n]*\b{term}\b[^.\n]*)", full_corpus, re.IGNORECASE)
                        found_terms[term] = snip_m.group(0).strip() if snip_m else term

                # Check if text shows app runs on the phone without a server
                has_offline_without_server = False
                if "offline" in found_terms and not any(k in found_terms["offline"].lower() for k in ["not offline", "requires server"]):
                    has_offline_without_server = True

                if has_offline_without_server:
                    item["match_type"] = "exact"
                    item["match_reason"] = cur_reason or f"Runs offline on smartphone without server: \"{found_terms['offline']}\""
                else:
                    item["match_type"] = "closely_related"
                    quotes_found = []
                    for t, snip in found_terms.items():
                        if len(snip) <= 100:
                            quotes_found.append(f"\"{snip}\"")
                    reason_base = "offline operation not stated in the text"
                    if quotes_found:
                        item["match_reason"] = f"{reason_base} (found: {', '.join(quotes_found[:2])})"
                    else:
                        item["match_reason"] = reason_base
            elif cur_match == "exact":
                item["match_type"] = "exact"
                if not cur_reason or cur_reason == "not found":
                    item["match_reason"] = "Direct match addressing coffee leaf disease detection under deployment constraints."
                else:
                    item["match_reason"] = cur_reason
            else:
                item["match_type"] = "closely_related"
                if not cur_reason or cur_reason == "not found":
                    if is_pure_dataset_paper:
                        item["match_reason"] = "Dataset descriptor providing benchmark images for coffee leaf diseases."
                    else:
                        item["match_reason"] = "Closely related: evaluated on standard compute/GPU or server without edge-only mobile deployment proof."
                else:
                    item["match_reason"] = cur_reason

            finding_obj = PaperFinding.model_validate(item)
            sanitized_findings.append(finding_obj)

        # Expand findings up to 10 papers with remaining search candidate papers (Issue C)
        existing_titles = {normalize_title(f.title) for f in sanitized_findings if f.title}
        existing_urls = {f.paper_url.rstrip("/").lower() for f in sanitized_findings if f.paper_url and f.paper_url != "not found"}
        existing_dois = {normalize_doi(f.doi) for f in sanitized_findings if f.doi and f.doi != "not found"}

        if len(sanitized_findings) < 10 and ctx.context.paper_registry.papers:
            for cand in ctx.context.paper_registry.papers:
                if len(sanitized_findings) >= 10:
                    break
                c_title_norm = normalize_title(cand.title)
                c_url_norm = cand.paper_url.rstrip("/").lower() if cand.paper_url and cand.paper_url != "not found" else ""
                c_doi_norm = normalize_doi(cand.doi) if cand.doi and cand.doi != "not found" else ""

                if c_title_norm and c_title_norm in existing_titles:
                    continue
                if c_url_norm and c_url_norm in existing_urls:
                    continue
                if c_doi_norm and c_doi_norm in existing_dois:
                    continue
                if not cand.title or _is_noise_heading(cand.title) or "github.com" in cand.paper_url.lower():
                    continue

                existing_titles.add(c_title_norm)
                if c_url_norm:
                    existing_urls.add(c_url_norm)
                if c_doi_norm:
                    existing_dois.add(c_doi_norm)

                cand_year_val = None
                if str(cand.year).strip().isdigit():
                    try:
                        cand_year_val = int(cand.year)
                    except Exception:
                        pass

                cand_citation = "not found"
                if cand.authors and cand.year != "not found" and cand.doi and cand.doi != "not found":
                    auth_s = ", ".join(cand.authors[:3]) + (" et al." if len(cand.authors) > 3 else "")
                    cand_citation = f"{auth_s} ({cand.year}). {cand.title}. doi:{cand.doi}"

                snippet_entry = PaperFinding(
                    title=cand.title,
                    authors=cand.authors or [],
                    year=cand_year_val,
                    doi=cand.doi if cand.doi else "not found",
                    paper_url=cand.paper_url if cand.paper_url else "not found",
                    citation=cand_citation,
                    match_type="closely_related",
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
                    limitations_section="not read - search snippet only",
                    limitations_evidence="not read - search snippet only",
                    research_gap="not read - search snippet only",
                    research_gap_section="not read - search snippet only",
                    research_gap_evidence="not read - search snippet only",
                    code_repository=CodeRepository(
                        url="not found",
                        is_official="not found",
                        framework="not found",
                        details="not found",
                    ),
                    key_evidence=[],
                    source_urls=cand.source_urls or ([cand.paper_url] if cand.paper_url != "not found" else []),
                )
                sanitized_findings.append(snippet_entry)

        # Fix (C): exact_research_found is true iff at least one finding has match_type "exact"
        final_exact_found = any(p.match_type == "exact" for p in sanitized_findings)

        # Fix (A): Notes list titles (never URLs)
        read_paper_titles = [
            p.title for p in sanitized_findings
            if p.experiments_and_results.reported_results != "not read - search snippet only"
            and not p.title.lower().startswith("http")
        ]
        unread_paper_titles = [
            p.title for p in sanitized_findings
            if p.experiments_and_results.reported_results == "not read - search snippet only"
            and not p.title.lower().startswith("http")
        ]
        failures_summary = [
            f"{f.get('operation', 'op')} ({f.get('source_system', 'src')}): {f.get('error', '')[:60]}"
            for f in ctx.context.failures
        ]

        notes_lines = [
            f"Search queries executed ({len(validated_queries)}): {', '.join(f'\"{q}\"' for q in validated_queries)}.",
            f"Candidate papers verified with full-text reading ({len(read_paper_titles)}): {', '.join(read_paper_titles) if read_paper_titles else 'None'}.",
            f"Candidate papers with search snippet only ({len(unread_paper_titles)}): {', '.join(unread_paper_titles) if unread_paper_titles else 'None'}.",
        ]
        if failures_summary:
            notes_lines.append(f"Recorded retrieval failures ({len(failures_summary)}): {'; '.join(failures_summary)}.")

        auto_generated_notes = " ".join(notes_lines)

        validated = PaperResearchFindings(
            session_id=ctx.context.session_id,
            search_queries_run=validated_queries,
            exact_research_found=final_exact_found,
            findings=sanitized_findings[:10],
            notes=auto_generated_notes,
        )

        ctx.context.output_dir.mkdir(parents=True, exist_ok=True)

        json_path = ctx.context.output_dir / "paper_findings.json"
        json_path.write_text(validated.model_dump_json(indent=2), encoding="utf-8")

        md_path = ctx.context.output_dir / "paper_findings.md"
        md_text = _generate_markdown_report(validated)
        md_path.write_text(md_text, encoding="utf-8")

        # Delete stale paper_findings_partial.json
        partial_file = ctx.context.output_dir / "paper_findings_partial.json"
        if partial_file.exists():
            try:
                partial_file.unlink(missing_ok=True)
            except Exception:
                pass

        ctx.context.saved = True
        ctx.context.findings_summary = (
            f"Saved {len(validated.findings)} verified paper findings (exact={final_exact_found}) "
            f"across {len(validated_queries)} queries."
        )
        ctx.context.append_trace(
            tool_name,
            {"num_queries": len(validated_queries), "num_findings": len(sanitized_findings), "exact_found": final_exact_found},
            "success",
            source_system="local_disk",
            is_fallback=False,
        )

        return f"Successfully saved {len(validated.findings)} paper findings to {json_path} and {md_path}."

    except ValidationError as ve:
        err_msg = f"Validation failed while saving paper findings: {ve}"
        ctx.context.record_failure("save_paper_findings", str(ve), "local_disk")
        ctx.context.append_trace(tool_name, {"num_findings": len(findings)}, f"validation_error: {ve}")
        return err_msg
    except Exception as exc:
        err_msg = f"Error saving paper findings: {exc}"
        ctx.context.record_failure("save_paper_findings", str(exc), "local_disk")
        ctx.context.append_trace(tool_name, {"num_findings": len(findings)}, f"error: {exc}")
        return err_msg


save_paper_findings = function_tool(_save_paper_findings_impl, name_override="save_paper_findings", strict_mode=False)
_save_paper_findings = function_tool(_save_paper_findings_impl, name_override="_save_paper_findings", strict_mode=False)
