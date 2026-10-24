"""Function tools for the Existing Project Research Agent."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from agents import RunContextWrapper, function_tool
from pydantic import ValidationError

from app.config import MAX_TOOL_CALLS
from project_research.schema import Finding, ProjectResearchFindings, RepositoryDetails


@dataclass
class ProjectResearchContext:
    """Context carried through the ProjectResearcher run."""

    session_id: str
    output_dir: Path
    trace_calls: list[dict[str, Any]] = field(default_factory=list)
    saved: bool = False
    findings_summary: str = ""
    tool_calls_count: int = 0
    max_tool_calls: int = MAX_TOOL_CALLS
    cache: dict[str, str] = field(default_factory=dict)
    candidate_urls: list[str] = field(default_factory=list)
    search_queries_run: list[str] = field(default_factory=list)

    def append_trace(self, tool_name: str, arguments: dict[str, Any], status: str) -> None:
        call_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "arguments": arguments,
            "status": status,
        }
        self.trace_calls.append(call_record)
        self.flush_trace()

    def flush_trace(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            trace_path = self.output_dir / "project_research_trace.json"
            trace_path.write_text(json.dumps(self.trace_calls, indent=2), encoding="utf-8")
        except Exception:
            pass

    def check_and_increment_budget(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        """Returns budget exhaustion message if limit reached; otherwise increments counter."""
        if self.tool_calls_count >= self.max_tool_calls:
            msg = "BUDGET REACHED: call save_findings now with what you have"
            self.append_trace(tool_name, arguments, "budget_reached")
            return msg
        self.tool_calls_count += 1
        return None

    def get_cache_key(self, tool_name: str, arguments: dict[str, Any]) -> str:
        return f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"

    def get_cached_result(self, cache_key: str) -> str | None:
        return self.cache.get(cache_key)

    def set_cached_result(self, cache_key: str, result: str) -> None:
        self.cache[cache_key] = result

    def record_candidate_url(self, url: str) -> None:
        if url and url not in self.candidate_urls:
            self.candidate_urls.append(url)


def _get_github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Research-Agent/1.0",
    }
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
    return headers


def _get_hf_headers() -> dict[str, str]:
    headers = {
        "User-Agent": "AI-Research-Agent/1.0",
    }
    hf_token = os.getenv("HF_TOKEN", "").strip()
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    return headers


def _format_source_tag(tool_name: str, url: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat()
    return f"[{tool_name} | {url} | {timestamp}]"


@function_tool
async def github_search_repositories(
    ctx: RunContextWrapper[ProjectResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search repositories on GitHub.

    Returns repository full_names, URLs, descriptions, and key metrics.
    """
    tool_name = "github_search_repositories"
    limit = min(max(1, max_results), 5)
    call_args = {"query": query, "max_results": limit}

    if query and query not in ctx.context.search_queries_run:
        ctx.context.search_queries_run.append(query)

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit")
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "per_page": limit}

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=_get_github_headers())

        source_tag = _format_source_tag(tool_name, str(resp.url))

        if resp.status_code == 403:
            msg = f"{source_tag} GitHub API rate limit reached or forbidden (HTTP 403). Try again later or set GITHUB_TOKEN."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code == 429:
            msg = f"{source_tag} GitHub API rate limit reached (HTTP 429)."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code != 200:
            msg = f"{source_tag} GitHub search returned HTTP {resp.status_code}: {resp.text[:300]}"
            ctx.context.append_trace(tool_name, call_args, f"error_{resp.status_code}")
            return msg

        data = resp.json()
        items = data.get("items", [])
        results = []
        for it in items[:limit]:
            repo_url = it.get("html_url", "")
            ctx.context.record_candidate_url(repo_url)
            results.append({
                "name": it.get("full_name"),
                "url": repo_url,
                "description": it.get("description") or "not found",
                "stars": it.get("stargazers_count", 0),
                "license": (it.get("license") or {}).get("spdx_id") or "not found",
                "last_update": it.get("pushed_at") or it.get("updated_at") or "not found",
            })

        result_str = json.dumps({"source_tag": source_tag, "total_count": data.get("total_count", 0), "items": results}, indent=2)
        ctx.context.set_cached_result(cache_key, result_str)
        ctx.context.append_trace(tool_name, call_args, "success")
        return result_str

    except Exception as exc:
        msg = f"[{tool_name} | {url} | {datetime.now(timezone.utc).isoformat()}] Request failed: {exc}"
        ctx.context.append_trace(tool_name, call_args, f"failed: {exc}")
        return msg


