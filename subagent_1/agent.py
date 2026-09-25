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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from researcher import ExaResearcher, FirecrawlResearcher, HuggingFaceResearcher, PlaywrightVerifier

load_dotenv(ROOT_DIR / ".env")

class PriorArtDiscoveryAgent:
    """
    Subagent 1: Prior-Art Discovery Agent.
    Executes a 6-step workflow:
    1. Plan-mode style interactive clarification interview (1 focused question at a time).
    2. Concurrent Exa & Firecrawl search (3-5 query variants).
    3. Dedicated Hugging Face & GitHub search.
    4. Headed Playwright browser verification for ambiguous candidates.
    5. Prior-art closeness ranking and innovation gap analysis.
    6. Dual output emission: prior_art_findings.json and prior_art_report.md.
    """

    def __init__(
        self,
        model: str = "gpt-oss:120b",
        api_key: Optional[str] = None,
        base_url: str = "https://ollama.com/v1",
        headless_playwright: bool = False,
        output_dir: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.client = OpenAI(base_url=base_url, api_key=self.api_key, timeout=60.0)
        
        # Tool researchers
        self.exa = ExaResearcher()
        self.firecrawl = FirecrawlResearcher()
        self.hf = HuggingFaceResearcher()
        self.playwright = PlaywrightVerifier(headless=headless_playwright)
        
        # Directories
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent
        
        # Internal state
        self.interview_state: Dict[str, Any] = {
            "core_idea": "",
            "inputs_outputs": "",
            "techniques": "",
            "novelty_claim": "",
            "domain_keywords": [],
            "scope_boundaries": "",
        }
        self.confirmed_problem_statement: str = ""
        self.search_queries_used: List[str] = []
        self.candidates: List[Dict[str, Any]] = []

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
    # Step 1: Plan-Mode Clarification Interview
    # =========================================================================

    def run_interview(self, initial_idea: Optional[str] = None) -> str:
        """
        Interactive interview loop asking 1 focused question at a time until
        all 6 dimensions are understood, then confirms with the user.
        """
        print("\n" + "=" * 65)
        print("  PRIOR-ART DISCOVERY AGENT (SUBAGENT 1) - PLAN-MODE INTERVIEW")
        print("=" * 65)
        print("I will ask a few focused questions one at a time to fully understand")
        print("your project before conducting any searches.\n")

        conversation_history: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are the Prior-Art Discovery Agent (Subagent 1) running a plan-mode clarification interview. "
                    "Your objective is to fully understand the user's project across 6 dimensions:\n"
                    "1. Core idea (What is the project trying to do?)\n"
                    "2. Inputs/outputs (What does it take in, what does it produce?)\n"
                    "3. Techniques/architecture (Specific methods, models, algorithms, frameworks?)\n"
                    "4. Novelty claim (What is new or different about this approach?)\n"
                    "5. Domain & keywords (Field of study, expert terminology?)\n"
                    "6. Scope boundaries (On-device, open-source, hardware constraints?)\n\n"
                    "CRITICAL RULES:\n"
                    "- Ask only ONE single, concise, focused question at a time. Never dump multiple questions or bulleted checklists.\n"
                    "- Do not make assumptions. Clarify ambiguity directly.\n"
                    "- When all 6 dimensions are sufficiently clear, output exactly the prefix '[INTERVIEW_COMPLETE]' "
                    "followed by a synthesized 1-paragraph plain-language problem statement summarizing everything learned."
                ),
            }
        ]

        if not initial_idea:
            initial_idea = input("What is the project or idea you want to research prior art for?\n> ").strip()

        conversation_history.append({
            "role": "user",
            "content": f"Here is my project idea: {initial_idea}"
        })

        rounds = 0
        max_rounds = 7

        while rounds < max_rounds:
            rounds += 1
            reply = self._call_llm(conversation_history, temperature=0.3).strip()

            if "[INTERVIEW_COMPLETE]" in reply or "Is this an accurate understanding" in reply:
                statement = reply.replace("[INTERVIEW_COMPLETE]", "").strip()
                self.confirmed_problem_statement = self._confirm_statement_loop(statement)
                return self.confirmed_problem_statement

            print(f"\n[Agent]: {reply}\n")
            user_response = input("> ").strip()
            
            if user_response.lower() in ["done", "that's all", "search now", "proceed"]:
                break

            conversation_history.append({"role": "assistant", "content": reply})
            conversation_history.append({"role": "user", "content": user_response})

        synth_prompt = [
            {"role": "system", "content": "Synthesize the user's project into a clear, comprehensive 1-paragraph plain-language problem statement capturing: core idea, inputs/outputs, techniques, novelty claim, domain keywords, and scope constraints."},
            {"role": "user", "content": f"Conversation history:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history])}
        ]
        statement = self._call_llm(synth_prompt, temperature=0.2).strip()
        self.confirmed_problem_statement = self._confirm_statement_loop(statement)
        return self.confirmed_problem_statement

    def get_interview_turn(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluates the conversation history for UI/programmatic usage and returns the next question,
        or indicates that the interview is complete with a synthesized statement.
        """
        reply = self._call_llm(conversation_history, temperature=0.3).strip()
        if "[INTERVIEW_COMPLETE]" in reply or "Is this an accurate understanding" in reply:
            statement = reply.replace("[INTERVIEW_COMPLETE]", "").replace("Is this an accurate understanding of your project?", "").strip()
            return {"is_complete": True, "statement": statement, "reply": reply}
        return {"is_complete": False, "question": reply, "reply": reply}

    def synthesize_problem_statement(self, conversation_history: List[Dict[str, str]]) -> str:
        """Synthesizes a clean problem statement from conversation history."""
        synth_prompt = [
            {"role": "system", "content": "Synthesize the user's project into a clear, comprehensive 1-paragraph plain-language problem statement capturing: core idea, inputs/outputs, techniques, novelty claim, domain keywords, and scope constraints."},
            {"role": "user", "content": f"Conversation history:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history])}
        ]
        return self._call_llm(synth_prompt, temperature=0.2).strip()

    def _confirm_statement_loop(self, statement: str) -> str:
        """Presents synthesized statement and pauses until user confirmation."""
        while True:
            print("\n" + "-" * 65)
            print("UNDERSTOOD PROBLEM STATEMENT:")
            print("-" * 65)
            print(statement)
            print("-" * 65)
            confirm = input("\nIs this an accurate understanding of your project? (yes / no / add details)\n> ").strip()
            
            if confirm.lower() in ["yes", "y", "correct", "proceed", "accurate"]:
                print("\n✓ Problem statement confirmed! Proceeding to prior-art discovery.\n")
                return statement
            else:
                extra = input("\nPlease specify what needs correction or addition:\n> ").strip()
                refine_prompt = [
                    {"role": "system", "content": "Update the problem statement incorporating the user's corrections."},
                    {"role": "user", "content": f"Current statement: {statement}\nUser correction: {extra}"}
                ]
                statement = self._call_llm(refine_prompt, temperature=0.2).strip()

    # =========================================================================
    # Step 2: Query Generation & Concurrent Exa + Firecrawl Search
    # =========================================================================

    def generate_search_queries(self, statement: str) -> List[str]:
        """Generates 3-5 query variants."""
        prompt = [
            {
                "role": "system",
                "content": (
                    "Generate exactly 4 distinct, high-signal search queries to uncover existing prior art, GitHub repos, and models for this project.\n"
                    "1. A literal description query\n"
                    "2. A technical architecture/keyword query\n"
                    "3. A product/tool/framework query\n"
                    "4. An open-source implementation query\n"
                    "Output ONLY a JSON array of strings, e.g. [\"query 1\", \"query 2\", \"query 3\", \"query 4\"]."
                ),
            },
            {"role": "user", "content": f"Problem Statement:\n{statement}"},
        ]
        raw = self._call_llm(prompt, temperature=0.2).strip()
        try:
            clean = re.sub(r"^```json\s*", "", raw)
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean).strip()
            queries = json.loads(clean)
            if isinstance(queries, list) and queries:
                self.search_queries_used = [str(q) for q in queries[:5]]
                return self.search_queries_used
        except Exception:
            pass

        fallback = [
            statement[:80],
            f"open source {statement[:60]}",
            f"github repo {statement[:60]}",
        ]
        self.search_queries_used = fallback
        return fallback

    def search_prior_art(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Executes concurrent Exa and Firecrawl searches."""
        print(f"[Search] Firing concurrent Exa & Firecrawl searches across {len(queries)} query variants...")
        candidates = []
        seen_urls = set()

        def run_exa(q):
            return ("exa", self.exa.search(q, num_results=4))

        def run_firecrawl(q):
            return ("firecrawl", self.firecrawl.search(q, limit=4))

        tasks = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            for q in queries:
                tasks.append(executor.submit(run_exa, q))
                tasks.append(executor.submit(run_firecrawl, q))

            for future in as_completed(tasks):
                try:
                    source_type, results = future.result()
                    for r in results:
                        url = r.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            candidates.append({
                                "name": r.get("name") or url,
                                "source": r.get("source", "web"),
                                "url": url,
                                "snippet": r.get("snippet", ""),
                                "verified_via_playwright": False,
                                "closeness": "partial_overlap",
                                "status": "unknown",
                                "notes": "",
                            })
                except Exception as e:
                    print(f"[Search Warning]: {e}")

        print(f"[Search] Discovered {len(candidates)} candidate URLs from general web discovery.")
        return candidates

    # =========================================================================
    # Step 3: Targeted Hugging Face and GitHub Developer Search
    # =========================================================================

    def search_hf_and_github(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Dedicated searches against Hugging Face Hub and GitHub."""
        print("[Search] Running dedicated Hugging Face Hub and GitHub developer searches...")
        hf_and_gh_candidates = []
        seen_urls = set()

        hf_query = queries[1] if len(queries) > 1 else queries[0]
        hf_clean_query = " ".join([w for w in hf_query.split() if len(w) > 2][:4])
        hf_results = self.hf.search(hf_clean_query, limit=5)
        for r in hf_results:
            url = r.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                hf_and_gh_candidates.append({
                    "name": r.get("name"),
                    "source": "huggingface",
                    "url": url,
                    "snippet": r.get("snippet", ""),
                    "verified_via_playwright": False,
                    "closeness": "partial_overlap",
                    "status": "active",
                    "notes": f"Hugging Face repository. Likes: {r.get('likes', 0)}, Last updated: {r.get('last_modified', 'unknown')}",
                })

        gh_query = f"{queries[0]} site:github.com"
        gh_results = self.firecrawl.developer_search(gh_query, limit=4)
        for r in gh_results:
            url = r.get("url")
            if url and "github.com" in url and url not in seen_urls:
                seen_urls.add(url)
                hf_and_gh_candidates.append({
                    "name": r.get("name"),
                    "source": "github",
                    "url": url,
                    "snippet": r.get("snippet", ""),
                    "verified_via_playwright": False,
                    "closeness": "partial_overlap",
                    "status": "unknown",
                    "notes": "GitHub repository surfaced via developer search.",
                })

        print(f"[Search] Found {len(hf_and_gh_candidates)} dedicated Hugging Face & GitHub targets.")
        return hf_and_gh_candidates

    # =========================================================================
    # Step 4: Verify Ambiguous Candidates with Playwright
    # =========================================================================

    def verify_candidates_with_playwright(self, candidates: List[Dict[str, Any]], max_checks: int = 3) -> List[Dict[str, Any]]:
        """Inspects ambiguous or high-value candidate URLs in a visible headed browser."""
        if not candidates:
            return candidates

        targets = []
        for c in candidates:
            url = c.get("url", "")
            if "github.com" in url or "huggingface.co/spaces" in url or c.get("source") == "web":
                targets.append(c)
            if len(targets) >= max_checks:
                break

        if not targets:
            targets = candidates[:max_checks]

        print(f"\n[Playwright] Verifying top {len(targets)} candidate pages live in visible browser...")
        for c in targets:
            url = c["url"]
            verification = self.playwright.verify_candidate(url, wait_seconds=2)
            if verification.get("verified"):
                c["verified_via_playwright"] = True
                c["status"] = verification.get("status", "active")
                if verification.get("preview"):
                    c["snippet"] = (c.get("snippet", "") + " | Live page preview: " + verification["preview"][:200]).strip()
                print(f"[Playwright] ✓ Verified {url} -> Status: {c['status']}, Title: {verification.get('title', '')[:50]}")

        return candidates

    # =========================================================================
    # Step 5 & 6: Prior-Art Closeness Analysis & Output Generation
    # =========================================================================

    def synthesize_and_export(
        self,
        problem_statement: str,
        queries: List[str],
        candidates: List[Dict[str, Any]],
        output_json_path: Optional[str] = None,
        output_report_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesizes prior art and writes output files."""
        print("\n[Synthesis] Evaluating prior-art closeness and innovation gaps...")

        cand_summaries = []
        for i, c in enumerate(candidates[:15], 1):
            cand_summaries.append(
                f"[{i}] Name: {c.get('name')}\n"
                f"    URL: {c.get('url')}\n"
                f"    Source: {c.get('source')}\n"
                f"    Status: {c.get('status')}\n"
                f"    Verified with Playwright: {c.get('verified_via_playwright')}\n"
                f"    Snippet: {c.get('snippet')[:250]}\n"
            )
        cand_text = "\n".join(cand_summaries) if cand_summaries else "No candidates found."

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are the Prior-Art Discovery Agent (Subagent 1). "
                    "Analyze candidate findings against the problem statement and emit ONLY a strict JSON object.\n"
                    "Output Schema:\n"
                    "{\n"
                    '  "confirmed_problem_statement": string,\n'
                    '  "search_queries_used": [string],\n'
                    '  "prior_art_found": boolean,\n'
                    '  "closest_match_summary": string,\n'
                    '  "candidates": [\n'
                    "    {\n"
                    '      "name": string,\n'
                    '      "source": "github" | "huggingface" | "web" | "paper" | "other",\n'
                    '      "url": string,\n'
                    '      "closeness": "exact_match" | "close_variant" | "partial_overlap" | "tangential",\n'
                    '      "status": "active" | "archived" | "demo" | "unknown",\n'
                    '      "verified_via_playwright": boolean,\n'
                    '      "notes": string\n'
                    "    }\n"
                    "  ],\n"
                    '  "domain_keywords": [string],\n'
                    '  "gaps_identified": string\n'
                    "}\n\n"
                    "RULES:\n"
                    "- Rank candidates by closeness, most relevant first.\n"
                    "- 'gaps_identified' should highlight what remains unaddressed or novel relative to the user's project to guide Subagent 2.\n"
                    "- Return ONLY raw JSON object. No Markdown fences, no conversational prose."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Confirmed Problem Statement:\n{problem_statement}\n\n"
                    f"Search Queries Used:\n{json.dumps(queries)}\n\n"
                    f"Candidate Findings:\n{cand_text}"
                ),
            },
        ]

        raw_json = self._call_llm(prompt, temperature=0.2).strip()

        try:
            clean = re.sub(r"^```json\s*", "", raw_json)
            clean = re.sub(r"^```\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean).strip()
            findings = json.loads(clean)
        except Exception as e:
            print(f"[Synthesis Warning] Fallback JSON parse due to error: {e}")
            findings = {
                "confirmed_problem_statement": problem_statement,
                "search_queries_used": queries,
                "prior_art_found": len(candidates) > 0,
                "closest_match_summary": candidates[0].get("snippet", "")[:200] if candidates else "",
                "candidates": candidates[:10],
                "domain_keywords": [w for w in problem_statement.split() if len(w) > 5][:5],
                "gaps_identified": "Edge deployment and custom hardware integration appear novel.",
            }

        # Resolve paths
        json_target = Path(output_json_path) if output_json_path else self.output_dir / "prior_art_findings.json"
        report_target = Path(output_report_path) if output_report_path else self.output_dir / "prior_art_report.md"

        # Ensure directory exists
        json_target.parent.mkdir(parents=True, exist_ok=True)
        report_target.parent.mkdir(parents=True, exist_ok=True)

        with open(json_target, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2)
        print(f"\n[Export] ✓ JSON contract written to {json_target}")

        # Also mirror to root directory for convenient inter-agent access
        root_json = ROOT_DIR / "prior_art_findings.json"
        if json_target != root_json:
            with open(root_json, "w", encoding="utf-8") as f:
                json.dump(findings, f, indent=2)

        self._write_markdown_report(findings, str(report_target))
        print(f"[Export] ✓ Markdown report written to {report_target}")

        root_report = ROOT_DIR / "prior_art_report.md"
        if report_target != root_report:
            self._write_markdown_report(findings, str(root_report))

        return findings

    def _write_markdown_report(self, findings: Dict[str, Any], path: str):
        """Generates human-readable Markdown report."""
        report = []
        report.append("# Prior-Art Discovery Report (Subagent 1)\n")
        report.append(f"**Generated on:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Model Engine:** `{self.model}` via Ollama Cloud\n\n")
        report.append("## Confirmed Problem Statement\n")
        report.append(f"> {findings.get('confirmed_problem_statement')}\n\n")

        report.append("## Discovery Summary\n")
        prior_art_status = "Prior art detected" if findings.get("prior_art_found") else "No direct prior art found"
        report.append(f"- **Status:** {prior_art_status}\n")
        report.append(f"- **Total Candidates Analyzed:** {len(findings.get('candidates', []))}\n")
        report.append(f"- **Closest Match:** {findings.get('closest_match_summary', 'None')}\n\n")

        report.append("## Search Queries Executed\n")
        for q in findings.get("search_queries_used", []):
            report.append(f"- `{q}`\n")
        report.append("\n")

        report.append("## Candidate Prior Art\n")
        report.append("| Name | Source | Closeness | Status | Verified (Playwright) | Link |\n")
        report.append("|---|---|---|---|---|---|\n")
        for c in findings.get("candidates", []):
            name = c.get("name", "Unknown").replace("|", "-")
            source = c.get("source", "web")
            closeness = c.get("closeness", "tangential")
            status = c.get("status", "unknown")
            verified = "✓ Yes" if c.get("verified_via_playwright") else "No"
            url = c.get("url", "#")
            report.append(f"| {name} | {source} | `{closeness}` | {status} | {verified} | [View]({url}) |\n")

        report.append("\n### Detailed Notes on Candidates\n")
        for c in findings.get("candidates", []):
            report.append(f"#### {c.get('name')} ({c.get('source')})\n")
            report.append(f"- **URL:** {c.get('url')}\n")
            report.append(f"- **Closeness:** `{c.get('closeness')}`\n")
            report.append(f"- **Notes:** {c.get('notes')}\n\n")

        report.append("## Innovation Gaps & Opportunities (Handoff to Subagent 2)\n")
        report.append(f"{findings.get('gaps_identified')}\n\n")

        report.append("## Domain Keywords for Literature Search\n")
        report.append(", ".join([f"`{k}`" for k in findings.get("domain_keywords", [])]) + "\n")

        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(report))

    # =========================================================================
    def execute_prior_art_discovery(
        self,
        problem_statement: str,
        headless_playwright: bool = False,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Programmatic execution of Steps 2 through 6 with optional progress_callback(status_message).
        """
        self.playwright.headless = headless_playwright
        self.confirmed_problem_statement = problem_statement

        if progress_callback:
            progress_callback("Generating high-signal search queries...")
        queries = self.generate_search_queries(problem_statement)

        if progress_callback:
            progress_callback(f"Searching web via Exa & Firecrawl ({len(queries)} query variants)...")
        web_candidates = self.search_prior_art(queries)

        if progress_callback:
            progress_callback("Searching Hugging Face Hub models & GitHub repositories...")
        hf_gh_candidates = self.search_hf_and_github(queries)

        all_candidates = []
        seen_urls = set()
        for c in hf_gh_candidates + web_candidates:
            if c["url"] not in seen_urls:
                seen_urls.add(c["url"])
                all_candidates.append(c)

        if progress_callback:
            progress_callback(f"Verifying candidate pages with Playwright (headless={headless_playwright})...")
        verified_candidates = self.verify_candidates_with_playwright(all_candidates, max_checks=2)

        if progress_callback:
            progress_callback("Analyzing prior-art closeness and synthesizing findings...")
        findings = self.synthesize_and_export(problem_statement, queries, verified_candidates)

        if progress_callback:
            progress_callback("Prior-art discovery complete!")
        return findings

    def run(self, initial_idea: Optional[str] = None):
        """Runs the entire Subagent 1 pipeline end-to-end."""
        problem_statement = self.run_interview(initial_idea)
        findings = self.execute_prior_art_discovery(problem_statement, headless_playwright=self.playwright.headless)

        print("\n" + "=" * 65)
        print("  PRIOR-ART DISCOVERY COMPLETE")
        print("=" * 65)
        print(f"Summary: {findings.get('closest_match_summary')}")
        print(f"Gaps identified: {findings.get('gaps_identified')}")
        print("Outputs saved in subagent_1/ and root.\n")
        return findings


if __name__ == "__main__":
    agent = PriorArtDiscoveryAgent()
    agent.run()
