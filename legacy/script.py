#!/usr/bin/env python3
"""
A chatbot script that talks to Ollama Cloud API with access to
Firecrawl MCP and Exa MCP tools. Supports explicit routing:
- "Use Factual MCP for this task" (or Firecrawl MCP)
- "Use Hexa MCP for this task" (or Exa MCP)
"""

import os
import re
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

# Ollama Cloud API (OpenAI-compatible endpoint)
client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key=OLLAMA_API_KEY,
    timeout=60.0,
)
DEFAULT_MODEL = "gpt-oss:120b"

# ==========================================
# Tool Definitions
# ==========================================

FIRECRAWL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "firecrawl_scrape",
            "description": "Scrape a single web page and return its clean markdown content. Use for reading a specific article, doc page, or URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to scrape"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "firecrawl_search",
            "description": "Search the web for pages and articles using Firecrawl search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query keywords"},
                    "limit": {"type": "integer", "description": "Number of results to return", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "firecrawl_map",
            "description": "Map and discover all indexed URLs on a domain or website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Base website domain (e.g. https://example.com)"},
                    "limit": {"type": "integer", "description": "Max URLs to return", "default": 10},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "firecrawl_crawl",
            "description": "Crawl an entire website starting from a URL. Use for gathering content across many pages of a site.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The starting URL to crawl"},
                    "max_depth": {"type": "integer", "description": "Max pages to crawl", "default": 2},
                },
                "required": ["url"],
            },
        },
    },
]