@function_tool
async def github_get_repository(
    ctx: RunContextWrapper[ProjectResearchContext],
    full_name: str,
) -> str:
    """Get metadata for a GitHub repository.

    Returns description, stars, license, language, topics, last pushed date, and archived status.
    """
    clean_name = full_name.strip().strip("/")
    tool_name = "github_get_repository"
    call_args = {"full_name": clean_name}

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit")
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    url = f"https://api.github.com/repos/{clean_name}"

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_get_github_headers())

        source_tag = _format_source_tag(tool_name, str(resp.url))

        if resp.status_code == 403:
            msg = f"{source_tag} GitHub API rate limit reached or forbidden (HTTP 403)."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code == 429:
            msg = f"{source_tag} GitHub API rate limit reached (HTTP 429)."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code == 404:
            msg = f"{source_tag} Repository {clean_name} not found (HTTP 404)."
            ctx.context.append_trace(tool_name, call_args, "not_found")
            return msg

        if resp.status_code != 200:
            msg = f"{source_tag} GitHub repository lookup failed (HTTP {resp.status_code}): {resp.text[:300]}"
            ctx.context.append_trace(tool_name, call_args, f"error_{resp.status_code}")
            return msg

        data = resp.json()
        lic = data.get("license") or {}
        repo_url = data.get("html_url") or f"https://github.com/{clean_name}"
        ctx.context.record_candidate_url(repo_url)

        details = {
            "source_tag": source_tag,
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "url": repo_url,
            "description": data.get("description") or "not found",
            "stars": data.get("stargazers_count", "not found"),
            "license": lic.get("spdx_id") or lic.get("name") or "not found",
            "language": data.get("language") or "not found",
            "topics": data.get("topics") or [],
            "last_pushed_at": data.get("pushed_at") or data.get("updated_at") or "not found",
            "archived": data.get("archived", False),
        }

        result_str = json.dumps(details, indent=2)
        ctx.context.set_cached_result(cache_key, result_str)
        ctx.context.append_trace(tool_name, call_args, "success")
        return result_str

    except Exception as exc:
        msg = f"[{tool_name} | {url} | {datetime.now(timezone.utc).isoformat()}] Request failed: {exc}"
        ctx.context.append_trace(tool_name, call_args, f"failed: {exc}")
        return msg


@function_tool
async def github_get_readme(
    ctx: RunContextWrapper[ProjectResearchContext],
    full_name: str,
) -> str:
    """Get the README content of a GitHub repository, truncated to ~3000 characters."""
    clean_name = full_name.strip().strip("/")
    tool_name = "github_get_readme"
    call_args = {"full_name": clean_name}

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit")
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    url = f"https://api.github.com/repos/{clean_name}/readme"

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_get_github_headers())

        source_tag = _format_source_tag(tool_name, str(resp.url))

        if resp.status_code == 403:
            msg = f"{source_tag} GitHub API rate limit reached or forbidden (HTTP 403)."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code == 429:
            msg = f"{source_tag} GitHub API rate limit reached (HTTP 429)."
            ctx.context.append_trace(tool_name, call_args, "rate_limited")
            return msg

        if resp.status_code == 404:
            msg = f"{source_tag} README for {clean_name} not found (HTTP 404)."
            ctx.context.append_trace(tool_name, call_args, "not_found")
            return msg

        if resp.status_code != 200:
            msg = f"{source_tag} Failed to fetch README (HTTP {resp.status_code}): {resp.text[:300]}"
            ctx.context.append_trace(tool_name, call_args, f"error_{resp.status_code}")
            return msg

        data = resp.json()
        raw_b64 = data.get("content", "")
        encoding = data.get("encoding", "base64")

        text = ""
        if encoding == "base64" and raw_b64:
            try:
                text = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
            except Exception:
                text = raw_b64
        else:
            text = raw_b64

        truncated = False
        if len(text) > 3000:
            text = text[:3000] + "\n...[truncated to 3000 characters]..."
            truncated = True

        out = {
            "source_tag": source_tag,
            "full_name": clean_name,
            "truncated": truncated,
            "content": text or "not found",
        }
        result_str = json.dumps(out, indent=2)
        ctx.context.set_cached_result(cache_key, result_str)
        ctx.context.append_trace(tool_name, call_args, "success")
        return result_str

    except Exception as exc:
        msg = f"[{tool_name} | {url} | {datetime.now(timezone.utc).isoformat()}] Request failed: {exc}"
        ctx.context.append_trace(tool_name, call_args, f"failed: {exc}")
        return msg


