"""Score paired prompt versions against the same frozen extraction dataset."""

import unicodedata


class ScoreError(ValueError):
    """The dataset or run pair cannot support a fair comparison."""


def _require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ScoreError(f'{label} must be a non-empty string')
    return value


def _normalize(value):
    return unicodedata.normalize('NFC', value.strip())


def _validate_dataset(dataset):
    if not isinstance(dataset, dict):
        raise ScoreError('dataset must be an object')
    version = _require_text(dataset.get('version'), 'dataset version')
    fields = dataset.get('fields')
    cases = dataset.get('cases')
    if (not isinstance(fields, list) or not fields
            or not all(isinstance(field, str) and field.strip() for field in fields)
            or len(fields) != len(set(fields))):
        raise ScoreError('dataset fields must be unique non-empty strings')
    if not isinstance(cases, list) or not cases:
        raise ScoreError('dataset cases must be a non-empty list')
    expected_by_id = {}
    for case in cases:
        if not isinstance(case, dict):
            raise ScoreError('each dataset case must be an object')
        case_id = _require_text(case.get('id'), 'case id')
        expected = case.get('expected')
        if case_id in expected_by_id:
            raise ScoreError(f'duplicate dataset case id: {case_id}')
        if (not isinstance(expected, dict) or set(expected) != set(fields)
                or not all(isinstance(value, str) for value in expected.values())):
            raise ScoreError(f'case has invalid expected fields: {case_id}')
        expected_by_id[case_id] = expected
    return version, fields, expected_by_id


def _validate_run(run, dataset_version, expected_ids, label):
    if not isinstance(run, dict):
        raise ScoreError(f'{label} run must be an object')
    if run.get('dataset_version') != dataset_version:
        raise ScoreError(f'{label} run uses a different dataset version')
    prompt_version = _require_text(run.get('prompt_version'), f'{label} prompt version')
    results = run.get('results')
    if not isinstance(results, list):
        raise ScoreError(f'{label} results must be a list')
    by_id = {}
    for result in results:
        if not isinstance(result, dict):
            raise ScoreError(f'{label} result must be an object')
        case_id = _require_text(result.get('case_id'), f'{label} case id')
        if case_id in by_id:
            raise ScoreError(f'{label} run has duplicate case id: {case_id}')
        if result.get('status') not in ('ok', 'error'):
            raise ScoreError(f'{label} result has invalid status: {case_id}')
        if result['status'] == 'error' and 'output' in result:
            raise ScoreError(f'{label} failed result must not contain output: {case_id}')
        by_id[case_id] = result
    if set(by_id) != expected_ids:
        raise ScoreError(f'{label} result case set differs from frozen dataset')
    return prompt_version, by_id


def _evaluate(fields, expected_by_id, result_by_id):
    structural_successes = 0
    exact_successes = 0
    field_successes = {field: 0 for field in fields}
    per_case = {}
    failed_runs = 0
    for case_id, expected in expected_by_id.items():
        result = result_by_id[case_id]
        output = result.get('output') if result['status'] == 'ok' else None
        if result['status'] == 'error':
            failed_runs += 1
        shape_ok = (
            isinstance(output, dict)
            and set(output) == set(fields)
            and all(isinstance(value, str) for value in output.values())
        )
        if shape_ok:
            structural_successes += 1
        field_matches = {
            field: bool(shape_ok and _normalize(output[field]) == _normalize(expected[field]))
            for field in fields
        }
        for field, matches in field_matches.items():
            field_successes[field] += int(matches)
        exact = bool(shape_ok and all(field_matches.values()))
        exact_successes += int(exact)
        per_case[case_id] = {'exact_match': exact, 'field_matches': field_matches}
    denominator = len(expected_by_id)
    return {
        'cases': denominator,
        'structural_success': structural_successes / denominator,
        'exact_match': exact_successes / denominator,
        'field_accuracy': {
            field: count / denominator for field, count in field_successes.items()
        },
        'failed_runs': failed_runs,
        'per_case': per_case,
    }


def score_pair(dataset, before, after):
    dataset_version, fields, expected_by_id = _validate_dataset(dataset)
    expected_ids = set(expected_by_id)
    before_version, before_results = _validate_run(
        before, dataset_version, expected_ids, 'before'
    )
    after_version, after_results = _validate_run(
        after, dataset_version, expected_ids, 'after'
    )
    before_score = _evaluate(fields, expected_by_id, before_results)
    after_score = _evaluate(fields, expected_by_id, after_results)
    regressions = [
        case_id for case_id in expected_by_id
        if before_score['per_case'][case_id]['exact_match']
        and not after_score['per_case'][case_id]['exact_match']
    ]
    field_regressions = {
        field: [
            case_id for case_id in expected_by_id
            if before_score['per_case'][case_id]['field_matches'][field]
            and not after_score['per_case'][case_id]['field_matches'][field]
        ]
        for field in fields
    }
    return {
        'dataset_version': dataset_version,
        'before_prompt_version': before_version,
        'after_prompt_version': after_version,
        'cases': len(expected_by_id),
        'before': before_score,
        'after': after_score,
        'exact_match_delta': after_score['exact_match'] - before_score['exact_match'],
        'regressed_cases': regressions,
        'field_regressions': field_regressions,
    }
