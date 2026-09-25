import os
import json
import time
import requests
from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv()

class ExaResearcher:
    """
    Exa neural/semantic web searcher for discovering conceptually similar projects.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EXA_API_KEY")

    def search(self, query: str, num_results: int = 5):
        """Perform semantic/neural web search via Exa."""
        if not self.api_key:
            return []
        try:
            resp = requests.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={"query": query, "numResults": num_results},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "name": item.get("title") or item.get("url"),
                        "url": item.get("url"),
                        "snippet": item.get("text", ""),
                        "source": "web" if "github.com" not in item.get("url", "") else "github",
                    })
                return results
            else:
                print(f"Exa search error {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            print(f"Exa search exception: {e}")
            return []

    def fetch(self, url: str):
        """Fetch content using Exa."""
        if not self.api_key:
            return ""
        try:
            resp = requests.post(
                "https://api.exa.ai/contents",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={"urls": [url]},
                timeout=15,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return results[0].get("text", "")
            return ""
        except Exception as e:
            print(f"Exa fetch error: {e}")
            return ""

    def search_academic_preprints(self, query: str, num_results: int = 5):
        """Search academic preprints and papers on arXiv, OpenReview, bioRxiv."""
        if not self.api_key:
            return []
        try:
            resp = requests.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "numResults": num_results,
                    "includeDomains": ["arxiv.org", "openreview.net", "biorxiv.org", "medrxiv.org", "semanticscholar.org"],
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title") or item.get("url"),
                        "url_or_doi": item.get("url"),
                        "snippet": item.get("text", "")[:300],
                        "source": "paper",
                        "authors": "Unknown",
                        "year": "Recent",
                    })
                return results
            return []
        except Exception as e:
            print(f"Exa preprint search error: {e}")
            return []


class FirecrawlResearcher:
    """
    Firecrawl web crawler and developer searcher.
    Note: Does NOT call firecrawl_research_* tools reserved for Subagent 2.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")

    def search(self, query: str, limit: int = 5):
        """Search the web for pages and articles using Firecrawl."""
        if not self.api_key:
            return []
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                "https://api.firecrawl.dev/v1/search",
                json={"query": query, "limit": limit},
                headers=headers,
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                res_data = data.get("data", [])
                if isinstance(res_data, dict):
                    raw_results = res_data.get("web", []) or res_data.get("results", [])
                elif isinstance(res_data, list):
                    raw_results = res_data
                else:
                    raw_results = []
                results = []
                for item in raw_results[:limit]:
                    url = item.get("url", "")
                    results.append({
                        "name": item.get("title") or url,
                        "url": url,
                        "snippet": item.get("description") or item.get("markdown", "")[:300],
                        "source": "github" if "github.com" in url else "web",
                    })
                return results
            else:
                print(f"Firecrawl search error {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            print(f"Firecrawl search exception: {e}")
            return []

    def developer_search(self, query: str, limit: int = 5):
        """Developer-oriented search specifically for code, frameworks, and APIs."""
        # Use technical code & GitHub qualifiers
        augmented_query = f"{query} site:github.com OR site:gitlab.com OR documentation"
        return self.search(augmented_query, limit=limit)

    def scrape(self, url: str):
        """Scrape a single URL for clean markdown content."""
        if not self.api_key:
            return ""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                json={"url": url, "formats": ["markdown"]},
                headers=headers,
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("markdown") or data.get("markdown", "")
            return ""
        except Exception as e:
            print(f"Firecrawl scrape error for {url}: {e}")
            return ""


class HuggingFaceResearcher:
    """
    Hugging Face hub researcher for models, spaces, and datasets with structured metadata.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        self.api = HfApi(token=self.api_key)

    def search(self, query: str, limit: int = 5):
        """Search models and spaces on Hugging Face."""
        results = []
        try:
            # Search models
            models = list(self.api.list_models(search=query, limit=limit))
            for m in models:
                results.append({
                    "name": m.id,
                    "source": "huggingface",
                    "url": f"https://huggingface.co/{m.id}",
                    "likes": getattr(m, "likes", 0),
                    "downloads": getattr(m, "downloads", 0),
                    "last_modified": str(getattr(m, "last_modified", "unknown")),
                    "snippet": f"Hugging Face Model by {m.author or m.id.split('/')[0]} (Likes: {getattr(m, 'likes', 0)}, Downloads: {getattr(m, 'downloads', 0)})",
                })
        except Exception as e:
            print(f"HuggingFace model search error: {e}")

        try:
            # Search spaces
            spaces = list(self.api.list_spaces(search=query, limit=limit))
            for s in spaces:
                results.append({
                    "name": s.id,
                    "source": "huggingface",
                    "url": f"https://huggingface.co/spaces/{s.id}",
                    "likes": getattr(s, "likes", 0),
                    "last_modified": str(getattr(s, "last_modified", "unknown")),
                    "snippet": f"Hugging Face Space by {s.author or s.id.split('/')[0]} (Likes: {getattr(s, 'likes', 0)})",
                })
        except Exception as e:
            print(f"HuggingFace space search error: {e}")

        return results[:limit]

    def get_details(self, repo_id: str, repo_type: str = "model"):
        """Fetch repo info from Hugging Face."""
        try:
            if repo_type == "model":
                info = self.api.model_info(repo_id)
                return {
                    "id": info.id,
                    "downloads": getattr(info, "downloads", 0),
                    "likes": getattr(info, "likes", 0),
                    "tags": getattr(info, "tags", []),
                }
            elif repo_type == "space":
                info = self.api.space_info(repo_id)
                return {
                    "id": info.id,
                    "likes": getattr(info, "likes", 0),
                }
        except Exception as e:
            print(f"HuggingFace details error: {e}")
            return {}


class PlaywrightVerifier:
    """
    Playwright browser verifier for targeted candidate inspection.
    Configured for visible headed mode so the user can watch the verification live.
    """
    def __init__(self, headless: bool = False):
        self.headless = headless

    def verify_candidate(self, url: str, wait_seconds: int = 2):
        """
        Loads the candidate page in a visible browser window, extracts text and title,
        and verifies if it is an active/valid implementation.
        """
        from playwright.sync_api import sync_playwright

        result = {
            "url": url,
            "title": "",
            "preview": "",
            "verified": False,
            "status": "unknown",
            "error": None,
        }

        print(f"\n[Playwright] Opening browser (headed={not self.headless}) to inspect candidate: {url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                time.sleep(wait_seconds)  # Allow user to see the page render
                
                title = page.title()
                content = page.inner_text("body")[:1000].strip()
                
                result["title"] = title
                result["preview"] = content[:300]
                result["verified"] = True
                
                # Check status signals
                lower_content = content.lower()
                if "404" in title.lower() or "not found" in lower_content:
                    result["status"] = "archived"
                elif "archived" in lower_content:
                    result["status"] = "archived"
                elif "demo" in lower_content or "prototype" in lower_content:
                    result["status"] = "demo"
                else:
                    result["status"] = "active"

        except Exception as e:
            print(f"[Playwright] Verification warning for {url}: {e}")
            result["error"] = str(e)

        return result


class FirecrawlPaperResearcher:
    """
    Dedicated academic research paper client leveraging Firecrawl's research tools:
    - firecrawl_research_search_papers
    - firecrawl_research_inspect_paper
    - firecrawl_research_related_papers
    - firecrawl_research_read_paper
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")

    async def _call_tool_async(self, tool_name: str, arguments: dict) -> str:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import os

        params = StdioServerParameters(
            command="npx",
            args=["-y", "firecrawl-mcp"],
            env={**os.environ, "FIRECRAWL_API_KEY": self.api_key or ""}
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(tool_name, arguments)
                if res.content and len(res.content) > 0:
                    return res.content[0].text
                return ""

    def _call_tool(self, tool_name: str, arguments: dict) -> str:
        import asyncio
        try:
            return asyncio.run(self._call_tool_async(tool_name, arguments))
        except Exception as e:
            print(f"[FirecrawlPaper] Tool {tool_name} error: {e}")
            return ""

    def _parse_url(self, paper_id: str) -> str:
        if paper_id.startswith("pmid:"):
            return f"https://pubmed.ncbi.nlm.nih.gov/{paper_id.replace('pmid:', '')}/"
        elif paper_id.startswith("pmcid:"):
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper_id.replace('pmcid:', '')}/"
        elif paper_id.startswith("arxiv:"):
            return f"https://arxiv.org/abs/{paper_id.replace('arxiv:', '')}"
        elif paper_id.startswith("doi:"):
            return f"https://doi.org/{paper_id.replace('doi:', '')}"
        return f"https://semanticscholar.org/paper/{paper_id}"

    def search_papers(self, query: str, k: int = 10) -> list:
        """Search academic paper metadata and abstracts with natural language query."""
        import re
        raw = self._call_tool("firecrawl_research_search_papers", {"query": query, "k": k})
        if not raw:
            return []
        papers = []
        blocks = raw.split("## [")
        for b in blocks:
            if not b.strip():
                continue
            m = re.match(r"^([^\]]+)\]\s*(\[[^\]]+\]|[^\n]+)\n+(.*)", b.strip(), re.DOTALL)
            if m:
                pid, title, abstract = m.groups()
                pid = pid.strip()
                title = title.strip().strip("[]")
                papers.append({
                    "paper_id": pid,
                    "title": title,
                    "abstract": abstract.strip(),
                    "url_or_doi": self._parse_url(pid),
                    "source": "paper",
                })
        return papers

    def inspect_paper(self, paper_id: str) -> dict:
        """Retrieve full metadata, authors, year, categories, and abstract for a paper ID."""
        import re
        raw = self._call_tool("firecrawl_research_inspect_paper", {"paperId": paper_id})
        if not raw:
            return {}

        title_m = re.search(r"^#\s*\[?([^\]\n]+)\]?", raw)
        title = title_m.group(1).strip() if title_m else ""

        authors_m = re.search(r"Authors:\s*([^\n]+)", raw)
        authors = authors_m.group(1).strip() if authors_m else "Unknown"

        dates_m = re.search(r"Dates:.*?(\b20\d{2}\b|\b19\d{2}\b)", raw)
        year = dates_m.group(1) if dates_m else "Recent"

        abstract_m = re.search(r"## Abstract\s*(.*)", raw, re.DOTALL)
        abstract = abstract_m.group(1).strip() if abstract_m else ""

        return {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract,
            "url_or_doi": self._parse_url(paper_id),
        }

    def get_related_papers(self, seed_ids: list, intent: str, k: int = 5, mode: str = "similar") -> list:
        """Traverse citation graph for related papers."""
        import re
        raw = self._call_tool("firecrawl_research_related_papers", {
            "seed_ids": seed_ids,
            "intent": intent,
            "k": k,
            "mode": mode,
        })
        if not raw:
            return []
        related = []
        blocks = raw.split("## [")
        for b in blocks:
            if not b.strip():
                continue
            m = re.match(r"^([^\]]+)\]\s*(\[[^\]]+\]|[^\n]+)\n+(.*)", b.strip(), re.DOTALL)
            if m:
                pid, title, abstract = m.groups()
                pid = pid.strip()
                title = title.strip().strip("[]")
                related.append({
                    "paper_id": pid,
                    "title": title,
                    "abstract": abstract.strip(),
                    "url_or_doi": self._parse_url(pid),
                    "source": "paper",
                })
        return related

    def read_paper(self, paper_id: str, question: str, k: int = 3) -> str:
        """Retrieve relevant in-body passages from paper."""
        return self._call_tool("firecrawl_research_read_paper", {
            "paperId": paper_id,
            "question": question,
            "k": k,
        })