@function_tool
async def hf_search(
    ctx: RunContextWrapper[ProjectResearchContext],
    kind: Literal["model", "dataset", "space"],
    query: str,
    max_results: int = 5,
) -> str:
    """Search models, datasets, or Spaces on Hugging Face Hub."""
    tool_name = "hf_search"
    limit = min(max(1, max_results), 5)
    call_args = {"kind": kind, "query": query, "max_results": limit}

    if query and query not in ctx.context.search_queries_run:
        ctx.context.search_queries_run.append(query)

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit")
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    kind_endpoint_map = {
        "model": "https://huggingface.co/api/models",
        "dataset": "https://huggingface.co/api/datasets",
        "space": "https://huggingface.co/api/spaces",
    }
    url = kind_endpoint_map.get(kind, "https://huggingface.co/api/models")
    params = {"search": query, "limit": limit, "full": "false"}

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=_get_hf_headers())

        source_tag = _format_source_tag(tool_name, str(resp.url))

        if resp.status_code != 200:
            msg = f"{source_tag} Hugging Face search failed (HTTP {resp.status_code}): {resp.text[:300]}"
            ctx.context.append_trace(tool_name, call_args, f"error_{resp.status_code}")
            return msg

        data = resp.json()
        items = []
        if isinstance(data, list):
            for it in data[:limit]:
                repo_id = it.get("id") or it.get("_id")
                repo_url = f"https://huggingface.co/{'spaces/' if kind == 'space' else ('datasets/' if kind == 'dataset' else '')}{repo_id}"
                ctx.context.record_candidate_url(repo_url)
                items.append({
                    "name": repo_id,
                    "url": repo_url,
                    "description": it.get("description") or "not found",
                    "downloads": it.get("downloads", 0),
                    "likes": it.get("likes", 0),
                    "pipeline_tag": it.get("pipeline_tag") or "not found",
                })

        result_str = json.dumps({"source_tag": source_tag, "kind": kind, "items": items}, indent=2)
        ctx.context.set_cached_result(cache_key, result_str)
        ctx.context.append_trace(tool_name, call_args, "success")
        return result_str

    except Exception as exc:
        msg = f"[{tool_name} | {url} | {datetime.now(timezone.utc).isoformat()}] Request failed: {exc}"
        ctx.context.append_trace(tool_name, call_args, f"failed: {exc}")
        return msg


@function_tool
async def hf_get_details(
    ctx: RunContextWrapper[ProjectResearchContext],
    kind: Literal["model", "dataset", "space"],
    repo_id: str,
) -> str:
    """Get metadata and model/dataset/space card text (truncated to ~3000 chars) for a Hugging Face repository."""
    clean_id = repo_id.strip().strip("/")
    tool_name = "hf_get_details"
    call_args = {"kind": kind, "repo_id": clean_id}

    cache_key = ctx.context.get_cache_key(tool_name, call_args)
    cached = ctx.context.get_cached_result(cache_key)
    if cached is not None:
        ctx.context.append_trace(tool_name, call_args, "cache_hit")
        return f"[CACHED: already called with these arguments]\n{cached}"

    budget_msg = ctx.context.check_and_increment_budget(tool_name, call_args)
    if budget_msg:
        return budget_msg

    kind_endpoint_map = {
        "model": f"https://huggingface.co/api/models/{clean_id}",
        "dataset": f"https://huggingface.co/api/datasets/{clean_id}",
        "space": f"https://huggingface.co/api/spaces/{clean_id}",
    }
    url = kind_endpoint_map.get(kind, f"https://huggingface.co/api/models/{clean_id}")

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_get_hf_headers())

        source_tag = _format_source_tag(tool_name, str(resp.url))

        if resp.status_code == 404:
            msg = f"{source_tag} Hugging Face {kind} '{clean_id}' not found (HTTP 404)."
            ctx.context.append_trace(tool_name, call_args, "not_found")
            return msg

        if resp.status_code != 200:
            msg = f"{source_tag} Hugging Face details failed (HTTP {resp.status_code}): {resp.text[:300]}"
            ctx.context.append_trace(tool_name, call_args, f"error_{resp.status_code}")
            return msg

        data = resp.json()

        card_data = data.get("cardData") or {}
        description = data.get("description") or card_data.get("description") or ""

        card_text = ""
        card_url = f"https://huggingface.co/{'spaces/' if kind == 'space' else ('datasets/' if kind == 'dataset' else '')}{clean_id}/raw/main/README.md"
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                card_resp = await client.get(card_url, headers=_get_hf_headers())
                if card_resp.status_code == 200:
                    card_text = card_resp.text
        except Exception:
            pass

        combined_card = card_text or description or "not found"
        truncated = False
        if len(combined_card) > 3000:
            combined_card = combined_card[:3000] + "\n...[truncated to 3000 characters]..."
            truncated = True

        repo_url = f"https://huggingface.co/{'spaces/' if kind == 'space' else ('datasets/' if kind == 'dataset' else '')}{clean_id}"
        ctx.context.record_candidate_url(repo_url)

        out = {
            "source_tag": source_tag,
            "id": clean_id,
            "kind": kind,
            "url": repo_url,
            "description": description or "not found",
            "tags": data.get("tags") or [],
            "pipeline_tag": data.get("pipeline_tag") or "not found",
            "license": card_data.get("license") or data.get("license") or "not found",
            "downloads": data.get("downloads", "not found"),
            "likes": data.get("likes", "not found"),
            "last_update": data.get("lastModified") or "not found",
            "card_truncated": truncated,
            "card_text": combined_card,
        }

        result_str = json.dumps(out, indent=2)
        ctx.context.set_cached_result(cache_key, result_str)
        ctx.context.append_trace(tool_name, call_args, "success")
        return result_str

    except Exception as exc:
        msg = f"[{tool_name} | {url} | {datetime.now(timezone.utc).isoformat()}] Request failed: {exc}"
        ctx.context.append_trace(tool_name, call_args, f"failed: {exc}")
        return msg


