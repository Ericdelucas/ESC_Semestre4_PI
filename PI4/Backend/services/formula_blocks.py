"""Conversao blocos <-> texto do construtor visual, reutilizando o parser de formulas.

Blocos sao dicts {'type': 'var'|'num'|'op'|'paren', 'value': str}. A expressao
gerada so contem referencias [Fonte::Conta], numeros, operadores e parenteses, e
continua a passar pela AST restrita de evaluate_formula antes de qualquer calculo.
"""
from __future__ import annotations

import math
import re

from Backend.services.formula_metrics import FormulaError, bind_variables

OPERATORS = ('+', '-', '*', '/', '%')
MAX_BLOCKS = 200
_NUMBER = re.compile(r'\d{1,15}(?:\.\d{1,10})?')
_TOKEN = re.compile(r'\s*(?:__metric_(\d+)|(\d+(?:\.\d*)?|\.\d+)|([-+*/%])|([()]))')
SOURCE_LABELS = {
    'Financeiro': 'Demonstrações calculadas',
    'Indicador': 'Indicadores Monte Carlo',
    'CSV': 'Contas do Cti.csv',
    'Catalogo': 'KPIs do catálogo',
}
_STATEMENTS = {'DRE': 'DRE', 'BAL': 'Balanço', 'FLU': 'Fluxo de caixa'}


class BlockError(FormulaError):
    """Erro estrutural num bloco especifico (index) da formula."""

    def __init__(self, message: str, index: int | None = None):
        super().__init__(message)
        self.index = index


def check_structure(blocks: list[dict]) -> None:
    """Gramatica operando/operador com +/- unarios e parenteses equilibrados."""
    if not blocks:
        raise BlockError('Arraste blocos para montar a fórmula.')
    if len(blocks) > MAX_BLOCKS:
        raise BlockError(f'Use no máximo {MAX_BLOCKS} blocos.')
    expect_operand = True
    open_parens: list[int] = []
    for index, block in enumerate(blocks):
        kind, value = block.get('type'), block.get('value')
        if kind in ('var', 'num') or (kind == 'paren' and value == '('):
            if not expect_operand:
                raise BlockError('Falta um operador antes deste bloco.', index)
            if kind == 'paren':
                open_parens.append(index)
            else:
                expect_operand = False
        elif kind == 'op' and value in OPERATORS:
            if expect_operand and value not in ('+', '-'):
                raise BlockError(f'O operador {value} precisa de um valor à esquerda.', index)
            expect_operand = True
        elif kind == 'paren' and value == ')':
            if expect_operand:
                raise BlockError('Parêntese fechado sem valor dentro ou depois de um operador.', index)
            if not open_parens:
                raise BlockError('Parêntese fechado sem o correspondente "(".', index)
            open_parens.pop()
        else:
            raise BlockError('Bloco desconhecido.', index)
    if expect_operand:
        raise BlockError('A fórmula não pode terminar num operador.', len(blocks) - 1)
    if open_parens:
        raise BlockError('Parêntese aberto sem o correspondente ")".', open_parens[-1])


def blocks_to_expression(blocks: list[dict], variables: dict[str, float]) -> str:
    """Serializa blocos validados; so aceita chaves existentes e numeros simples."""
    check_structure(blocks)
    parts: list[str] = []
    for index, block in enumerate(blocks):
        kind, value = block['type'], str(block['value'])
        if kind == 'var':
            if value not in variables or '[' in value or ']' in value:
                raise BlockError(f'Variável desconhecida: {value}.', index)
            parts.append(f'[{value}]')
        elif kind == 'num':
            if not _NUMBER.fullmatch(value):
                raise BlockError('Número inválido: use dígitos e ponto decimal.', index)
            parts.append(value)
        else:
            parts.append(value)
    def unary(index: int) -> bool:
        return blocks[index]['type'] == 'op' and (
            index == 0 or blocks[index - 1]['type'] == 'op' or blocks[index - 1]['value'] == '(')

    text = parts[0]
    for index in range(1, len(parts)):
        tight = parts[index] == ')' or blocks[index - 1]['value'] == '(' or unary(index - 1)
        text += parts[index] if tight else ' ' + parts[index]
    return text


def expression_to_blocks(expression: str, variables: dict[str, float], *,
                         choices: dict[str, str] | None = None) -> list[dict]:
    """Converte texto livre em blocos com as mesmas regras de nomes da avaliacao."""
    source, keys = bind_variables(expression, variables, choices=choices)
    blocks: list[dict] = []
    position = 0
    while position < len(source):
        match = _TOKEN.match(source, position)
        if not match or match.end() == position:
            rest = source[position:].strip()
            if not rest:
                break
            raise FormulaError(f'Trecho sem bloco equivalente: "{rest[:20]}". '
                               'Use nomes do catálogo, números, parênteses e + - * / %.')
        metric, number, operator, paren = match.groups()
        if metric is not None:
            blocks.append({'type': 'var', 'value': keys[int(metric)]})
        elif number is not None:
            blocks.append({'type': 'num', 'value': number.rstrip('.') or '0'})
        elif operator is not None:
            blocks.append({'type': 'op', 'value': operator})
        else:
            blocks.append({'type': 'paren', 'value': paren})
        position = match.end()
    if len(blocks) > MAX_BLOCKS:
        raise BlockError(f'Use no máximo {MAX_BLOCKS} blocos.')
    return blocks


def block_palette(variables: dict[str, float]) -> list[dict]:
    """Variaveis agrupadas por fonte e demonstracao, prontas para a paleta visual."""
    palette = []
    order = {source: rank for rank, source in enumerate(SOURCE_LABELS)}
    for key in sorted(variables, key=lambda item: (order.get(item.split('::', 1)[0], len(order)), item)):
        source, _, name = key.partition('::')
        prefix = re.match(r'([A-Z]{3})\s*-\s*', name)
        group = SOURCE_LABELS.get(source, source)
        if prefix and prefix.group(1) in _STATEMENTS:
            group += ' · ' + _STATEMENTS[prefix.group(1)]
        value = variables[key]
        palette.append({
            'key': key,
            'source': source,
            'group': group,
            'label': name.split(' · ', 1)[-1],
            'value': value if math.isfinite(value) else None,
        })
    return palette
