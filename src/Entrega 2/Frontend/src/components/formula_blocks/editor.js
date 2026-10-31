/* Local assets only. Streamlit v1's JSON postMessage protocol (API version 1). */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let blocks = [], metrics = [], selected = -1, initialized = false, maxBlocks = 120;
  let dragging = null;
  let unavailableMetrics = new Set();
  const numberPattern = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
  const send = (type, data) => window.parent.postMessage({isStreamlitMessage: true, type, ...data}, '*');
  let lastFrameHeight = null;
  const height = () => {
    const nextHeight = document.body.scrollHeight;
    if (nextHeight !== lastFrameHeight) {
      lastFrameHeight = nextHeight;
      send('streamlit:setFrameHeight', {height: nextHeight});
    }
  };
  const announce = text => { $('status').textContent = text; height(); };
  const expression = () => blocks.map(b => b.kind === 'metric' ? `[${b.value}]` :
    b.kind === 'number' && /^[+-]/.test(b.value) ? `(${b.value})` : b.value).join(' ');

  function publish(message) {
    renderCanvas();
    announce(message);
    send('streamlit:setComponentValue', {value: {blocks}, dataType: 'json'});
  }

  function insert(block, position = blocks.length) {
    if (blocks.length >= maxBlocks) { announce(`Limite de ${maxBlocks} blocos atingido.`); return; }
    blocks.splice(position, 0, {...block});
    selected = position;
    publish('Bloco adicionado.');
  }

  function move(from, position) {
    if (from < 0 || from >= blocks.length) return;
    const [block] = blocks.splice(from, 1);
    const destination = position > from ? position - 1 : position;
    blocks.splice(destination, 0, block);
    selected = destination;
    publish('Bloco movido.');
  }

  function dragSource(element, payload) {
    element.draggable = true;
    element.addEventListener('dragstart', event => {
      dragging = payload;
      event.dataTransfer.effectAllowed = payload.kind === 'move' ? 'move' : 'copy';
      event.dataTransfer.setData('text/plain', JSON.stringify(payload));
      element.classList.add('dragging');
      $('canvas').classList.add('drag-active');
      announce(payload.kind === 'move'
        ? 'Arraste até um encaixe para mover o bloco.'
        : 'Solte no canvas para adicionar. Os encaixes indicam a posição na fórmula.');
    });
    element.addEventListener('dragend', () => {
      const cancelled = dragging !== null;
      finishDrag();
      if (cancelled) {
        renderMetrics();
        renderCanvas();
        announce('Arraste cancelado. A fórmula foi mantida.');
      }
    });
  }

  function finishDrag() {
    dragging = null;
    $('canvas').classList.remove('drag-active');
    document.querySelectorAll('.over, .dragging').forEach(el => {
      el.classList.remove('over');
      el.classList.remove('dragging');
    });
  }

  function drop(event, position) {
    event.preventDefault();
    event.stopPropagation();
    if (!dragging) return;
    const payload = dragging;
    finishDrag();
    if (payload.kind === 'move') move(payload.index, position);
    else insert(payload, position);
  }

  function dropTarget(element, position) {
    element.addEventListener('dragover', event => {
      if (!dragging) return;
      event.preventDefault();
      event.stopPropagation();
      document.querySelectorAll('.over').forEach(el => el.classList.remove('over'));
      element.classList.add('over');
      event.dataTransfer.dropEffect = dragging.kind === 'move' ? 'move' : 'copy';
    });
    element.addEventListener('dragleave', () => element.classList.remove('over'));
    element.addEventListener('drop', event => drop(event, position));
  }

  function describe(button, block) {
    if (block.kind === 'metric') {
      const divider = block.value.indexOf('::');
      const source = divider >= 0 ? block.value.slice(0, divider) : 'Métrica';
      const name = divider >= 0 ? block.value.slice(divider + 2) : block.value;
      button.textContent = name;
      const small = document.createElement('small');
      small.textContent = source;
      button.append(small);
      button.title = block.value;
    } else button.textContent = block.value;
  }

  function renderCanvas() {
    const sequence = $('sequence');
    sequence.replaceChildren();
    if (!blocks.length) {
      const empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = 'Arraste os primeiros blocos para cá';
      sequence.append(empty);
    }
    for (let index = 0; index <= blocks.length; index++) {
      const slot = document.createElement('div');
      slot.className = 'slot';
      slot.setAttribute('aria-hidden', 'true');
      dropTarget(slot, index);
      sequence.append(slot);
      if (index === blocks.length) break;
      const block = blocks[index];
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `block ${block.kind}${selected === index ? ' selected' : ''}`;
      if (block.kind === 'metric' && !metrics.includes(block.value)) button.classList.add('missing');
      button.setAttribute('aria-pressed', String(selected === index));
      button.setAttribute('aria-label', `Bloco ${index + 1}: ${block.value}`);
      describe(button, block);
      if (unavailableMetrics.has(block.value)) button.classList.add('missing');
      button.addEventListener('click', () => {
        selected = index;
        renderCanvas();
        $('sequence').querySelectorAll('.block')[index].focus();
        announce(`Bloco ${index + 1} selecionado. Use os botões para mover ou excluir.`);
      });
      button.addEventListener('keydown', event => {
        if (event.key === 'Delete' || event.key === 'Backspace') {
          event.preventDefault(); selected = index; removeSelected();
        } else if (event.altKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
          event.preventDefault();
          const offset = event.key === 'ArrowLeft' ? -1 : 1;
          if (index + offset >= 0 && index + offset < blocks.length) {
            move(index, offset < 0 ? index - 1 : index + 2);
            $('sequence').querySelectorAll('.block')[selected].focus();
          }
        }
      });
      dragSource(button, {kind: 'move', index});
      // Dropping onto a block inserts before it; the trailing slot appends.
      dropTarget(button, index);
      sequence.append(button);
    }
    $('expression').textContent = expression() || 'A expressão aparecerá aqui.';
    $('left').disabled = selected <= 0;
    $('right').disabled = selected < 0 || selected >= blocks.length - 1;
    $('remove').disabled = selected < 0;
    $('clear').disabled = blocks.length === 0;
    height();
  }

  function renderMetrics() {
    const query = $('search').value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const container = $('metrics');
    container.replaceChildren();
    const filtered = metrics.filter(name => name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().includes(query));
    for (const value of filtered) {
      const block = {kind: 'metric', value};
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'metric';
      describe(button, block);
      if (unavailableMetrics.has(value)) {
        button.classList.add('unavailable');
        button.title = `${value} — sem valor numérico nos filtros atuais`;
        const status = document.createElement('small');
        status.textContent = 'Sem valor numérico no recorte';
        button.append(status);
      }
      button.addEventListener('click', () => insert(block));
      dragSource(button, block);
      container.append(button);
    }
    if (!filtered.length) container.textContent = 'Nenhuma métrica encontrada.';
  }

  function removeSelected() {
    if (selected < 0) return;
    blocks.splice(selected, 1);
    selected = -1;
    publish('Bloco excluído.');
  }

  for (const value of ['+', '-', '*', '/', '(', ')']) {
    const block = {kind: 'operator', value};
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = value;
    button.setAttribute('aria-label', `Adicionar ${value}`);
    button.addEventListener('click', () => insert(block));
    dragSource(button, block);
    $('operators').append(button);
  }
  $('number-form').addEventListener('submit', event => {
    event.preventDefault();
    const value = $('number').value.trim().replace(',', '.');
    if (!numberPattern.test(value) || !Number.isFinite(Number(value))) {
      announce('Informe um número finito, como 2, -10 ou 0,25.'); return;
    }
    insert({kind: 'number', value});
  });
  $('search').addEventListener('input', renderMetrics);
  $('clear').addEventListener('click', () => { blocks = []; selected = -1; publish('Fórmula limpa.'); });
  $('left').addEventListener('click', () => { if (selected > 0) move(selected, selected - 1); });
  $('right').addEventListener('click', () => { if (selected >= 0 && selected < blocks.length - 1) move(selected, selected + 2); });
  $('remove').addEventListener('click', removeSelected);
  $('canvas').addEventListener('dragover', event => { if (dragging) event.preventDefault(); });
  $('canvas').addEventListener('drop', event => drop(event, blocks.length));
  window.addEventListener('message', event => {
    if (event.source !== window.parent || event.data?.type !== 'streamlit:render') return;
    const {args, theme} = event.data;
    metrics = args.metrics || [];
    unavailableMetrics = new Set(args.unavailable_metrics || []);
    maxBlocks = args.max_blocks || 120;
    // Reruns may carry the previous Python draft while our latest edit is in flight.
    // Only hydrate on mount, so rapid edits cannot be overwritten by stale renders.
    if (!initialized) { blocks = args.initial_blocks || []; initialized = true; }
    if (theme) {
      for (const [name, value] of Object.entries({bg: theme.backgroundColor, panel: theme.secondaryBackgroundColor, text: theme.textColor, accent: theme.primaryColor})) {
        if (value) document.documentElement.style.setProperty(`--${name}`, value);
      }
    }
    // A calculation finishing during a new drag must not replace its source DOM.
    if (!dragging) {
      renderMetrics();
      renderCanvas();
    }
  });
  new ResizeObserver(height).observe(document.querySelector('.editor'));
  send('streamlit:componentReady', {apiVersion: 1});
})();
