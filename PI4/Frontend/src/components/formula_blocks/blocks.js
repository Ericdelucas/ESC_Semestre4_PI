// Construtor de formulas por blocos em canvas livre (arrastar e soltar com Pointer Events).
// A formula e a cadeia encaixada no bloco "Fórmula ="; blocos soltos no canvas ficam de fora.
// Python envia {palette, blocks, expression, status, sync_error}; o componente devolve
// setStateValue('formula', {expression, blocks, rev}). O calculo continua na AST restrita do Python.

const INSTANCES = new WeakMap();
const OPERATORS = { '+': '+', '-': '−', '*': '×', '/': '÷', '%': '%' };
const SOURCE_TAGS = { Financeiro: 'FIN', Indicador: 'IND', CSV: 'CSV', Catalogo: 'KPI' };
const NUMBER = /^\d{1,15}(\.\d{1,10})?$/;
const MAX_BLOCKS = 200;
const GAP = 6;
const ROW = 46;
const PAD = 14;
const SNAP_X = 70;
const SNAP_Y = 30;
const numberFormat = new Intl.NumberFormat('pt-BR', { maximumSignificantDigits: 6 });

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function plain(text) {
  return String(text).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

// Mesma gramatica de Backend/services/formula_blocks.py::check_structure.
function checkStructure(blocks) {
  if (!blocks.length) return null;
  let expectOperand = true;
  const open = [];
  for (let index = 0; index < blocks.length; index++) {
    const { type, value } = blocks[index];
    if (type === 'var' || type === 'num' || (type === 'paren' && value === '(')) {
      if (!expectOperand) return { index, message: 'Falta um operador antes deste bloco.' };
      if (type === 'num' && !NUMBER.test(value)) return { index, message: 'Número inválido: use dígitos e vírgula decimal.' };
      if (type === 'paren') open.push(index);
      else expectOperand = false;
    } else if (type === 'op') {
      if (expectOperand && value !== '+' && value !== '-') {
        return { index, message: `O operador ${OPERATORS[value]} precisa de um valor à esquerda.` };
      }
      expectOperand = true;
    } else if (type === 'paren' && value === ')') {
      if (expectOperand) return { index, message: 'Parêntese fechado sem valor dentro ou depois de um operador.' };
      if (!open.length) return { index, message: 'Parêntese fechado sem o correspondente "(".' };
      open.pop();
    }
  }
  if (expectOperand) return { index: blocks.length - 1, message: 'A fórmula não pode terminar num operador.' };
  if (open.length) return { index: open[open.length - 1], message: 'Parêntese aberto sem o correspondente ")".' };
  return null;
}

// Mesma formatacao de blocks_to_expression no Python.
function toExpression(blocks) {
  const part = (b) => (b.type === 'var' ? `[${b.value}]` : b.value);
  const unary = (i) => blocks[i].type === 'op' && (i === 0 || blocks[i - 1].type === 'op' || blocks[i - 1].value === '(');
  let text = blocks.length ? part(blocks[0]) : '';
  for (let i = 1; i < blocks.length; i++) {
    const tight = blocks[i].value === ')' || blocks[i - 1].value === '(' || unary(i - 1);
    text += (tight ? '' : ' ') + part(blocks[i]);
  }
  return text;
}

function create(root) {
  const s = {
    nodes: new Map(), chain: [], elements: new Map(), anchor: { x: PAD, y: PAD },
    selected: null, history: [], emitted: undefined, lastExpression: undefined,
    paletteSignature: null, palette: new Map(), emit: () => {}, nextId: 1, drag: null,
  };

  const box = el('div', 'fb');
  const stage = el('div', 'fb-stage');
  const label = el('p', 'fb-label', 'Arraste blocos para o canvas e encaixe-os em “Fórmula =”');
  const canvas = el('div', 'fb-canvas');
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'application');
  canvas.setAttribute('aria-label', 'Canvas da fórmula');
  const anchorEl = el('div', 'fb-block fb-anchor', 'Fórmula =');
  anchorEl.title = 'Arraste para mover a fórmula inteira';
  const slotEl = el('div', 'fb-slot');
  slotEl.hidden = true;
  const trash = el('div', 'fb-trash', '🗑 Solte aqui para remover');
  trash.hidden = true;
  const message = el('p', 'fb-msg');
  message.setAttribute('aria-live', 'polite');
  const warning = el('div', 'fb-warn');
  warning.hidden = true;

  const tools = el('div', 'fb-tools');
  for (const [op, symbol] of Object.entries(OPERATORS)) tools.append(sourceChip({ type: 'op', value: op }, symbol, `operador ${symbol}`));
  tools.append(sourceChip({ type: 'paren', value: '(' }, '(', 'abre parêntese'));
  tools.append(sourceChip({ type: 'paren', value: ')' }, ')', 'fecha parêntese'));
  tools.append(sourceChip({ type: 'num', value: '1' }, '123', 'número'));
  tools.append(el('span', 'fb-sep'));
  const button = (text, title) => {
    const b = el('button', 'fb-btn', text);
    b.type = 'button';
    b.title = title;
    tools.append(b);
    return b;
  };
  const removeButton = button('Remover', 'Remove o bloco selecionado (Delete)');
  const tidyButton = button('Organizar', 'Remove os blocos soltos que não fazem parte da fórmula');
  const undoButton = button('Desfazer', 'Desfaz a última alteração (Ctrl+Z)');
  const clearButton = button('Limpar', 'Remove todos os blocos');

  const paletteBox = el('div', 'fb-palette');
  const search = el('input', 'fb-search');
  search.type = 'search';
  search.placeholder = 'Buscar variável (EBITDA, Receita, NCG, ROIC…)';
  search.setAttribute('aria-label', 'Buscar variável');
  const groups = el('div', 'fb-groups');
  paletteBox.append(search, groups);
  const help = el('p', 'fb-help',
    'Segure e arraste variáveis e operadores para o canvas. Perto da fórmula o bloco encaixa (aparece o contorno); '
    + 'longe dela fica solto. Arraste blocos da fórmula para reordenar ou para fora/lixeira para remover. '
    + 'Clique num bloco da paleta para encaixá-lo no fim. Teclado: ←/→ seleciona, Alt+←/→ move, Delete remove.');

  canvas.append(trash);
  stage.append(canvas, slotEl, anchorEl);
  box.append(label, stage, message, warning, tools, paletteBox, help);
  root.append(box);

  // ---------- modelo ----------
  function snapshot() {
    return JSON.stringify({ nodes: [...s.nodes.values()], chain: s.chain, anchor: s.anchor });
  }
  function checkpoint() {
    s.history = [...s.history.slice(-49), snapshot()];
  }
  function restore(raw) {
    const saved = JSON.parse(raw);
    for (const element of s.elements.values()) element.remove();
    s.elements.clear();
    s.nodes = new Map(saved.nodes.map((n) => [n.id, n]));
    s.chain = saved.chain;
    s.anchor = saved.anchor;
    s.selected = null;
  }
  function newNode(block, x = 0, y = 0) {
    const node = { id: s.nextId++, type: block.type, value: String(block.value), x, y };
    s.nodes.set(node.id, node);
    return node;
  }
  function chainBlocks() {
    return s.chain.map((id) => ({ type: s.nodes.get(id).type, value: s.nodes.get(id).value }));
  }
  function changed() {
    render();
    const blocks = chainBlocks();
    const expression = toExpression(blocks);
    if (expression === s.emitted) return;
    s.emitted = expression;
    s.synced = false;
    renderMessage(checkStructure(blocks));
    s.emit({ expression, blocks, rev: `${Date.now()}-${Math.random()}` });
  }
  function insertInChain(block, index) {
    if (s.nodes.size >= MAX_BLOCKS) return;
    checkpoint();
    const node = newNode(block);
    const at = index ?? (s.chain.includes(s.selected) ? s.chain.indexOf(s.selected) + 1 : s.chain.length);
    s.chain.splice(at, 0, node.id);
    s.selected = node.id;
    changed();
    if (node.type === 'num') focusNumber(node.id);
  }
  function removeNode(id) {
    if (id === null || !s.nodes.has(id)) return;
    checkpoint();
    const index = s.chain.indexOf(id);
    s.nodes.delete(id);
    if (index >= 0) s.chain.splice(index, 1);
    s.selected = index > 0 ? s.chain[index - 1] : null;
    changed();
  }

  // ---------- desenho ----------
  function canvasOrigin() {
    return { left: canvas.offsetLeft, top: canvas.offsetTop };
  }
  function place(element, x, y) {
    const origin = canvasOrigin();
    element.style.left = `${origin.left + x}px`;
    element.style.top = `${origin.top + y}px`;
  }
  function elementFor(node) {
    let element = s.elements.get(node.id);
    if (element) return element;
    element = el('div', `fb-block fb-${node.type}`);
    element.dataset.id = String(node.id);
    if (node.type === 'var') {
      const info = s.palette.get(node.value);
      const [source, name] = node.value.split('::');
      element.append(el('span', 'fb-tag', SOURCE_TAGS[source] || source), el('span', 'fb-name', info ? info.label : name));
      const value = info && info.value !== null ? numberFormat.format(info.value) : 'sem dados';
      element.title = `${node.value} = ${value}`;
    } else if (node.type === 'num') {
      const input = el('input');
      input.inputMode = 'decimal';
      input.value = node.value.replace('.', ',');
      input.setAttribute('aria-label', 'Valor numérico');
      const fit = () => { input.style.width = `${Math.max(3, input.value.length + 1)}ch`; };
      fit();
      input.addEventListener('input', () => { fit(); layout(); });
      input.addEventListener('change', () => {
        const typed = input.value.trim();
        // "1.234,5" (pt-BR) ou "1234.5": o ponto so e milhar quando ha virgula.
        const value = typed.includes(',') ? typed.replace(/\./g, '').replace(',', '.') : typed;
        if (value === node.value) return;
        checkpoint();
        node.value = value;
        changed();
      });
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { input.blur(); canvas.focus(); }
        e.stopPropagation();
      });
      element.append(el('span', 'fb-grip', '⋮'), input);
      element.title = 'Número: segure a borda para arrastar; use vírgula para decimais';
    } else {
      element.textContent = node.type === 'op' ? OPERATORS[node.value] : node.value;
      element.title = node.type === 'op' ? `Operador ${OPERATORS[node.value]}` : 'Parêntese';
    }
    element.addEventListener('pointerdown', (e) => pointerDown(e, { id: node.id }));
    stage.append(element);
    s.elements.set(node.id, element);
    return element;
  }

  function render() {
    for (const [id, element] of s.elements) {
      if (!s.nodes.has(id)) { element.remove(); s.elements.delete(id); }
    }
    const error = checkStructure(chainBlocks());
    for (const node of s.nodes.values()) {
      const element = elementFor(node);
      const index = s.chain.indexOf(node.id);
      element.classList.toggle('fb-loose', index < 0);
      element.classList.toggle('fb-sel', s.selected === node.id);
      element.classList.toggle('fb-bad', Boolean(error) && error.index === index);
    }
    removeButton.disabled = s.selected === null;
    tidyButton.disabled = s.nodes.size === s.chain.length;
    undoButton.disabled = !s.history.length;
    clearButton.disabled = !s.nodes.size;
    layout();
    renderMessage(error);
  }

  // Calcula posicoes da cadeia com quebra de linha; placeholder abre o espaco do encaixe.
  function chainPositions(ids, placeholder) {
    const items = ids.map((id) => ({ id, width: s.elements.get(id)?.offsetWidth || 40 }));
    if (placeholder) items.splice(placeholder.index, 0, { id: null, width: placeholder.width });
    const maxX = canvas.clientWidth - PAD;
    const rowStart = s.anchor.x + 24;
    let x = s.anchor.x + anchorEl.offsetWidth + GAP * 2;
    let y = s.anchor.y;
    const positions = [];
    const slots = [];
    items.forEach((item, index) => {
      if (x + item.width > maxX && x > rowStart + 1) { x = rowStart; y += ROW; }
      slots.push({ index, x, y });
      positions.push({ ...item, x, y });
      x += item.width + GAP;
    });
    if (x > maxX - 30) { x = rowStart; y += ROW; }
    slots.push({ index: items.length, x, y });
    return { positions, slots, bottom: y + ROW };
  }

  function layout(placeholder) {
    const { positions, bottom } = chainPositions(s.chain.filter((id) => id !== s.drag?.id), placeholder);
    place(anchorEl, s.anchor.x, s.anchor.y);
    let needed = bottom;
    for (const item of positions) {
      if (item.id === null) { place(slotEl, item.x, item.y); slotEl.style.width = `${item.width}px`; continue; }
      place(s.elements.get(item.id), item.x, item.y);
    }
    slotEl.hidden = !placeholder;
    for (const node of s.nodes.values()) {
      if (s.chain.includes(node.id) || node.id === s.drag?.id) continue;
      place(s.elements.get(node.id), node.x, node.y);
      needed = Math.max(needed, node.y + ROW);
    }
    canvas.style.height = `${Math.max(220, needed + PAD + 40)}px`;
  }

  function renderMessage(error) {
    message.className = 'fb-msg';
    if (error) {
      message.classList.add('fb-err');
      message.textContent = `Bloco ${error.index + 1} da fórmula: ${error.message}`;
    } else if (!s.chain.length || s.syncError) {
      message.classList.add('fb-hint');
      message.textContent = s.chain.length ? '' : 'Encaixe blocos à direita de “Fórmula =”.';
    } else if (s.status && s.synced) {
      message.classList.add(s.status.ok ? 'fb-ok' : 'fb-err');
      message.textContent = s.status.text;
    } else {
      message.classList.add('fb-hint');
      message.textContent = 'Calculando…';
    }
  }

  function focusNumber(id) {
    const input = s.elements.get(id)?.querySelector('input');
    if (input) { input.focus(); input.select(); }
  }

  // ---------- arrastar e soltar ----------
  function pointerDown(e, source) {
    if (e.button !== 0 || e.target.tagName === 'INPUT' || s.drag) return;
    e.preventDefault();
    // Medido ja: depois do despacho, e.target no Shadow DOM passa a ser o host.
    const rect = e.currentTarget.getBoundingClientRect();
    const start = { x: e.clientX, y: e.clientY, grabX: e.clientX - rect.left, grabY: e.clientY - rect.top };
    let dragging = false;
    const move = (ev) => {
      if (!dragging) {
        if (Math.hypot(ev.clientX - start.x, ev.clientY - start.y) < 5) return;
        dragging = true;
        startDrag(source, start);
      }
      updateDrag(ev);
    };
    const finish = (ev, cancelled) => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointercancel', cancel);
      if (dragging) endDrag(ev, cancelled);
      else click(source);
    };
    const up = (ev) => finish(ev, false);
    const cancel = (ev) => finish(ev, true);
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    window.addEventListener('pointercancel', cancel);
  }

  function click(source) {
    if (source.block) insertInChain(source.block);
    else if (source.id !== undefined) {
      s.selected = s.selected === source.id ? null : source.id;
      render();
      canvas.focus();
    }
  }

  function startDrag(source, start) {
    checkpoint();
    let element;
    let id = null;
    if (source.anchor) element = anchorEl;
    else if (source.block) {
      const node = newNode(source.block);
      s.nodes.delete(node.id); // so entra no modelo se for solto no canvas
      s.pending = node;
      id = node.id;
      element = elementFor(node);
    } else {
      id = source.id;
      element = s.elements.get(id);
    }
    s.drag = { id, source, element, grabX: start.grabX, grabY: start.grabY,
      wasInChain: id !== null && s.chain.includes(id), slot: null };
    element.classList.add('fb-dragging');
    trash.hidden = source.anchor;
    canvas.classList.add('fb-active');
    s.selected = id;
  }

  function dragPoint(ev) {
    const stageRect = stage.getBoundingClientRect();
    const origin = canvasOrigin();
    return {
      x: ev.clientX - stageRect.left - origin.left - s.drag.grabX,
      y: ev.clientY - stageRect.top - origin.top - s.drag.grabY,
      inCanvas: (() => {
        const r = canvas.getBoundingClientRect();
        return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
      })(),
      inTrash: (() => {
        if (trash.hidden) return false;
        const r = trash.getBoundingClientRect();
        return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
      })(),
    };
  }

  function updateDrag(ev) {
    const drag = s.drag;
    const point = dragPoint(ev);
    place(drag.element, point.x, point.y);
    if (drag.source.anchor) {
      s.anchor = { x: Math.max(0, Math.min(point.x, canvas.clientWidth - anchorEl.offsetWidth)), y: Math.max(0, point.y) };
      layout();
      return;
    }
    trash.classList.toggle('fb-over', point.inTrash);
    drag.slot = null;
    if (point.inCanvas && !point.inTrash) {
      const { slots } = chainPositions(s.chain.filter((id) => id !== drag.id));
      const midY = point.y + drag.element.offsetHeight / 2;
      let best = null;
      for (const slot of slots) {
        const dx = Math.abs(point.x - slot.x);
        const dy = Math.abs(midY - (slot.y + ROW / 2 - GAP));
        if (dx < SNAP_X && dy < SNAP_Y && (!best || dx + dy < best.d)) best = { index: slot.index, d: dx + dy };
      }
      drag.slot = best && best.index;
    }
    layout(drag.slot === null ? undefined : { index: drag.slot, width: drag.element.offsetWidth });
  }

  function endDrag(ev, cancelled) {
    const drag = s.drag;
    const point = dragPoint(ev);
    drag.element.classList.remove('fb-dragging');
    trash.hidden = true;
    trash.classList.remove('fb-over');
    canvas.classList.remove('fb-active');
    s.drag = null;
    if (cancelled) {
      // Gesto interrompido pelo navegador (ex.: scroll no toque): volta ao estado anterior.
      s.pending = null;
      restore(s.history.pop());
      changed();
      return;
    }
    if (drag.source.anchor) { changed(); return; }
    const node = s.nodes.get(drag.id) || s.pending;
    s.pending = null;
    if (drag.wasInChain) s.chain.splice(s.chain.indexOf(drag.id), 1);
    if (point.inTrash || !point.inCanvas) {
      // Fora do canvas ou na lixeira: remove (ou descarta o bloco novo da paleta).
      s.nodes.delete(drag.id);
      s.selected = null;
    } else {
      s.nodes.set(node.id, node);
      if (drag.slot !== null) s.chain.splice(drag.slot, 0, node.id);
      else {
        node.x = Math.max(0, Math.min(point.x, canvas.clientWidth - drag.element.offsetWidth));
        node.y = Math.max(0, point.y);
      }
    }
    changed();
    if (node.type === 'num' && drag.slot !== null && !drag.wasInChain) focusNumber(node.id);
  }

  anchorEl.addEventListener('pointerdown', (e) => pointerDown(e, { anchor: true }));

  function sourceChip(block, text, aria) {
    const chip = el('button', `fb-chip fb-${block.type}`, text);
    chip.type = 'button';
    chip.title = `Arraste ou clique para inserir ${aria}`;
    chip.setAttribute('aria-label', `Inserir ${aria}`);
    chip.addEventListener('pointerdown', (e) => pointerDown(e, { block }));
    chip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); insertInChain(block); }
    });
    return chip;
  }

  // ---------- botoes e teclado ----------
  removeButton.addEventListener('click', () => removeNode(s.selected));
  tidyButton.addEventListener('click', () => {
    checkpoint();
    for (const id of [...s.nodes.keys()]) if (!s.chain.includes(id)) s.nodes.delete(id);
    changed();
  });
  undoButton.addEventListener('click', () => {
    if (!s.history.length) return;
    restore(s.history.pop());
    changed();
  });
  clearButton.addEventListener('click', () => {
    checkpoint();
    s.nodes.clear();
    s.chain = [];
    s.selected = null;
    changed();
  });

  canvas.addEventListener('keydown', (e) => {
    const index = s.chain.indexOf(s.selected);
    const last = s.chain.length - 1;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); undoButton.click(); return; }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      if (last < 0) return;
      const step = e.key === 'ArrowLeft' ? -1 : 1;
      const current = index >= 0 ? index : (step < 0 ? last + 1 : -1);
      const target = Math.min(last, Math.max(0, current + step));
      if (e.altKey && index >= 0 && target !== index) {
        checkpoint();
        s.chain.splice(index, 1);
        s.chain.splice(target, 0, s.selected);
        changed();
      } else { s.selected = s.chain[target]; render(); }
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      removeNode(s.selected ?? (e.key === 'Backspace' && last >= 0 ? s.chain[last] : null));
    } else if (e.key === 'Escape') {
      s.selected = null;
      render();
    } else if (e.key in OPERATORS) {
      e.preventDefault();
      insertInChain({ type: 'op', value: e.key });
    } else if (e.key === '(' || e.key === ')') {
      e.preventDefault();
      insertInChain({ type: 'paren', value: e.key });
    } else if (/^\d$/.test(e.key)) {
      e.preventDefault();
      insertInChain({ type: 'num', value: e.key });
      const input = s.elements.get(s.selected)?.querySelector('input');
      if (input) input.setSelectionRange(input.value.length, input.value.length);
    }
  });

  // ---------- paleta ----------
  function renderPalette(palette) {
    s.palette = new Map(palette.map((item) => [item.key, item]));
    groups.replaceChildren();
    const byGroup = new Map();
    for (const item of palette) {
      if (!byGroup.has(item.group)) byGroup.set(item.group, []);
      byGroup.get(item.group).push(item);
    }
    for (const [name, items] of byGroup) {
      const details = el('details');
      const summary = el('summary', '', name + ' ');
      summary.append(el('span', 'fb-count', `(${items.length})`));
      const list = el('div', 'fb-items');
      for (const item of items) {
        const chip = sourceChip({ type: 'var', value: item.key }, '', item.key);
        chip.classList.add('fb-item');
        chip.dataset.key = item.key;
        chip.dataset.search = plain(`${item.key} ${item.label}`);
        chip.append(el('span', 'fb-tag', SOURCE_TAGS[item.source] || item.source), el('span', 'fb-name', item.label));
        if (item.value === null) chip.classList.add('fb-nan');
        chip.title = `${item.key} = ${item.value === null ? 'sem dados nos filtros atuais' : numberFormat.format(item.value)}`;
        list.append(chip);
      }
      details.append(summary, list);
      groups.append(details);
    }
    if (!palette.length) groups.append(el('p', 'fb-none', 'Sem variáveis para os filtros atuais; use números.'));
    filterPalette();
  }

  function filterPalette() {
    const terms = plain(search.value).split(/[\s_]+/).filter(Boolean);
    for (const details of groups.querySelectorAll('details')) {
      let shown = 0;
      for (const chip of details.querySelectorAll('.fb-item')) {
        const match = terms.every((term) => chip.dataset.search.includes(term));
        chip.hidden = !match;
        shown += match;
      }
      details.hidden = !shown;
      if (terms.length) details.open = shown > 0;
    }
  }
  search.addEventListener('input', filterPalette);
  search.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const first = groups.querySelector('.fb-item:not([hidden])');
    if (first) insertInChain({ type: 'var', value: first.dataset.key });
  });

  new ResizeObserver(() => { if (!s.drag) layout(); }).observe(canvas);

  s.update = (data) => {
    box.dataset.disabled = data.disabled ? '1' : '0';
    const signature = JSON.stringify(data.palette || []);
    const paletteChanged = signature !== s.paletteSignature;
    if (paletteChanged) {
      s.paletteSignature = signature;
      renderPalette(data.palette || []);
    }
    s.status = data.status || null;
    s.syncError = data.sync_error || null;
    let replaced = false;
    // Texto vindo do Python so substitui a cadeia se nao for o eco da ultima edicao local.
    if (data.expression !== s.lastExpression) {
      s.lastExpression = data.expression;
      if (data.expression !== s.emitted && Array.isArray(data.blocks) && !s.drag) {
        for (const id of s.chain) s.nodes.delete(id);
        s.chain = data.blocks.map((block) => newNode(block).id);
        s.selected = null;
        s.emitted = data.expression;
        replaced = true;
      }
    }
    s.synced = data.expression === s.emitted;
    warning.hidden = !s.syncError;
    warning.textContent = s.syncError
      ? `O texto não pôde ser convertido em blocos: ${s.syncError} Os blocos mostram a última versão válida.`
      : '';
    if (s.drag) return;
    if (replaced || paletteChanged) render();
    else renderMessage(checkStructure(chainBlocks()));
  };
  return s;
}

export default function (component) {
  const { data, parentElement, setStateValue } = component;
  let state = INSTANCES.get(parentElement);
  if (!state) {
    state = create(parentElement);
    INSTANCES.set(parentElement, state);
  }
  state.emit = (formula) => setStateValue('formula', formula);
  state.update(data || {});
}
