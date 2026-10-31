/* Unit tests for the editor's DOM events and Streamlit bridge, without a browser. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

class Element {
  constructor() {
    this.children = []; this.handlers = {}; this.value = ''; this.style = {setProperty() {}};
    this.classes = new Set();
    this.classList = {add: name => this.classes.add(name), remove: name => this.classes.delete(name), contains: name => this.classes.has(name)};
  }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  setAttribute() {}
  addEventListener(name, handler) { (this.handlers[name] ??= []).push(handler); }
  fire(name, event = {}) {
    event.preventDefault ??= () => {};
    event.stopPropagation ??= () => {};
    for (const handler of this.handlers[name] || []) handler(event);
  }
  querySelectorAll(selector) { return this.children.filter(el => el.className?.split(' ').includes(selector.slice(1))); }
  focus() {}
}

function editor(initial = []) {
  const ids = ['canvas', 'sequence', 'expression', 'metrics', 'operators', 'number-form', 'number', 'search', 'clear', 'left', 'right', 'remove', 'status'];
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  const messages = [];
  let onMessage;
  const parent = {postMessage(message) { messages.push(structuredClone(message)); }};
  const allElements = [...Object.values(elements)];
  const document = {
    getElementById: id => elements[id], createElement: () => { const el = new Element(); allElements.push(el); return el; },
    body: {scrollHeight: 600}, documentElement: new Element(),
    querySelector: () => new Element(), querySelectorAll: selector => allElements.filter(el =>
      selector.split(',').some(item => el.classes.has(item.trim().slice(1)))),
  };
  const window = {parent, addEventListener(name, handler) { if (name === 'message') onMessage = handler; }};
  const source = fs.readFileSync(path.join(__dirname, '../../Frontend/src/components/formula_blocks/editor.js'), 'utf8');
  vm.runInNewContext(source, {window, document, ResizeObserver: class { observe() {} }});
  const render = (metrics = ['Financeiro::EBITDA', 'Financeiro::Capex', 'CSV::DRE - Ebit'], unavailable_metrics = []) => onMessage({source: parent,
    data: {type: 'streamlit:render', args: {metrics, unavailable_metrics, initial_blocks: initial, max_blocks: 120}}});
  const latest = () => messages.filter(m => m.type === 'streamlit:setComponentValue').at(-1)?.value.blocks;
  render();
  return {elements, messages, latest, render};
}

const transfer = () => ({setData() {}});

test('palette drag/drop, reorder and stale rerenders preserve the current expression', () => {
  const {elements: e, latest, render, messages} = editor();
  assert.equal(messages[0].type, 'streamlit:componentReady');
  e.metrics.children[0].fire('dragstart', {dataTransfer: transfer()});
  e.canvas.fire('drop');
  e.operators.children[1].fire('click'); // minus
  e.metrics.children[1].fire('click');
  assert.equal(e.expression.textContent, '[Financeiro::EBITDA] - [Financeiro::Capex]');
  render(); // Python may still send initial_blocks=[] while processing an edit.
  assert.equal(latest().length, 3);
  assert.equal(e.sequence.querySelectorAll('.block').length, 3);
  const last = e.sequence.querySelectorAll('.block')[2];
  last.fire('dragstart', {dataTransfer: transfer()});
  e.sequence.children[0].fire('drop'); // first insertion slot
  assert.equal(e.expression.textContent, '[Financeiro::Capex] [Financeiro::EBITDA] -');
  e.right.fire('click');
  assert.equal(latest()[1].value, 'Financeiro::Capex');
  e.remove.fire('click');
  assert.equal(latest().length, 2);
  e.clear.fire('click');
  assert.equal(latest().length, 0);
  assert.equal(e.remove.disabled, true);
});

test('parentheses, numeric constants, search, keyboard and rehydration', () => {
  const {elements: e, latest} = editor([{kind: 'operator', value: '('}]);
  e.number.value = '-0,25'; e['number-form'].fire('submit');
  e.operators.children[5].fire('click');
  assert.equal(e.expression.textContent, '( (-0.25) )');
  e.number.value = '1e999'; e['number-form'].fire('submit');
  assert.equal(latest().length, 3);
  assert.match(e.status.textContent, /número finito/);
  e.search.value = 'dre'; e.search.fire('input');
  assert.equal(e.metrics.children.length, 1);
  e.metrics.children[0].fire('click');
  assert.equal(latest()[3].value, 'CSV::DRE - Ebit');
  e.sequence.querySelectorAll('.block')[3].fire('keydown', {key: 'ArrowLeft', altKey: true});
  assert.equal(latest()[2].value, 'CSV::DRE - Ebit');
  e.sequence.querySelectorAll('.block')[2].fire('keydown', {key: 'Delete'});
  assert.equal(latest().length, 3);
});

test('metric and operator drags give immediate feedback without Python messages', () => {
  const {elements: e, messages, latest, render} = editor();
  const metric = e.metrics.children[0];
  metric.fire('dragstart', {dataTransfer: transfer()});
  assert.equal(metric.classList.contains('dragging'), true);
  assert.equal(e.canvas.classList.contains('drag-active'), true);
  assert.match(e.status.textContent, /Solte no canvas/);
  assert.equal(latest(), undefined); // Hover and drag feedback stays local.
  render(); // Do not replace DOM while another rerun finishes.
  assert.equal(e.metrics.children[0], metric);
  const slot = e.sequence.children.at(-1);
  slot.fire('dragover', {dataTransfer: transfer()});
  assert.equal(slot.classList.contains('over'), true);
  slot.fire('drop');
  assert.equal(e.canvas.classList.contains('drag-active'), false);
  assert.equal(metric.classList.contains('dragging'), false);
  assert.equal(slot.classList.contains('over'), false);
  assert.equal(latest().length, 1);

  const operator = e.operators.children[0];
  operator.fire('dragstart', {dataTransfer: transfer()});
  const target = e.sequence.querySelectorAll('.block')[0];
  target.fire('dragover', {dataTransfer: transfer()});
  assert.equal(target.classList.contains('over'), true);
  target.fire('drop');
  assert.equal(latest()[0].value, '+');
  assert.equal(latest()[1].value, 'Financeiro::EBITDA');
  assert.equal(messages.filter(m => m.type === 'streamlit:setComponentValue').length, 2);
});

test('cancelled drags reset feedback and do not mutate the formula', () => {
  const {elements: e, latest} = editor();
  const operator = e.operators.children[0];
  operator.fire('dragstart', {dataTransfer: transfer()});
  operator.fire('dragend');
  assert.equal(operator.classList.contains('dragging'), false);
  assert.equal(e.canvas.classList.contains('drag-active'), false);
  assert.match(e.status.textContent, /cancelado/);
  assert.equal(latest(), undefined);
});

test('palette renders every supplied metric and keeps unavailable metrics visible', () => {
  const {elements: e, render} = editor();
  const metrics = Array.from({length: 250}, (_, i) => `Nova fonte::Métrica ${i}`);
  render(metrics, [metrics[0]]);
  assert.equal(e.metrics.children.length, 250);
  assert.equal(e.metrics.children[0].classList.contains('unavailable'), true);
  assert.match(e.metrics.children[0].title, /sem valor numérico/);
  e.metrics.children[0].fire('click');
  assert.equal(e.sequence.querySelectorAll('.block')[0].classList.contains('missing'), true);
});
