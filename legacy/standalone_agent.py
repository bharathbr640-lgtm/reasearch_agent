import sys
from agent_manager import ResearchAgentManager
from utils import load_env_vars

def check_connectivity(manager):
    print("\n--- Connectivity Check ---")

    # Test Ollama
    try:
        res = manager.llm.chat([{"role": "user", "content": "Hi"}])
        print(f"✅ Ollama: Working (Response: {res[:20]}...)")
    except Exception as e:
        print(f"❌ Ollama: Failed ({e})")

    # Test Exa
    try:
        res = manager.exa.search("test connectivity")
        if res:
            print(f"✅ Exa: Working (Found {len(res)} results)")
        else:
            print("⚠️ Exa: Connected but returned no results")
    except Exception as e:
        print(f"❌ Exa: Failed ({e})")

    # Test Firecrawl
    try:
        # Use a reliable URL for testing
        res = manager.firecrawl.scrape("https://example.com")
        if res:
            print(f"✅ Firecrawl: Working (Scraped content length: {len(res)})")
        else:
            print("⚠️ Firecrawl: Connected but returned no content")
    except Exception as e:
        print(f"❌ Firecrawl: Failed ({e})")
    print("--------------------------\n")

def main():
    print("--- Standalone Research Agent (Direct Access) ---")
    print("Commands: '/test' to check connectivity, 'exit' to quit.")

    try:
        manager = ResearchAgentManager()
    except Exception as e:
        print(f"Error initializing manager: {e}")
        sys.exit(1)

    while True:
        query = input("\nAsk me anything or use a command:\n> ").strip()

        if not query:
            continue

        if query.lower() == 'exit':
            print("Goodbye!")
            break

        if query.lower() == '/test':
            check_connectivity(manager)
            continue

        print("\nSearching and synthesizing answer... please wait...")
        try:
            # Use the established Exa -> Firecrawl -> Ollama pipeline
            answer = manager.run_research(query)
            print("\n--- Answer ---")
            print(answer)
            print("\n----------------")
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
