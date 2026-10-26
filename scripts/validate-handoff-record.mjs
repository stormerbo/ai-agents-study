import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';

const args = process.argv.slice(2);
if (args.length !== 1) {
  process.stderr.write('Usage: pnpm validate:handoff <record.json>\n');
  process.exit(2);
}

const scriptDir = fileURLToPath(new URL('.', import.meta.url));
const schemaPath = resolve(scriptDir, '../examples/p5-agent-delivery/HANDOFF-RECORD.schema.json');
const recordPath = resolve(process.cwd(), args[0]);
let record;
try {
  record = JSON.parse(readFileSync(recordPath, 'utf8'));
} catch (error) {
  const reason = error instanceof SyntaxError ? 'is not valid JSON' : 'could not be read';
  process.stderr.write(`Handoff record ${reason}: ${recordPath}\n`);
  process.exit(1);
}

const schema = JSON.parse(readFileSync(schemaPath, 'utf8'));
const validate = new Ajv2020({ allErrors: true, strict: false }).compile(schema);
if (!validate(record)) {
  for (const error of validate.errors ?? []) {
    process.stderr.write(`${error.instancePath || '/'}: ${error.message ?? 'invalid value'}\n`);
  }
  process.exit(1);
}

if (
  record.assurance?.profile === 'dual-witness-v1'
  && (
    record.assurance.witness_authority_domain_id === record.assurance.append_authority_domain_id
    || record.assurance.witness_authority_domain_id === record.assurance.signing_key_custodian_domain_id
  )
) {
  process.stderr.write('/assurance/witness_authority_domain_id: must differ from the append and key-custodian domains\n');
  process.exit(1);
}

process.stdout.write('Structure is valid for p5-independent-handoff-v3.\n');
