"""Varredura de cauda de risco e disparo de um unico e-mail consolidado."""

from __future__ import annotations

import os
import time
from datetime import date
from functools import lru_cache

import pandas as pd

from Backend.metrics import probabilidade_caixa_negativo
from Backend.services.dashboard_pipeline import CSV_PATH, prepare_dashboard_data
from Backend.services.email_service import enviar_alerta_email, html_alerta_consolidado

SELO_RUINA = "Encerramento com Caixa Insuficiente"
FUNCOES_EXECUTIVAS = {"CEO", "CFO"}
_LOGIN_ENVIADO: set[str] = set()
_ULTIMO_DIGEST: dict[str, float] = {}


def limiar_ruina() -> float:
    try:
        return float(os.environ.get("RISK_RUIN_THRESHOLD", "15") or 15)
    except ValueError:
        return 15.0


def forcar_alerta_login() -> bool:
    return os.environ.get("FORCE_EMAIL_ALERT_ON_LOGIN", "").strip().lower() in {"1", "true", "yes", "sim"}


def limiar_liquidez() -> float:
    try:
        return float(os.environ.get("RISK_LIQUIDEZ_MIN", "1.0") or 1.0)
    except ValueError:
        return 1.0


def _debounce_segundos(origem: str) -> float:
    padrao = "900" if origem == "login" else "45"
    chave = "ALERT_DEBOUNCE_LOGIN_SECONDS" if origem == "login" else "ALERT_DEBOUNCE_MANUAL_SECONDS"
    try:
        return max(1.0, float(os.environ.get(chave, padrao) or padrao))
    except ValueError:
        return float(padrao)


@lru_cache(maxsize=1)
def _ranking_cache(mtime: float) -> pd.DataFrame:
    _ = mtime
    _df, _ind, ranking = prepare_dashboard_data(CSV_PATH)
    return ranking


def _ranking() -> pd.DataFrame:
    caminho = CSV_PATH
    mtime = caminho.stat().st_mtime if caminho.exists() else 0.0
    cache = CSV_PATH.parent / "cache" / "ranking.parquet"
    if cache.exists():
        mtime = max(mtime, cache.stat().st_mtime)
    return _ranking_cache(mtime)


def _check(
    ident: str,
    label: str,
    valor: str,
    limiar: str,
    critico: bool,
    nota: str,
    *,
    location: str,
    formula: str,
    threshold_text: str,
    status: str,
    proximity: int,
) -> dict[str, object]:
    return {
        "id": ident,
        "label": label,
        "value": valor,
        "threshold": limiar,
        "critical": critico,
        "note": nota,
        "location": location,
        "formula": formula,
        "threshold_text": threshold_text,
        "status": status,
        "proximity": max(0, min(100, int(proximity))),
    }


def _status_ruina(valor: float, limiar: float) -> str:
    if valor > limiar:
        return "critico"
    if valor > 5:
        return "atencao"
    return "conforme"


def _proximidade(numerador: float, denominador: float) -> int:
    if denominador <= 0:
        return 0
    return max(0, min(100, int(round((numerador / denominador) * 100))))


def _fmt_int(valor: float | int) -> str:
    return f"{int(round(float(valor))):,}".replace(",", ".")


def _sumario_executivo(checks: list[dict[str, object]], metricas: dict[str, object], simulado: bool) -> str:
    n = int(metricas.get("n_cenarios") or 0)
    p_ruina = float(metricas.get("p_ruina") or 0)
    n_ruina = int(metricas.get("n_ruina") or 0)
    p5 = float(metricas.get("p5_caixa_ano12") or 0)
    liq = float(metricas.get("liquidez_media") or 0)
    limiar = float(metricas.get("limiar_ruina") or 15)
    criticos = [c for c in checks if c.get("status") == "critico" and c.get("id") != "simulacao"]
    atencao = [c for c in checks if c.get("status") == "atencao" and c.get("id") != "simulacao"]
    p5_txt = f"R$ {_fmt_int(p5)}"
    base = (
        f"O motor CTI reavaliou {_fmt_int(n)} cenários de Monte Carlo no horizonte de 12 anos. "
        f"A probabilidade de caixa negativo no Ano 12 é {p_ruina:.2f}% ({_fmt_int(n_ruina)} trajetória(s)). "
        f"O percentil P5 do caixa de encerramento está em {p5_txt} e a liquidez média em {liq:.2f}x."
    )
    if criticos:
        nomes = ", ".join(str(c.get("label")) for c in criticos)
        leitura = (
            f" Solvência sob pressão: {len(criticos)} métrica(s) acima do limiar de governança ({nomes}). "
            f"O limiar oficial de ruína do modelo é {limiar:.0f}%."
        )
    elif atencao:
        leitura = (
            f" Solvência preservada, com {len(atencao)} ponto(s) em atenção. "
            f"Nenhuma métrica ultrapassou o limiar crítico de {limiar:.0f}%."
        )
    else:
        leitura = (
            f" Solvência do conjunto está dentro dos limiares: ruína bem abaixo de {limiar:.0f}%, "
            "P5 positivo e liquidez acima de 1,0x."
        )
    extra = " Este envio inclui o selo de validação de canal (simulação) e não altera os números do modelo." if simulado else ""
    return base + leitura + extra


