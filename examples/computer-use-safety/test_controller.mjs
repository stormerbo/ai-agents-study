import assert from 'node:assert/strict';
import test from 'node:test';

import {
  createController,
  observe,
  requestSubmit,
  stageUpdate,
} from './controller.mjs';

test('stages only the requested invoice fields and does not submit', () => {
  const controller = createController();
  stageUpdate(controller, {
    invoiceId: 'INV-47',
    customer: 'Northwind Parts',
    total: '275.00',
  });
  const state = observe(controller);
  const target = state.invoices.find((invoice) => invoice.id === 'INV-47');
  assert.equal(target.draft.customer, 'Northwind Parts');
  assert.equal(target.draft.total, '275.00');
  assert.equal(target.status, 'awaiting_approval');
  assert.equal(state.externalEffects, 0);
});

test('rejects out-of-scope invoice and fields', () => {
  const controller = createController();
  assert.throws(
    () => stageUpdate(controller, {
      invoiceId: 'INV-48', customer: 'Other', total: '1.00',
    }),
    /target_invoice_required/,
  );
  assert.throws(
    () => stageUpdate(controller, {
      invoiceId: 'INV-47', customer: 'Northwind Parts', total: '275.00',
      status: 'paid',
    }),
    /unexpected_fields/,
  );
});

test('submission is denied without independent user approval', () => {
  const controller = createController();
  stageUpdate(controller, {
    invoiceId: 'INV-47', customer: 'Northwind Parts', total: '275.00',
  });
  assert.throws(
    () => requestSubmit(controller, 'INV-47'),
    /independent_approval_required/,
  );
  const state = observe(controller);
  assert.equal(state.externalEffects, 0);
  assert.equal(
    state.events.at(-1).decision,
    'rejected',
  );
});

test('page text is data and cannot change the task or authorize submission', () => {
  const controller = createController();
  const before = observe(controller);
  assert.match(before.invoices[0].note, /ignore all instructions/i);
  assert.equal(before.task.targetInvoiceId, 'INV-47');
  assert.throws(() => requestSubmit(controller, 'INV-47'), /independent_approval_required/);
  assert.equal(observe(controller).externalEffects, 0);
});