def _generate_markdown_report(findings_obj: ProjectResearchFindings) -> str:
    lines = [
        f"# Existing Project Research Findings",
        f"",
        f"- **Session ID:** `{findings_obj.session_id}`",
        f"- **Total Findings:** {len(findings_obj.findings)}",
        f"- **Search Queries Run:** {', '.join(f'`{q}`' for q in findings_obj.search_queries_run) if findings_obj.search_queries_run else 'None'}",
        f"",
    ]
    if findings_obj.notes:
        lines.extend([
            f"## Notes",
            f"{findings_obj.notes}",
            f"",
        ])

    lines.append("## Findings")
    lines.append("")

    for idx, f in enumerate(findings_obj.findings, 1):
        lines.extend([
            f"### {idx}. {f.name} ({f.platform.title()} {f.kind.title()})",
            f"- **URL:** [{f.url}]({f.url})",
            f"- **Problem Solved:** {f.problem_solved}",
            f"- **Input / Output:** {f.input_output}",
            f"- **Dataset:** {f.dataset}",
            f"- **Model & Architecture:** {f.model_and_architecture}",
            f"- **Method:** {f.method}",
            f"- **Evaluation & Results:** {f.evaluation_and_results}",
            f"- **Repository Details:** Stars: {f.repository_details.stars} | License: {f.repository_details.license} | Language: {f.repository_details.language} | Last Update: {f.repository_details.last_update} | Archived: {f.repository_details.archived}",
            f"- **Reproducibility:** {f.reproducibility}",
            f"- **Known Limitations:** {f.known_limitations}",
            f"",
            f"**Field Sources:**",
        ])
        for field_name, src in f.field_sources.items():
            lines.append(f"- *{field_name}*: `{src}`")
        lines.append("")

    return "\n".join(lines)


@function_tool(strict_mode=False)
async def save_findings(
    ctx: RunContextWrapper[ProjectResearchContext],
    search_queries_run: list[str],
    findings: list[Finding],
    notes: str = "",
) -> str:
    """Save the completed project research findings to disk.

    Call this EXACTLY ONCE at the end of the research process.
    Writes outputs/{session_id}/project_findings.json and project_findings.md.
    """
    tool_name = "save_findings"
    try:
        # Merge search queries run tracked in context with those provided
        all_queries = list(dict.fromkeys(search_queries_run + ctx.context.search_queries_run))

        validated = ProjectResearchFindings(
            session_id=ctx.context.session_id,
            search_queries_run=all_queries,
            findings=[Finding.model_validate(item) for item in findings[:10]],
            notes=notes,
        )

        ctx.context.output_dir.mkdir(parents=True, exist_ok=True)

        json_path = ctx.context.output_dir / "project_findings.json"
        json_path.write_text(validated.model_dump_json(indent=2), encoding="utf-8")

        md_path = ctx.context.output_dir / "project_findings.md"
        md_text = _generate_markdown_report(validated)
        md_path.write_text(md_text, encoding="utf-8")

        ctx.context.saved = True
        ctx.context.findings_summary = f"Saved {len(validated.findings)} findings across {len(all_queries)} queries."
        ctx.context.append_trace(tool_name, {"num_queries": len(all_queries), "num_findings": len(findings)}, "success")

        return f"Successfully saved {len(validated.findings)} findings to {json_path} and {md_path}."

    except ValidationError as ve:
        err_msg = (
            f"Validation failed while saving findings: {ve}\n"
            "Ensure every finding item contains exact keys: 'name', 'url', 'platform' ('github'|'huggingface'), "
            "'kind' ('repository'|'model'|'dataset'|'space'), 'problem_solved', 'input_output', 'dataset', "
            "'model_and_architecture', 'method', 'evaluation_and_results', 'repository_details', 'reproducibility', "
            "'known_limitations', 'field_sources'. Mark missing fields as 'not found'."
        )
        ctx.context.append_trace(tool_name, {"num_findings": len(findings)}, f"validation_error: {ve}")
        return err_msg
    except Exception as exc:
        err_msg = f"Error saving findings: {exc}"
        ctx.context.append_trace(tool_name, {"num_findings": len(findings)}, f"error: {exc}")
        return err_msg
