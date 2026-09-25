from llm import OllamaLLM
from researcher import FirecrawlResearcher, ExaResearcher
from utils import load_env_vars

class ResearchAgentManager:
    def __init__(self):
        env = load_env_vars()
        self.llm = OllamaLLM(env["OLLAMA_API_KEY"])
        self.firecrawl = FirecrawlResearcher(env["FIRECRAWL_API_KEY"])
        self.exa = ExaResearcher(env.get("EXA_API_KEY"))

    def get_follow_ups(self, user_idea, history):
        # Wraps the LLM logic to determine if we are ready or need more questions
        response = self.llm.generate_follow_ups(user_idea, history)
        is_ready = response.startswith("READY")
        clean_response = response.replace("READY", "").strip()
        return is_ready, clean_response

    def synthesize_problem(self, history):
        return self.llm.synthesize_problem(history)

    def run_research(self, problem_statement):
        # 1. Discovery Phase: Use Exa for high-quality discovery
        print("Executing Discovery Phase (Exa)...")
        discovery_results = self.exa.search(problem_statement)

        # 2. Extraction Phase: Use Firecrawl to scrape the results found by Exa
        print("Executing Extraction Phase (Firecrawl)...")
        all_content = []

        # Use URLs from Exa results
        urls_to_scrape = [res.get("url") for res in discovery_results if res.get("url")]

        # Fallback to Firecrawl search if Exa results are empty
        if not urls_to_scrape:
            print("Exa returned no results, falling back to Firecrawl search...")
            fc_search = self.firecrawl.search(problem_statement)
            urls_to_scrape = [res.get("url") for res in fc_search if res.get("url")]

        for url in urls_to_scrape:
            content = self.firecrawl.scrape(url)
            if content:
                all_content.append(f"Source: {url}\nContent: {content}")

        research_data = "\n\n".join(all_content)
        return self.llm.analyze_research(problem_statement, research_data)
