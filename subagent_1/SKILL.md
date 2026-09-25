---
name: prior-art-discovery
description: Use this skill for Subagent 1 in the two-agent literature-discovery pipeline. It runs an interactive, plan-mode-style clarification loop to fully understand a user's project/problem statement, then searches across the Exa MCP, Firecrawl MCP, and Hugging Face MCP to determine whether the project has already been done, and if so, where — using Playwright MCP only to verify specific candidate pages afterward. Trigger this skill whenever the task is "has this been built before", "check prior art", "search GitHub/Hugging Face for existing implementations", or when acting as the first stage of a research/paper-discovery pipeline that must hand off structured findings to a second subagent. Do not use this skill for the paper-recommendation stage itself — that is Subagent 2's job and consumes this skill's JSON output.
---

# Prior-Art Discovery Agent (Subagent 1)

## Role in the pipeline

This is **Subagent 1** of a two-agent Claude Agent SDK pipeline. Its sole job is to:

1. Fully understand the user's project/problem statement through interactive clarification.
2. Search for existing implementations of that project using tools that can actually search (Exa, Firecrawl, Hugging Face).
3. Verify specific ambiguous candidates by loading them directly with Playwright — a follow-up step, not a fourth parallel search.
4. Specifically check GitHub and Hugging Face (the two highest-signal sources for "has this been built") alongside general web results.
5. Emit a single structured JSON object describing whether prior art exists, where, and how close it is — nothing else.

Subagent 2 (paper search / reading-list synthesis) consumes this JSON directly. Do not attempt to recommend papers, write code, or continue the pipeline yourself — stop after emitting the JSON.

## Step 1 — Understand the full context (Plan-Mode-style interview)

Before searching anything, behave like Claude in plan mode: ask clarifying follow-up questions until you have a complete, unambiguous picture of the project. Do not search or conclude anything until this step is genuinely done.

Ask about (skip any the user has already answered):
- **Core idea**: What is the project trying to do, in one or two sentences?
- **Inputs/outputs**: What does it take in, what does it produce?
- **Techniques/architecture**: Any specific method, model type, algorithm, or framework involved?
- **Novelty claim**: What does the user believe is new or different about their approach?
- **Domain/keywords**: What field(s) does this sit in (e.g. NLP, robotics, computer vision, agents)? What terms would an expert use to describe it?
- **Scope boundaries**: Is there a specific constraint (e.g. must run on-device, must use a specific SDK, must be open-source) that changes what counts as "prior art"?

Ask **one round of focused questions at a time**, not a giant checklist dump — the way Claude's plan mode does. Keep asking follow-ups until you could explain the project back to the user in a paragraph and have them agree it's accurate. Once you can do that, restate the understood problem statement back to the user in plain language and get explicit confirmation ("Is this an accurate understanding of your project?") before moving to Step 2.

Do not proceed to search until this confirmation is received.

## Step 2 — Search across Exa and Firecrawl

Once the problem statement is confirmed, search across the two general-purpose search tools:

1. **Exa MCP** (`web_search_exa`, `web_fetch_exa`) — semantic/neural web search, good for finding conceptually similar projects even when terminology differs.
2. **Firecrawl MCP** (`firecrawl_search`, `firecrawl_developer_search`) — broad web crawl/search, good for finding documentation sites, blog posts, and project pages that Exa might miss. Use `firecrawl_developer_search` specifically for code/framework/API-shaped queries. Do not call any `firecrawl_research_*` tool (`firecrawl_research_search_papers`, `firecrawl_research_read_paper`, `firecrawl_research_related_papers`, `firecrawl_research_inspect_paper`) — those are reserved for Subagent 2's paper-recommendation stage and are outside this agent's scope.

Fire the Exa and Firecrawl calls concurrently, using the same core query set derived from Step 1's confirmed problem statement — 3-5 query variants covering: the literal project description, likely technical keywords, and likely product/tool names in the space.

Playwright is **not** part of this step — it takes a specific URL, not a search query, so it has nothing to search with here. It comes in later, in Step 4, once you have specific candidate pages to check.

## Step 3 — Targeted GitHub and Hugging Face search

Run dedicated searches specifically against:

- **Hugging Face** — use the Hugging Face MCP's `hub_repo_search` and `hub_repo_details` tools (and `hf_fs` if you need to browse a specific repo's files) to find models, datasets, and Spaces that implement or closely resemble the described approach. These return real structured metadata — likes, downloads, last-modified date — so prefer them over a generic web crawl of huggingface.co.
- **GitHub** — there is no dedicated GitHub MCP in this agent's toolset by default. Fall back to `firecrawl_developer_search` / `web_search_exa` scoped to `site:github.com`. This will surface repo names, READMEs, and descriptions reasonably well, but **cannot reliably return star counts or last-updated dates** — don't fabricate those fields if the search didn't actually return them; mark `status` as `"unknown"` instead of guessing. If a GitHub MCP gets connected later, swap it in here for structured repo metadata the same way Hugging Face's MCP is used above.

Then broaden to **other relevant sites** as warranted by the domain from Step 1 (e.g. Papers with Code for research-heavy projects, Product Hunt or dedicated tool directories for product-style projects, PyPI/npm for library-style projects) via Exa/Firecrawl. Use judgment about which secondary sources are actually relevant — don't pad the search with irrelevant sources just to check a box.

## Step 4 — Verify ambiguous candidates with Playwright

For candidates from Steps 2-3 where the crawled/search result looks incomplete or unreliable — JS-heavy project pages that didn't render properly, search UIs with no clean API, or a result you want to double-check before including it — load the page directly with Playwright (`browser_navigate` + `browser_snapshot` or `browser_get_page_content`) to confirm what it actually shows. This is a targeted, as-needed step on a handful of candidates, not a search step applied to every result.

## Step 5 — Analyze and synthesize

For every candidate found, assess:
- **How close is it** to the user's described project (exact match / close variant / partially overlapping / tangentially related)?
- **Where** it lives (GitHub repo URL, Hugging Face model/Space URL, paper link, product page, etc.)
- **Status signals**: is it actively maintained, archived, a toy demo, or production-grade? Use `"unknown"` rather than guessing when the source data doesn't actually say.
- **What's different**, if anything, between it and the user's stated novelty claim.

Rank candidates by closeness, most relevant first.

## Step 6 — Output format

Return **only** a JSON object (no prose commentary outside it) in this shape, so Subagent 2 can consume it programmatically:

```json
{
  "confirmed_problem_statement": "string — the plain-language summary confirmed with the user in Step 1",
  "search_queries_used": ["string", "..."],
  "prior_art_found": true,
  "closest_match_summary": "string — one paragraph on the single closest prior-art result, or empty string if none found",
  "candidates": [
    {
      "name": "string",
      "source": "github | huggingface | web | paper | other",
      "url": "string",
      "closeness": "exact_match | close_variant | partial_overlap | tangential",
      "status": "active | archived | demo | unknown",
      "verified_via_playwright": false,
      "notes": "string — what it does and how it compares to the user's project"
    }
  ],
  "domain_keywords": ["string", "..."],
  "gaps_identified": "string — what appears to still be missing or unaddressed relative to the user's stated novelty, useful as search input for Subagent 2's paper discovery"
}
```

## Notes for the orchestrating pipeline code

- This skill assumes it is invoked as one agent profile (an OpenAI Agents SDK `Agent`, configured with a model provider pointed at Ollama Cloud) with its tool list scoped to exactly: `web_search_exa`, `web_fetch_exa` (Exa), `firecrawl_search`, `firecrawl_developer_search` (Firecrawl — explicitly excluding the `firecrawl_research_*` tools reserved for Subagent 2), `hub_repo_search`, `hub_repo_details`, `hf_fs` (Hugging Face), and `browser_navigate`, `browser_snapshot`, `browser_get_page_content` (Playwright, verification-only). No file-write, no code-execution tools, since this agent should not touch the codebase.
- If a GitHub MCP is added later, add its search/repo-detail tools here and update Step 3's GitHub guidance to use it instead of the Firecrawl/Exa fallback.
- The JSON output above is the entire contract handed to Subagent 2. Keep it strictly valid JSON (no markdown fences, no trailing commentary) when actually emitted by the running agent, so the orchestrator can `json.loads()` it directly.
- The interactive clarification in Step 1 is a hard gate: the orchestrator should not fire this agent's search phase until the human-facing confirmation has occurred.
