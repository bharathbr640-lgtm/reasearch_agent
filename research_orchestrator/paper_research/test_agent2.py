"""Comprehensive unit tests for Agent 2 (Research Paper Discovery and Evidence Collection Agent)."""

import asyncio
import json
import unittest
from pathlib import Path
import tempfile
import shutil

from paper_research.schema import (
    PaperFinding,
    PaperResearchFindings,
    DatasetInfo,
    ModelInfo,
    ExperimentsAndResults,
    CodeRepository,
)
from paper_research.tools import (
    PaperResearchContext,
    PaperRegistry,
    normalize_paper_identifiers,
    normalize_title,
    normalize_doi,
    _extract_sections,
    _find_matching_section,
    _find_matching_sections,
    _is_noise_heading,
    _is_noise_content,
    _clean_header_name,
    _search_research_papers_impl,
    _read_paper_full_text_impl,
    _find_in_text_impl,
    _search_paper_code_repository_impl,
    _save_paper_findings_impl,
)
from paper_research.run import _write_partial_findings
from agents import RunContextWrapper


class TestAgent2(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="agent2_test_"))
        self.session_id = "test-session-123"
        self.ctx = PaperResearchContext(
            session_id=self.session_id,
            output_dir=self.test_dir,
            research_spec_summary="Test problem specification",
            max_tool_calls=10,
        )
        self.wrapper = RunContextWrapper(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_normalize_paper_identifiers(self):
        # 1. PMCID
        ids_pmc = normalize_paper_identifiers("pmcid:PMC11679138")
        self.assertEqual(ids_pmc["pmcid"], "PMC11679138")
        self.assertEqual(ids_pmc["canonical_url"], "https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/")
        self.assertEqual(ids_pmc["paper_id"], "pmcid:PMC11679138")

        # 2. arXiv
        ids_arx = normalize_paper_identifiers("arxiv:2601.12109")
        self.assertEqual(ids_arx["arxiv_id"], "2601.12109")
        self.assertEqual(ids_arx["canonical_url"], "https://arxiv.org/abs/2601.12109")
        self.assertEqual(ids_arx["pdf_url"], "https://arxiv.org/pdf/2601.12109.pdf")
        self.assertEqual(ids_arx["paper_id"], "arxiv:2601.12109")

        # 3. DOI
        ids_doi = normalize_paper_identifiers("10.1038/s41598-026-60625-4")
        self.assertEqual(ids_doi["doi"], "10.1038/s41598-026-60625-4")
        self.assertEqual(ids_doi["canonical_url"], "https://doi.org/10.1038/s41598-026-60625-4")
        self.assertEqual(ids_doi["paper_id"], "doi:10.1038/s41598-026-60625-4")

        # 4. PMID
        ids_pmid = normalize_paper_identifiers("pmid:42420345")
        self.assertEqual(ids_pmid["pmid"], "42420345")
        self.assertEqual(ids_pmid["canonical_url"], "https://pubmed.ncbi.nlm.nih.gov/42420345/")

    def test_schema_instantiation_and_none_handling(self):
        data = {
            "title": "Robust Leaf Net",
            "authors": None,
            "year": None,
            "doi": None,
            "paper_url": None,
            "citation": None,
            "match_type": "exact",
            "dataset": {"name": "JMuBEN Dataset", "description": None, "source": None},
            "model": {"model_name": "MobileNetV3", "architecture": None},
            "experiments_and_results": {"reported_results": "98.5% accuracy", "evidence_location": None},
            "code_repository": {"url": None, "is_official": None},
            "limitations": None,
            "research_gap": None,
            "key_evidence": None,
            "source_urls": None,
        }
        pf = PaperFinding.model_validate(data)
        self.assertEqual(pf.match_type, "exact")
        self.assertEqual(pf.authors, [])
        self.assertEqual(pf.doi, "not found")
        self.assertEqual(pf.paper_url, "not found")
        self.assertEqual(pf.dataset.description, "not found")
        self.assertEqual(pf.experiments_and_results.evidence_location, "not found")

    def test_schema_instantiation_and_coercion(self):
        data = {
            "title": "Robust Leaf Net",
            "authors": "Alice Solo",
            "year": "2023",
            "doi": "10.1000/leaf",
            "paper_url": "https://example.com/leaf",
            "citation": "Solo, 2023",
            "match_type": "exact",
            "dataset": "JMuBEN Dataset 50k",
            "model": "MobileNetV3",
            "experiments_and_results": "98.5% test accuracy on test set",
            "code_repository": "https://github.com/example/leafnet",
            "key_evidence": "MobileNetV3 achieves 98.5% accuracy",
            "source_urls": "https://example.com/leaf",
        }
        pf = PaperFinding.model_validate(data)
        self.assertEqual(pf.match_type, "exact")
        self.assertEqual(pf.authors, ["Alice Solo"])
        self.assertEqual(pf.dataset.name, "JMuBEN Dataset 50k")
        self.assertEqual(pf.model.model_name, "MobileNetV3")
        self.assertEqual(pf.experiments_and_results.reported_results, "98.5% test accuracy on test set")
        self.assertEqual(pf.code_repository.url, "https://github.com/example/leafnet")

    def test_section_extraction_and_lengths(self):
        sample_md = """
# LeafLiteX Study
## Abstract
This study proposes a lightweight mobile model for leaf disease detection.
## Dataset
We collected 10,000 coffee leaf images from farms in Brazil and Colombia.
## Methodology
U-Net segmentation combined with quantized MobileNetV3 is deployed on Android.
## Experimental Results
Overall accuracy reaches 98.7% with an inference latency of 45ms.
## Limitations
Performance drops slightly under heavy occlusion or low-light conditions.
## Conclusion
The lightweight solution is viable for offline edge deployment.
"""
        sections = _extract_sections(sample_md)
        self.assertIn("abstract", sections)
        self.assertIn("dataset", sections)
        self.assertIn("methodology", sections)
        self.assertIn("experimental results", sections)
        self.assertIn("limitations", sections)

        # Method extraction up to 6000 chars
        content, sec_found = _find_matching_section(sections, "method", sample_md)
        self.assertIn("MobileNetV3", content)
        self.assertIn("methodology", sec_found.lower())

        # Results extraction
        res_content, sec_found = _find_matching_section(sections, "results", sample_md)
        self.assertIn("98.7%", res_content)

    async def test_read_under_500_chars_fails_and_records_failure(self):
        # A read under 500 characters must return FAILED and be recorded in failures
        self.ctx.paper_texts["https://example.com/tiny"] = "Short abstract only."
        res = await _read_paper_full_text_impl(self.wrapper, "https://example.com/tiny")
        self.assertIn("FAILED", res)
        self.assertIn("below the 500-character threshold", res)
        self.assertTrue(any(f["operation"] == "read_paper_full_text" for f in self.ctx.failures))

    async def test_step3_find_in_text_without_read_returns_error(self):
        # Calling find_in_text without reading full text first must return error
        res = _find_in_text_impl(self.wrapper, query="accuracy", paper_url_or_id="https://example.com/unread")
        self.assertIn("ERROR: No verified full-text", res)
        self.assertEqual(self.ctx.trace_calls[-1]["status"], "failed_no_full_text")

    async def test_find_in_text_searches_full_text(self):
        full_text = "Verified research study.\n\n" + ("The proposed edge detector has a parameter size of 4.2 MB and 98.1% accuracy.\n\n" * 15)
        rec = self.ctx.paper_registry.register_candidate(
            title="Edge Detector Study",
            paper_url="https://doi.org/10.1000/edgedetect",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)

        res = _find_in_text_impl(self.wrapper, query="4.2 MB", paper_url_or_id="https://doi.org/10.1000/edgedetect")
        self.assertIn("VERIFIED SEARCH RESULT", res)
        self.assertIn("4.2 MB", res)

        # Negative search
        res_neg = _find_in_text_impl(self.wrapper, query="nonexistent metric xyz", paper_url_or_id="https://doi.org/10.1000/edgedetect")
        self.assertIn("was NOT found in the verified full text", res_neg)

    async def test_step4_save_rejects_github_as_paper_and_cleans_placeholders(self):
        full_text = "Detailed paper text.\n\n" + ("Experiments show high performance.\n\n" * 20)
        rec = self.ctx.paper_registry.register_candidate(
            title="Real Coffee Paper",
            paper_url="https://example.com/test",
            doi="",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)
        self.ctx.search_queries_run = ["coffee leaf disease"]

        findings_input = [
            # 1. GitHub repo - should be rejected as paper
            {
                "title": "github.com/example/coffeerepo",
                "paper_url": "https://github.com/example/coffeerepo",
                "match_type": "closely_related",
            },
            # 2. Real paper with placeholder DOI and dataset link in code_repository
            {
                "title": "Real Coffee Paper",
                "paper_url": "https://example.com/test",
                "doi": "10.1109/XXXX.12345",  # Placeholder
                "citation": "pp. XXX-XXX",      # Placeholder
                "match_type": "closely_related",
                "code_repository": {
                    "url": "https://data.mendeley.com/datasets/xyz",  # Dataset link
                },
                "key_evidence": ["Experiments show high performance."],
            },
        ]

        msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf disease"],
            exact_research_found=False,
            findings=findings_input,
            notes="Audit test",
        )
        self.assertIn("Successfully saved", msg)

        # Inspect saved JSON
        saved_json = json.loads((self.test_dir / "paper_findings.json").read_text())
        self.assertEqual(len(saved_json["findings"]), 1)  # GitHub repo rejected
        f0 = saved_json["findings"][0]
        self.assertEqual(f0["title"], "Real Coffee Paper")
        self.assertEqual(f0["doi"], "not found")  # XXX rejected
        self.assertEqual(f0["citation"], "not found")  # XXX rejected
        self.assertEqual(f0["code_repository"]["url"], "not found")  # Dataset link stripped from code_repository
        self.assertEqual(f0["dataset"]["source"], "https://data.mendeley.com/datasets/xyz")  # Moved to dataset.source

    async def test_step4_unread_paper_marked_search_snippet_only(self):
        self.ctx.search_queries_run = ["test query"]

        findings_input = [
            {
                "title": "Unread Study",
                "paper_url": "https://example.com/unread_paper",
                "match_type": "exact",
                "method": "Invented method that was never read",
                "experiments_and_results": {
                    "reported_results": "99.9% invented accuracy",
                    "evidence_location": "Table 99",
                },
                "key_evidence": ["Invented quote"],
            }
        ]

        await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["test query"],
            exact_research_found=False,
            findings=findings_input,
        )

        saved_json = json.loads((self.test_dir / "paper_findings.json").read_text())
        f0 = saved_json["findings"][0]
        self.assertEqual(f0["match_type"], "closely_related")  # Cannot be exact if unread
        self.assertEqual(f0["method"], "not read - search snippet only")
        self.assertEqual(f0["experiments_and_results"]["reported_results"], "not read - search snippet only")
        self.assertEqual(f0["experiments_and_results"]["evidence_location"], "not read - search snippet only")
        self.assertEqual(f0["key_evidence"], [])

    async def test_step4_stale_partial_findings_deleted_on_success(self):
        partial_file = self.test_dir / "paper_findings_partial.json"
        partial_file.write_text('{"status": "incomplete"}')
        self.assertTrue(partial_file.exists())

        self.ctx.search_queries_run = ["query 1"]
        await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["query 1"],
            exact_research_found=False,
            findings=[],
        )
        self.assertFalse(partial_file.exists())

    def test_partial_save_on_error(self):
        self.ctx.search_queries_run = ["executed query 1"]
        self.ctx.candidate_urls = ["https://example.com/candidate"]
        self.ctx.append_trace("test_tool", {"a": 1}, "success")

        out_path = _write_partial_findings(self.test_dir, self.session_id, self.ctx, "TurnCapExceeded: 3 turns")
        self.assertTrue(out_path.exists())
        data = json.loads(out_path.read_text())
        self.assertEqual(data["status"], "incomplete")
        self.assertEqual(data["failure_reason"], "TurnCapExceeded: 3 turns")
        self.assertIn("executed query 1", data["search_queries_run"])
        self.assertIn("https://example.com/candidate", data["candidate_urls_seen"])

    async def test_step5_code_repository_unavailable(self):
        res = await _search_paper_code_repository_impl(self.wrapper, "NonExistentPaperTitleXYZ123456", "UnknownAuthor")
        self.assertIn("No associated repository found on GitHub", res)
        last_repo = self.ctx.repositories_inspected[-1]
        self.assertEqual(last_repo["candidates_found"], 0)

    async def test_bug_b_exact_failing_cases(self):
        """Verify the exact failing cases from Bug (B) are correctly recognized as read."""
        leaflitex_text = (
            "# LeafLiteX mobile application for leaf disease detection using U-Net segmentation\n\n"
            "## Abstract\nThis paper introduces LeafLiteX for mobile deployment.\n\n"
            "## Methodology\nWe use U-Net segmentation and MobileNetV3-Large quantized for TFLite.\n\n"
            "## Dataset\nDataset includes 8,000 leaf images labeled by experts.\n\n"
            "## Experimental Results\nThe model achieves 98.4% accuracy with 38ms latency.\n\n"
            "## Limitations\nField testing was limited to daylight conditions.\n\n"
            + ("Detailed experimental analysis text follows.\n\n" * 200)
        )
        self.assertTrue(len(leaflitex_text) >= 8000)

        rec_leaf = self.ctx.paper_registry.register_candidate(
            title="LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning.",
            doi="10.1038/s41598-026-60625-4",
            paper_url="https://doi.org/10.1038/s41598-026-60625-4",
            authors=["Pawan Kumar Verma", "Divya Midhun"],
            year="2026",
            abstract="LeafLiteX mobile application abstract",
        )
        self.ctx.paper_registry.record_read_text(
            rec_leaf,
            leaflitex_text,
            source_system="firecrawl_mcp",
            is_fallback=False,
        )

        energy_text = (
            "Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification\n\n"
            "Abstract: We propose an energy-aware ensemble of lightweight CNNs for coffee leaf disease.\n\n"
            "Method: Knowledge distillation compresses ensembles into efficient models.\n\n"
            "Results: Accuracy is 97.2% with 22% energy reduction on mobile processors.\n\n"
            "Limitations: Evaluated on simulated mobile battery profiles.\n\n"
            + ("Detailed energy consumption benchmarking data.\n\n" * 200)
        )
        self.assertTrue(len(energy_text) >= 8000)

        rec_energy = self.ctx.paper_registry.register_candidate(
            title="Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification",
            paper_id="arxiv:2601.12109",
            paper_url="https://arxiv.org/abs/2601.12109",
            authors=["Larissa Ferreira Rodrigues Moreira"],
            year="2026",
            abstract="Energy-Aware ensemble abstract",
        )
        self.ctx.paper_registry.record_read_text(
            rec_energy,
            energy_text,
            source_system="arxiv_pdf_pypdf_fallback",
            is_fallback=True,
        )

        self.ctx.search_queries_run = ["coffee leaf disease detection"]

        findings_input = [
            {
                "title": "LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning",
                "doi": "10.1038/s41598-026-60625-4",
                "paper_url": "not found",
                "citation": "not found",
                "match_type": "closely_related",
                "method": "U-Net segmentation with MobileNetV3-Large",
                "experiments_and_results": {
                    "reported_results": "98.4% accuracy",
                    "evidence_location": "Results section",
                },
                "limitations": "Field testing limited to daylight conditions",
                "key_evidence": ["The model achieves 98.4% accuracy"],
            },
            {
                "title": "Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification",
                "doi": "not found",
                "paper_url": "not found",
                "citation": "not found",
                "match_type": "exact",
                "method": "Knowledge-distilled compact CNN ensembles",
                "experiments_and_results": {
                    "reported_results": "97.2% accuracy with 22% energy reduction",
                    "evidence_location": "Results section",
                },
                "limitations": "Evaluated on simulated mobile battery profiles",
                "key_evidence": ["Accuracy is 97.2% with 22% energy reduction"],
            },
        ]

        save_msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf disease detection"],
            exact_research_found=True,
            findings=findings_input,
            notes="Completed audit",
        )
        self.assertIn("Successfully saved", save_msg)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        saved_findings = saved_data["findings"]
        self.assertEqual(len(saved_findings), 2)

        # Check LeafLiteX
        f_leaf = saved_findings[0]
        self.assertNotEqual(f_leaf["method"], "not read - search snippet only")
        self.assertEqual(f_leaf["method"], "U-Net segmentation with MobileNetV3-Large")
        self.assertEqual(f_leaf["paper_url"], "https://doi.org/10.1038/s41598-026-60625-4")
        self.assertIn("https://doi.org/10.1038/s41598-026-60625-4", f_leaf["source_urls"])
        self.assertIn("doi:10.1038/s41598-026-60625-4", f_leaf["citation"])

        # Check Energy-Aware Ensemble
        f_energy = saved_findings[1]
        self.assertNotEqual(f_energy["method"], "not read - search snippet only")
        self.assertEqual(f_energy["method"], "Knowledge-distilled compact CNN ensembles")
        self.assertEqual(f_energy["paper_url"], "https://arxiv.org/abs/2601.12109")
        self.assertIn("https://arxiv.org/abs/2601.12109", f_energy["source_urls"])
        self.assertEqual(f_energy["match_type"], "exact")

    async def test_missing_read_paper_triggers_warning_then_succeeds(self):
        full_text = "DeepEMPR full text.\n\n" + ("DeepEMPR achieves robust coffee rust detection.\n\n" * 20)
        rec = self.ctx.paper_registry.register_candidate(
            title="DeepEMPR: coffee leaf disease detection",
            paper_id="pmcid:PMC11623072",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "europe_pmc_xml_fallback", True)

        warn_msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf"],
            exact_research_found=False,
            findings=[],
            notes="",
        )
        self.assertIn("ERROR", warn_msg)
        self.assertIn("DeepEMPR", warn_msg)

        success_msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf"],
            exact_research_found=False,
            findings=[{
                "title": "DeepEMPR: coffee leaf disease detection",
                "paper_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/",
                "match_type": "closely_related",
            }],
            notes="",
        )
        self.assertIn("Successfully saved", success_msg)

    async def test_bug_a_noise_rejection_and_dataset_model_handling(self):
        """Test Bug A: Noise heading/content rejection, dataset papers set model to 'not applicable', dataset split/size extraction."""
        # 1. Noise heading detection
        self.assertTrue(_is_noise_heading("Author Contributions"))
        self.assertTrue(_is_noise_heading("CRediT authorship contribution statement"))
        self.assertTrue(_is_noise_heading("Ethics declarations"))
        self.assertTrue(_is_noise_heading("Competing interests"))
        self.assertTrue(_is_noise_heading("References"))
        self.assertTrue(_is_noise_heading("Funding"))
        self.assertFalse(_is_noise_heading("Experimental Results"))
        self.assertFalse(_is_noise_heading("Methodology"))

        # 2. Noise content detection
        noise_author = "John Doe: Conceptualization, Methodology, Writing - review & editing. [author] pubmed.ncbi.nlm.nih.gov/123456"
        self.assertTrue(_is_noise_content(noise_author))
        self.assertTrue(_is_noise_content("This research was funded by National Science Foundation grant number 12345"))
        self.assertFalse(_is_noise_content("We train a MobileNetV2 network using Adam optimizer and learning rate 0.001."))

        # 3. Dataset split into name, size, split
        ds = DatasetInfo.model_validate({
            "name": "Arabica Coffee Leaf Dataset (1,200 images, 80/20 train/test split)",
        })
        self.assertEqual(ds.name, "Arabica Coffee Leaf Dataset")
        self.assertEqual(ds.size, "1,200 images")
        self.assertEqual(ds.split, "80/20 train/test split")

        # 4. Dataset paper sets model to "not applicable"
        full_text = "Arabica dataset paper.\n\n" + ("We introduce a benchmark dataset of coffee leaf images.\n\n" * 20)
        rec = self.ctx.paper_registry.register_candidate(
            title="A comprehensive dataset of coffee leaf images",
            paper_url="https://doi.org/10.1016/j.dib.2021.107142",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)

        save_msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf dataset"],
            exact_research_found=False,
            findings=[{
                "title": "A comprehensive dataset of coffee leaf images",
                "paper_url": "https://doi.org/10.1016/j.dib.2021.107142",
                "match_type": "closely_related",
                "model": {"model_name": "Deep Learning Classifier"},  # Hallucinated classifier
            }],
        )
        self.assertIn("Successfully saved", save_msg)
        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text())
        saved_f = saved_data["findings"][0]
        self.assertEqual(saved_f["model"]["model_name"], "not applicable")
        self.assertEqual(saved_f["model"]["architecture"], "not applicable")

    def test_bug_b_section_lookup_and_aliases(self):
        """Test Bug B: Section lookup aliases, multi-section querying, and non-silent missing sections."""
        sample_md = """
# Coffee Detection Paper
## Abstract
Study of coffee leaf diseases.
## Motivation for the choice of methods used
Background and related work overview.
## Methodology
We employ a modified MobileNetV3 backbone for rapid on-device inference.
## Experimental Results
Overall accuracy is 96.8% with F1 score 0.95.
## Discussion
Detailed comparison with previous benchmarks.
## Limitations
Dataset size is limited to one agricultural region.
"""
        sections = _extract_sections(sample_md)

        # 1. Alias matching: "method" / "methods" matches "Methodology" and ignores "motivation for..."
        out, label, found = _find_matching_sections(sections, "methods")
        self.assertIn("MobileNetV3", out)
        self.assertNotIn("Background and related work", out)
        self.assertIn("methodology", label.lower())

        # 2. Multi-section lookup in one call
        out_multi, label_multi, found_multi = _find_matching_sections(sections, "method, results, limitations")
        self.assertIn("Methodology", out_multi)
        self.assertIn("Experimental Results", out_multi)
        self.assertIn("Limitations", out_multi)
        self.assertEqual(len(found_multi), 3)

        # 3. Missing section returns explicit "section not found" with available section names
        out_missing, label_missing, found_missing = _find_matching_sections(sections, "dataset")
        self.assertIn("section not found: 'dataset'", out_missing)
        self.assertIn("Available sections:", out_missing)
        self.assertIn("Methodology", out_missing)
        self.assertEqual(found_missing, [])

    def test_bug_c_strict_arxiv_and_doi_isolation(self):
        """Test Bug C: Strict arXiv regex, DOI does not produce fake arXiv URL, and neighboring papers are isolated."""
        # 1. DOI with digits like 2021.107142 must NOT create an arXiv ID
        ids = normalize_paper_identifiers("10.1016/j.dib.2021.107142")
        self.assertEqual(ids["doi"], "10.1016/j.dib.2021.107142")
        self.assertEqual(ids["arxiv_id"], "")
        self.assertNotIn("arxiv.org", ids["canonical_url"])

        # 2. Valid arXiv ID has month 01-12
        ids_valid = normalize_paper_identifiers("arxiv:2403.12345")
        self.assertEqual(ids_valid["arxiv_id"], "2403.12345")
        self.assertEqual(ids_valid["canonical_url"], "https://arxiv.org/abs/2403.12345")

        # 3. PaperRegistry.find_paper does not merge neighboring papers with generic overlapping tokens
        registry = PaperRegistry()
        p1 = registry.register_candidate(
            title="Arabica coffee leaf disease dataset",
            paper_url="https://doi.org/10.1016/j.dib.2021.107142",
        )
        p2 = registry.register_candidate(
            title="CoLeaf-DB: An open database for coffee leaf diseases",
            paper_url="https://doi.org/10.1016/j.dib.2022.999999",
        )
        p3 = registry.register_candidate(
            title="Coffee Disease Visualization and Classification using CNN",
            paper_url="https://doi.org/10.1109/VIS2023.12345",
        )

        match1 = registry.find_paper(title="Arabica coffee leaf disease dataset")
        self.assertIsNotNone(match1)
        self.assertEqual(match1.paper_url, p1.paper_url)

        match2 = registry.find_paper(title="CoLeaf-DB: An open database for coffee leaf diseases")
        self.assertIsNotNone(match2)
        self.assertEqual(match2.paper_url, p2.paper_url)

        match3 = registry.find_paper(title="Coffee Disease Visualization and Classification using CNN")
        self.assertIsNotNone(match3)
        self.assertEqual(match3.paper_url, p3.paper_url)

        # Source URLs isolation: p1's URLs do not contaminate p2
        self.assertNotIn(p2.paper_url, p1.source_urls)
        self.assertNotIn(p1.paper_url, p2.source_urls)

    def test_numeric_section_headers_and_rocole_alias_matching(self):
        """Test Issue (B): Numeric section headers and RoCoLe experimental design matching."""
        sections = {
            "abstract": "Abstract text",
            "1\\. data": "Data section content for RoCoLe",
            "2\\. experimental design, materials, and methods": "The coffee plants images of healthy and unhealthy leaves were acquired using a 5-MP smartphone camera.",
            "4.1 datasets": "Dataset section content with PlantVillage",
        }
        # 1. Matching '1. data' matches '1\\. data'
        out1, label1, found1 = _find_matching_sections(sections, "1. data")
        self.assertIn("1\\. data", found1)
        self.assertIn("Data section content", out1)

        # 2. Matching '4.1 datasets' matches '4.1 datasets'
        out2, label2, found2 = _find_matching_sections(sections, "4.1 datasets")
        self.assertIn("4.1 datasets", found2)

        # 3. Matching 'method' matches '2\\. experimental design, materials, and methods'
        out3, label3, found3 = _find_matching_sections(sections, "method")
        self.assertIn("2\\. experimental design, materials, and methods", found3)

        # 4. Matching full section title directly without comma splitting issue
        out4, label4, found4 = _find_matching_sections(sections, "2. experimental design, materials, and methods")
        self.assertIn("2\\. experimental design, materials, and methods", found4)

    async def test_rocole_method_validation_and_evidence_quote_verification(self):
        """Test Issues (B), (C), (D): Method validation without auto-fill, EvidenceQuote structure, and expansion."""
        full_text = (
            "# RoCoLe Paper\n\n"
            "## Abstract\nRoCoLe dataset introduces robusta coffee leaf images.\n\n"
            "## 2. Experimental Design, Materials, and Methods\nThe coffee plants images of healthy and unhealthy leaves were acquired using a 5-MP smartphone camera under natural field conditions. Expert evaluation categorized rust severity.\n\n"
            "## Limitations\nModel size 78 MB may be large for ultra-light devices; unsupported fabricated sentence here.\n\n"
            + ("Detailed study text.\n\n" * 150)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="RoCoLe: A robusta coffee leaf images dataset",
            paper_url="https://doi.org/10.1016/j.dib.2019.104414",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)

        # 1. Test that leaving method empty/not reported when a methods section exists returns an ERROR (Issue C)
        err_msg = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["rocole coffee leaf"],
            exact_research_found=False,
            findings=[{
                "title": "RoCoLe: A robusta coffee leaf images dataset",
                "paper_url": "https://doi.org/10.1016/j.dib.2019.104414",
                "match_type": "closely_related",
                "method": "not reported",
            }],
        )
        self.assertIn("ERROR", err_msg)
        self.assertIn("methods section exists", err_msg)

        # Register 5 dummy candidates in registry to test expansion to 10
        for i in range(1, 6):
            self.ctx.paper_registry.register_candidate(
                title=f"Candidate Study {i}",
                paper_url=f"https://example.com/candidate{i}",
                year="2024",
                doi=f"10.1000/cand{i}",
            )

        # 2. When valid method is supplied, it validates and saves cleanly
        findings_input = [
            {
                "title": "RoCoLe: A robusta coffee leaf images dataset",
                "paper_url": "https://doi.org/10.1016/j.dib.2019.104414",
                "match_type": "closely_related",
                "method": "Images acquired using a 5-MP smartphone camera under natural field conditions.",
                "limitations": "Model size 78 MB may be large for ultra-light devices; completely fabricated claim xyz",
                "key_evidence": [],
            }
        ]

        save_res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["rocole coffee leaf"],
            exact_research_found=False,
            findings=findings_input,
        )
        self.assertIn("Successfully saved", save_res)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        f0 = saved_data["findings"][0]

        # Method verified and saved without heuristic overwriting
        self.assertIn("5-MP smartphone camera", f0["method"])

        # Limitations verified and quote added, fabricated sentence pruned
        self.assertIn("78 MB", f0["limitations"])
        self.assertNotIn("completely fabricated claim xyz", f0["limitations"])
        self.assertTrue(any("78 MB" in q["quote"] for q in f0["key_evidence"]))
        # Verify EvidenceQuote structure {quote, section, field}
        self.assertIn("section", f0["key_evidence"][0])
        self.assertIn("field", f0["key_evidence"][0])

        # Expanded to include remaining candidates
        self.assertEqual(len(saved_data["findings"]), 6)

    def test_unicode_normalization_effresvit_hyphen(self):
        """Test Issue (B): Unicode non-breaking hyphen in EffResViT section header."""
        sections = {
            "abstract": "EffResViT abstract.",
            "3.3. proposed effresvit\u2011se fusionnet model": "EffResViT architecture combines MobileNetV3 and Transformer blocks with SE attention.",
            "4.2. classification results": "The proposed EffResViT model achieved 99.2% classification accuracy on the test set.",
        }

        # 1. Target with regular hyphen matches header with non-breaking hyphen
        out1, label1, found1 = _find_matching_sections(sections, "3.3. proposed effresvit-se fusionnet model")
        self.assertIn("MobileNetV3 and Transformer", out1)
        self.assertIn("3.3. proposed effresvit", label1)

        # 2. Numbered lookup: '4.2' matches '4.2. classification results'
        out2, label2, found2 = _find_matching_sections(sections, "4.2")
        self.assertIn("99.2% classification accuracy", out2)
        self.assertIn("4.2. classification results", found2)

        # 3. Category lookup: 'results' matches 4.2
        out3, label3, found3 = _find_matching_sections(sections, "results")
        self.assertIn("99.2% classification accuracy", out3)
        self.assertIn("4.2. classification results", found3)

    async def test_save_check_fails_when_results_section_unread(self):
        """Test Issue (A): Save fails when outline contains unrequested results section."""
        full_text = (
            "# EffResViT Paper\n\n"
            "## Abstract\nLightweight model for coffee leaf diseases.\n\n"
            "## 3. Methodology\nProposed fusion architecture.\n\n"
            "## 4. Experiments and Results\nPerformance evaluation on coffee leaves.\n\n"
            "## 4.2 Classification Results\nAchieved 99.2% accuracy.\n\n"
            "## 5. Conclusion\nSummary of findings.\n\n"
            + ("Paper text.\n\n" * 100)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="EffResViT Coffee Leaf Disease Detection",
            paper_url="https://example.com/effresvit",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)
        # Agent only requested "all" (which is only outline + abstract)
        self.ctx.paper_sections_requested["https://example.com/effresvit"] = {"all"}

        findings = [{
            "title": "EffResViT Coffee Leaf Disease Detection",
            "paper_url": "https://example.com/effresvit",
            "match_type": "closely_related",
            "method": "Proposed fusion architecture",
        }]

        res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["effresvit"],
            exact_research_found=False,
            findings=findings,
        )
        self.assertIn("ERROR", res)
        self.assertIn("missing requested sections", res)
        self.assertIn("results", res)

    async def test_coffee_leaf_rust_keeps_real_model_fields(self):
        """Test Issue (D): Papers that train/evaluate models (Coffee Leaf Rust) keep real model fields."""
        full_text = (
            "# Coffee Leaf Rust Disease Detection\n\n"
            "## Abstract\nWe evaluate YOLOv8 and YOLOv5 for coffee leaf rust detection in field conditions.\n\n"
            "## 3. Methodology\nWe apply YOLOv8 object detection framework.\n\n"
            "## 4. Results\nmAP is 69.4% and precision is 94.25%.\n\n"
            + ("Paper text.\n\n" * 100)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="Coffee Leaf Rust disease detection using YOLOv8",
            paper_url="https://example.com/clr_yolo",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_mcp", False)

        findings = [{
            "title": "Coffee Leaf Rust disease detection using YOLOv8",
            "paper_url": "https://example.com/clr_yolo",
            "match_type": "closely_related",
            "method": "YOLOv8 framework trained on field images",
            "model": {
                "model_name": "YOLOv8",
                "architecture": "CNN-based single-stage detector",
            },
        }]

        res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["coffee leaf rust yolo"],
            exact_research_found=False,
            findings=findings,
        )
        self.assertIn("Successfully saved", res)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        f0 = saved_data["findings"][0]
        self.assertEqual(f0["model"]["model_name"], "YOLOv8")
        self.assertNotEqual(f0["model"]["model_name"], "not applicable")
        self.assertEqual(f0["model"]["architecture"], "CNN-based single-stage detector")

    async def test_round7_fix_a_title_resolution_and_notes(self):
        """Fix A: Title resolved from candidate registry, never URL; citation includes title; notes list titles."""
        full_text = (
            "# DeepEMPR: Deep Learning for Coffee Leaf Disease\n\n"
            "## Abstract\nThis paper proposes DeepEMPR.\n\n"
            "## 3. Methodology\nWe propose an efficient MobileNet-based model.\n\n"
            "## 4. Results\nDeepEMPR achieves 98.2% accuracy.\n\n"
            "## 5. Conclusion\nFuture work will address real-time deployment.\n\n"
            + ("Paper body text.\n\n" * 50)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="DeepEMPR: an efficient framework for coffee leaf disease detection",
            paper_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/",
            paper_id="pmcid:PMC11623072",
            authors=["Jane Doe", "John Smith"],
            year="2024",
            doi="10.1038/s41598-024-00000-0",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_scrape", False)

        findings = [{
            "title": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/",  # URL as title
            "paper_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/",
            "match_type": "closely_related",
            "method": "Efficient MobileNet-based model",
            "experiments_and_results": {
                "reported_results": "98.2% accuracy",
                "evidence_location": "4. Results",
            },
            "key_evidence": ["DeepEMPR achieves 98.2% accuracy."],
        }]

        res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["deepempr coffee"],
            exact_research_found=False,
            findings=findings,
        )
        self.assertIn("Successfully saved", res)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        f0 = saved_data["findings"][0]
        # Title must be resolved from candidate registry, not URL
        self.assertEqual(f0["title"], "DeepEMPR: an efficient framework for coffee leaf disease detection")
        # Citation must contain the real title and not empty '. .'
        self.assertIn("DeepEMPR: an efficient framework", f0["citation"])
        self.assertNotIn(". .", f0["citation"])
        # Notes must contain the title, not URL
        self.assertIn("DeepEMPR: an efficient framework", saved_data["notes"])
        self.assertNotIn("https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/", saved_data["notes"])

    async def test_round7_fix_b_literature_citations_and_dataset_papers(self):
        """Fix B: Literature review citations / figure captions rejected from results; dataset papers get not applicable."""
        full_text = (
            "# Arabica Coffee Leaves Dataset\n\n"
            "## Abstract\nWe provide 1,685 images of Arabica coffee leaves.\n\n"
            "## Description\nDataset contains images of healthy and diseased leaves.\n\n"
            + ("Dataset description.\n\n" * 50)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="Arabica Coffee Leaves: A dataset for leaf disease detection",
            paper_url="https://doi.org/10.1016/j.dib.2021.107142",
            doi="10.1016/j.dib.2021.107142",
            authors=["Alice Wonder"],
            year="2021",
        )
        self.ctx.paper_registry.record_read_text(rec, full_text, "firecrawl_scrape", False)

        findings = [{
            "title": "Arabica Coffee Leaves: A dataset for leaf disease detection",
            "paper_url": "https://doi.org/10.1016/j.dib.2021.107142",
            "doi": "10.1016/j.dib.2021.107142",
            "match_type": "closely_related",
            "method": "Image collection and curation",
            "dataset": {
                "name": "Arabica Coffee Leaves, 1,685 images of healthy and diseased leaves",
            },
            "experiments_and_results": {
                "reported_results": "Accuracy 95%",  # Keyword match that shouldn't apply to pure dataset paper
                "evidence_location": "Read full text",
            },
        }]

        res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["arabica coffee leaves dataset"],
            exact_research_found=False,
            findings=findings,
        )
        self.assertIn("Successfully saved", res)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        f0 = saved_data["findings"][0]
        # Pure dataset paper gets not applicable for all 4 result fields
        exp = f0["experiments_and_results"]
        self.assertEqual(exp["reported_results"], "not applicable")
        self.assertEqual(exp["evaluation_metrics"], "not applicable")
        self.assertEqual(exp["experimental_setup"], "not applicable")
        self.assertEqual(exp["baseline_comparisons"], "not applicable")
        self.assertEqual(f0["model"]["model_name"], "not applicable")
        # Dataset name cleaned
        self.assertTrue(len(f0["dataset"]["name"]) <= 60)
        self.assertIn("1,685", f0["dataset"]["size"])

    async def test_round7_fix_c_manso_offline_audit_and_exact_consistency(self):
        """Fix C: Manso without proven offline operation is closely_related with match_reason."""
        manso_text = (
            "# Smartphone Application to Detection and Classification of Coffee Leaf Miner and Rust\n\n"
            "## Abstract\nWe develop an Android smartphone application for coffee disease.\n\n"
            "## System Design\nThe mobile phone captures images and sends them for processing.\n\n"
            "## 3. Methodology\nWe evaluate CNN models.\n\n"
            "## 4. Results\nAccuracy is 98.5%.\n\n"
            "## 5. Conclusion\nThe mobile application facilitates disease diagnosis in the field.\n\n"
            + ("More text.\n\n" * 50)
        )
        rec = self.ctx.paper_registry.register_candidate(
            title="Smartphone Application to Detection and Classification of Coffee Leaf Miner and Rust",
            paper_url="https://arxiv.org/abs/1904.00742",
            paper_id="arxiv:1904.00742",
            authors=["Manso et al."],
            year="2019",
        )
        self.ctx.paper_registry.record_read_text(rec, manso_text, "arxiv_pdf_pypdf_fallback", False)

        findings = [{
            "title": "Smartphone Application to Detection and Classification of Coffee Leaf Miner and Rust",
            "paper_url": "https://arxiv.org/abs/1904.00742",
            "match_type": "exact",  # Agent claimed exact
            "method": "Mobile CNN classifier",
            "experiments_and_results": {
                "reported_results": "Accuracy is 98.5%",
                "evidence_location": "4. Results",
            },
            "key_evidence": ["Accuracy is 98.5%."],
        }]

        res = await _save_paper_findings_impl(
            self.wrapper,
            search_queries_run=["smartphone coffee leaf rust"],
            exact_research_found=True,
            findings=findings,
        )
        self.assertIn("Successfully saved", res)

        saved_data = json.loads((self.test_dir / "paper_findings.json").read_text(encoding="utf-8"))
        f0 = saved_data["findings"][0]
        # Demoted to closely_related because offline without server not stated
        self.assertEqual(f0["match_type"], "closely_related")
        self.assertIn("offline operation not stated in the text", f0["match_reason"])
        # exact_research_found must match findings (must be False since no exact findings)
        self.assertFalse(saved_data["exact_research_found"])

        # Markdown report must also reflect no exact research found
        saved_md = (self.test_dir / "paper_findings.md").read_text(encoding="utf-8")
        self.assertIn("No exact research paper was found", saved_md)

    def test_round7_fix_d_budget_accounting_and_refunds(self):
        """Fix D: save_paper_findings does not consume budget; validation errors refund budget."""
        self.ctx.tool_calls_count = 5
        self.ctx.max_tool_calls = 50

        # Save paper findings shouldn't count against budget and returns None (allowed)
        self.assertIsNone(self.ctx.check_and_increment_budget("save_paper_findings", {}))
        self.assertEqual(self.ctx.tool_calls_count, 5)

        # Normal tool counts
        self.assertIsNone(self.ctx.check_and_increment_budget("read_paper_full_text", {}))
        self.assertEqual(self.ctx.tool_calls_count, 6)

        # Refund for validation error
        self.ctx.refund_budget_for_validation_error()
        self.assertEqual(self.ctx.tool_calls_count, 5)

        # Budget reached at max_tool_calls - 3 (save reserve)
        self.ctx.tool_calls_count = 47
        res = self.ctx.check_and_increment_budget("read_paper_full_text", {})
        self.assertIsNotNone(res)
        self.assertIn("BUDGET REACHED", res)

    def test_round7_fix_e_clean_dataset_name_and_evidence_quote(self):
        """Fix E: clean_dataset_name handles commas in numbers, balances parens, length <= 60."""
        from paper_research.schema import clean_dataset_name, EvidenceQuote

        raw_name = "Arabica Coffee Leaves, 1,685 images of healthy and diseased leaves"
        cleaned = clean_dataset_name(raw_name)
        self.assertIn("Arabica Coffee Leaves", cleaned)
        self.assertTrue(len(cleaned) <= 60)

        raw_with_paren = "RoCoLe (Robusta Coffee Leaf dataset (1,560 images)"
        cleaned_paren = clean_dataset_name(raw_with_paren)
        self.assertEqual(cleaned_paren.count("("), cleaned_paren.count(")"))

        # Evidence quote string representation
        eq = EvidenceQuote(quote="Achieves 98.5% accuracy", section="Results", field="reported_results")
        self.assertEqual(str(eq), '[Results] "Achieves 98.5% accuracy"')


if __name__ == "__main__":
    unittest.main()

