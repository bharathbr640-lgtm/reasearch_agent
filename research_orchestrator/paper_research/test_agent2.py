"""Unit tests for Agent 2 (Research Paper Discovery and Evidence Collection Agent).

Covers Stages 1 through 5 using offline mock data (no network calls) and verifies
full compatibility with check_answers.py.
"""

import asyncio
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agents import RunContextWrapper
from paper_research.check_answers import check_findings
from paper_research.schema import (
    CodeRepository,
    DatasetInfo,
    EvidenceQuote,
    ExperimentsAndResults,
    ExtractedBooleanField,
    ExtractedField,
    ModelInfo,
    PaperExtractionOutput,
    PaperFinding,
    PaperResearchFindings,
    clean_dataset_name,
)
from paper_research.tools import (
    PaperRecord,
    PaperRegistry,
    PaperResearchContext,
    _clean_header_name,
    _extract_sections,
    _is_noise_heading,
    _normalize_for_match,
    _select_papers_impl,
    assemble_findings,
    bucket_paper_sections,
    normalize_doi,
    normalize_paper_identifiers,
    normalize_title,
    validate_extraction,
)


SAMPLE_PAPER_TEXT = """
# DeepEMPR: Deep Learning-Based Arabica Coffee Pest and Disease Diagnosis System

## Abstract
Plant diseases and pests significantly reduce coffee production worldwide.
In this study, we propose DeepEMPR, an intelligent diagnosis system for Arabica coffee leaf diseases.
The system identifies four major conditions: coffee leaf rust, leaf miner, cercospora, and spider mites.

## 2. Materials and Methods
### 2.1 Dataset Collection and Preprocessing
A total of 58,555 images were gathered under real field conditions across multiple plantations.
The dataset was split into 70% training, 15% validation, and 15% testing sets.

### 2.2 Proposed Architecture
We developed DeepEMPR using an improved EfficientNetV2 backbone integrated with squeeze-and-excitation attention blocks.
Data augmentation techniques including rotation, shearing, and color jitter were applied.

## 3. Results and Discussion
Experimental evaluation shows that DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories.
Precision was 98.8%, recall was 99.0%, and the F1-score reached 98.9%.
When compared against baseline ResNet-50 (accuracy 92.4%) and MobileNetV2 (accuracy 90.1%), our model achieved superior performance.

## 4. Limitations and Future Work
The current model was trained exclusively on daytime photos; performance under artificial night lighting has not been evaluated.
Future research will investigate quantization for microcontrollers.
"""

SAMPLE_APP_PAPER_TEXT = """
# Mobile-Coffee: A Real-Time Smartphone Application for Coffee Leaf Disease Detection

## Abstract
Smallholder farmers require immediate disease diagnosis on inexpensive smartphones.
We present Mobile-Coffee, a mobile application running on Android devices for real-time coffee leaf rust detection.

## 2. System Design and Mobile Deployment
The mobile app was built for Android smartphones using TensorFlow Lite.
All inference is executed completely on the mobile phone offline without requiring an internet connection or remote server.

## 3. Experimental Results
On the field test set of 2,400 leaf images, Mobile-Coffee achieved 94.25% classification accuracy.
Average latency per frame was 32 milliseconds on a mid-range phone.

## 4. Discussion and Limitations
Battery consumption increases during continuous camera stream processing.
"""

SAMPLE_DATASET_PAPER_TEXT = """
# Arabica-Pest: A Benchmark Dataset for Coffee Leaf Pathologies

## Abstract
This paper introduces Arabica-Pest, a public benchmark image dataset for coffee leaf pathologies.
We present no machine learning model or classifier, but provide detailed annotations for the computer vision community.

## 2. Dataset Description
The dataset contains 15,200 high-resolution leaf images covering 5 fungal infections.
Images are split into 80% train and 20% test partitions.

## 3. Data Availability and Format
All images and labels in YOLO format are hosted on Zenodo.
"""