def varrer_riscos() -> dict[str, object]:
    """Avalia todas as metricas primeiro e devolve um payload unico."""
    ranking = _ranking()
    caixa = pd.to_numeric(ranking.get("caixa_ano12"), errors="coerce") if not ranking.empty else pd.Series(dtype=float)
    liquidez = pd.to_numeric(ranking.get("liquidez"), errors="coerce") if not ranking.empty else pd.Series(dtype=float)
    p_ruina = probabilidade_caixa_negativo(ranking)
    p5 = float(caixa.quantile(0.05)) if not caixa.empty else 0.0
    n_cenarios = int(ranking["CENA"].nunique()) if "CENA" in ranking.columns and not ranking.empty else 0
    n_ruina = int((caixa < 0).sum()) if not caixa.empty else 0
    liq_media = float(liquidez.mean()) if not liquidez.empty else 0.0
    share_liq_baixa = float((liquidez < limiar_liquidez()).mean() * 100) if not liquidez.empty else 0.0
    share_selo = 0.0
    if "selo" in ranking.columns and not ranking.empty:
        share_selo = float((ranking["selo"].astype(str) == SELO_RUINA).mean() * 100)

    ruina_limiar = limiar_ruina()
    liq_limiar = limiar_liquidez()
    st_ruina = _status_ruina(p_ruina, ruina_limiar)
    st_p5 = "critico" if p5 < 0 else "conforme"
    st_liq = "critico" if liq_media < liq_limiar else ("atencao" if 0 < liq_media < liq_limiar * 1.2 else "conforme")
    st_selo = _status_ruina(share_selo, ruina_limiar)
    prox_liq = _proximidade(liq_limiar, liq_media) if liq_media > 0 else 100
    checks = [
        _check(
            "p_ruina",
            "Probabilidade de caixa negativo (Ano 12)",
            f"{p_ruina:.2f}%",
            f"> {ruina_limiar:.0f}%",
            st_ruina == "critico",
            f"{n_ruina} de {n_cenarios} cenários encerram com caixa negativo.",
            location="Secção: Distribuição & Probabilidades / Card: Probabilidade de caixa negativo no Ano 12",
            formula="média(caixa_ano12 < 0) × 100, com caixa_ano12 = FLU Saldo Final no Ano 12 (fallback BAL Disponível).",
            threshold_text=f"Referencial do modelo: 0%–5% controlada; acima de {ruina_limiar:.0f}% dispara alerta de governança.",
            status=st_ruina,
            proximity=_proximidade(p_ruina, ruina_limiar),
        ),
        _check(
            "p5_caixa",
            "Cauda P5 do caixa de encerramento",
            f"R$ {_fmt_int(p5)}",
            "< 0",
            st_p5 == "critico",
            "P5 negativo indica cauda material de ruína.",
            location="Secção: Distribuição & Probabilidades / Card: P5 (percentis da cauda) e boxplot de caixa final; Faixa de Risco (envelope P5–P95)",
            formula="Percentil 5 (P5) do caixa_ano12 — fluxo de caixa acumulado no Ano 12, incluindo a leitura de reversibilidade dos ativos no ranking.",
            threshold_text="Valor tolerável > 0 para evitar insolvência operacional na cauda pessimista.",
            status=st_p5,
            proximity=100 if p5 < 0 else 0,
        ),
        _check(
            "liquidez",
            "Liquidez média",
            f"{liq_media:.2f}x",
            f"< {liq_limiar:.1f}x",
            st_liq == "critico",
            f"{share_liq_baixa:.1f}% dos cenários abaixo do limiar.",
            location="Secção: Solvência & Liquidez Geral (Poder Concedente) / Card: Liquidez Geral; CFO → Faixa de Risco / liquidez corrente",
            formula="Média entre cenários de |Ativo Circulante| / |Passivo Circulante| (ranking de liquidez).",
            threshold_text=f"Mínimo aceitável {liq_limiar:.1f}x. Abaixo disso há aperto de solvência de curto prazo.",
            status=st_liq,
            proximity=prox_liq,
        ),
        _check(
            "selo_ruina",
            f"Selo «{SELO_RUINA}»",
            f"{share_selo:.2f}%",
            f"> {ruina_limiar:.0f}%",
            st_selo == "critico",
            "Concentração do selo de encerramento com caixa insuficiente.",
            location="Secção: Mapeamento de Risco × Retorno / filtro do selo Encerramento com Caixa Insuficiente",
            formula="percentual de cenários classificados com caixa_ano12 < 0 (selo de ruína tem prioridade sobre os demais).",
            threshold_text=f"Acima de {ruina_limiar:.0f}% da nuvem no selo de ruína exige revisão de CAPEX, payout e caixa.",
            status=st_selo,
            proximity=_proximidade(share_selo, ruina_limiar),
        ),
        _check(
            "n_cenarios",
            "Cenários simulados (Monte Carlo)",
            _fmt_int(n_cenarios),
            "base ativa",
            False,
            "Universo da varredura consolidada.",
            location="Cabeçalho do Dashboard CTI e Secção: Distribuição & Probabilidades",
            formula="contagem distinta de CENA na base Cti.csv após o pipeline de indicadores.",
            threshold_text="Informativo. Confirma o universo da simulação; não é gatilho de alerta.",
            status="conforme",
            proximity=0,
        ),
    ]
    motivos = [str(item["note"]) for item in checks if item["critical"]]
    critico = any(bool(item["critical"]) for item in checks)
    metricas = {
        "n_cenarios": n_cenarios,
        "p_ruina": round(p_ruina, 2),
        "n_ruina": n_ruina,
        "p5_caixa_ano12": p5,
        "liquidez_media": round(liq_media, 4),
        "share_liquidez_baixa": round(share_liq_baixa, 2),
        "share_selo_ruina": round(share_selo, 2),
        "limiar_ruina": ruina_limiar,
    }
    resumo = _sumario_executivo(checks, metricas, False)
    return {
        "critical": critico,
        "summary": resumo,
        "reasons": motivos,
        "checks": checks,
        "metrics": metricas,
    }


