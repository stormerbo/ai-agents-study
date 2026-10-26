"""Offline fixture for comparing single-agent and multi-agent orchestration.

This module measures only its deterministic fixture. It makes no model-quality
or production-latency claim.
"""

import json


TASKS = (
    {'id': 'case-01', 'kind': 'refund'},
    {'id': 'case-02', 'kind': 'delivery'},
    {'id': 'case-03', 'kind': 'account'},
)

EXPECTED = {
    'case-01': 'refund: allow',
    'case-02': 'delivery: inspect',
    'case-03': 'account: verify',
}

FIXTURES = {
    ('single', 'case-01'): ('{"answer":"refund: allow"}', 120, 30, 11),
    ('single', 'case-02'): ('{"answer":"delivery: inspect"}', 118, 31, 12),
    ('single', 'case-03'): ('{"answer":"account: verify"}', 117, 29, 10),
    ('classifier', 'case-01'): ('{"route":"refund"}', 90, 8, 5),
    ('classifier', 'case-02'): ('{"route":"delivery"}', 90, 8, 5),
    ('classifier', 'case-03'): ('{"route":"account"}', 90, 8, 5),
    ('policy', 'case-01'): ('{"decision":"allow"}', 82, 7, 4),
    ('policy', 'case-02'): ('{"decision":"inspect"}', 82, 7, 4),
    ('policy', 'case-03'): ('{"decision":"verify"}', 82, 7, 4),
    ('synthesizer', 'case-01'): ('{"answer":"refund: allow"}', 105, 12, 6),
    ('synthesizer', 'case-02'): ('{"answer":"delivery: inspect"}', 105, 12, 6),
    ('synthesizer', 'case-03'): ('{"answer":"account: verify"}', 105, 12, 6),
}


class FixtureFailure(Exception):
    """A controlled worker failure in the offline exercise."""


class FixtureModel:
    def __init__(self, failure=None):
        self.failure = failure
        self.trace = []
        self.input_tokens = 0
        self.output_tokens = 0
        self.fixture_elapsed_ms = 0
        self.call_count = 0

    def call(self, role, task_id, context=None):
        raw, input_tokens, output_tokens, latency_ms = FIXTURES[(role, task_id)]
        if self.failure and role == 'classifier' and task_id == TASKS[0]['id']:
            if self.failure == 'timeout':
                raw = None
            elif self.failure == 'invalid_result':
                raw = 'not-json'
            elif self.failure == 'refusal':
                raw = '{"refusal":"cannot classify"}'
            elif self.failure == 'duplicate_key':
                raw = '{"route":"refund","route":"account"}'
        self.trace.append({
            'type': 'model_call',
            'role': role,
            'task_id': task_id,
            'input': context or {'task_id': task_id},
            'output': raw,
        })
        self.call_count += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.fixture_elapsed_ms += latency_ms
        if raw is None:
            raise FixtureFailure('worker_timeout')
        return raw

    def handoff(self, task_id, source, target, payload):
        self.trace.append({
            'type': 'handoff',
            'task_id': task_id,
            'from': source,
            'to': target,
            'payload': payload,
        })


def _object_without_duplicate_keys(raw):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as error:
        raise ValueError('invalid_json') from error
    if not isinstance(value, dict):
        raise ValueError('result_must_be_object')
    return value


def _run_result(model, status, cases):
    return {
        'status': status,
        'case_ids': [task['id'] for task in TASKS],
        'cases': cases,
        'calls': model.call_count,
        'input_tokens': model.input_tokens,
        'output_tokens': model.output_tokens,
        'fixture_elapsed_ms': model.fixture_elapsed_ms,
        'trace': model.trace,
    }


def run_single():
    model = FixtureModel()
    cases = []
    for task in TASKS:
        try:
            result = _object_without_duplicate_keys(model.call(
                'single', task['id'], {'task': task}
            ))
            answer = result.get('answer')
            if not isinstance(answer, str):
                raise ValueError('missing_answer')
        except (FixtureFailure, ValueError, json.JSONDecodeError) as error:
            return _run_result(model, 'failed', cases + [
                {
                    'case_id': task['id'],
                    'status': 'failed',
                    'error': str(error),
                    'answer': None,
                }
            ])
        cases.append({
            'case_id': task['id'],
            'status': 'completed',
            'answer': answer,
            'fixture_match': answer == EXPECTED[task['id']],
        })
    return _run_result(model, 'completed', cases)


def run_multi(failure=None):
    model = FixtureModel(failure=failure)
    cases = []
    for task in TASKS:
        try:
            classification = _object_without_duplicate_keys(
                model.call('classifier', task['id'], {'task': task})
            )
            if 'refusal' in classification:
                raise ValueError('worker_refusal')
            route = classification.get('route')
            if route != task['kind']:
                raise ValueError('invalid_route')
            model.handoff(task['id'], 'classifier', 'policy', {'route': route})
            policy = _object_without_duplicate_keys(
                model.call('policy', task['id'], {'route': route})
            ).get('decision')
            if not isinstance(policy, str) or not policy:
                raise ValueError('invalid_policy_result')
            model.handoff(
                task['id'], 'policy', 'synthesizer',
                {'route': route, 'decision': policy},
            )
            answer = _object_without_duplicate_keys(
                model.call(
                    'synthesizer', task['id'],
                    {'route': route, 'decision': policy},
                )
            ).get('answer')
            if not isinstance(answer, str):
                raise ValueError('missing_answer')
        except (FixtureFailure, ValueError, json.JSONDecodeError) as error:
            cases.append({
                'case_id': task['id'],
                'status': 'failed',
                'error': str(error),
                'answer': None,
            })
            return _run_result(model, 'failed', cases)
        cases.append({
            'case_id': task['id'],
            'status': 'completed',
            'answer': answer,
            'fixture_match': answer == EXPECTED[task['id']],
        })
    return _run_result(model, 'completed', cases)
