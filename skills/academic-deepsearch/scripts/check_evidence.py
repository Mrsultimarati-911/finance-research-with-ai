#!/usr/bin/env python3
"""Read back local locators and validate claim references, not claim semantics.

Apache-2.0. Original implementation, 2026-10-05. Read-only; no remote fetches.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

from local_search import ensure_output_distinct, evidence_record, file_hash, scoped_path, units


def locator_key(locator):
    return json.dumps(locator, sort_keys=True, ensure_ascii=False)


def validate_locator(locator):
    if not isinstance(locator, dict):
        return False
    kind = locator.get("type")
    integer_fields = {"text": ["line_start", "line_end"], "pdf": ["physical_page"],
                      "docx_paragraph": ["paragraph_index"], "docx_table_cell": ["table_index", "row", "column"],
                      "csv_record": ["record_number", "physical_line_start", "physical_line_end"]}
    if kind == "xlsx_cell":
        import re
        return isinstance(locator.get("sheet"), str) and bool(locator["sheet"]) and isinstance(locator.get("cell"), str) and bool(re.fullmatch(r"[A-Z]+[1-9]\d*", locator["cell"]))
    if kind not in integer_fields:
        return False
    positive = all(type(locator.get(field)) is int and locator[field] >= 1 for field in integer_fields[kind])
    if not positive:
        return False
    return locator["line_end"] >= locator["line_start"] if kind == "text" else locator["physical_line_end"] >= locator["physical_line_start"] if kind == "csv_record" else True


def check_document(document, root):
    root, _ = scoped_path(root)
    result = {"schema_version": 2, "status": "passed", "scope_root": str(root), "checks": [], "claims": [],
              "meaning": "Passed means source, locator, exact extracted excerpt and citation identifiers were checked; it does not prove a claim is semantically supported.",
              "limitations": ["No remote URL is fetched or authenticated.", "Extraction layout, OCR correctness, units and semantic reasoning still require source review."]}
    evidence = document.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")
    seen = set()
    groups = defaultdict(list)
    for item in evidence:
        check = {"evidence_id": item.get("evidence_id"), "status": "pending", "source_path": item.get("source_path")}
        result["checks"].append(check)
        identifier = item.get("evidence_id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            check.update({"status": "failed", "reason": "missing_or_duplicate_evidence_id"})
            continue
        seen.add(identifier)
        if item.get("source_type") != "local_file":
            check.update({"status": "unverified", "reason": "nonlocal_source_requires_actual_host_readback"})
            continue
        if not validate_locator(item.get("locator")):
            check.update({"status": "failed", "reason": "invalid_locator"})
            continue
        if not isinstance(item.get("excerpt"), str):
            check.update({"status": "failed", "reason": "excerpt_must_be_text"})
            continue
        try:
            _, path = scoped_path(root, item["source_path"])
            if not path.is_file():
                raise ValueError("source is not a file")
            groups[str(path)].append((item, check))
        except (KeyError, OSError, ValueError) as exc:
            check.update({"status": "failed", "reason": "source_scope_or_access", "detail": str(exc)})
    for path_string, entries in groups.items():
        try:
            _, path = scoped_path(root, path_string)
            sha = file_hash(path)
            wanted = defaultdict(list)
            for item, check in entries:
                if item.get("sha256") != sha:
                    check.update({"status": "failed", "reason": "source_changed_or_hash_missing"})
                    continue
                expected_id = evidence_record(path, sha, item["locator"], item["excerpt"], {}, "")["evidence_id"]
                if item["evidence_id"] != expected_id:
                    check.update({"status": "failed", "reason": "evidence_id_does_not_match_source_locator"})
                    continue
                wanted[locator_key(item["locator"])].append((item, check))
            details = {}
            encodings = {item.get("metadata", {}).get("encoding") for item, check in entries if check["status"] == "pending"} - {None}
            if len(encodings) > 1:
                raise ValueError("conflicting evidence encoding declarations")
            header_modes = {item.get("metadata", {}).get("header_present", True) for item, check in entries if check["status"] == "pending"}
            if len(header_modes) > 1:
                raise ValueError("conflicting CSV header declarations")
            for locator, text, metadata in units(path, details, next(iter(encodings), None), next(iter(header_modes), True)):
                for item, check in wanted.pop(locator_key(locator), []):
                    declared = item.get("metadata", {})
                    # Verify extracted context/values as well as the main excerpt.
                    normalize = lambda value: json.loads(json.dumps(value, ensure_ascii=False, default=str))
                    metadata_matches = all(normalize(declared[key]) == normalize(value) for key, value in metadata.items() if key in declared)
                    check.update({"status": "failed", "reason": "excerpt_mismatch"} if item["excerpt"] != text else {"status": "failed", "reason": "extracted_metadata_mismatch"} if not metadata_matches else {"status": "unverified", "reason": "requires_visual_review", "locator_readback": "matched"} if metadata.get("needs_review") else {"status": "passed", "reason": "exact_local_readback"})
                if not wanted:
                    break
            for remaining in wanted.values():
                for _, check in remaining:
                    check.update({"status": "failed", "reason": "locator_not_found"})
        except Exception as exc:
            for _, check in entries:
                if check["status"] == "pending":
                    check.update({"status": "unverified", "reason": "readback_error", "detail": f"{type(exc).__name__}: {exc}"})
    state_by_id = {item["evidence_id"]: item["status"] for item in result["checks"]}
    claims = document.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("claims must be a list")
    for index, claim in enumerate(claims, 1):
        identifiers = claim.get("evidence_ids", [])
        missing = [identifier for identifier in identifiers if identifier not in seen] if isinstance(identifiers, list) else []
        unsupported = [identifier for identifier in identifiers if state_by_id.get(identifier) != "passed"] if isinstance(identifiers, list) else []
        status = "failed" if not isinstance(identifiers, list) or not identifiers or missing else "unverified" if unsupported else "references_checked"
        result["claims"].append({"claim_id": claim.get("claim_id", f"claim-{index}"), "status": status, "missing_evidence_ids": missing, "unverified_evidence_ids": unsupported, "semantic_support": "not_checked"})
    all_states = [item["status"] for item in result["checks"]] + [item["status"] for item in result["claims"]]
    result["status"] = "failed" if "failed" in all_states else "unverified" if "unverified" in all_states else "passed" if all_states else "no_evidence"
    return result


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.document.read_text(encoding="utf-8-sig"))
        result = check_document(document, args.root)
        content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            ensure_output_distinct(args.out, [args.document] + [item.get("source_path") for item in document.get("evidence", []) if item.get("source_type") == "local_file"])
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(content, encoding="utf-8")
            print(json.dumps({"output": str(args.out.resolve()), "status": result["status"]}))
        else:
            print(content, end="")
        return 2 if result["status"] in {"failed", "no_evidence"} else 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
