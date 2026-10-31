"""Bidirectional visual editor; expressions are always rebuilt in Python."""
from pathlib import Path
import re
import math

import streamlit as st
import streamlit.components.v1 as components

from Backend.services.formula_metrics import FormulaError, variable_reference

_component = components.declare_component(
    'formula_blocks', path=str(Path(__file__).with_name('formula_blocks')),
)
MAX_BLOCKS = 120
_NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')


def _validate_blocks(blocks):
    if not isinstance(blocks, list) or len(blocks) > MAX_BLOCKS:
        raise FormulaError(f'Use no máximo {MAX_BLOCKS} blocos na fórmula.')
    for block in blocks:
        if not isinstance(block, dict):
            raise FormulaError('Bloco inválido.')
        kind, value = block.get('kind'), block.get('value')
        if not isinstance(value, str):
            raise FormulaError('Valor de bloco inválido.')
        if kind == 'metric' and 0 < len(value) <= 4000:
            continue
        if kind == 'operator' and value in ('+', '-', '*', '/', '(', ')'):
            continue
        if kind == 'number' and len(value) <= 64 and _NUMBER.fullmatch(value):
            continue
        raise FormulaError('Bloco inválido. Use métricas, números e operadores da paleta.')


def blocks_expression(blocks, variables):
    """Validate the component payload, fixing each metric to its selected source."""
    _validate_blocks(blocks)
    tokens = []
    for block in blocks:
        kind, value = block['kind'], block['value']
        if kind == 'metric':
            if value not in variables:
                raise FormulaError(f'Métrica indisponível nos filtros atuais: {value}.')
            tokens.append(variable_reference(value, variables))
        elif kind == 'operator':
            tokens.append(value)
        else:
            # Parentheses preserve signed constants when placed next to operators.
            tokens.append(f'({value})' if value.startswith(('+', '-')) else value)
    expression = ' '.join(tokens)
    if len(expression) > 4000:
        raise FormulaError('A fórmula excede o limite de 4000 caracteres.')
    return expression


def render_formula_blocks(persona, variables):
    state_key = f'formula_blocks_{persona}'
    blocks = st.session_state.get(state_key, [])
    payload = _component(
        initial_blocks=blocks, metrics=sorted(variables), max_blocks=MAX_BLOCKS,
        unavailable_metrics=[key for key, value in variables.items() if not math.isfinite(value)],
        key=f'formula_canvas_{persona}', default={'blocks': blocks},
    )
    if not isinstance(payload, dict) or 'blocks' not in payload:
        raise FormulaError('Não foi possível ler os blocos da fórmula.')
    blocks = payload['blocks']
    _validate_blocks(blocks)
    # Keep the draft even if its expression is incomplete or filters remove a metric.
    st.session_state[state_key] = blocks
    return blocks_expression(blocks, variables), blocks