EXA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search_exa",
            "description": "Search the web for relevant documents, news, and knowledge using Exa AI neural search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch_exa",
            "description": "Read and extract full webpage contents as clean Markdown from URLs using Exa MCP crawler.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to fetch",
                    },
                    "max_characters": {"type": "integer", "description": "Max characters per page", "default": 3000},
                },
                "required": ["urls"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exa_search",
            "description": "Search the web for relevant documents and knowledge using Exa AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]

ALL_TOOLS = FIRECRAWL_TOOLS + EXA_TOOLS


# ==========================================
# MCP Execution Handlers
# ==========================================

def call_firecrawl_scrape(url: str) -> str:
    """Call Firecrawl MCP to scrape a webpage."""
    if not FIRECRAWL_API_KEY:
        return json.dumps({"error": "FIRECRAWL_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        markdown = data.get("data", {}).get("markdown") or data.get("markdown") or ""
        if markdown:
            return markdown[:4000]
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": f"Firecrawl scrape failed: {str(e)}"})


def call_firecrawl_search(query: str, limit: int = 5) -> str:
    """Call Firecrawl MCP search."""
    if not FIRECRAWL_API_KEY:
        return json.dumps({"error": "FIRECRAWL_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://api.firecrawl.dev/v1/search",
            json={"query": query, "limit": limit},
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", {}).get("web", []) or data.get("data", [])
        return json.dumps(results[:limit], indent=2)
    except Exception as e:
        return json.dumps({"error": f"Firecrawl search failed: {str(e)}"})


def call_firecrawl_map(url: str, limit: int = 10) -> str:
    """Call Firecrawl MCP map."""
    if not FIRECRAWL_API_KEY:
        return json.dumps({"error": "FIRECRAWL_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://api.firecrawl.dev/v1/map",
            json={"url": url, "limit": limit},
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": f"Firecrawl map failed: {str(e)}"})


def call_firecrawl_crawl(url: str, max_depth: int = 2) -> str:
    """Call Firecrawl MCP crawl."""
    if not FIRECRAWL_API_KEY:
        return json.dumps({"error": "FIRECRAWL_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            json={"url": url, "maxDepth": max_depth, "limit": 3},
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": f"Firecrawl crawl failed: {str(e)}"})


def call_web_search_exa(query: str, num_results: int = 5) -> str:
    """Call Exa MCP neural web search."""
    if not EXA_API_KEY:
        return json.dumps({"error": "EXA_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {EXA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "numResults": num_results,
            "type": "neural",
            "contents": {"highlights": True}
        }
        resp = requests.post(
            "https://api.exa.ai/search",
            json=payload,
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return json.dumps(results[:num_results], indent=2)
    except Exception as e:
        return json.dumps({"error": f"Exa search failed: {str(e)}"})


def call_web_fetch_exa(urls: list, max_characters: int = 3000) -> str:
    """Call Exa MCP content fetching."""
    if not EXA_API_KEY:
        return json.dumps({"error": "EXA_API_KEY not configured in .env"})
    try:
        headers = {
            "Authorization": f"Bearer {EXA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "urls": urls if isinstance(urls, list) else [urls],
            "text": {"maxCharacters": max_characters}
        }
        resp = requests.post(
            "https://api.exa.ai/contents",
            json=payload,
            headers=headers,
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Exa fetch failed: {str(e)}"})


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Route a tool call to the correct MCP implementation."""
    # Firecrawl tools
    if tool_name == "firecrawl_scrape":
        return call_firecrawl_scrape(arguments.get("url", ""))
    elif tool_name == "firecrawl_search":
        return call_firecrawl_search(arguments.get("query", ""), arguments.get("limit", 5))
    elif tool_name == "firecrawl_map":
        return call_firecrawl_map(arguments.get("url", ""), arguments.get("limit", 10))
    elif tool_name == "firecrawl_crawl":
        return call_firecrawl_crawl(arguments.get("url", ""), arguments.get("max_depth", 2))

    # Exa tools
    elif tool_name in ["web_search_exa", "exa_search"]:
        return call_web_search_exa(arguments.get("query", ""), arguments.get("num_results", 5))
    elif tool_name == "web_fetch_exa":
        return call_web_fetch_exa(arguments.get("urls", []), arguments.get("max_characters", 3000))

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ==========================================
# MCP Preference & Routing
# ==========================================

def detect_mcp_routing(user_text: str) -> tuple[str, list | None, str | None]:
    """
    Detect explicit user commands:
    - If user does NOT ask for MCP (e.g. 'hi', 'hello', normal conversation) -> 'chat' mode (no tools attached)
    - If user says 'Use Factual MCP' (or Firecrawl) -> 'firecrawl' mode (Firecrawl tools only)
    - If user says 'Use Hexa MCP' (or Exa) -> 'exa' mode (Exa tools only)
    - If user says 'Use MCP' generally -> 'mcp_all' mode (both toolsets available)
    """
    lower = user_text.lower()

    # Check if the user explicitly triggered MCP
    has_mcp_trigger = any(
        kw in lower for kw in ["mcp", "use factual", "use firecrawl", "use hexa", "use exa"]
    )

    if not has_mcp_trigger:
        # Standard conversational mode: no tools attached
        return "chat", None, None

    # Check for specific provider requested
    is_firecrawl = bool(re.search(r"\b(use\s+)?(factual|firecrawl)\b", lower))
    is_exa = bool(re.search(r"\b(use\s+)?(hexa|exa)\b", lower))

    if is_firecrawl and not is_exa:
        return (
            "firecrawl",
            FIRECRAWL_TOOLS,
            "User explicitly requested Firecrawl / Factual MCP. Use ONLY Firecrawl tools (firecrawl_scrape, firecrawl_search, firecrawl_map, firecrawl_crawl) for this task."
        )
    elif is_exa and not is_firecrawl:
        return (
            "exa",
            EXA_TOOLS,
            "User explicitly requested Exa / Hexa MCP. Use ONLY Exa tools (web_search_exa, web_fetch_exa, exa_search) for this task."
        )
    else:
        # General 'use mcp' trigger
        return (
            "mcp_all",
            ALL_TOOLS,
            "User requested MCP tools. Both Firecrawl MCP (scraping, crawling, mapping) and Exa MCP (neural web search, page fetching) are available. Choose the best tool for the user's request."
        )


# ==========================================
# Main Chatbot Loop
# ==========================================

def chatbot():
    """Run the interactive chatbot loop."""
    print("=" * 60)
    print("🤖  AI Chatbot with Optional MCP Tools")
    print("    • Normal conversation: Just chat naturally ('hi', 'hello')")
    print("    • Explicit MCP triggers:")
    print("      - 'Use Factual MCP for this task' (Firecrawl)")
    print("      - 'Use Hexa MCP for this task' (Exa)")
    print("      - 'Use MCP for this task' (Both)")
    print("=" * 60)
    print("Type 'quit' or 'exit' to stop.\n")

    base_system_prompt = (
        "You are a helpful and intelligent AI assistant. In normal conversation, respond naturally and conversationally. "
        "When MCP tools are provided and requested, use them to gather real-time data, search the web, or scrape pages, "
        "and synthesize your answers accurately citing the retrieved information."
    )

    conversation_history = [{"role": "system", "content": base_system_prompt}]

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            if not user_input:
                continue

            # Determine MCP routing
            mode, active_tools, routing_instruction = detect_mcp_routing(user_input)

            # Build messages for this turn
            turn_messages = list(conversation_history)

            # Only show banners and inject routing instructions when MCP is explicitly triggered
            if mode == "firecrawl":
                print("\n🔥 [Firecrawl / Factual MCP Triggered]")
                turn_messages.append({"role": "system", "content": f"[Active MCP Policy: {routing_instruction}]"})
            elif mode == "exa":
                print("\n⚡ [Exa / Hexa MCP Triggered]")
                turn_messages.append({"role": "system", "content": f"[Active MCP Policy: {routing_instruction}]"})
            elif mode == "mcp_all":
                print("\n🌐 [MCP Tools Triggered: Firecrawl & Exa Available]")
                turn_messages.append({"role": "system", "content": f"[Active MCP Policy: {routing_instruction}]"})
            # In 'chat' mode, no banner is printed and no tool instructions are added

            turn_messages.append({"role": "user", "content": user_input})

            print("Thinking...", end="", flush=True)

            try:
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=turn_messages,
                    tools=active_tools if active_tools else None,
                    tool_choice="auto" if active_tools else None,
                )
            except Exception as e:
                print(f"\r❌ Error contacting Ollama API: {e}\n")
                continue

            message = response.choices[0].message
            print("\r", end="")  # Clear thinking indicator

            # Process tool calls in a loop
            call_count = 0
            while message.tool_calls and call_count < 5:
                call_count += 1
                turn_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                })

                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}

                    # Tag which provider is being executed
                    provider = "Firecrawl" if "firecrawl" in tool_name else "Exa"
                    print(f"[{provider} MCP: Executing {tool_name} with {args}]")

                    result = execute_tool(tool_name, args)

                    turn_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Re-query the model with tool execution output
                print("Synthesizing answer...", end="", flush=True)
                try:
                    response = client.chat.completions.create(
                        model=DEFAULT_MODEL,
                        messages=turn_messages,
                        tools=active_tools if active_tools else None,
                        tool_choice="auto" if active_tools else None,
                    )
                    message = response.choices[0].message
                    print("\r", end="")
                except Exception as e:
                    print(f"\r❌ Error during tool synthesis: {e}\n")
                    break

            final_reply = message.content or ""
            print(f"Bot: {final_reply}\n")

            # Preserve the exchange in history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": final_reply})

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}\n")


if __name__ == "__main__":
    chatbot()