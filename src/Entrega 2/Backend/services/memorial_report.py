"""Memorial CTI calculado por requisição; layout inspirado no modelo do professor."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, KeepTogether

from Backend.metrics.financial_kpis import build_dre, build_break_even, build_financial_statement, is_all_scenarios, _wide
from Backend.metrics.commercial_kpis import calculate_ltv_cac
from Backend.services.risk_alerts import varrer_riscos


def numero(value, percent=False):
    if pd.isna(value):
        return 'Não definido'
    value = float(value) * (100 if percent else 1)
    return f'{value:,.2f}'.replace(',', '@').replace('.', ',').replace('@', '.') + ('%' if percent else '')


def gerar_memorial_pdf(df, ranking, *, scenario='Todos', year=None):
    """Calcula a partir da base recebida. Não grava arquivo nem dispara SMTP."""
    if df.empty:
        raise ValueError('Base CTI vazia.')
    if not is_all_scenarios(scenario) and scenario not in set(df['CENA'].astype(str)):
        raise ValueError('Cenário não encontrado na base CTI.')
    if year is not None and year not in set(pd.to_numeric(df['ano_num'], errors='coerce')):
        raise ValueError('Ano não encontrado na base CTI.')
    # Calcula antes do filtro anual para preservar alinhamento das premissas comerciais.
    dre = build_dre(df, scenario)
    be = build_break_even(df, scenario)
    fs = build_financial_statement(df, scenario)
    commercial = calculate_ltv_cac(df, scenario)
    balance_accounts = ['BAL - Ativo Circulante', 'BAL - Passivo Circulante',
                        'BAL - Realizável a Longo Prazo', 'BAL - Exigível a Longo Prazo',
                        'BAL - Total do Ativo', 'FLU - Investimentos']
    balance = _wide(df, scenario, balance_accounts)
    if year is not None:
        dre, be, fs, commercial, balance = [frame.loc[frame.ano_num == year] for frame in [dre, be, fs, commercial, balance]]
    if dre.empty:
        raise ValueError('Sem DRE para os filtros selecionados.')
    risks = varrer_riscos(ranking)
    recorte = df if is_all_scenarios(scenario) else df.loc[df['CENA'].astype(str) == scenario]
    if year is not None:
        recorte = recorte.loc[recorte.ano_num == year]
    # Fontes Unicode para o símbolo de verificação e rubricas portuguesas.
    font_dir = Path('/usr/share/fonts/truetype/dejavu')
    font, bold, mono = 'Helvetica', 'Helvetica-Bold', 'Courier'
    if (font_dir / 'DejaVuSans.ttf').exists():
        for name, file in [('CTIMemorial', 'DejaVuSans.ttf'), ('CTIMemorialBold', 'DejaVuSans-Bold.ttf'), ('CTIMemorialMono', 'DejaVuSansMono.ttf')]:
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(font_dir / file)))
        font, bold, mono = 'CTIMemorial', 'CTIMemorialBold', 'CTIMemorialMono'
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CTIBody', fontName=font, fontSize=8, leading=12, spaceAfter=5))
    styles.add(ParagraphStyle('CTIHeading', fontName=bold, fontSize=13, leading=18, textColor=colors.HexColor('#1e3a5f'), spaceBefore=12, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle('CTISub', parent=styles['CTIHeading'], fontSize=10, leading=14))
    styles.add(ParagraphStyle('CTICode', parent=styles['CTIBody'], fontName=mono, fontSize=7, leading=10, backColor=colors.HexColor('#f0f4fa'), borderPadding=6, spaceBefore=6, spaceAfter=10))
    styles.add(ParagraphStyle('CTIWhite', parent=styles['CTIBody'], fontName=bold, textColor=colors.white))
    story = []
    def p(value, style='CTIBody'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])
    def text(value): story.append(p(value))
    def table(headers, rows, widths=None):
        t = Table([[p(c, 'CTIWhite') for c in headers]] + [[p(c) for c in row] for row in rows], colWidths=widths or [171]*3, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e6da4')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f4fa'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#CFDCEB')),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(t);story.append(Spacer(1, 7))
    def section(title, fields):
        story.append(PageBreak());story.append(p(title, 'CTIHeading'))
        table(['BASE DE DADOS DESTA SEÇÃO'], [[fields]], [513])
    def metric(title, formula, value, steps, percent=False, note=''):
        story.append(p(title, 'CTISub'))
        table(['CAMPO', 'FÓRMULA', 'RESULTADO'], [[title, formula, numero(value, percent)]], [135, 245, 133])
        valid = not pd.isna(value)
        # ZapfDingbats inclui o sinal de verificação em instalações sem DejaVu.
        check = '✓' if font != 'Helvetica' else ''
        v = p('Verificação: ' + steps + (' ' + check if valid else ' — sem resultado definido.'))
        if valid and font == 'Helvetica':
            v = Paragraph(escape('Verificação: ' + steps) + ' <font name="ZapfDingbats">3</font>', styles['CTIBody'])
        story.append(v)
        story.append(p(formula, 'CTICode'))
        if note: text(note)
    issued = datetime.now(ZoneInfo('America/Araguaina')).strftime('%d/%m/%Y %H:%M:%S')
    story.append(p('MEMORIAL DE CÁLCULO / DOCUMENTAÇÃO TÉCNICA CTI', 'CTIHeading'))
    text('Dashboard Financeiro CTI • CEO, CFO, Acionistas e Poder Concedente')
    text('Gerado pela API em ' + issued + ' (America/Araguaina). Valores monetários em reais, sem escala.')
    table(['DADOS BASE', 'SEÇÕES COBERTAS'], [[
        f'Fonte: Cti.csv / Parquet do pipeline\nRegistros da base ativa: {len(df):,}\nRegistros no recorte: {len(recorte):,}\nHorizonte disponível: Ano {df.ano_num.min()}–{df.ano_num.max()}\nCenário: {scenario}\nAno: {year if year is not None else "Todos"}',
        '1. DRE e KPIs\n2. Cenários e eficiência\n3. Risco consolidado\n4. Solvência e retorno'
    ]], [300, 213])
    text('Cenário específico: soma por ano/conta. Todos: média por ano/conta. Não somar cenários como empresas independentes. Ano Todos apresenta resultados anuais separados. O risco de cauda usa o universo completo de cenários, explicitado na seção 3.')
    text('Sinais e fórmulas do projeto são preservados. Cálculos usam a precisão da base; exibição com duas casas. ✓ indica reconciliação com a regra implementada, não auditoria independente. A base contém trajetórias simuladas.')
    section('SEÇÃO 1 — DRE E KPIs FINANCEIROS', f'Base longa CTI; cenário {scenario}; ano {year or "Todos"}. Campos DRE: Receita, Tributos, Custos, EBITDA, Resultado Operacional, Resultado Financeiro, IR/CS e Resultado Líquido. build_dre e build_break_even.')
    for _, r in dre.iterrows():
        y = int(r.ano_num); b = be.loc[be.ano_num == y].iloc[0]
        story.append(p(f'Ano {y}', 'CTIHeading'))
        metric('1.1 Receita Líquida', 'RL = Receita + Tributos', r['Receita Líquida'], f"{numero(r['DRE - Receita'])} + ({numero(r['DRE - Tributos'])}) = {numero(r['Receita Líquida'])}")
        for n, title, raw in [('1.2', 'EBITDA', 'DRE - EBITDA'), ('1.3', 'EBIT', 'DRE - Resultado Operacional')]:
            metric(n+' '+title, title+' = '+raw, r[title], f"conta informada {numero(r[raw])} = {numero(r[title])}", note='Leitura direta da conta; não força uma identidade independente com depreciação.')
        ll = r['DRE - Resultado Líquido']
        llsteps = f"|{numero(ll)}| > 1e-9; usa informado = {numero(r['Lucro Líquido'])}" if abs(ll)>1e-9 else f"{numero(r.EBIT)} + ({numero(r['Resultado Financeiro'])}) + ({numero(r['DRE - Imposto de Renda e Contribuição Social'])}) = {numero(r['Lucro Líquido'])}"
        metric('1.4 Lucro Líquido', 'LL informado se |LL| > 1e-9; senão EBIT + RF + IR/CS', r['Lucro Líquido'], llsteps)
        margin = b['Margem de Contribuição (%)']
        metric('1.5 Break-Even', 'CV = |Custos|; CF = |Outros| + |D&A| + |Desp. financeiras|; m = (RL − CV)/RL; BE = CF/m', b['Break-Even'], f"CV = {numero(abs(r.Custos))}; CF = {numero(abs(r['Outros Operacionais']))} + {numero(abs(r['Depreciação']))} + {numero(abs(r['Despesas Financeiras']))} = {numero(b['Custos Fixos'])}; m = ({numero(r['Receita Líquida'])} − {numero(abs(r.Custos))}) / {numero(r['Receita Líquida'])} = {numero(margin, True)}; BE = {numero(b['Custos Fixos'])} / {margin} = {numero(b['Break-Even'])}")
        metric('1.6 Margem de Segurança', 'MS = (RL − BE)/RL', b['Margem de Segurança (%)'], f"({numero(r['Receita Líquida'])} − {numero(b['Break-Even'])}) / {numero(r['Receita Líquida'])} = {numero(b['Margem de Segurança (%)'], True)}", percent=True, note='Denominadores nulos: não definido. Margem de contribuição negativa não implica viabilidade econômica.')
    story.append(p('Resumo anual da seção', 'CTISub'))
    table(['ANO', 'RECEITA LÍQUIDA', 'LUCRO LÍQUIDO'], [[int(r.ano_num),numero(r['Receita Líquida']),numero(r['Lucro Líquido'])] for _,r in dre.iterrows()])
    section('SEÇÃO 2 — CENÁRIOS E EFICIÊNCIA', f'Recorte {scenario}; ano {year or "Todos"}; calculate_ltv_cac. Premissas comerciais buscadas por aliases; ausentes usam os padrões do código.')
    text('CAC = investimento / novos clientes; LTV = ticket × margem de contribuição × retenção. Padrões somente na ausência de premissas: ticket 4.500; retenção 10 meses; investimento 100.000; novos clientes 1.000. Ticket precisa ter periodicidade compatível com meses. Séries encontradas são médias anuais e alinhadas com preenchimento para frente/trás; os resultados abaixo são os devolvidos pela função, sem substituir premissas presentes.')
    for _, c in commercial.iterrows():
        text(f'Ano {int(c.ano_num)}')
        table(['CAMPO', 'FÓRMULA', 'RESULTADO'], [['CAC','Investimento / Novos clientes',numero(c.CAC)],['LTV','Ticket × m × Retenção',numero(c.LTV)],['LTV/CAC','LTV / CAC',numero(c['LTV/CAC'])]])
        metric('2.1 Reconciliação LTV/CAC', 'Q = LTV / CAC', c['LTV/CAC'], f"{numero(c.LTV)} / {numero(c.CAC)} = {numero(c['LTV/CAC'])}")
    story.append(p('Resumo do recorte', 'CTISub'))
    table(['CAMPO','FÓRMULA','RESULTADO'], [['Registros','Contagem após cenário/ano',len(recorte)],['Cenários','CENA distinta no recorte',recorte.CENA.nunique()],['Anos','ano_num distinto no recorte',recorte.ano_num.nunique()]])
    section('SEÇÃO 3 — RISCO DO UNIVERSO DE CENÁRIOS', 'Ranking atual do pipeline; universo integral, independente dos filtros DRE. Campos: caixa_ano12, liquidez, selo, CENA. varrer_riscos(ranking). Esta seção não envia e-mail.')
    text(risks['summary'])
    for i, c in enumerate(risks['checks'],1):
        story.append(p(f"3.{i} {c['label']}", 'CTISub'))
        table(['CAMPO','FÓRMULA','RESULTADO'], [[c['label'],c['formula'],c['value']]])
        text(f"Estado: {c['status']}. Limiar: {c['threshold']}. {c['note']}")
    m = risks['metrics']; n=m['n_cenarios']
    if n: metric('3.6 Probabilidade de caixa negativo', '100 × n_ruína / n_cenários',100*m['n_ruina']/n,f"100 × {m['n_ruina']} / {n} = {numero(100*m['n_ruina']/n)}%")
    text('Favorável/conforme refere-se aos limites do CTI. Ruína até 5% é controlada, acima de 5% gera atenção e acima do limite configurado é crítica. P5 negativo é crítico. Liquidez abaixo do mínimo é crítica e entre o mínimo e 120% dele gera atenção. Médias favoráveis não eliminam trajetórias ruins.')
    table(['INDICADOR','RESULTADO','ESTADO'], [[c['label'],c['value'],c['status']] for c in risks['checks']])
    section('SEÇÃO 4 — SOLVÊNCIA E RETORNO', f'Base longa, cenário {scenario}; ano {year or "Todos"}. BAL: AC, PC, Realizável LP, Exigível LP, Ativo; FLU: Investimentos. build_financial_statement; WACC 10%, payout 35%.')
    for _, bal in balance.iterrows():
        y=int(bal.ano_num); s=fs.loc[fs.ano_num==y].iloc[0]
        ac,pc,lp,elp=[abs(bal[k]) for k in balance_accounts[:4]]
        lg=(ac+lp)/(pc+elp) if pc+elp else float('nan')
        text(f'Ano {y}')
        metric('4.1 Liquidez Geral', 'LG = (|AC| + |Realizável LP|)/(|PC| + |Exigível LP|)',lg,f"({numero(ac)} + {numero(lp)}) / ({numero(pc)} + {numero(elp)}) = {numero(lg)}",note='Liquidez geral do concedente difere da liquidez corrente média do ranking de risco.')
        metric('4.2 CAPEX','CAPEX = |FLU - Investimentos|',abs(bal['FLU - Investimentos']),f"|{numero(bal['FLU - Investimentos'])}| = {numero(abs(bal['FLU - Investimentos']))}")
        metric('4.3 Dividendos','0,35 × max(LL, 0)',s.Dividendos,f"0,35 × {numero(max(s['Lucro Líquido'],0))} = {numero(s.Dividendos)}")
        metric('4.4 Lucro retido','max(LL, 0) − Dividendos',s.Retido,f"{numero(max(s['Lucro Líquido'],0))} − {numero(s.Dividendos)} = {numero(s.Retido)}")
        metric('4.5 EVA','EVA = NOPAT − Capital Investido × WACC',s.EVA,f"{numero(s.NOPAT)} − {numero(s['Capital Investido'])} × {s.WACC} = {numero(s.EVA)}")
    text('Capital investido, NOPAT, ROIC e EVA preservam as regras de build_financial_statement. Retenção é política hipotética; não comprova reinvestimento efetivo.')
    table(['ANO','ROIC','EVA'],[[int(r.ano_num),numero(r.ROIC,True),numero(r.EVA)] for _,r in fs.iterrows()])
    output=BytesIO()
    def footer(canvas, document):
        canvas.setFont(font,7);canvas.drawString(41,23,'CTI • Memorial dinâmico • '+issued);canvas.drawRightString(554,23,str(document.page))
    SimpleDocTemplate(output,pagesize=A4,leftMargin=41,rightMargin=41,topMargin=35,bottomMargin=38,title='Memorial de cálculo CTI').build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()