def _destinatarios(principal: str) -> tuple[str, list[str]]:
    destino = (principal or "").strip().lower()
    ceo = (os.environ.get("EMAIL_ALERTA_CEO") or "ericdelucass@gmail.com").strip().lower()
    copias = [ceo] if ceo and ceo != destino else []
    return destino, copias


def _chave_digest(destino: str, copias: list[str]) -> str:
    pessoas = ",".join(sorted({destino, *copias}))
    return f"{date.today().isoformat()}|{pessoas}|digest"


def _dentro_debounce(chave: str, segundos: float) -> bool:
    ultimo = _ULTIMO_DIGEST.get(chave)
    return ultimo is not None and (time.time() - ultimo) < segundos


def _marcar_envio(chave: str) -> None:
    _ULTIMO_DIGEST[chave] = time.time()


def _aplicar_simulacao(varredura: dict[str, object]) -> dict[str, object]:
    checks = list(varredura.get("checks") or [])
    checks.append(
        _check(
            "simulacao",
            "Validação de canal (simulação)",
            "ativa",
            "disparo único de teste",
            True,
            "Incluída no mesmo e-mail consolidado; não gera mensagem extra.",
            location="Menu ⋮ do Dashboard → Simular alerta de risco / flag FORCE_EMAIL_ALERT_ON_LOGIN.",
            formula="Não altera os indicadores. Apenas autoriza o envio do digest quando o modelo está abaixo do limiar.",
            threshold_text="Uso de validação. Não é um gatilho de solvência.",
            status="atencao",
            proximity=100,
        )
    )
    varredura["checks"] = checks
    varredura["critical"] = True
    varredura["simulated"] = True
    varredura["summary"] = _sumario_executivo(
        checks,
        varredura.get("metrics") if isinstance(varredura.get("metrics"), dict) else {},
        True,
    )
    varredura["reasons"] = [str(item.get("note") or "") for item in checks if item.get("critical")]
    return varredura


def disparar_alerta_risco(
    destinatario: str,
    *,
    forcar: bool = False,
    simular: bool = False,
    origem: str = "auto",
) -> dict[str, object]:
    """Varre o modelo inteiro e, no fim, envia no maximo um e-mail consolidado."""
    varredura = varrer_riscos()
    if simular:
        varredura = _aplicar_simulacao(varredura)
    destino, copias = _destinatarios(destinatario)
    chave = _chave_digest(destino, copias)
    varredura["skipped"] = None
    if origem == "login" and destino in _LOGIN_ENVIADO:
        varredura["sent"] = False
        varredura["recipients"] = []
        varredura["email_error"] = None
        varredura["skipped"] = "sessao_login"
        return varredura
    if not forcar and _dentro_debounce(chave, _debounce_segundos(origem if origem == "login" else "manual")):
        varredura["sent"] = False
        varredura["recipients"] = []
        varredura["email_error"] = None
        varredura["skipped"] = "debounce"
        return varredura
    if not varredura["critical"]:
        varredura["sent"] = False
        varredura["recipients"] = []
        varredura["email_error"] = None
        return varredura

    corpo = html_alerta_consolidado(
        str(varredura["summary"]),
        list(varredura.get("checks") or []),
        [str(item.get("note") or "") for item in (varredura.get("checks") or []) if item.get("critical")],
    )
    resultado = enviar_alerta_email(
        destino,
        "Grupo ESC · Relatório executivo de risco CTI",
        corpo,
        copias=copias,
    )
    if resultado.get("success"):
        _marcar_envio(chave)
        if origem == "login":
            _LOGIN_ENVIADO.add(destino)
        varredura["sent"] = True
        varredura["recipients"] = [destino, *copias]
        varredura["email_error"] = None
        return varredura
    varredura["sent"] = False
    varredura["recipients"] = []
    varredura["email_error"] = str(resultado.get("detail") or resultado.get("message") or "SMTP_ERROR")
    return varredura
