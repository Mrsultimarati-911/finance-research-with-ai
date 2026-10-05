#!/usr/bin/env python3
"""Optional structured evidence/scope check, not a semantic or factual validator.

Original project code, Apache-2.0. Methods adapted from the evidence-first
proposal workflow; changed 2026-10-05 for financial research. See PROVENANCE.md.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

LIMITATION = 'Structural checks only; verify sources, prose and methods separately'


def check_project(project):
    issues = []

    def issue(code, item, reason):
        issues.append(dict(code=code, item=item, reason=reason))

    def result():
        return dict(passed=not issues, issues=issues, limitation=LIMITATION)

    if not isinstance(project, dict):
        issue('input_error', 'project', 'Project must be a JSON object')
        return result()

    def rows(name):
        values = project.get(name, [])
        if not isinstance(values, list):
            issue('input_error', name, 'Collection must be an array of objects')
            return []
        valid = []
        for index, row in enumerate(values):
            if not isinstance(row, dict):
                issue('input_error', f'{name}[{index}]', 'Row must be an object')
            else:
                valid.append(row)
        return valid

    def nonblank(value):
        return isinstance(value, str) and bool(value.strip())

    def indexed(name):
        result = {}
        for row in rows(name):
            identifier = row.get('id')
            if not nonblank(identifier) or identifier in result:
                issue('invalid_id', name, 'IDs must be nonblank strings and unique')
            else:
                result[identifier] = row
        return result

    def references(row, field, identifier):
        values = row.get(field, [])
        if not isinstance(values, list):
            issue('input_error', identifier, f'{field} must be an array of IDs')
            return []
        valid = []
        for value in values:
            if not nonblank(value):
                issue('input_error', identifier, f'{field} entries must be nonblank string IDs')
            else:
                valid.append(value)
        return valid

    def boolean(row, field, identifier):
        if field in row and not isinstance(row[field], bool):
            issue('input_error', identifier, f'{field} must be a JSON boolean')
        return row.get(field) is True

    def allowed(value, choices):
        return isinstance(value, str) and value in choices

    questions, sources, datasets, tasks, claims = [indexed(n) for n in ('questions','sources','datasets','tasks','claims')]
    if not questions or not tasks:
        issue('empty_plan', 'project', 'A project check needs questions and research tasks')
    for identifier, question in questions.items():
        if not nonblank(question.get('text')):
            issue('invalid_question_text', identifier, 'Question must have nonblank text')
    for identifier, source in sources.items():
        if not allowed(source.get('read_range'), {'full_text','abstract','metadata','user_material'}):
            issue('invalid_read_range', identifier, 'Unknown source read range')
    for identifier, data in datasets.items():
        if not allowed(data.get('status'), {'available','permission_pending','unknown'}):
            issue('invalid_data_status', identifier, 'Unknown data availability status')
    for identifier, claim in claims.items():
        ids = references(claim, 'source_ids', identifier)
        ranges = [sources[x].get('read_range') for x in ids if x in sources]
        for key in ids:
            if key not in sources: issue('unknown_source', identifier, key)
        kind = claim.get('kind')
        if not allowed(kind, {'literature_fact','user_fact','hypothesis','analysis'}):
            issue('invalid_claim_kind', identifier, str(kind))
        if kind == 'literature_fact' and not any(r in ('abstract','full_text') for r in ranges):
            issue('insufficient_evidence', identifier, 'Literature fact needs read abstract/full text')
        if kind == 'user_fact' and 'user_material' not in ranges:
            issue('unsupported_user_fact', identifier, 'Team/data facts need user material')
        if boolean(claim, 'requires_full_text', identifier) and 'full_text' not in ranges:
            issue('full_text_required', identifier, 'Requested detail exceeds read range')
    covered = set()
    for identifier, task in tasks.items():
        question_ids = references(task, 'question_ids', identifier)
        dataset_ids = references(task, 'dataset_ids', identifier)
        conditional = boolean(task, 'conditional', identifier)
        if not question_ids:
            issue('task_without_question', identifier, 'Task must answer a question')
        for key in question_ids:
            if key not in questions: issue('unknown_question', identifier, key)
            else: covered.add(key)
        for key in dataset_ids:
            if key not in datasets: issue('unknown_dataset', identifier, key)
            elif datasets[key].get('status') != 'available' and not conditional:
                issue('unconfirmed_data_commitment', identifier, key)
    for identifier in sorted(questions.keys() - covered):
        issue('uncovered_question', identifier, 'No research task covers question')
    for material in rows('materials'):
        if not nonblank(material.get('name')):
            issue('input_error', 'materials', 'Material must have a nonblank name')
        if not allowed(material.get('status'), {'available','permission_pending','unknown'}):
            issue('invalid_material_status', material.get('name'), 'Unknown material availability status')
        if material.get('status') != 'available' and material.get('marker') != '待补':
            issue('missing_marker', material.get('name'), 'Unknown materials must be marked 待补')
    if 'template_sections' in project or 'draft_sections' in project:
        for field in ('template_sections', 'draft_sections'):
            if field in project:
                headings = project[field]
                if not isinstance(headings, list) or not headings or not all(nonblank(h) for h in headings):
                    issue('input_error', field, 'Sections must be a nonempty array of nonblank headings')
        paired = all(field in project for field in ('template_sections', 'draft_sections'))
        if not paired or project['template_sections'] != project['draft_sections']:
            issue('template_mismatch', 'sections', 'Given template and draft sections must both be supplied and match')
    if 'untouched_before' in project or 'untouched_after' in project:
        for field in ('untouched_before', 'untouched_after'):
            if field in project:
                sections = project[field]
                if not isinstance(sections, dict) or not all(nonblank(k) and isinstance(v, str) for k, v in sections.items()):
                    issue('input_error', field, 'Untouched sections must map nonblank headings to text')
        paired = all(field in project for field in ('untouched_before', 'untouched_after'))
        if not paired or project['untouched_before'] != project['untouched_after']:
            issue('scope_changed', 'untouched_sections', 'Before and after sections must both be supplied and match')
    return result()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    args = parser.parse_args()
    try:
        result = check_project(json.loads(Path(args.input).read_text(encoding='utf-8-sig')))
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        result = dict(passed=False, issues=[dict(code='input_error', reason=str(exc))], limitation=LIMITATION)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
