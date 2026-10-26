"""Score two prompt-result files on one frozen dataset."""

import argparse
import hashlib
import json
from pathlib import Path

from score import ScoreError, score_pair


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ScoreError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _reject_constant(value):
    raise ScoreError(f'non-finite JSON number: {value}')


def _read_json(path):
    try:
        return json.loads(
            Path(path).read_text(encoding='utf-8'),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ScoreError(f'cannot read JSON artifact: {path}') from error


def canonical_dataset_sha256(dataset):
    encoded = json.dumps(
        dataset,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--before', required=True)
    parser.add_argument('--after', required=True)
    args = parser.parse_args()
    try:
        dataset = _read_json(args.dataset)
        before = _read_json(args.before)
        after = _read_json(args.after)
        digest = canonical_dataset_sha256(dataset)
        if before.get('dataset_sha256') != digest or after.get('dataset_sha256') != digest:
            raise ScoreError('run dataset hash does not match frozen dataset')
        report = score_pair(dataset, before, after)
        report['dataset_sha256'] = digest
        report['notice'] = (
            'Exact-match fixture score; it does not establish semantic quality '
            'or generalize beyond this dataset.'
        )
    except ScoreError as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
