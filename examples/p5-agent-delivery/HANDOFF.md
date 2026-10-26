# Independent handoff record

Use this packet only after a release candidate has a clean commit and immutable
image digest. The operator must not have implemented the candidate. Copy
[`HANDOFF-RECORD.template.json`](HANDOFF-RECORD.template.json) to a new,
append-only record location; never overwrite an earlier run. This blank
template is preparation, not evidence that a handoff, review, or release passed.
Use stable identity-system subject IDs in the JSON; do not enter names, email
addresses, or credentials. Validate the completed JSON against
[`HANDOFF-RECORD.schema.json`](HANDOFF-RECORD.schema.json) (JSON Schema 2020-12)
before storing it. The schema checks record shape and allowed status values; it
does not verify that identities, evidence, signatures, or reported events are
authentic. `record_status: complete` means the record has been filled out; it
does not mean the handoff or release was accepted. Change the template and
schema together, and version the schema when the record contract changes. Keep a
completed copy in the access-controlled evidence store, outside Git. For the
formal blind-holdout authorization
preflight, also complete the project
[`official holdout run record`](../../docs/superpowers/templates/official-holdout-run-record.md).
Version 3 records the deployment assurance profile. Keep the blank template at
`local-reference` until a named risk owner and service trust domains have been
reviewed. `single-authority-v1` requires the risk owner, append-authority and
key-custodian domains, plus an explicit statement that compromise of that
authority is out of scope. If that compromise is in scope, select
`dual-witness-v1`, identify the separate witness domain and pinned witness root,
and record the terminal witness receipt digest for a finished holdout. The
schema checks required fields and formats; a reviewer must still establish that
the domains and identities are actually independent. A historical anchor does
not substitute for the witness receipt. These fields are declarations only:
the v3 record does not cryptographically prove risk-owner approval or reviewer
sign-off. A release must retain separate signed attestations bound to the exact
frozen-spec and handoff digests before claiming that the profile was approved.
The local acceptance prototype can verify their Ed25519 signatures when verifier-owned individual signer keys and the handoff digest are pinned. This does not independently prove the key-to-person mapping, organizational role authorization, or live key revocation; production identity-root/IdP verification remains open.
The registry records one-time permission and status; a separate data service
delivers test inputs and releases answer labels to the scorer only after the
candidate runtime closes. The one-time data capability is a secret: pass it only
to the trusted runtime/data service, never copy it into this handoff record, logs,
or candidate environment. See the [data-plane contract](../../docs/superpowers/plans/2026-10-20-stage5-capstone.md#题面和答案怎样分开送达).

From the repository root, validate a completed record with:

```bash
pnpm validate:handoff /path/to/completed-record.json
```

The command prints only structural errors, not the record's field values.
The JSON's `registry_state`, `execution_observation`, and `quality_decision` are
separate facts: a registry lookup failure is not `not_found`, and an unknown
execution is not a terminal registry event or a quality pass. `registry_state`
is the authority for whether a holdout version was consumed; `runner_outcome`
records what the execution process reported and cannot replace the registry
event.

To create the unsigned candidate inventory, first build/publish the image and
record its immutable OCI digest, then run all six drills against the same clean
commit. From `examples/p4-durable-support`, run:

```bash
uv run --frozen python ../p5-agent-delivery/release_candidate.py \
  --image-digest "$P5_IMAGE_DIGEST" \
  --output ../../verify-output/stage5-release/candidate-001.json
```

The command refuses a dirty checkout, missing/untracked material, evaluation
hash drift, or incomplete same-commit drills; output paths inside the checkout
must remain under ignored `verify-output/`. A generated manifest records
`publishable: false`, unsigned provenance, and `holdout: not_run`; the candidate
hash is an identity for later evidence, not approval or proof of authenticity.
The command accepts the OCI digest as an operator input and does not prove that
the image was built from the recorded commit. An official holdout must also
verify a separately signed build-provenance statement from the approved builder,
covering the exact source/material closure, build recipe and toolchain, OCI index
and platform manifest digests. The runtime must report the image digest it
actually resolved. Until those values are authenticated and match the frozen
spec, do not request or issue hidden-data capability.
The runtime supervisor must also resolve the frozen OCI index to the target
platform manifest and attest that resolution before the registry reserves the
holdout and returns a one-time capability. The registry issues and consumes the
preflight nonce in that reservation; the custodian only redeems the scoped
capability to open a session. The candidate is launched by the immutable
platform-manifest digest; the supervisor records the same digest at process
start. A candidate-provided image string is not admission evidence.

The handoff operator should work from a fresh clone using
[`RUNBOOK.md`](RUNBOOK.md), verify the recorded commit and image digest, run the
six selectors in [`DRILLS.md`](DRILLS.md), and record actual commands, exit
codes, environment versions, report paths, and artifact hashes. Do not paste
credentials, prompts, provider request/response bodies, or customer data into
the record. Record the credential source (for example, local secret manager)
and whether a key was present; never record its value.

The holdout fields must be filled and reviewed before an official blind
holdout run: owner, executor, custodian, runtime operator, scorer, recovery
operator, reviewer, and release approver subject IDs; maximum spend as an exact
decimal string; termination conditions; candidate, image, dataset, scorer,
and executor hashes; authorization/reservation/terminal event IDs; durable
report path; and externally controlled append-only registry location. The report must bind
the authorization, reservation, and terminal event IDs to the same candidate,
image, dataset, scorer, and executor identities. A failed or interrupted run
still consumes that evaluation version's allowance. Do not reset the registry
or rerun against the same holdout version. A changed candidate requires a
newly authorized holdout version.

For this reference runner, `executor_sha256` is the frozen executor bundle hash,
not just the orchestrator file hash. `executor_bundle_sha256()` hashes
`evaluation/official_holdout.py`, `evaluation/subprocess_candidate.py`, and
`evaluation/canonicalization.py` in a fixed order with length-prefixed paths
and contents. Compute the value from a
clean checkout with the pinned environment before requesting authorization:

```bash
uv run --project examples/p4-durable-support -- python -c 'import sys; sys.path.insert(0, "examples/p5-agent-delivery/evaluation"); from official_holdout import executor_bundle_sha256; print(executor_bundle_sha256())'
```

The release manifest separately records each file hash. If any of these files
changes after authorization, recompute the bundle hash and obtain a new run spec;
do not reuse the existing authorization. The dependency lock and evaluator runtime
image remain separate handoff fields and must also be pinned for a formal run.

`evaluation/run_fixture.py` is not the official holdout runner. Its `holdout`
split and expected outputs are both checked into the repository; it replays
synthetic results and never executes the candidate. Reports say
`blind_holdout: false` and `official_holdout_consumed: false`. Do not attach
those reports as candidate-quality evidence or use their local fixture marker
as the external consumption registry. The real hidden-input execution,
independent scoring and registry integration remain to be implemented or
provided by the designated evaluation operator.

The independent reviewer records a decision only after checking the source
and evidence artifacts. `ready-for-human-acceptance` is not release approval;
the final release decision and rollback authority must be recorded separately.

## Record workflow

1. Create a new copy of the JSON template in a durable evidence location.
2. Verify the candidate commit, lockfile hash, image digest, prompt/tool/data/
   scorer hashes, and all six drill reports before starting the live service.
3. Execute the documented clean-checkout procedure and bounded smoke. Stop on
   any identity, authorization, usage, unknown-state, or cleanup discrepancy.
4. Obtain the preassigned holdout operator's approval, then run the separately
   governed blind evaluation once and attach its immutable report. Do not use
   the offline fixture runner for this step.
5. Have the independent reviewer inspect failures as well as passes, complete
   the record, and capture the separate publication/rollback decision.
