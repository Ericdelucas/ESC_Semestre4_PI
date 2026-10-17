"""Relatório PDF da varredura real, sem disparo SMTP nem alteração de métricas."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPORTS_DIR = Path(__file__).resolve().parents[1] / "relatorios"
STATUS = {"conforme": "Favorável / conforme", "atencao": "Atenção", "critico": "Crítico"}


def gerar_relatorio_riscos(varredura: dict) -> bytes:
    """Usa o snapshot recebido, inclusive seus limiares; não refaz a varredura."""
    checks = [c for c in varredura.get("checks", []) if c.get("id") != "simulacao"]
    metrics = varredura.get("metrics") or {}
    if not checks or not metrics.get("n_cenarios"):
        raise ValueError("Varredura sem cenários ou indicadores para gerar relatório.")
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    def p(text):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles["BodyText"])
    story = []
    def heading(text): story.append(Paragraph(text, styles["Heading2"]))
    def text(value): story.append(p(value)); story.append(Spacer(1, 7))
    def table(headers, rows, widths):
        data = [[p(c) for c in row] for row in [headers] + rows]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#DCE8F5')),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F6FA')]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor('#CBD5E1')),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(t)
    story.append(Paragraph("CTI — Relatório de riscos financeiros", styles["Title"]))
    text("Emitido em " + datetime.now(ZoneInfo("America/Araguaina")).strftime("%d/%m/%Y às %H:%M:%S") + " (America/Araguaina).")
    text(f"Base: Cti.csv / ranking.parquet; universo consolidado: {metrics['n_cenarios']} cenários; horizonte de 12 anos. A varredura utiliza o snapshot do pipeline, sem aplicar os filtros de cenário/ano da tela.")
    heading("1. Diagnóstico atual")
    critical = [c for c in checks if c.get("status") == "critico"]
    attention = [c for c in checks if c.get("status") == "atencao"]
    diagnosis = "Crítico: há indicadores fora dos limites do modelo." if critical else "Atenção: há indicadores próximos dos limites do modelo." if attention else "Favorável: os indicadores avaliados estão dentro dos limites do modelo."
    text(diagnosis)
    table(["INDICADOR", "RESULTADO", "ESTADO"], [[c['label'], c['value'], STATUS.get(c.get('status'), str(c.get('status')))] for c in checks], [235, 105, 175])
    text("Os termos favorável/conforme descrevem as regras do CTI; não constituem uma nota universal de desempenho nem garantia de solvência. Médias favoráveis podem coexistir com cenários individuais ruins.")
    if 'n_ruina' in metrics:
        text(f"Cenários com caixa negativo no Ano 12: {metrics['n_ruina']} de {metrics['n_cenarios']}. Cenários com liquidez abaixo do limite: {metrics.get('share_liquidez_baixa', 'não informado')}%.")
    heading("2. Quando os indicadores estão favoráveis ou ruins")
    ruin = metrics.get('limiar_ruina', 15)
    liq = metrics.get('limiar_liquidez', 1.0)
    table(["INDICADOR", "FAVORÁVEL", "ATENÇÃO / CRÍTICO"], [
        ["Probabilidade de caixa negativo", f"Até 5%, respeitado o limite crítico configurado de {ruin}%.", f"Acima de 5%: atenção, se não crítico. Acima de {ruin}%: crítico."],
        ["P5 do caixa final", "Positivo: cauda pessimista com caixa acima de zero.", "Negativo: crítico. Exatamente zero: conforme no código, sem folga de caixa."],
        ["Liquidez média", f"Pelo menos {1.2*liq:g}x (120% do mínimo configurado).", f"De {liq:g}x até abaixo de {1.2*liq:g}x: atenção. Abaixo de {liq:g}x: crítico."],
        ["Selo de caixa insuficiente", f"Até 5%, respeitado o limite crítico de {ruin}%.", f"Acima de 5%: atenção, se não crítico. Acima de {ruin}%: crítico."],
        ["Quantidade de cenários", "Informativa; confirma o universo avaliado.", "Não é gatilho de qualidade financeira."],
    ], [135, 175, 205])
    text("As faixas acima são referências de interpretação das regras implementadas, não resultados de cenários adversos inventados. O selo e a probabilidade de caixa negativo descrevem o mesmo risco sob classificações relacionadas; não são evidências independentes.")
    heading("3. Leitura e ações recomendadas")
    if critical:
        text("Revisar os indicadores críticos antes de decisões de CAPEX e distribuição. Examinar os cenários com caixa negativo, as fontes de financiamento e a evolução anual da liquidez.")
    elif attention:
        text("Acompanhar os indicadores em atenção, testar a sensibilidade de caixa e liquidez e preservar folga financeira antes de novos compromissos.")
    else:
        text("Manter o monitoramento. Investigar as trajetórias com caixa insuficiente e a parcela com baixa liquidez, mesmo quando a média e o P5 do conjunto são favoráveis.")
    text("Esta análise cobre caixa final, cauda P5, liquidez média e selo de caixa insuficiente; não certifica todos os riscos financeiros do projeto.")
    heading("4. Fórmulas, limites e rastreabilidade")
    for c in checks:
        text(c['label'] + ': ' + str(c.get('formula', '')) + '\nLimiar: ' + str(c.get('threshold', '')) + '\nObservação: ' + str(c.get('note', '')))
    text("Fontes: Backend/services/risk_alerts.py e Backend/metrics/financial_kpis.py. Percentuais e valores da tabela são os exibidos pela varredura, com seu arredondamento de apresentação.")
    if varredura.get('simulated'):
        text("A origem inclui uma simulação de envio. O selo artificial de validação foi excluído deste diagnóstico; os indicadores financeiros permanecem reais.")
    text("A geração deste PDF não envia e-mail. O alerta por SMTP segue as regras próprias de criticidade e intervalo entre envios.")
    output = BytesIO()
    SimpleDocTemplate(output, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36, title="CTI — Riscos financeiros").build(story)
    return output.getvalue()


def salvar_relatorio_riscos(varredura: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "Relatorio_Riscos_Financeiros_CTI.pdf"
    path.write_bytes(gerar_relatorio_riscos(varredura))
    return path
