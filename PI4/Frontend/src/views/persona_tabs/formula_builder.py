"""Construtor e apresentacao exclusivamente numerica de formulas."""
from uuid import uuid4

import streamlit as st

from Backend.services.formula_blocks import block_palette, expression_to_blocks
from Backend.services.formula_metrics import FormulaError, evaluate_formula, formula_variables, format_formula_value, variable_reference, variable_aliases, _name
from src.components.formula_blocks_component import edited_formula, formula_blocks_editor


# Compartilha o catalogo entre o dialogo e os KPIs durante a sessao.
_cached_variables = st.cache_data(show_spinner="Calculando variáveis financeiras…", max_entries=8)(formula_variables)

def render_formula_builder(persona, df, ind, cena, ano):
    if df is None or ind is None:
        st.info('Base de dados indisponível.')
        return
    expression_key = f'formula_expression_{persona}'
    selection_key = f'formula_var_{persona}'
    blocks_key = f'formula_blocks_{persona}'
    name = st.text_input('Nome da nova fórmula', value='Minha fórmula', key=f'formula_name_{persona}')
    # Preenchido no fim, com o resultado; o callback corre antes do text_input existir.
    blocks_slot = st.container()

    def apply_blocks():
        edited = edited_formula(blocks_key)
        if edited is not None:
            st.session_state[expression_key] = edited['expression']

    expression = st.text_input('Ou escreva a fórmula em texto (sincronizada com os blocos)', key=expression_key,
                               placeholder='Ex.: (EBITDA - Capex) / 2',
                               help='Use +, -, *, /, parênteses e nomes de métricas. Exemplo de teste: 10 + 20 / 2.')
    test = st.button('Testar Fórmula', key=f'formula_test_{persona}', type='primary')
    preview = st.empty()
    style = st.selectbox('Mostrar resultado como', ['Número', 'Moeda', 'Percentual'], key=f'formula_style_{persona}')
    with st.expander('Opções avançadas'):
        aggregation = st.selectbox('Consolidar anos por', ['mean', 'sum', 'min', 'max'],
                                   format_func={'mean': 'Média', 'sum': 'Soma', 'min': 'Mínimo', 'max': 'Máximo'}.get,
                                   key=f'formula_agg_{persona}')
        decimals = st.slider('Casas decimais', 0, 6, 2, key=f'formula_decimals_{persona}')
        st.caption('Os filtros do painel definem cenário e período. Em Todos os cenários, usamos '
                   'a média das métricas calculadas por cenário e depois consolidamos os anos. '
                   'ROIC financeiro é fração; ROIC do catálogo é percentual. O formato % só acrescenta o símbolo.')
    # Os controles essenciais sao renderizados antes de carregar as metricas.
    variables = {}
    load_error = None
    try:
        variables = _cached_variables(df, ind, cena, ano, aggregation)
    except FormulaError as exc:
        load_error = str(exc)

    def insert_variable():
        selected = st.session_state.get(selection_key)
        if selected:
            current = st.session_state.get(expression_key, '')
            reference = variable_reference(selected, variables)
            st.session_state[expression_key] = current + (' ' if current and not current.endswith(' ') else '') + reference
            st.session_state[selection_key] = None

    st.selectbox('Inserir uma variável na fórmula', sorted(variables), index=None,
                 placeholder='Pesquise EBITDA, ROIC, Capex ou uma conta…',
                 key=selection_key, on_change=insert_variable)
    st.caption('Nomes vêm dos dados carregados. Espaços, underscores e acentos são equivalentes. '
               'Fontes repetidas usam a prioridade Financeiro → Indicador → CSV → Catálogo; você pode escolher outra abaixo.')
    if load_error:
        st.warning(load_error + ' Você ainda pode testar expressões com números.')
    result = None
    error = None
    choices = {}
    if expression.strip():
        try:
            resolved = {}
            result = evaluate_formula(expression, variables, resolved=resolved)
            with st.expander('Variáveis reconhecidas e fontes usadas', expanded=True):
                aliases = variable_aliases(variables)
                for index, (typed, key) in enumerate(resolved.items()):
                    candidates = [key] if '::' in typed else aliases.get(_name(typed), [key])
                    if _name(typed) in choices:
                        continue
                    if len(candidates) > 1:
                        chosen = st.selectbox(f'Fonte para {typed}', candidates,
                                              key=f'formula_source_{persona}_{_name(typed)}',
                                              format_func=lambda item: f'{item} = {variables[item]:,.6g}')
                        choices[_name(typed)] = chosen
                    else:
                        st.caption(f'{typed} → {key} = {variables[key]:,.6g}')
            result = evaluate_formula(expression, variables, choices=choices)
            preview.metric('Resultado do teste', format_formula_value(result, style, decimals))
        except FormulaError as exc:
            error = str(exc)
            preview.error(error)
    elif test:
        preview.info('Digite uma fórmula para testar. Exemplo: 10 + 20 / 2.')
    else:
        preview.caption('Digite a expressão e clique em Testar Fórmula para conferir o número antes de criar.')
    blocks, sync_error = [], None
    if expression.strip():
        try:
            blocks = expression_to_blocks(expression, variables, choices=choices)
        except FormulaError as exc:
            blocks, sync_error = None, str(exc)
    status = ({'ok': True, 'text': '= ' + format_formula_value(result, style, decimals)} if result is not None
              else {'ok': False, 'text': error} if error else None)
    with blocks_slot:
        formula_blocks_editor(key=blocks_key, palette=block_palette(variables), blocks=blocks,
                              expression=expression, status=status, sync_error=sync_error,
                              on_change=apply_blocks)
    if st.button('Criar fórmula / Salvar KPI', disabled=result is None or not name.strip(), key=f'formula_save_{persona}'):
        from src.controllers.custom_analysis import custom_analyses, custom_key
        analysis = dict(id=uuid4().hex, kind='formula', label=name.strip(), expression=expression,
                        aggregation=aggregation, style=style, decimals=decimals, choices=choices)
        custom_analyses(persona).append(analysis)
        st.session_state['nav_key'] = custom_key(analysis)
        st.session_state[f'show_custom_analysis_dialog_{persona}'] = False
        st.rerun()


def render_formula_kpi(df, ind, analysis, cena, ano):
    try:
        variables = _cached_variables(df, ind, cena, ano, analysis['aggregation'])
        result = evaluate_formula(analysis['expression'], variables, choices=analysis.get('choices'))
    except FormulaError as exc:
        st.error(str(exc))
        return
    st.metric(analysis['label'], format_formula_value(result, analysis['style'], analysis['decimals']))
    # Code span: * e _ da expressao nao viram Markdown; formulas salvas nunca contem crases.
    st.caption(f"Fórmula: `{analysis['expression']}`")