class TestAgent2Redesign(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="agent2_test_"))
        self.session_id = "test-session-123"
        self.ctx = PaperResearchContext(
            session_id=self.session_id,
            output_dir=self.test_dir,
            research_spec_summary="Edge deployment of coffee leaf disease diagnosis on mobile phones",
            max_tool_calls=20,
        )
        self.wrapper = RunContextWrapper(self.ctx)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. Identifier Normalization & Registry Tests
    # -------------------------------------------------------------
    def test_normalize_identifiers(self):
        norm_pmc = normalize_paper_identifiers("pmcid:PMC11679138")
        self.assertEqual(norm_pmc["pmcid"], "PMC11679138")
        self.assertEqual(norm_pmc["canonical_url"], "https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/")

        norm_arx = normalize_paper_identifiers("arxiv:2601.12109")
        self.assertEqual(norm_arx["arxiv_id"], "2601.12109")
        self.assertEqual(norm_arx["pdf_url"], "https://arxiv.org/pdf/2601.12109.pdf")

        norm_doi = normalize_paper_identifiers("10.1038/s41598-026-60625-4")
        self.assertEqual(norm_doi["doi"], "10.1038/s41598-026-60625-4")
        self.assertEqual(norm_doi["canonical_url"], "https://doi.org/10.1038/s41598-026-60625-4")

        # Strip URL prefixes
        self.assertEqual(normalize_doi("https://doi.org/10.1016/j.dib.2021.107142"), "10.1016/j.dib.2021.107142")
        self.assertEqual(normalize_title("DeepEMPR: Deep Learning-Based Arabica!"), "deepemprdeeplearningbasedarabica")

    def test_paper_registry(self):
        registry = PaperRegistry()
        rec = registry.register_candidate(
            title="DeepEMPR Study",
            paper_url="https://doi.org/10.1016/j.test.1",
            doi="10.1016/j.test.1",
            paper_id="doi:10.1016/j.test.1",
        )
        self.assertEqual(rec.title, "DeepEMPR Study")
        self.assertEqual(rec.doi, "10.1016/j.test.1")

        found = registry.find_paper("10.1016/j.test.1")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "DeepEMPR Study")

    # -------------------------------------------------------------
    # 2. Stage 1: Selector Tool Tests
    # -------------------------------------------------------------
    async def test_stage1_select_papers(self):
        self.ctx.candidate_papers_seen = [
            {"title": "Paper 1", "url": "https://arxiv.org/abs/2601.00001", "paper_id": "arxiv:2601.00001"},
            {"title": "Paper 2", "url": "https://arxiv.org/abs/2601.00002", "paper_id": "arxiv:2601.00002"},
            {"title": "Paper 3", "url": "https://arxiv.org/abs/2601.00003", "paper_id": "arxiv:2601.00003"},
            {"title": "Paper 4", "url": "https://arxiv.org/abs/2601.00004", "paper_id": "arxiv:2601.00004"},
            {"title": "Paper 5", "url": "https://arxiv.org/abs/2601.00005", "paper_id": "arxiv:2601.00005"},
            {"title": "Paper 6", "url": "https://arxiv.org/abs/2601.00006", "paper_id": "arxiv:2601.00006"},
        ]

        # Select 5 papers
        res = await _select_papers_impl(self.wrapper, ["arxiv:2601.00001", "arxiv:2601.00002", "arxiv:2601.00003", "arxiv:2601.00004", "arxiv:2601.00005", "arxiv:2601.00006"])
        self.assertIn("Successfully selected 5 papers", res)
        self.assertEqual(len(self.ctx.selected_papers), 5)
        self.assertTrue(self.ctx.selection_done)

    # -------------------------------------------------------------
    # 3. Stage 2: Section Extraction and Bucketing Tests
    # -------------------------------------------------------------
    def test_stage2_extraction_and_bucketing(self):
        sections = _extract_sections(SAMPLE_PAPER_TEXT)
        self.assertTrue(any("abstract" in k for k in sections))
        self.assertTrue(any("results" in k for k in sections))

        buckets = bucket_paper_sections(SAMPLE_PAPER_TEXT, sections)
        self.assertIn("abstract", buckets)
        self.assertIn("dataset", buckets)
        self.assertIn("method", buckets)
        self.assertIn("results", buckets)
        self.assertIn("limitations", buckets)

        # Abstract bucket
        self.assertIn("DeepEMPR", buckets["abstract"])
        # Dataset bucket
        self.assertIn("58,555", buckets["dataset"])
        # Method bucket
        self.assertIn("EfficientNetV2", buckets["method"])
        # Results bucket
        self.assertIn("99.1%", buckets["results"])
        # Limitations bucket
        self.assertIn("daytime photos", buckets["limitations"])

    # -------------------------------------------------------------
    # 4. Stage 3/4: Validation Logic Tests
    # -------------------------------------------------------------
    def test_stage4_validation_quote_matching_and_number_checking(self):
        sections = _extract_sections(SAMPLE_PAPER_TEXT)
        buckets = bucket_paper_sections(SAMPLE_PAPER_TEXT, sections)
        headings = list(sections.keys())

        # Valid extraction output
        extraction = PaperExtractionOutput(
            problem_addressed=ExtractedField(
                value="Coffee leaf disease diagnosis across plantations",
                quote="In this study, we propose DeepEMPR, an intelligent diagnosis system for Arabica coffee leaf diseases.",
                section="Abstract",
            ),
            research_objective=ExtractedField(
                value="Identify four major conditions",
                quote="The system identifies four major conditions: coffee leaf rust, leaf miner, cercospora, and spider mites.",
                section="Abstract",
            ),
            domain=ExtractedField(
                value="Arabica coffee leaf disease",
                quote="diagnosis system for Arabica coffee leaf diseases.",
                section="Abstract",
            ),
            input_type=ExtractedField(
                value="Leaf images",
                quote="A total of 58,555 images were gathered under real field conditions",
                section="2.1 Dataset Collection and Preprocessing",
            ),
            output_type=ExtractedField(
                value="Diagnostic categories",
                quote="across all diagnostic categories.",
                section="3. Results and Discussion",
            ),
            dataset_name=ExtractedField(
                value="Arabica Leaf Dataset",
                quote="A total of 58,555 images were gathered under real field conditions across multiple plantations.",
                section="2.1 Dataset Collection and Preprocessing",
            ),
            dataset_size=ExtractedField(
                value="58,555 images",
                quote="A total of 58,555 images were gathered under real field conditions across multiple plantations.",
                section="2.1 Dataset Collection and Preprocessing",
            ),
            dataset_split=ExtractedField(
                value="70% train, 15% val, 15% test",
                quote="The dataset was split into 70% training, 15% validation, and 15% testing sets.",
                section="2.1 Dataset Collection and Preprocessing",
            ),
            model_name=ExtractedField(
                value="DeepEMPR",
                quote="We developed DeepEMPR using an improved EfficientNetV2 backbone integrated with squeeze-and-excitation attention blocks.",
                section="2.2 Proposed Architecture",
            ),
            architecture=ExtractedField(
                value="EfficientNetV2 with squeeze-and-excitation",
                quote="We developed DeepEMPR using an improved EfficientNetV2 backbone integrated with squeeze-and-excitation attention blocks.",
                section="2.2 Proposed Architecture",
            ),
            method=ExtractedField(
                value="EfficientNetV2 with attention blocks and data augmentation",
                quote="We developed DeepEMPR using an improved EfficientNetV2 backbone integrated with squeeze-and-excitation attention blocks.",
                section="2.2 Proposed Architecture",
            ),
            evaluation_metrics=ExtractedField(
                value="Accuracy, Precision, Recall, F1",
                quote="Precision was 98.8%, recall was 99.0%, and the F1-score reached 98.9%.",
                section="3. Results and Discussion",
            ),
            reported_results=ExtractedField(
                value="99.1% accuracy, 98.8% precision",
                quote="Experimental evaluation shows that DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories. Precision was 98.8%",
                section="3. Results and Discussion",
            ),
            baselines=ExtractedField(
                value="ResNet-50 92.4%, MobileNetV2 90.1%",
                quote="When compared against baseline ResNet-50 (accuracy 92.4%) and MobileNetV2 (accuracy 90.1%), our model achieved superior performance.",
                section="3. Results and Discussion",
            ),
            limitations=ExtractedField(
                value="Only tested on daytime photos",
                quote="The current model was trained exclusively on daytime photos; performance under artificial night lighting has not been evaluated.",
                section="4. Limitations and Future Work",
            ),
            research_gap=ExtractedField(
                value="Quantization for microcontrollers",
                quote="Future research will investigate quantization for microcontrollers.",
                section="4. Limitations and Future Work",
            ),
            is_dataset_paper=False,
            same_task=ExtractedBooleanField(
                value=True,
                quote="The system identifies four major conditions: coffee leaf rust, leaf miner, cercospora, and spider mites.",
                section="Abstract",
            ),
            phone_app=ExtractedBooleanField(
                value=False,
                quote="",
                section="not found",
            ),
            offline_stated=ExtractedBooleanField(
                value=False,
                quote="",
                section="not found",
            ),
        )

        val_ext, rejections = validate_extraction(extraction, buckets, headings, "DeepEMPR", drop_failures=False)
        self.assertEqual(len(rejections), 0)
        self.assertEqual(val_ext.reported_results.value, "99.1% accuracy, 98.8% precision")
        self.assertEqual(val_ext.dataset_size.value, "58,555 images")

    def test_stage4_results_quote_must_come_from_results_bucket(self):
        sections = _extract_sections(SAMPLE_PAPER_TEXT)
        buckets = bucket_paper_sections(SAMPLE_PAPER_TEXT, sections)
        headings = list(sections.keys())

        # Bad extraction where reported_results quote is from Abstract
        bad_extraction = PaperExtractionOutput(
            reported_results=ExtractedField(
                value="Four major conditions",
                quote="The system identifies four major conditions: coffee leaf rust, leaf miner, cercospora, and spider mites.",
                section="Abstract",
            )
        )

        # With drop_failures=True, results field from abstract must be rejected and dropped
        val_ext, rejections = validate_extraction(bad_extraction, buckets, headings, "DeepEMPR", drop_failures=True)
        self.assertTrue(any(r["field"] == "reported_results" for r in rejections))
        self.assertEqual(val_ext.reported_results.value, "not found")

    def test_stage4_number_mismatch_rejected(self):
        sections = _extract_sections(SAMPLE_PAPER_TEXT)
        buckets = bucket_paper_sections(SAMPLE_PAPER_TEXT, sections)
        headings = list(sections.keys())

        # Value contains 99.9% but quote has 99.1%
        bad_num = PaperExtractionOutput(
            reported_results=ExtractedField(
                value="99.9% accuracy",
                quote="Experimental evaluation shows that DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories.",
                section="3. Results and Discussion",
            )
        )
        val_ext, rejections = validate_extraction(bad_num, buckets, headings, "DeepEMPR", drop_failures=True)
        self.assertTrue(any("99.9" in r["reason"] for r in rejections))
        self.assertEqual(val_ext.reported_results.value, "not found")

    def test_stage4_dataset_paper_rules(self):
        sections = _extract_sections(SAMPLE_DATASET_PAPER_TEXT)
        buckets = bucket_paper_sections(SAMPLE_DATASET_PAPER_TEXT, sections)
        headings = list(sections.keys())

        ds_ext = PaperExtractionOutput(
            is_dataset_paper=True,
            dataset_name=ExtractedField(
                value="Arabica-Pest",
                quote="This paper introduces Arabica-Pest, a public benchmark image dataset for coffee leaf pathologies.",
                section="Abstract",
            ),
            model_name=ExtractedField(
                value="Deep Classifier",  # Hallucinated
                quote="",
                section="None",
            ),
            reported_results=ExtractedField(
                value="95% accuracy",  # Hallucinated
                quote="",
                section="None",
            ),
        )

        val_ext, _ = validate_extraction(ds_ext, buckets, headings, "Arabica-Pest", drop_failures=True)
        self.assertEqual(val_ext.model_name.value, "not applicable")
        self.assertEqual(val_ext.architecture.value, "not applicable")
        self.assertEqual(val_ext.reported_results.value, "not applicable")
        self.assertEqual(val_ext.evaluation_metrics.value, "not applicable")

    # -------------------------------------------------------------
    # 5. Stage 5: Assembler and Exact Match Logic
    # -------------------------------------------------------------
    async def test_stage5_exact_match_determination(self):
        # Paper 1: Mobile App with offline stated
        sections_app = _extract_sections(SAMPLE_APP_PAPER_TEXT)
        buckets_app = bucket_paper_sections(SAMPLE_APP_PAPER_TEXT, sections_app)
        cand_app = {
            "title": "Mobile-Coffee",
            "url": "https://arxiv.org/abs/2601.12109",
            "doi": "not found",
            "paper_id": "arxiv:2601.12109",
            "authors": ["Carlos Farmer"],
            "year": "2024",
        }
        ext_app = PaperExtractionOutput(
            problem_addressed=ExtractedField(
                value="Coffee leaf rust detection on smartphones",
                quote="We present Mobile-Coffee, a mobile application running on Android devices for real-time coffee leaf rust detection.",
                section="Abstract",
            ),
            reported_results=ExtractedField(
                value="94.25% accuracy, 32ms latency",
                quote="Mobile-Coffee achieved 94.25% classification accuracy. Average latency per frame was 32 milliseconds on a mid-range phone.",
                section="3. Experimental Results",
            ),
            method=ExtractedField(
                value="Android app using TensorFlow Lite",
                quote="The mobile app was built for Android smartphones using TensorFlow Lite.",
                section="2. System Design and Mobile Deployment",
            ),
            same_task=ExtractedBooleanField(
                value=True,
                quote="real-time coffee leaf rust detection.",
                section="Abstract",
            ),
            phone_app=ExtractedBooleanField(
                value=True,
                quote="The mobile app was built for Android smartphones using TensorFlow Lite.",
                section="2. System Design and Mobile Deployment",
            ),
            offline_stated=ExtractedBooleanField(
                value=True,
                quote="All inference is executed completely on the mobile phone offline without requiring an internet connection or remote server.",
                section="2. System Design and Mobile Deployment",
            ),
        )
        val_app, _ = validate_extraction(ext_app, buckets_app, list(sections_app.keys()), "Mobile-Coffee")

        # Paper 2: DeepEMPR (not a phone app)
        cand_deep = {
            "title": "DeepEMPR",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/",
            "doi": "10.1016/j.deep.2023",
            "paper_id": "pmcid:PMC8165403",
            "authors": ["Dev Team"],
            "year": "2023",
        }
        ext_deep = PaperExtractionOutput(
            problem_addressed=ExtractedField(
                value="Diagnosis system for Arabica coffee",
                quote="In this study, we propose DeepEMPR, an intelligent diagnosis system for Arabica coffee leaf diseases.",
                section="Abstract",
            ),
            dataset_size=ExtractedField(
                value="58,555 images",
                quote="A total of 58,555 images were gathered under real field conditions across multiple plantations.",
                section="2.1 Dataset Collection and Preprocessing",
            ),
            reported_results=ExtractedField(
                value="99.1% accuracy",
                quote="Experimental evaluation shows that DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories.",
                section="3. Results and Discussion",
            ),
            same_task=ExtractedBooleanField(
                value=True,
                quote="diagnosis system for Arabica coffee leaf diseases.",
                section="Abstract",
            ),
            phone_app=ExtractedBooleanField(value=False, quote="", section="not found"),
            offline_stated=ExtractedBooleanField(value=False, quote="", section="not found"),
        )
        val_deep, _ = validate_extraction(ext_deep, buckets_app, list(sections_app.keys()), "DeepEMPR")

        # Add search candidate for snippet-only entry
        self.ctx.candidate_papers_seen = [
            {"title": "Unread Candidate", "url": "https://doi.org/10.1000/unread", "authors": ["Unread Author"], "year": "2022"}
        ]

        validated_list = [
            (cand_app, val_app, list(sections_app.keys())),
            (cand_deep, val_deep, list(sections_app.keys())),
        ]

        findings_obj = await assemble_findings(self.ctx, validated_list, self.ctx.research_spec_summary)

        # Check exact matching
        self.assertTrue(findings_obj.exact_research_found)
        finding_app = next(f for f in findings_obj.findings if f.title == "Mobile-Coffee")
        self.assertEqual(finding_app.match_type, "exact")

        finding_deep = next(f for f in findings_obj.findings if f.title == "DeepEMPR")
        self.assertEqual(finding_deep.match_type, "closely_related")

        # Check snippet entry
        finding_unread = next(f for f in findings_obj.findings if f.title == "Unread Candidate")
        self.assertEqual(finding_unread.method, "not read - search snippet only")

    # -------------------------------------------------------------
    # 6. check_answers.py Compatibility Test
    # -------------------------------------------------------------
    async def test_check_answers_compatibility(self):
        # Save stored text so Check 3 passes
        stored_papers_dir = self.ctx.output_dir / "stored_papers"
        stored_papers_dir.mkdir(parents=True, exist_ok=True)
        (stored_papers_dir / "pmcid_PMC8165403.txt").write_text(SAMPLE_PAPER_TEXT, encoding="utf-8")
        (stored_papers_dir / "arxiv_2601_12109.txt").write_text(SAMPLE_APP_PAPER_TEXT, encoding="utf-8")

        # Create paper findings adhering to all 7 quality checks
        findings_data = {
            "session_id": self.session_id,
            "search_queries_run": ["coffee leaf disease mobile", "arabica leaf rust offline"],
            "exact_research_found": True,
            "findings": [
                {
                    "title": "Mobile-Coffee Application",
                    "authors": ["Carlos Farmer"],
                    "year": "2024",
                    "doi": "not found",
                    "paper_url": "https://arxiv.org/abs/2601.12109",
                    "citation": "Farmer (2024). Mobile-Coffee Application.",
                    "match_type": "exact",
                    "match_reason": "Validated edge deployment",
                    "problem_addressed": "Diagnosis of coffee leaf rust on mobile devices",
                    "research_objective": "Real-time coffee disease recognition",
                    "domain": "Mobile plant pathology",
                    "input_type": "Camera photo",
                    "output_type": "Disease label",
                    "dataset": {"name": "Field Leaves", "size": "2,400 images", "split": "not reported"},
                    "model": {"model_name": "TensorFlow Lite CNN", "architecture": "Mobile CNN"},
                    "method": "The mobile app was built for Android smartphones using TensorFlow Lite.",
                    "experiments_and_results": {
                        "reported_results": "Mobile-Coffee achieved 94.25% classification accuracy.",
                        "evaluation_metrics": "Accuracy",
                        "baseline_comparisons": "not reported",
                    },
                    "limitations": "Battery consumption increases during continuous camera stream processing.",
                    "research_gap": "not reported",
                    "code_repository": {"url": "not found"},
                    "key_evidence": [
                        {"quote": "Mobile-Coffee achieved 94.25% classification accuracy.", "section": "Results", "field": "reported_results"},
                        {"quote": "The mobile app was built for Android smartphones using TensorFlow Lite.", "section": "Methods", "field": "method"},
                    ],
                    "source_urls": ["https://arxiv.org/abs/2601.12109"],
                },
                {
                    "title": "DeepEMPR Diagnosis System",
                    "authors": ["Research Team"],
                    "year": "2023",
                    "doi": "10.1016/j.deepempr.2023",
                    "paper_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/",
                    "citation": "Research Team (2023). DeepEMPR Diagnosis System. doi:10.1016/j.deepempr.2023",
                    "match_type": "closely_related",
                    "match_reason": "High accuracy diagnosis without edge deployment proof",
                    "problem_addressed": "Plant disease diagnosis across large coffee plantations",
                    "research_objective": "Multi-class disease detection using attention networks",
                    "domain": "Agricultural deep learning",
                    "input_type": "High resolution RGB images",
                    "output_type": "Pest and disease classification",
                    "dataset": {"name": "Arabica Coffee Dataset", "size": "58,555 images", "split": "70/15/15"},
                    "model": {"model_name": "DeepEMPR", "architecture": "EfficientNetV2 with attention"},
                    "method": "We developed DeepEMPR using an improved EfficientNetV2 backbone integrated with squeeze-and-excitation attention blocks.",
                    "experiments_and_results": {
                        "reported_results": "DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories.",
                        "evaluation_metrics": "Accuracy, Precision, Recall, F1",
                        "baseline_comparisons": "ResNet-50 92.4%",
                    },
                    "limitations": "The current model was trained exclusively on daytime photos; performance under artificial night lighting has not been evaluated.",
                    "research_gap": "Future research will investigate quantization for microcontrollers.",
                    "code_repository": {"url": "not found"},
                    "key_evidence": [
                        {"quote": "DeepEMPR achieved an overall accuracy of 99.1% across all diagnostic categories.", "section": "Results", "field": "reported_results"},
                        {"quote": "A total of 58,555 images were gathered under real field conditions across multiple plantations.", "section": "Dataset", "field": "dataset_size"},
                    ],
                    "source_urls": ["https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/"],
                },
            ],
            "notes": "Research completed successfully.",
        }

        findings_path = self.ctx.output_dir / "paper_findings.json"
        findings_path.write_text(json.dumps(findings_data, indent=2), encoding="utf-8")

        results = check_findings(findings_path, self.ctx.output_dir)
        for check_name, (passed, msg) in results.items():
            self.assertTrue(passed, f"Check failed: {check_name} -> {msg}")


if __name__ == "__main__":
    unittest.main()
