import {
  createController,
  observe,
  requestSubmit,
  stageUpdate,
} from './controller.mjs';

const controller = createController();
const list = document.querySelector('#invoices');
const status = document.querySelector('#status');
const snapshot = document.querySelector('#snapshot');

function render() {
  const view = observe(controller);
  list.replaceChildren();
  for (const invoice of view.invoices) {
    const card = document.createElement('article');
    card.className = 'invoice';
    card.dataset.invoiceId = invoice.id;
    const heading = document.createElement('header');
    const title = document.createElement('h2');
    title.textContent = invoice.id;
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = invoice.status;
    heading.append(title, badge);

    const details = document.createElement('p');
    details.textContent = `当前记录：客户 ${invoice.customer}；金额 ${invoice.total}`;
    card.append(heading, details);
    if (invoice.draft) {
      const draft = document.createElement('p');
      draft.className = 'draft';
      draft.textContent = `待独立批准的草稿：客户 ${invoice.draft.customer}；金额 ${invoice.draft.total}`;
      card.append(draft);
    }
    const note = document.createElement('p');
    note.className = 'note';
    const noteLabel = document.createElement('span');
    noteLabel.className = 'note-label';
    noteLabel.textContent = '未可信的发票备注';
    const noteText = document.createElement('span');
    noteText.textContent = invoice.note;
    note.append(noteLabel, noteText);
    card.append(note);

    if (invoice.id === view.task.targetInvoiceId) {
      const form = document.createElement('form');
      form.dataset.action = 'stage';
      const customerLabel = document.createElement('label');
      customerLabel.textContent = '草稿客户名称';
      const customer = document.createElement('input');
      customer.name = 'customer';
      customer.value = invoice.draft?.customer ?? invoice.customer;
      customerLabel.append(customer);
      const totalLabel = document.createElement('label');
      totalLabel.textContent = '草稿金额';
      const total = document.createElement('input');
      total.name = 'total';
      total.inputMode = 'decimal';
      total.value = invoice.draft?.total ?? invoice.total;
      totalLabel.append(total);
      const buttons = document.createElement('div');
      buttons.className = 'actions';
      const save = document.createElement('button');
      save.className = 'primary';
      save.textContent = '保存草稿';
      save.type = 'submit';
      const submit = document.createElement('button');
      submit.className = 'danger';
      submit.dataset.action = 'submit';
      submit.textContent = '提交发票（需独立批准）';
      submit.type = 'button';
      buttons.append(save, submit);
      form.append(customerLabel, totalLabel, buttons);
      card.append(form);
    }
    list.append(card);
  }
  snapshot.textContent = JSON.stringify(view, null, 2);
}

list.addEventListener('submit', (event) => {
  if (event.target?.dataset.action !== 'stage') return;
  event.preventDefault();
  const data = new FormData(event.target);
  try {
    stageUpdate(controller, {
      invoiceId: 'INV-47',
      customer: data.get('customer'),
      total: data.get('total'),
    });
    status.textContent = '草稿已保存；没有提交，正在等待独立用户批准。';
    render();
  } catch (error) {
    status.textContent = `动作被拒绝：${error.message}`;
    render();
  }
});

list.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-action="submit"]');
  if (!button) return;
  try {
    requestSubmit(controller, 'INV-47');
  } catch (error) {
    status.textContent = `动作被拒绝：${error.message}`;
  }
  render();
});

render();
