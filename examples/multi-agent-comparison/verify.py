"""Run the deterministic single-agent/multi-agent comparison fixture."""

import json

from comparison import run_multi, run_single


def summarize(result):
    return {
        'status': result['status'],
        'fixture_matches': sum(
            case.get('fixture_match', False) for case in result['cases']
        ),
        'cases': len(result['case_ids']),
        'calls': result['calls'],
        'input_tokens': result['input_tokens'],
        'output_tokens': result['output_tokens'],
        'fixture_elapsed_ms': result['fixture_elapsed_ms'],
    }


def main():
    single = run_single()
    multi = run_multi()
    drills = {
        failure: run_multi(failure=failure)
        for failure in ('timeout', 'invalid_result', 'refusal', 'duplicate_key')
    }
    assert single['case_ids'] == multi['case_ids']
    assert single['cases'] == multi['cases']
    assert single['status'] == multi['status'] == 'completed'
    assert all(result['status'] == 'failed' for result in drills.values())
    print(json.dumps({
        'notice': 'Fixture-only orchestration evidence; not a model-quality claim.',
        'single_agent': summarize(single),
        'multi_agent': summarize(multi),
        'failure_drills': {
            failure: {
                'status': result['status'],
                'error': result['cases'][0]['error'],
                'model_roles_called': [
                    event['role'] for event in result['trace']
                    if event['type'] == 'model_call'
                ],
            }
            for failure, result in drills.items()
        },
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
