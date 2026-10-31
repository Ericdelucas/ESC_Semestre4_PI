"""Catalogo dinamico e interpretador aritmetico, sem execucao de codigo Python."""
from __future__ import annotations

import ast
import math
import operator
import re
import unicodedata

import pandas as pd

from Backend.metrics.custom_catalog import FINANCIAL_METRICS_DICT
from Backend.metrics.financial_kpis import build_financial_statement, build_break_even
from Backend.metrics.financial_kpis import probabilidade_caixa_negativo
from Backend.metrics.commercial_kpis import calculate_ltv_cac
from Backend.metrics.dashboard_metrics import operating_metrics, concession_metrics
from Backend.services.scenario_filter import filtrar_cenario_ano


class FormulaError(ValueError):
    """Formula invalida ou dados insuficientes para um resultado numerico."""


# Register sources, never individual metric names. Every output column is exported.
FORMULA_SOURCES = {
    'Financeiro': build_financial_statement,
    'Equilibrio': build_break_even,
    'Comercial': calculate_ltv_cac,
}
_AXES = {'ANO', 'ano_num', 'CENA', 'CONTA'}


def _numeric(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce').astype(float)
    text = series.astype('string').str.strip().str.replace('R$', '', regex=False).str.strip()
    comma = text.str.contains(',', regex=False, na=False)
    text = text.where(~comma, text.str.replace('.', '', regex=False).str.replace(',', '.', regex=False))
    return pd.to_numeric(text, errors='coerce').astype(float)


def formula_variables(df: pd.DataFrame, ind: pd.DataFrame, cena: str = 'Todos',
                      ano: str | int = 'Todos', aggregation: str = 'mean', *,
                      ranking: pd.DataFrame | None = None) -> dict[str, float]:
    """Soma registros da mesma conta/cenario/ano; media cenarios; consolida anos.

    Derivadas sao calculadas por cenario antes da media Monte Carlo.
    As formulas combinam os escalares consolidados, nao series temporais.
    """
    if aggregation not in {'mean', 'sum', 'min', 'max'}:
        raise FormulaError('Consolidacao desconhecida.')
    raw, selected = filtrar_cenario_ano(df, cena_sel=cena, ano_sel=ano)
    _, indicators = filtrar_cenario_ano(ind, cena_sel=cena, ano_sel=ano)
    if raw.empty and indicators.empty:
        raise FormulaError('Nao existem dados para os filtros selecionados.')
    values: dict[str, float] = {}

    def add(prefix: str, frame: pd.DataFrame) -> None:
        # Object/nullable columns can hold valid numbers or entirely missing KPIs.
        # Keep their names visible even when there is no numeric value to aggregate.
        _, frame = filtrar_cenario_ano(frame, cena_sel=cena, ano_sel=ano)
        for col in frame.columns:
            if col in _AXES:
                continue
            series = _numeric(frame[col]).replace([math.inf, -math.inf], math.nan)
            value = math.nan
            if not series.empty and 'ano_num' in frame:
                grouped = series.groupby(frame['ano_num'], observed=True)
                annual = grouped.mean().where(grouped.count() == grouped.size())
                expected = selected['ano_num'].unique() if not selected.empty else frame['ano_num'].unique()
                annual = annual.reindex(expected)
                if len(annual) and annual.notna().all():
                    value = float(annual.agg(aggregation))
            values[f'{prefix}::{col}'] = value

    add('Coluna CSV', selected)
    add('Indicador', indicators)

    def add_ranking():
        if ranking is None:
            return
        ranks, _ = filtrar_cenario_ano(ranking, cena_sel=cena, ano_sel='Todos')
        for col in ranking.columns:
            if col in _AXES:
                continue
            series = _numeric(ranks[col])
            values[f'Ranking::{col}'] = float(series.mean()) if len(series) and series.notna().all() else math.nan
        values['Contexto::p_ruina'] = probabilidade_caixa_negativo(ranks) if len(ranks) else math.nan
        values['Contexto::n_cenarios'] = float(ranks.get('CENA', pd.Series(dtype=str)).nunique())

    if raw.empty:
        # Discover the builders' complete schema, but never publish synthetic
        # values as real data for an indicators-only dataset.
        schema = pd.DataFrame({'CENA': ['_schema'], 'ano_num': [1],
                               'CONTA': ['DRE - Receita'], 'VALOR': [0.]})
        unavailable = formula_variables(schema, pd.DataFrame(), aggregation=aggregation)
        for key in unavailable:
            values.setdefault(key, math.nan)
        for account in df.get('CONTA', pd.Series(dtype=str)).dropna().unique():
            values[f'CSV::{account}'] = math.nan
        add_ranking()
        return values
    wide = (raw.groupby(['CENA', 'ano_num', 'CONTA'], observed=True)['VALOR']
            .sum(min_count=1).unstack('CONTA').reset_index())
    add('CSV', wide)
    for account in df['CONTA'].dropna().unique():
        values.setdefault(f'CSV::{account}', math.nan)
    # Codifica cada par cenario/ano como uma linha independente para reutilizar
    # os calculos vetorizados sem executar dois builders por cenario Monte Carlo.
    pairs = raw[['CENA', 'ano_num']].drop_duplicates().sort_values(['CENA', 'ano_num']).reset_index(drop=True)
    pairs['_period'] = pairs.index
    batch = raw.merge(pairs, on=['CENA', 'ano_num'], how='left')
    batch['ano_num'] = batch['_period']
    batch['CENA'] = '_formula'
    original_years = pairs.set_index('_period')['ano_num']
    original_scenarios = pairs.set_index('_period')['CENA']

    def restore(frame):
        frame = frame.copy()
        frame['CENA'] = frame['ano_num'].map(original_scenarios)
        frame['ano_num'] = frame['ano_num'].map(original_years)
        return frame

    frames = {prefix: builder(batch, '_formula') for prefix, builder in FORMULA_SOURCES.items()}
    statement = frames['Financeiro']
    breakeven = frames['Equilibrio']
    extra = [col for col in breakeven if col not in statement]
    if extra:
        statement = statement.merge(breakeven[['ano_num', *extra]], on='ano_num', how='outer')
    capex = batch.loc[batch['CONTA'] == 'FLU - Investimentos'].groupby('ano_num')['VALOR'].sum().abs()
    statement['Capex'] = statement['ano_num'].map(capex)
    statement = restore(statement)
    if not statement.empty:
        statement = concession_metrics(operating_metrics(statement))
    add('Financeiro', statement)
    for prefix, frame in frames.items():
        if prefix != 'Financeiro':
            add(prefix, restore(frame))
    computed = wide[['ano_num']].copy()
    for name, metric in FINANCIAL_METRICS_DICT.items():
        try:
            result = metric['formula'](wide)
            computed[name] = _numeric(result) if isinstance(result, pd.Series) else result
        except KeyError:
            computed[name] = math.nan
    computed['CENA'] = wide['CENA']
    add('Catalogo', computed)
    add_ranking()
    return values


def custom_formula_variables(variables, analyses, catalogs=None):
    """Expose saved KPIs of the active persona, including dependent formulas.

    Unavailable inputs or circular dependencies stay visible as NaN. Catalogs
    let each saved KPI retain its own year-aggregation rule.
    """
    values = dict(variables)
    pending = {f"Personalizado::{item['id']} · {item['label']}": item
               for item in analyses if item.get('kind') == 'formula'}
    custom = dict.fromkeys(pending, math.nan)
    while pending:
        progress = False
        for key, item in list(pending.items()):
            source = (catalogs or {}).get(item.get('aggregation', 'mean'), variables)
            try:
                value = evaluate_formula(item['expression'], {**source, **custom}, choices=item.get('choices'))
            except FormulaError:
                continue
            custom[key] = value
            del pending[key]
            progress = True
        if not progress:
            break
    values.update(custom)
    return values


def _plain(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).casefold()


def _name(text: str) -> str:
    # Mesma regra para todas as contas: acentos, espacos e underscores sao equivalentes.
    words = re.findall(r'[a-z0-9]+', _plain(text))
    return ' '.join(word[:-1] if len(word) > 3 and word.endswith('s') else word for word in words)


def variable_aliases(variables: dict[str, float]) -> dict[str, list[str]]:
    """Descobre nomes e variantes a partir das fontes, sem lista de metricas."""
    aliases: dict[str, list[str]] = {}
    prefixes = {match.group(1) for key in variables
                if (match := re.match(r'([A-Z]{2,5})\s*-', key.split('::', 1)[-1]))}
    for key in variables:
        short = key.split('::', 1)[-1]
        names = {short, short.split(' · ', 1)[-1]}
        names.update(re.sub(r'^[A-Z]{2,5}\s*-\s*', '', name) for name in list(names))
        if key.startswith('Financeiro::'):
            names.update(f'{prefix} - {short}' for prefix in prefixes)
        for name in names:
            normalized = _name(name)
            if key not in aliases.setdefault(normalized, []):
                aliases[normalized].append(key)
    # Politica uniforme de origem para TODOS os nomes repetidos, nao por metrica.
    priority = {'Financeiro': 0, 'Indicador': 1, 'CSV': 2, 'Catalogo': 3}
    for name, candidates in aliases.items():
        candidates.sort(key=lambda key: (
            priority.get(key.split('::', 1)[0], 4),
            _name(key.split('::', 1)[-1]) != name,
            key,
        ))
    return aliases


def variable_reference(key: str, variables: dict[str, float]) -> str:
    # Inclusao pelo catalogo sempre fixa a fonte escolhida.
    return f'[{key}]'


def evaluate_formula(expression: str, variables: dict[str, float], *,
                     choices: dict[str, str] | None = None,
                     resolved: dict[str, str] | None = None) -> float:
    """Interpreta nomes livres ou entre colchetes e aritmetica via AST restrita."""
    if not expression.strip() or len(expression) > 4000:
        raise FormulaError('Informe uma formula com ate 4000 caracteres.')
    aliases = variable_aliases(variables)
    bindings = {}
    choices = choices or {}
    # Faz o matching dos nomes completos antes dos nomes curtos.
    patterns = [re.escape(_plain(key)) for key in variables]
    for name in aliases:
        words = name.split()
        # Forma singular/plural e separadores livres, gerados para cada nome.
        patterns.append(r'[\s_\-·]+'.join(re.escape(word) + ('s?' if len(word) > 2 else '') for word in words))
    patterns.sort(key=len, reverse=True)
    pattern = r'\[([^\[\]]+)\]'
    if patterns:
        pattern += r'|(?<![\w.:])(?:' + '|'.join(patterns) + r')(?![\w:])'
    full_names = {_plain(key): key for key in variables}

    def substitute(match: re.Match) -> str:
        name = match.group(1) if match.group(1) is not None else match.group(0)
        exact = full_names.get(_plain(name))
        candidates = [exact] if exact else aliases.get(_name(name), [])
        if not candidates:
            raise FormulaError(f'Variavel desconhecida: {name}. Selecione uma conta no catálogo.')
        key = exact or choices.get(_name(name), candidates[0])
        if key not in candidates:
            raise FormulaError(f'Fonte invalida para {name}.')
        if resolved is not None:
            resolved[name] = key
        alias = f'__metric_{len(bindings)}'
        bindings[alias] = variables[key]
        return alias

    if '__metric_' in expression:
        raise FormulaError('Nome de variavel reservado.')
    source = re.sub(pattern, substitute, _plain(expression)).strip()
    try:
        tree = ast.parse(source, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 256:
            raise FormulaError('Formula muito complexa.')
        ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
               ast.Div: operator.truediv, ast.Mod: operator.mod}

        def visit(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                value = visit(node.body)
            elif isinstance(node, ast.Constant) and type(node.value) in (int, float):
                value = float(node.value)
            elif isinstance(node, ast.Name) and node.id in bindings:
                value = float(bindings[node.id])
            elif isinstance(node, ast.BinOp) and type(node.op) in ops:
                value = ops[type(node.op)](visit(node.left), visit(node.right))
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
            elif isinstance(node, ast.Name):
                raise FormulaError(f'Variável desconhecida: {node.id}. Busque o nome no catálogo ou insira a referência completa.')
            else:
                raise FormulaError('Use nomes do catálogo, números, parênteses e + - * / %.')
            if not math.isfinite(value):
                raise FormulaError('A formula utiliza dados ausentes ou resulta em valor nao finito.')
            return value

        return visit(tree)
    except (SyntaxError, ZeroDivisionError, OverflowError, RecursionError) as exc:
        raise FormulaError('Formula invalida, divisao por zero ou limite numerico excedido.') from exc


def format_formula_value(value: float, style: str = 'Número', decimals: int = 2) -> str:
    formatted = f'{value:,.{decimals}f}'.translate(str.maketrans({',': '.', '.': ','}))
    return ('R$ ' if style == 'Moeda' else '') + formatted + ('%' if style == 'Percentual' else '')
