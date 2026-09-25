# Curated Academic Reading List (Subagent 2)
**Generated on:** 2026-09-14 14:13:15
**Model Engine:** `gpt-oss:120b` via Ollama Cloud

## Research Context & Objectives
> **Confirmed Problem:** The project is a locally hosted price‑comparison agent that takes a list of product URLs as input and returns a ranked list of vendors showing each vendor’s price, shipping cost, and a direct purchase link. It will first try public vendor APIs for price data and fall back to web‑scraping (using tools such as Playwright or BeautifulSoup) when APIs are unavailable. An LLM running on the user’s local server via Ollama will be employed to normalize product titles and perform enhanced product‑matching across sites, ensuring that the same item is compared even when descriptions differ. The novelty lies in the LLM‑driven matching layer that improves accuracy over traditional string‑based methods. The solution targets the e‑commerce domain, using open‑source libraries and a self‑hosted LLM to respect privacy and run entirely on the user’s local server.

> **Target Gaps Identified by Subagent 1:** No discovered open‑source project fully combines: (1) a self‑hosted LLM via Ollama for product‑title normalization, (2) automatic fallback to Playwright/BeautifulSoup scraping when vendor APIs are missing, (3) extraction of shipping costs, and (4) a ranking engine that outputs a vendor‑wise price list with direct purchase links. Existing tools either lack the LLM‑driven matching layer, omit Ollama integration, or do not provide end‑to‑end price aggregation and ranking. These missing pieces define the novel contribution for the proposed agent.

## Search Queries Used
- `LLM‑driven product title normalization for e‑commerce price comparison using self‑hosted models`
- `Integration of Ollama self‑hosted large language models with web‑scraping fallback (Playwright/BeautifulSoup) for vendor API missing cases`
- `Automated extraction of shipping costs from e‑commerce webpages via hybrid LLM and scraping techniques`
- `Hybrid API‑plus‑scraping architecture with ranking engine for vendor‑wise price and shipping aggregation`

## Top 5 Ranked Academic Papers

### #1. [Using LLMs for the Extraction and Normalization of Product Attribute Values](https://arxiv.org/abs/2403.02130)
- **Authors:** Alexander Brinkmann; Nick Baumann; Christian Bizer
- **Year:** 2024
- **Link / DOI:** [https://arxiv.org/abs/2403.02130](https://arxiv.org/abs/2403.02130)
- **Relevance to Identified Gaps:** Directly addresses Subagent 1's missing LLM‑driven product‑title normalization layer by presenting a concrete LLM‑based pipeline for extracting and normalizing attribute values from noisy e‑commerce titles, which can be adapted to run on a self‑hosted Ollama model.

### #2. [Webscraper: Leverage Multimodal Large Language Models for Index-Content Web Scraping](https://arxiv.org/abs/2603.29161)
- **Authors:** Unknown
- **Year:** 2026
- **Link / DOI:** [https://arxiv.org/abs/2603.29161](https://arxiv.org/abs/2603.29161)
- **Relevance to Identified Gaps:** Provides a detailed framework for LLM‑augmented, dynamic web‑scraping that can serve as the automatic fallback to Playwright/BeautifulSoup when vendor APIs are unavailable, exactly filling the scraping‑fallback gap identified by Subagent 1.

### #3. [AXE: Low-Cost Cross-Domain Web Structured Information Extraction](https://arxiv.org/abs/2602.01838)
- **Authors:** Unknown
- **Year:** 2026
- **Link / DOI:** [https://arxiv.org/abs/2602.01838](https://arxiv.org/abs/2602.01838)
- **Relevance to Identified Gaps:** Introduces a cost‑effective pipeline for extracting structured fields (price, shipping cost, purchase link) from arbitrary e‑commerce pages, directly solving the shipping‑cost extraction and link‑harvesting components missing in the current open‑source landscape.

### #4. [Method for Aggregating Unstructured Data Using Large Language Models](https://arxiv.org/abs/2604.16425)
- **Authors:** Unknown
- **Year:** 2026
- **Link / DOI:** [https://arxiv.org/abs/2604.16425](https://arxiv.org/abs/2604.16425)
- **Relevance to Identified Gaps:** Describes an LLM‑centric aggregation engine that consolidates heterogeneous product data into a ranked list, matching Subagent 1's requirement for a vendor‑wise price ranking module with direct purchase links.

### #5. [EPM-RL: Reinforcement Learning for On-Premise Product Mapping in E-Commerce](https://arxiv.org/abs/2604.23993)
- **Authors:** Minhyeong Yu; Wonduk Seo
- **Year:** 2026
- **Link / DOI:** [https://arxiv.org/abs/2604.23993](https://arxiv.org/abs/2604.23993)
- **Relevance to Identified Gaps:** Presents a reinforcement‑learning approach for on‑premise product mapping that outperforms heuristic string matching, offering a concrete algorithm to enhance the LLM‑driven matching layer envisioned in Subagent 1.

