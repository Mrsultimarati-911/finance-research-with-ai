"""Check local Markdown resources and math syntax; does not verify source claims."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def prose_lines(text: str):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        match = re.match(r"(`{3,}|~{3,})", stripped)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            yield number, ""
            continue
        if fence is None:
            yield number, re.sub(r"(`+).*?\1", "", line)


def heading_ids(text: str) -> set[str]:
    ids = set(re.findall(r'<[^>]+\bid=["\']([^"\']+)["\']', text))
    seen = {}
    for _, line in prose_lines(text):
        match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
        slug = re.sub(r"[^\w\-\s]", "", title).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        ids.add(slug if count == 0 else f"{slug}-{count}")
    return ids


def math_errors(block: str, line: int) -> list[str]:
    errors, depth = [], 0
    for char in re.sub(r"\\[{}]", "", block):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                errors.append(f"line {line}: unexpected closing math brace")
                depth = 0
    if depth:
        errors.append(f"line {line}: unclosed math brace")
    stack = []
    for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", block):
        action, environment = match.groups()
        if action == "begin":
            stack.append(environment)
        elif not stack or stack.pop() != environment:
            errors.append(f"line {line}: mismatched math environment {environment}")
    if stack:
        errors.append(f"line {line}: unclosed math environment")
    return errors


def check(path: Path) -> dict:
    path = path.resolve()
    text = path.read_text(encoding="utf-8-sig")
    errors, warnings, resource_count, math_count = [], [], 0, 0
    numbered = list(prose_lines(text))
    content = "\n".join(line for _, line in numbered)
    pattern = re.compile(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+\"[^\"]*\")?\)")
    for match in pattern.finditer(content):
        target = match.group(1) or match.group(2)
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) and not re.match(r"^[a-zA-Z]:[/\\]", target):
            continue
        raw_file, _, fragment = target.partition("#")
        resource = (path.parent / unquote(raw_file)).resolve() if raw_file else path
        resource_count += 1
        if not resource.exists():
            errors.append(f"missing local resource: {target}")
        elif fragment and resource.is_file() and resource.suffix.lower() == ".md":
            anchors = heading_ids(resource.read_text(encoding="utf-8-sig"))
            if unquote(fragment) not in anchors:
                errors.append(f"missing anchor: {target}")
    display_start, display = None, []
    for number, line in numbered:
        delimiters = list(re.finditer(r"(?<!\\)\$\$", line))
        if delimiters:
            if line.strip() != "$$":
                warnings.append(f"line {number}: put display delimiters on separate lines")
            # Scan every delimiter so same-line math can still be balanced.
            cursor = 0
            for delimiter in delimiters:
                segment = line[cursor:delimiter.start()]
                if display_start is not None:
                    display.append(segment)
                    errors.extend(math_errors("\n".join(display), display_start))
                    math_count += 1
                    display_start, display = None, []
                else:
                    display_start, display = number, []
                cursor = delimiter.end()
            if display_start is not None:
                display.append(line[cursor:])
            continue
        if display_start is not None:
            display.append(line)
            continue
        dollars = list(re.finditer(r"(?<!\\)\$", line))
        if len(dollars) % 2:
            errors.append(f"line {number}: unpaired inline dollar delimiter; escape literal currency dollars")
        for a, b in zip(dollars[::2], dollars[1::2]):
            errors.extend(math_errors(line[a.end():b.start()], number))
            math_count += 1
    if display_start is not None:
        errors.append(f"line {display_start}: unclosed display math")
    return {"file": str(path), "errors": errors, "warnings": warnings,
            "local_resources_checked": resource_count, "math_blocks_checked": math_count,
            "scope": "Local resources and basic math syntax only; source fidelity not certified."}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=Path, nargs="+")
    args = parser.parse_args()
    reports = []
    for path in args.files:
        try:
            reports.append(check(path))
        except (OSError, UnicodeError) as exc:
            reports.append({"file": str(path), "errors": [str(exc)], "warnings": []})
    print(json.dumps({"reports": reports}, ensure_ascii=False, indent=2))
    return 1 if any(report["errors"] for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
