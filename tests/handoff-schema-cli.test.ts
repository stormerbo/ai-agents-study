import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const validatorPath = 'scripts/validate-handoff-record.mjs';
const templatePath = 'examples/p5-agent-delivery/HANDOFF-RECORD.template.json';

function runValidator(path?: string) {
  return spawnSync(process.execPath, path ? [validatorPath, path] : [validatorPath], {
    cwd: process.cwd(),
    encoding: 'utf8',
  });
}

describe('handoff record schema command', () => {
  it('validates the checked-in blank template without printing record contents', () => {
    const result = runValidator(templatePath);

    expect(result.status).toBe(0);
    expect(result.stdout).toContain('Structure is valid');
    expect(result.stdout).not.toContain(readFileSync(templatePath, 'utf8'));
  });

  it('returns a validation error for an invalid record without echoing its data', () => {
    const directory = mkdtempSync(join(tmpdir(), 'handoff-schema-'));
    const recordPath = join(directory, 'invalid.json');
    const record = JSON.parse(readFileSync(templatePath, 'utf8'));
    record.holdout.registry_state = 'invented-state';
    writeFileSync(recordPath, JSON.stringify(record));

    try {
      const result = runValidator(recordPath);
      expect(result.status).toBe(1);
      expect(result.stderr).toContain('registry_state');
      expect(result.stderr).not.toContain('invented-state');
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  it('requires explicit trust ownership for the selected assurance profile', () => {
    const directory = mkdtempSync(join(tmpdir(), 'handoff-schema-'));
    const recordPath = join(directory, 'record.json');
    const record = JSON.parse(readFileSync(templatePath, 'utf8'));
    record.schema = 'p5-independent-handoff-v3';
    record.assurance = {
      profile: 'single-authority-v1',
      risk_owner_subject_id: null,
      append_authority_domain_id: 'registry-domain',
      signing_key_custodian_domain_id: 'key-domain',
      append_authority_compromise_in_scope: false,
      witness_authority_domain_id: null,
      witness_root_fingerprint_sha256: null,
      terminal_witness_receipt_sha256: null,
    };
    writeFileSync(recordPath, JSON.stringify(record));

    try {
      expect(runValidator(recordPath).status).toBe(1);
      record.assurance.risk_owner_subject_id = 'risk-owner-42';
      writeFileSync(recordPath, JSON.stringify(record));
      expect(runValidator(recordPath).status).toBe(0);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  it('requires an independent witness and terminal receipt for dual-witness holdouts', () => {
    const directory = mkdtempSync(join(tmpdir(), 'handoff-schema-'));
    const recordPath = join(directory, 'record.json');
    const record = JSON.parse(readFileSync(templatePath, 'utf8'));
    record.schema = 'p5-independent-handoff-v3';
    record.assurance = {
      profile: 'dual-witness-v1',
      risk_owner_subject_id: 'risk-owner-42',
      append_authority_domain_id: 'registry-domain',
      signing_key_custodian_domain_id: 'key-domain',
      append_authority_compromise_in_scope: true,
      witness_authority_domain_id: 'witness-domain',
      witness_root_fingerprint_sha256: 'a'.repeat(64),
      terminal_witness_receipt_sha256: null,
    };
    record.holdout.registry_state = 'consumed';
    writeFileSync(recordPath, JSON.stringify(record));

    try {
      expect(runValidator(recordPath).status).toBe(1);
      record.assurance.terminal_witness_receipt_sha256 = 'b'.repeat(64);
      writeFileSync(recordPath, JSON.stringify(record));
      expect(runValidator(recordPath).status).toBe(0);
      record.assurance.witness_authority_domain_id = 'registry-domain';
      writeFileSync(recordPath, JSON.stringify(record));
      const sameDomain = runValidator(recordPath);
      expect(sameDomain.status).toBe(1);
      expect(sameDomain.stderr).toContain('witness_authority_domain_id');
      record.assurance.witness_authority_domain_id = 'witness-domain';
      writeFileSync(recordPath, JSON.stringify(record));
      expect(runValidator(recordPath).status).toBe(0);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  it('shows usage and exits with a usage error when no record is provided', () => {
    const result = runValidator();

    expect(result.status).toBe(2);
    expect(result.stderr).toContain('Usage:');
  });
});
