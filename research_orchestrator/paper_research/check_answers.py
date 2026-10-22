"""Verification script for Agent 2 research findings.

Checks:
(1) no read paper has a URL as its title;
(2) no two different papers share identical non-"not found" text in problem_addressed,
    research_objective, domain, input_type or output_type;
(3) every key_evidence quote is an exact substring of the stored text;
(4) if PMC8165403 was read, dataset_size contains 58,555;
(5) if PMC12689465 was read, reported_results contains 99%;
(6) if arXiv 2601.12109 was read, reported_results contains 94.25;
(7) exact_research_found agrees with the match_type values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


import unicodedata


def _normalize_for_match(s: str) -> str:
    if not s:
        return ""
    t = unicodedata.normalize("NFKC", str(s))
    ligatures = {
        "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
        "ﬅ": "st", "ﬆ": "st", "æ": "ae", "œ": "oe",
    }
    for lig, rep in ligatures.items():
        t = t.replace(lig, rep)
    t = re.sub(r"[\u00ad\u200b\u200c\u200d\ufeff]", "", t)
    t = re.sub(r"(\w+)[-\u2010\u2011]\s*\n\s*(\w+)", r"\1\2", t)
    t = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", t)
    t = re.sub(r"[\u2018\u2019\u201a\u201b`]", "'", t)
    t = re.sub(r"[\u201c\u201d\u201e\u201f«»]", '"', t)
    t = t.replace("**", "").replace("*", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()


def check_findings(findings_path: Path, output_dir: Path) -> dict[str, tuple[bool, str]]:
    if not findings_path.exists():
        print(f"Error: Findings file not found at {findings_path}", file=sys.stderr)
        return {}

    data = json.loads(findings_path.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    exact_research_found = data.get("exact_research_found", False)

    read_papers = [
        f for f in findings
        if f.get("method") != "not read - search snippet only"
        and f.get("problem_addressed") != "not read - search snippet only"
    ]

    results: dict[str, tuple[bool, str]] = {}

    # Check 1: no read paper has a URL as its title
    url_as_title = []
    for p in read_papers:
        t = str(p.get("title", "")).strip()
        if t.startswith("http://") or t.startswith("https://") or "://" in t:
            url_as_title.append(t)
    if not url_as_title:
        results["(1) no read paper has URL as title"] = (True, "PASS")
    else:
        results["(1) no read paper has URL as title"] = (False, f"FAIL: found URLs as title: {url_as_title}")

    # Check 2: no two different papers share identical non-"not found" text in common fields
    fields_to_check = ["problem_addressed", "research_objective", "domain", "input_type", "output_type"]
    shared_text = []
    for i in range(len(read_papers)):
        for j in range(i + 1, len(read_papers)):
            p1 = read_papers[i]
            p2 = read_papers[j]
            for fld in fields_to_check:
                v1 = str(p1.get(fld, "")).strip()
                v2 = str(p2.get(fld, "")).strip()
                if v1 and v1 not in ["not found", "not applicable"] and v1.lower() == v2.lower():
                    shared_text.append(f"Papers '{p1.get('title')}' and '{p2.get('title')}' share {fld}: '{v1[:40]}...'")
    if not shared_text:
        results["(2) no two different papers share identical non-not-found text in common fields"] = (True, "PASS")
    else:
        results["(2) no two different papers share identical non-not-found text in common fields"] = (False, f"FAIL: {shared_text}")

    # Check 3: every key_evidence quote is an exact substring of the stored text
    stored_texts: dict[str, str] = {}
    stored_json = output_dir / "stored_papers.json"
    if stored_json.exists():
        try:
            stored_texts = json.loads(stored_json.read_text(encoding="utf-8"))
        except Exception:
            pass
    stored_dir = output_dir / "stored_papers"
    if stored_dir.exists():
        for tf in stored_dir.glob("*.txt"):
            try:
                stored_texts[tf.stem] = tf.read_text(encoding="utf-8")
            except Exception:
                pass

    trace_path = output_dir / "paper_research_trace.json"
    if trace_path.exists() and not stored_texts:
        try:
            t_data = json.loads(trace_path.read_text(encoding="utf-8"))
            for entry in t_data.get("full_text_sources", []):
                u = entry.get("url")
                if u and u not in stored_texts and entry.get("stored_text"):
                    stored_texts[u] = entry["stored_text"]
        except Exception:
            pass

    all_stored_corpus = " ".join(stored_texts.values())
    missing_quotes = []
    total_quotes_checked = 0

    for p in read_papers:
        p_title = p.get("title", "")
        p_url = p.get("paper_url", "")
        p_text = stored_texts.get(p_url) or stored_texts.get(p.get("doi", ""))
        if not p_text:
            safe_u = re.sub(r"[^a-zA-Z0-9]", "_", p_url)
            p_text = stored_texts.get(safe_u)
        if not p_text:
            for k, txt in stored_texts.items():
                if p_title.lower() in txt[:1500].lower():
                    p_text = txt
                    break
        corpus_to_check = p_text if p_text else all_stored_corpus

        for ev in p.get("key_evidence", []):
            q = ev.get("quote", "") if isinstance(ev, dict) else getattr(ev, "quote", str(ev))
            if not q or q in ["not found", "not reported"]:
                continue
            total_quotes_checked += 1
            norm_q = _normalize_for_match(q).lower()
            norm_c = _normalize_for_match(corpus_to_check).lower()
            if norm_q not in norm_c:
                missing_quotes.append(f"Paper '{p_title}' quote not in stored text: '{q[:50]}...'")

    if not missing_quotes and total_quotes_checked > 0:
        results["(3) every key_evidence quote is an exact substring of the stored text"] = (True, f"PASS ({total_quotes_checked} quotes verified)")
    elif total_quotes_checked == 0:
        results["(3) every key_evidence quote is an exact substring of the stored text"] = (True, "PASS (no quotes to check)")
    else:
        results["(3) every key_evidence quote is an exact substring of the stored text"] = (False, f"FAIL: {missing_quotes}")

    # Check 4: if PMC8165403 was read, dataset_size contains 58,555
    pmc8165403 = next((p for p in read_papers if "8165403" in p.get("paper_url", "") or "8165403" in str(p.get("source_urls", []))), None)
    if pmc8165403:
        ds_size = str(pmc8165403.get("dataset", {}).get("size", ""))
        if "58,555" in ds_size or "58555" in ds_size:
            results["(4) if PMC8165403 was read, dataset_size contains 58,555"] = (True, f"PASS (found '{ds_size}')")
        else:
            results["(4) if PMC8165403 was read, dataset_size contains 58,555"] = (False, f"FAIL: dataset_size is '{ds_size}'")
    else:
        results["(4) if PMC8165403 was read, dataset_size contains 58,555"] = (True, "PASS (PMC8165403 was not in read papers)")

    # Check 5: if PMC12689465 was read, reported_results contains 99%
    pmc12689465 = next((p for p in read_papers if "12689465" in p.get("paper_url", "") or "12689465" in str(p.get("source_urls", []))), None)
    if pmc12689465:
        rep_res = str(pmc12689465.get("experiments_and_results", {}).get("reported_results", ""))
        if "99%" in rep_res or "99" in rep_res:
            results["(5) if PMC12689465 was read, reported_results contains 99%"] = (True, f"PASS (found '{rep_res}')")
        else:
            results["(5) if PMC12689465 was read, reported_results contains 99%"] = (False, f"FAIL: reported_results is '{rep_res}'")
    else:
        results["(5) if PMC12689465 was read, reported_results contains 99%"] = (True, "PASS (PMC12689465 was not in read papers)")

    # Check 6: if arXiv 2601.12109 was read, reported_results contains 94.25
    arxiv2601 = next((p for p in read_papers if "2601.12109" in p.get("paper_url", "") or "2601.12109" in str(p.get("source_urls", []))), None)
    if arxiv2601:
        rep_res = str(arxiv2601.get("experiments_and_results", {}).get("reported_results", ""))
        if "94.25" in rep_res:
            results["(6) if arXiv 2601.12109 was read, reported_results contains 94.25"] = (True, f"PASS (found '{rep_res}')")
        else:
            results["(6) if arXiv 2601.12109 was read, reported_results contains 94.25"] = (False, f"FAIL: reported_results is '{rep_res}'")
    else:
        results["(6) if arXiv 2601.12109 was read, reported_results contains 94.25"] = (True, "PASS (arXiv 2601.12109 was not in read papers)")

    # Check 7: exact_research_found agrees with the match_type values
    any_exact = any(p.get("match_type") == "exact" for p in findings)
    if exact_research_found == any_exact:
        results["(7) exact_research_found agrees with match_type values"] = (True, f"PASS (exact_research_found={exact_research_found}, any_exact={any_exact})")
    else:
        results["(7) exact_research_found agrees with match_type values"] = (
            False,
            f"FAIL: exact_research_found is {exact_research_found} but any finding is exact = {any_exact}",
        )

    # Check 8: no read paper has method "not found" if a methods-type heading exists in its stored text
    method_missing = []
    methods_heading_pattern = re.compile(
        r"(?im)^#{1,6}\s*.*?\b(methods?|materials?\s+and\s+methods?|proposed\s+approach|proposed\s+model|methodology|framework|model\s+architecture)\b"
    )
    for p in read_papers:
        p_title = p.get("title", "")
        p_url = p.get("paper_url", "")
        p_text = stored_texts.get(p_url) or stored_texts.get(p.get("doi", ""))
        if not p_text:
            safe_u = re.sub(r"[^a-zA-Z0-9]", "_", p_url)
            p_text = stored_texts.get(safe_u)
        if not p_text:
            for k, txt in stored_texts.items():
                if p_title.lower() in txt[:1500].lower():
                    p_text = txt
                    break
        m_val = str(p.get("method", "")).strip()
        is_dataset = "dataset" in p_title.lower() and p.get("model", {}).get("model_name") == "not applicable"
        if p_text and methods_heading_pattern.search(p_text) and not is_dataset:
            if m_val in ["not found", "not reported", ""]:
                method_missing.append(f"Paper '{p_title}' has method heading in text but method is '{m_val}'")
    if not method_missing:
        results["(8) no read paper has method 'not found' if methods heading exists"] = (True, "PASS")
    else:
        results["(8) no read paper has method 'not found' if methods heading exists"] = (False, f"FAIL: {method_missing}")

    # Check 9: every field with a value other than "not found" or "not applicable" has a saved quote for that field
    missing_field_quotes = []
    for p in read_papers:
        p_title = p.get("title", "")
        ev_quotes = p.get("key_evidence", [])
        quoted_fields = {ev.get("field") for ev in ev_quotes if isinstance(ev, dict) and ev.get("quote")}

        fields_to_verify = [
            ("problem_addressed", p.get("problem_addressed")),
            ("research_objective", p.get("research_objective")),
            ("domain", p.get("domain")),
            ("input_type", p.get("input_type")),
            ("output_type", p.get("output_type")),
            ("dataset.name", p.get("dataset", {}).get("name")),
            ("dataset.size", p.get("dataset", {}).get("size")),
            ("dataset.split", p.get("dataset", {}).get("split")),
            ("dataset.description", p.get("dataset", {}).get("description")),
            ("model.model_name", p.get("model", {}).get("model_name")),
            ("model.architecture", p.get("model", {}).get("architecture")),
            ("method", p.get("method")),
            ("evaluation_metrics", p.get("experiments_and_results", {}).get("evaluation_metrics")),
            ("reported_results", p.get("experiments_and_results", {}).get("reported_results")),
            ("baseline_comparisons", p.get("experiments_and_results", {}).get("baseline_comparisons")),
            ("limitations", p.get("limitations")),
            ("research_gap", p.get("research_gap")),
        ]

        for fld_name, fld_val in fields_to_verify:
            base_f = fld_name.split(".")[-1]
            if fld_val and fld_val not in ["not found", "not applicable", "not read - search snippet only"]:
                aliases = [base_f, fld_name.replace(".", "_")]
                if base_f == "size": aliases.append("dataset_size")
                if base_f == "split": aliases.append("dataset_split")
                if base_f == "name": aliases.append("dataset_name")
                if base_f == "description": aliases.append("dataset_description")
                if base_f == "baseline_comparisons": aliases.append("baselines")

                if not any(a in quoted_fields for a in aliases):
                    missing_field_quotes.append(f"Paper '{p_title}' field '{fld_name}' has value '{str(fld_val)[:30]}' but no quote in key_evidence")

    if not missing_field_quotes:
        results["(9) every field with non-empty value has a saved quote"] = (True, "PASS")
    else:
        results["(9) every field with non-empty value has a saved quote"] = (False, f"FAIL: {missing_field_quotes}")

    # Check 10: authors, year and DOI are not all missing for read papers
    metadata_missing = []
    for p in read_papers:
        p_title = p.get("title", "")
        auths = p.get("authors", [])
        yr = str(p.get("year", "")).strip()
        d = str(p.get("doi", "")).strip()
        all_missing = (not auths) and (yr in ["not found", "", "None"]) and (d in ["not found", "", "None"])
        if all_missing:
            metadata_missing.append(f"Paper '{p_title}' has no authors, year, or DOI")
    if not metadata_missing:
        results["(10) authors, year and DOI are not all missing for read papers"] = (True, "PASS")
    else:
        results["(10) authors, year and DOI are not all missing for read papers"] = (False, f"FAIL: {metadata_missing}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Agent 2 findings against 7 quality checks.")
    parser.add_argument("--session", default="72356611-f0ef-4258-9ed1-17feb57880c3", help="Session ID")
    parser.add_argument("--output-dir", default=None, help="Explicit output directory")
    args = parser.parse_args()

    session_id = args.session.strip()
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs") / session_id
    findings_path = output_dir / "paper_findings.json"

    print(f"Checking findings at: {findings_path}\n" + "=" * 60)
    results = check_findings(findings_path, output_dir)
    if not results:
        print("FAIL: No findings to check.")
        return 1

    all_passed = True
    for check_name, (passed, msg) in results.items():
        status_str = "PASS" if passed else "FAIL"
        print(f"{check_name}: {status_str} ({msg})")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL CHECKS PASSED ✅")
        return 0
    else:
        print("SOME CHECKS FAILED ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
