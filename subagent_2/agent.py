import os
import sys
from pathlib import Path

# Add project root directory to sys.path so shared modules are always accessible
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import re
import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from researcher import FirecrawlPaperResearcher, ExaResearcher

load_dotenv(ROOT_DIR / ".env")

class PaperFinderAgent:
    """
    Subagent 2: Academic Paper Finder Agent.
    Consumes Subagent 1's prior_art_findings.json and confirmed problem statement.
    Executes a 5-step workflow:
    1. Reads input contract (domain_keywords, gaps_identified, closest_match_summary).
    2. Builds 3-5 academic query variants targeting the identified gaps and methods.
    3. Searches literature via Firecrawl paper tools (search, inspect, citation graph)
       with Exa preprint fallback.
    4. Ranks and narrows candidate papers to exactly top 5 by gap relevance.
    5. Emits strict paper_findings.json and paper_reading_list.md.
    """

    def __init__(
        self,
        model: str = "gpt-oss:120b",
        api_key: Optional[str] = None,
        base_url: str = "https://ollama.com/v1",
        output_dir: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.client = OpenAI(base_url=base_url, api_key=self.api_key, timeout=60.0)

        self.paper_researcher = FirecrawlPaperResearcher()
        self.exa = ExaResearcher()

        self.output_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent
        self.confirmed_problem_statement: str = ""
        self.subagent1_findings: Dict[str, Any] = {}
        self.search_queries_used: List[str] = []

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Call Ollama Cloud LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[LLM Error]: {e}")
            return ""

    # =========================================================================
    # Step 1: Read Input Contract
    # =========================================================================

    def load_input_contract(
        self,
        findings_json_path: Optional[str] = None,
        problem_statement: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Loads Subagent 1's JSON findings. No clarification interview is performed.
        """
        print("\n" + "=" * 65)
        print("  PAPER FINDER AGENT (SUBAGENT 2) - LITERATURE DISCOVERY")
        print("=" * 65)
        print("Ingesting Subagent 1 findings contract (No interview required)...\n")

        # Resolve path
        resolved_path = None
        candidates_to_try = [
            findings_json_path,
            ROOT_DIR / "subagent_1" / "prior_art_findings.json",
            ROOT_DIR / "prior_art_findings.json",
            "prior_art_findings.json",
        ]
        for c in candidates_to_try:
            if c and Path(c).exists():
                resolved_path = Path(c)
                break

        if resolved_path and resolved_path.exists():
            with open(resolved_path, "r", encoding="utf-8") as f:
                self.subagent1_findings = json.load(f)
            print(f"[Contract] Successfully loaded findings from {resolved_path}")
        else:
            print("[Contract Warning] prior_art_findings.json not found. Using fallback parameters.")
            self.subagent1_findings = {
                "confirmed_problem_statement": problem_statement or "Prior-art research project",
                "search_queries_used": [],
                "prior_art_found": False,
                "closest_match_summary": "",
                "candidates": [],
                "domain_keywords": ["machine learning", "edge AI"],
                "gaps_identified": "Edge real-time inference and hardware integration.",
            }

        self.confirmed_problem_statement = (
            problem_statement
            or self.subagent1_findings.get("confirmed_problem_statement", "")
        )

        print(f"[Problem Statement]: {self.confirmed_problem_statement[:120]}...")
        print(f"[Identified Gaps]: {self.subagent1_findings.get('gaps_identified', '')[:100]}...")
        print(f"[Domain Keywords]: {', '.join(self.subagent1_findings.get('domain_keywords', []))}\n")

        return self.subagent1_findings

    # =========================================================================
    # Step 2: Build Query Variants Seeded from Subagent 1's Findings
    # =========================================================================

    def build_query_variants(self) -> List[str]:
        """
        Constructs 3-5 search queries combining:
        - Literal technique/method names from domain_keywords
        - Specific angle in gaps_identified
        - Methods mentioned in closest_match_summary
        """
        keywords = self.subagent1_findings.get("domain_keywords", [])
        gaps = self.subagent1_findings.get("gaps_identified", "")
        closest = self.subagent1_findings.get("closest_match_summary", "")

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are Subagent 2 (Paper Finder). Generate 3 to 4 precise academic search queries "
                    "for peer-reviewed papers (PubMed, arXiv, IEEE). \n"
                    "RULES:\n"
                    "1. Every query must be traceable to Subagent 1's findings: domain keywords, identified gaps, or closest match methods.\n"
                    "2. Target the specific missing techniques in 'gaps_identified' rather than generic high-level topic searches.\n"
                    "3. Return ONLY a JSON array of strings, e.g. [\"query 1\", \"query 2\", \"query 3\"]."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Domain Keywords: {json.dumps(keywords)}\n"
                    f"Identified Gaps to Solve: {gaps}\n"
                    f"Closest Prior Art Match: {closest}\n"
                    f"Confirmed Problem Statement: {self.confirmed_problem_statement}"
                ),
            },
        ]

        raw = self._call_llm(prompt, temperature=0.2).strip()
        try:
            clean = re.sub(r"^```json\s*", "", raw)
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean).strip()
            queries = json.loads(clean)
            if isinstance(queries, list) and queries:
                self.search_queries_used = [str(q) for q in queries[:4]]
                return self.search_queries_used
        except Exception:
            pass

        kw_str = " ".join(keywords[:3]) if keywords else "prior art"
        fallback = [
            f"{kw_str} architecture method",
            f"real-time {kw_str} {gaps[:40]}",
            f"novel algorithm {kw_str}",
        ]
        self.search_queries_used = fallback
        return fallback

    # =========================================================================
    # Step 3: Search Literature (Firecrawl Paper Tools + Exa Fallback)
    # =========================================================================

    def search_literature(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        2-Pass literature discovery:
        Pass 1: firecrawl_research_search_papers across all query variants.
        Pass 2: inspect_paper on top candidates and expand via firecrawl_research_related_papers.
        Fallback: Exa preprint search (arXiv, bioRxiv, OpenReview) if needed.
        """
        print(f"[Search] Executing academic paper searches across {len(queries)} query variants...")
        candidates: List[Dict[str, Any]] = []
        seen_ids = set()
        seen_titles = set()

        # Pass 1: Firecrawl Paper Search
        for q in queries:
            print(f"  → Query: '{q}'")
            papers = self.paper_researcher.search_papers(q, k=6)
            for p in papers:
                pid = p.get("paper_id", "")
                title_norm = p.get("title", "").lower().strip()
                if pid not in seen_ids and title_norm not in seen_titles:
                    seen_ids.add(pid)
                    seen_titles.add(title_norm)
                    candidates.append(p)

        print(f"[Search] Found {len(candidates)} candidate papers from initial search.")

        # Pass 2: Inspect top candidate abstracts & expand citation graph
        top_seeds = [c["paper_id"] for c in candidates[:3] if c.get("paper_id")]
        for seed_id in top_seeds[:2]:
            print(f"[Citation Graph] Inspecting metadata for seed: {seed_id}")
            details = self.paper_researcher.inspect_paper(seed_id)
            for c in candidates:
                if c.get("paper_id") == seed_id:
                    if details.get("authors"):
                        c["authors"] = details["authors"]
                    if details.get("year"):
                        c["year"] = details["year"]
                    if details.get("abstract"):
                        c["abstract"] = details["abstract"]

            intent = f"{self.confirmed_problem_statement} {self.subagent1_findings.get('gaps_identified', '')}"[:120]
            print(f"[Citation Graph] Expanding related papers for {seed_id}...")
            related = self.paper_researcher.get_related_papers([seed_id], intent=intent, k=3)
            for r in related:
                r_pid = r.get("paper_id", "")
                r_title = r.get("title", "").lower().strip()
                if r_pid not in seen_ids and r_title not in seen_titles:
                    seen_ids.add(r_pid)
                    seen_titles.add(r_title)
                    candidates.append(r)

        # Fallback: Exa Academic Preprints if candidate pool is thin (< 5)
        if len(candidates) < 5:
            print("[Search Fallback] Fewer than 5 candidates from Firecrawl. Triggering Exa preprint search...")
            fallback_query = f"{queries[0]} arxiv bioRxiv"
            exa_papers = self.exa.search_academic_preprints(fallback_query, num_results=5)
            for ep in exa_papers:
                t_norm = ep.get("title", "").lower().strip()
                if t_norm not in seen_titles:
                    seen_titles.add(t_norm)
                    candidates.append({
                        "paper_id": ep.get("url_or_doi"),
                        "title": ep.get("title"),
                        "abstract": ep.get("snippet"),
                        "url_or_doi": ep.get("url_or_doi"),
                        "authors": ep.get("authors", "Unknown"),
                        "year": ep.get("year", "Recent"),
                        "source": "paper",
                    })

        print(f"[Search] Total pooled candidate papers: {len(candidates)}")
        return candidates

    # =========================================================================
    # Step 4: Rank and Narrow by Gap Relevance
    # =========================================================================

    def rank_and_narrow(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Judges candidate papers by how directly each explains the technique,
        approach, or gap identified in Subagent 1. Narrows to exactly top 5.
        """
        print("\n[Ranking] Evaluating candidate papers against Subagent 1 gaps...")

        if not candidates:
            return []

        cand_text_list = []
        for i, c in enumerate(candidates[:15], 1):
            cand_text_list.append(
                f"Candidate [{i}]:\n"
                f"  Title: {c.get('title')}\n"
                f"  ID/URL: {c.get('url_or_doi') or c.get('paper_id')}\n"
                f"  Authors: {c.get('authors', 'Unknown')}\n"
                f"  Year: {c.get('year', 'Unknown')}\n"
                f"  Abstract/Snippet: {c.get('abstract', '')[:350]}\n"
            )
        cand_blob = "\n".join(cand_text_list)

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are Subagent 2 (Paper Finder). You must evaluate the candidate papers and select "
                    "EXACTLY the top 5 most relevant papers that directly explain the missing techniques "
                    "or architecture identified in Subagent 1's gaps and closest prior art match.\n\n"
                    "CRITICAL RANKING CRITERIA:\n"
                    "1. Directness to gaps: Does this paper provide the solution, algorithm, or methodology for what was missing?\n"
                    "2. Avoid generic surveys if a paper detailing the exact method exists.\n"
                    "3. 'why_relevant' MUST reference Subagent 1's findings.\n\n"
                    "OUTPUT SCHEMA (JSON array of exactly 5 objects or fewer if insufficient):\n"
                    "[\n"
                    "  {\n"
                    '    "title": "exact paper title",\n'
                    '    "authors": "author list or primary author et al.",\n'
                    '    "year": "YYYY",\n'
                    '    "url_or_doi": "URL or DOI string",\n'
                    '    "relevance_rank": 1,\n'
                    '    "why_relevant": "concrete explanation referencing Subagent 1 findings"\n'
                    "  }\n"
                    "]\n"
                    "Return ONLY the JSON array. No markdown code block fences, no conversation."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Confirmed Problem Statement:\n{self.confirmed_problem_statement}\n\n"
                    f"Subagent 1 Identified Gaps:\n{self.subagent1_findings.get('gaps_identified')}\n\n"
                    f"Subagent 1 Closest Match Summary:\n{self.subagent1_findings.get('closest_match_summary')}\n\n"
                    f"Available Paper Candidates:\n{cand_blob}"
                ),
            },
        ]

        raw = self._call_llm(prompt, temperature=0.2).strip()

        try:
            clean = re.sub(r"^```json\s*", "", raw)
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean).strip()
            ranked_papers = json.loads(clean)
            if isinstance(ranked_papers, list) and ranked_papers:
                for idx, p in enumerate(ranked_papers[:5], 1):
                    p["relevance_rank"] = idx
                return ranked_papers[:5]
        except Exception as e:
            print(f"[Ranking Warning] LLM parsing failed ({e}), falling back to direct mapping.")

        fallback_ranked = []
        for idx, c in enumerate(candidates[:5], 1):
            fallback_ranked.append({
                "title": c.get("title", "Untitled Paper"),
                "authors": c.get("authors", "Unknown"),
                "year": c.get("year", "Recent"),
                "url_or_doi": c.get("url_or_doi") or f"https://pubmed.ncbi.nlm.nih.gov/{c.get('paper_id')}/",
                "relevance_rank": idx,
                "why_relevant": f"Addresses core techniques related to {self.subagent1_findings.get('gaps_identified', 'prior art gaps')[:60]}.",
            })
        return fallback_ranked

    # =========================================================================
    # Step 5: Output Generation (paper_findings.json & paper_reading_list.md)
    # =========================================================================

    def export_outputs(
        self,
        ranked_papers: List[Dict[str, Any]],
        output_json_path: Optional[str] = None,
        output_report_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emits strict JSON contract and formatted Markdown reading list."""
        notes = ""
        if len(ranked_papers) < 5:
            notes = f"Only {len(ranked_papers)} highly relevant papers were found meeting the strict gap-alignment criteria."

        findings = {
            "confirmed_problem_statement": self.confirmed_problem_statement,
            "search_queries_used": self.search_queries_used,
            "papers": ranked_papers,
            "notes": notes,
        }

        json_target = Path(output_json_path) if output_json_path else self.output_dir / "paper_findings.json"
        report_target = Path(output_report_path) if output_report_path else self.output_dir / "paper_reading_list.md"

        json_target.parent.mkdir(parents=True, exist_ok=True)
        report_target.parent.mkdir(parents=True, exist_ok=True)

        with open(json_target, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2)
        print(f"\n[Export] ✓ Strict JSON contract written to {json_target}")

        root_json = ROOT_DIR / "paper_findings.json"
        if json_target != root_json:
            with open(root_json, "w", encoding="utf-8") as f:
                json.dump(findings, f, indent=2)

        self._write_markdown_reading_list(findings, str(report_target))
        print(f"[Export] ✓ Curated reading list written to {report_target}")

        root_report = ROOT_DIR / "paper_reading_list.md"
        if report_target != root_report:
            self._write_markdown_reading_list(findings, str(root_report))

        return findings

    def _write_markdown_reading_list(self, findings: Dict[str, Any], path: str):
        """Generates structured reading list report."""
        report = []
        report.append("# Curated Academic Reading List (Subagent 2)\n")
        report.append(f"**Generated on:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Model Engine:** `{self.model}` via Ollama Cloud\n\n")

        report.append("## Research Context & Objectives\n")
        report.append(f"> **Confirmed Problem:** {findings.get('confirmed_problem_statement')}\n\n")
        if self.subagent1_findings.get("gaps_identified"):
            report.append(f"> **Target Gaps Identified by Subagent 1:** {self.subagent1_findings.get('gaps_identified')}\n\n")

        report.append("## Search Queries Used\n")
        for q in findings.get("search_queries_used", []):
            report.append(f"- `{q}`\n")
        report.append("\n")

        report.append("## Top 5 Ranked Academic Papers\n\n")
        for p in findings.get("papers", []):
            rank = p.get("relevance_rank", 1)
            title = p.get("title", "Untitled")
            authors = p.get("authors", "Unknown")
            year = p.get("year", "Unknown")
            url = p.get("url_or_doi", "#")
            why = p.get("why_relevant", "")

            report.append(f"### #{rank}. [{title}]({url})\n")
            report.append(f"- **Authors:** {authors}\n")
            report.append(f"- **Year:** {year}\n")
            report.append(f"- **Link / DOI:** [{url}]({url})\n")
            report.append(f"- **Relevance to Identified Gaps:** {why}\n\n")

        if findings.get("notes"):
            report.append("## Notes\n")
            report.append(f"{findings.get('notes')}\n\n")

        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(report))

    # =========================================================================
    # Full Orchestration
    # =========================================================================

    def execute_literature_discovery(
        self,
        findings_data: Optional[Any] = None,
        problem_statement: Optional[str] = None,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Programmatic execution of Subagent 2 with optional progress_callback(status_message).
        findings_data can be a path string (JSON file) or a dictionary.
        """
        if isinstance(findings_data, dict):
            self.subagent1_findings = findings_data
            self.confirmed_problem_statement = (
                problem_statement
                or findings_data.get("confirmed_problem_statement", "")
            )
        else:
            self.load_input_contract(findings_data, problem_statement)

        if progress_callback:
            progress_callback("Generating academic queries from domain keywords & gaps...")
        queries = self.build_query_variants()
        print(f"[Queries Generated]:\n" + "\n".join([f"  {i}. {q}" for i, q in enumerate(queries, 1)]))

        if progress_callback:
            progress_callback(f"Searching peer-reviewed literature across {len(queries)} query variants...")
        candidates = self.search_literature(queries)

        if progress_callback:
            progress_callback(f"Ranking {len(candidates)} candidate papers by gap relevance...")
        ranked_papers = self.rank_and_narrow(candidates)

        if progress_callback:
            progress_callback("Synthesizing reading list and JSON contract...")
        findings = self.export_outputs(ranked_papers)

        if progress_callback:
            progress_callback("Academic literature discovery complete!")
        return findings

    def run(
        self,
        findings_json_path: Optional[str] = None,
        problem_statement: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs Subagent 2 end-to-end without user interview."""
        findings = self.execute_literature_discovery(findings_json_path, problem_statement)
        ranked_papers = findings.get("papers", [])

        print("\n" + "=" * 65)
        print("  ACADEMIC LITERATURE DISCOVERY COMPLETE")
        print("=" * 65)
        print(f"Top Paper: {ranked_papers[0].get('title', 'None') if ranked_papers else 'None'}")
        print("Outputs saved in subagent_2/ and root.\n")
        return findings


if __name__ == "__main__":
    agent = PaperFinderAgent()
    agent.run()
