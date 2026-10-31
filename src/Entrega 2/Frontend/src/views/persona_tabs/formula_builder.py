"""Construtor visual e apresentação numérica de fórmulas."""
from uuid import uuid4

import streamlit as st

from Backend.services.formula_metrics import FormulaError, evaluate_formula, formula_variables, format_formula_value, custom_formula_variables
from src.components.formula_blocks import render_formula_blocks


_cached_variables = st.cache_data(show_spinner="Calculando variáveis financeiras…", max_entries=8)(formula_variables)


def _variables(persona, df, ind, cena, ano, aggregation, ranking=None):
    from src.controllers.custom_analysis import custom_analyses
    analyses = custom_analyses(persona)
    aggregations = {aggregation, *(item.get('aggregation', 'mean') for item in analyses if item.get('kind') == 'formula')}
    catalogs = {agg: _cached_variables(df, ind, cena, ano, agg, ranking=ranking) for agg in aggregations}
    return custom_formula_variables(catalogs[aggregation], analyses, catalogs)


def render_formula_builder(persona, df, ind, cena, ano, ranking=None):
    if df is None or ind is None:
        st.info('Base de dados indisponível.')
        return
    name = st.text_input('Nome da nova fórmula', value='Minha fórmula', key=f'formula_name_{persona}')
    style = st.selectbox('Mostrar resultado como', ['Número', 'Moeda', 'Percentual'], key=f'formula_style_{persona}')
    with st.expander('Opções avançadas'):
        aggregation = st.selectbox('Consolidar anos por', ['mean', 'sum', 'min', 'max'],
                                   format_func={'mean': 'Média', 'sum': 'Soma', 'min': 'Mínimo', 'max': 'Máximo'}.get,
                                   key=f'formula_agg_{persona}')
        decimals = st.slider('Casas decimais', 0, 6, 2, key=f'formula_decimals_{persona}')
        st.caption('Os filtros do painel definem cenário e período. Em Todos os cenários, usamos '
                   'a média das métricas calculadas por cenário e depois consolidamos os anos. '
                   'ROIC financeiro é fração; ROIC do catálogo é percentual. O formato % só acrescenta o símbolo.')
    variables = {}
    try:
        variables = _variables(persona, df, ind, cena, ano, aggregation, ranking)
    except FormulaError as exc:
        st.warning(str(exc) + ' Você ainda pode montar expressões com números.')

    st.caption('Arraste métricas e operadores da paleta para montar a fórmula. '
               'Cada bloco mantém sua fonte. Itens sem valor numérico no recorte continuam visíveis na paleta.')
    st.caption(f'{len(variables)} variáveis disponíveis nas fontes carregadas. Contas e colunas novas entram automaticamente.')
    expression, blocks, block_error = '', [], None
    try:
        expression, blocks = render_formula_blocks(persona, variables)
    except FormulaError as exc:
        block_error = str(exc)

    test = st.button('Testar Fórmula', key=f'formula_test_{persona}', type='primary')
    result = None
    if block_error:
        st.error(block_error)
    elif expression:
        try:
            result = evaluate_formula(expression, variables)
            st.metric('Resultado do teste', format_formula_value(result, style, decimals))
        except FormulaError as exc:
            st.error(str(exc))
    elif test:
        st.info('Adicione blocos para testar. Exemplo: 10 + 20 / 2.')
    else:
        st.caption('Monte a fórmula para conferir o resultado antes de criar o KPI.')

    if st.button('Criar fórmula / Salvar KPI', disabled=result is None or not name.strip(), key=f'formula_save_{persona}'):
        from src.controllers.custom_analysis import custom_analyses, custom_key, set_custom_analysis_modal
        analysis = dict(id=uuid4().hex, kind='formula', label=name.strip(), expression=expression,
                        blocks=blocks, aggregation=aggregation, style=style, decimals=decimals, choices={})
        custom_analyses(persona).append(analysis)
        st.session_state['nav_key'] = custom_key(analysis)
        set_custom_analysis_modal(persona, False)
        st.rerun()


def render_formula_kpi(df, ind, analysis, cena, ano, ranking=None, persona=None):
    try:
        variables = (_variables(persona, df, ind, cena, ano, analysis['aggregation'], ranking)
                     if persona is not None else _cached_variables(df, ind, cena, ano, analysis['aggregation'], ranking=ranking))
        result = evaluate_formula(analysis['expression'], variables, choices=analysis.get('choices'))
    except FormulaError as exc:
        st.error(str(exc))
        return
    st.metric(analysis['label'], format_formula_value(result, analysis['style'], analysis['decimals']))
