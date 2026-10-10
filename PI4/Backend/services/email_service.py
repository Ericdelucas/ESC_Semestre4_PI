"""Disparo de e-mails SMTP com diagnostico por fase (TCP, TLS, auth, envio)."""

from __future__ import annotations

import html
import logging
import os
import re
import smtplib
import socket
import ssl
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("cti.email")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SMTP_NAO_CONFIGURADO = "Preencha SMTP_USER e SMTP_PASSWORD no .env"
_PLACEHOLDERS = {
    "",
    "changeme",
    "password",
    "senha",
    "sua_senha",
    "smtp_password",
    "smtp_user",
    "your-email@gmail.com",
    "seu_email@gmail.com",
    "<smtp_user>",
    "<smtp_password>",
    "xxxxxxxx",
    "abcdefghijklmnop",
    "abcd efgh ijkl mnop",
}
SENHA_EXEMPLO_GMAIL = (
    "O Gmail recusou a senha (535 BadCredentials). "
    "O valor atual de SMTP_PASSWORD e o exemplo de documentacao (abcd efgh ijkl mnop), "
    "nao uma senha de aplicativo real. Gere uma em "
    "https://myaccount.google.com/apppasswords (conta com verificacao em 2 etapas) "
    "e cole as 16 letras no Backend/.env. Reinicie o uvicorn depois."
)


def _credencial(valor: str) -> str:
    return re.sub(r"\s+", "", (valor or "").strip())


def _senha_e_exemplo(senha: str) -> bool:
    limpa = _credencial(senha).lower()
    original = (senha or "").strip().lower()
    return limpa in _PLACEHOLDERS or original in _PLACEHOLDERS


def smtp_configurado() -> bool:
    usuario = _credencial(os.environ.get("SMTP_USER", ""))
    senha = os.environ.get("SMTP_PASSWORD", "")
    if not usuario or not _credencial(senha):
        return False
    if usuario.lower() in _PLACEHOLDERS or _senha_e_exemplo(senha):
        return False
    return True


def _remetente() -> str:
    return (os.environ.get("EMAIL_REMETENTE") or os.environ.get("SMTP_USER") or "").strip()


def validar_email(endereco: str) -> str:
    email = (endereco or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Informe um e-mail valido.")
    return email


def _porta_smtp() -> int:
    bruto = (os.environ.get("SMTP_PORT") or "587").strip()
    try:
        porta = int(bruto)
    except ValueError as exc:
        raise ValueError(f"SMTP_PORT invalida no .env: {bruto!r}") from exc
    if porta <= 0 or porta > 65535:
        raise ValueError(f"SMTP_PORT fora da faixa valida: {porta}")
    return porta


def _modo_smtp(porta: int) -> str:
    """465 = SSL direto; 587 (e demais) = STARTTLS. SMTP_MODE no .env sobrepoe."""
    forcado = (os.environ.get("SMTP_MODE") or "").strip().lower()
    if forcado in {"ssl", "smtps"}:
        return "ssl"
    if forcado in {"starttls", "tls"}:
        return "starttls"
    if porta == 465:
        return "ssl"
    return "starttls"


def _timeout() -> float:
    try:
        return max(5.0, float(os.environ.get("SMTP_TIMEOUT", "20") or 20))
    except ValueError:
        return 20.0


def _montar_mensagem(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    copias: list[str] | None = None,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = _remetente()
    msg["To"] = destinatario
    if copias:
        msg["Cc"] = ", ".join(copias)
    texto = re.sub(r"<[^>]+>", " ", corpo_html)
    texto = re.sub(r"\s+", " ", texto).strip()
    msg.attach(MIMEText(texto, "plain", "utf-8"))
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))
    return msg


def _falha(fase: str, codigo: str, exc: BaseException, *, servidor: str, porta: int, modo: str) -> dict[str, object]:
    extra = ""
    if isinstance(exc, smtplib.SMTPResponseException):
        extra = f" codigo_smtp={exc.smtp_code} resposta={exc.smtp_error!r}"
    detalhe = (
        f"Erro na fase de {fase}. "
        f"Servidor={servidor}:{porta} modo={modo}.{extra} "
        f"Excecao={type(exc).__name__}: {exc}"
    )
    logger.error("SMTP falhou na fase [%s] %s:%s (%s)", fase, servidor, porta, modo)
    logger.exception(detalhe)
    traceback.print_exc()
    return {
        "success": False,
        "message": codigo,
        "phase": fase,
        "detail": detalhe,
        "server": servidor,
        "port": porta,
        "mode": modo,
        "exception": type(exc).__name__,
    }


def enviar_alerta_email(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    copias: list[str] | None = None,
) -> dict[str, object]:
    """Envia HTML via SMTP, adaptando SSL (465) ou STARTTLS (587) a porta do .env."""
    try:
        destino = validar_email(destinatario)
    except ValueError as exc:
        return {"success": False, "message": "INVALID_EMAIL", "detail": str(exc), "phase": "validacao do destinatario"}
    senha_bruta = os.environ.get("SMTP_PASSWORD", "")
    if _senha_e_exemplo(senha_bruta):
        return {
            "success": False,
            "message": "SMTP_AUTH_FAILED",
            "detail": SENHA_EXEMPLO_GMAIL,
            "phase": "validacao das credenciais .env",
        }
    if not smtp_configurado():
        return {
            "success": False,
            "message": "SMTP_NOT_CONFIGURED",
            "detail": SMTP_NAO_CONFIGURADO,
            "phase": "validacao das credenciais .env",
        }
    remetente = _remetente()
    if not remetente:
        return {
            "success": False,
            "message": "SMTP_NOT_CONFIGURED",
            "detail": SMTP_NAO_CONFIGURADO,
            "phase": "validacao do remetente",
        }
    servidor = os.environ.get("SMTP_SERVER", "smtp.gmail.com").strip() or "smtp.gmail.com"
    try:
        porta = _porta_smtp()
    except ValueError as exc:
        return {"success": False, "message": "SMTP_PORT_INVALID", "detail": str(exc), "phase": "leitura da porta SMTP"}
    modo = _modo_smtp(porta)
    timeout = _timeout()
    usuario = _credencial(os.environ.get("SMTP_USER", ""))
    senha = _credencial(os.environ.get("SMTP_PASSWORD", ""))
    contexto = ssl.create_default_context()
    copias_ok: list[str] = []
    for copia in copias or []:
        try:
            extra = validar_email(copia)
        except ValueError:
            continue
        if extra != destino and extra not in copias_ok:
            copias_ok.append(extra)
    mensagem = _montar_mensagem(destino, assunto, corpo_html, copias_ok)
    smtp: smtplib.SMTP | None = None
    fase = "conexão TCP/Socket"
    logger.info("SMTP inicio destino=%s servidor=%s porta=%s modo=%s timeout=%s", destino, servidor, porta, modo, timeout)
    try:
        if modo == "ssl":
            logger.info("SMTP a abrir SMTP_SSL (SSL direto) em %s:%s", servidor, porta)
            smtp = smtplib.SMTP_SSL(servidor, porta, timeout=timeout, context=contexto)
        else:
            logger.info("SMTP a abrir SMTP + STARTTLS em %s:%s", servidor, porta)
            smtp = smtplib.SMTP(servidor, porta, timeout=timeout)
            smtp.set_debuglevel(1)
            fase = "negociação TLS/SSL (STARTTLS)"
            smtp.ehlo()
            smtp.starttls(context=contexto)
            smtp.ehlo()
        smtp.set_debuglevel(1)
        fase = "autenticação de utilizador/palavra-passe"
        try:
            smtp.login(usuario, senha)
        except smtplib.SMTPAuthenticationError as exc:
            detalhe = SENHA_EXEMPLO_GMAIL if _senha_e_exemplo(os.environ.get("SMTP_PASSWORD", "")) else (
                "O Gmail recusou utilizador/palavra-passe (535). "
                "Use uma senha de aplicativo de 16 letras, nao a senha da conta. "
                f"Resposta do servidor: {exc.smtp_code} {exc.smtp_error!r}"
            )
            logger.exception("SMTP autenticacao recusada")
            return {
                "success": False,
                "message": "SMTP_AUTH_FAILED",
                "phase": fase,
                "detail": detalhe,
                "server": servidor,
                "port": porta,
                "mode": modo,
                "exception": type(exc).__name__,
            }
        except smtplib.SMTPServerDisconnected as exc:
            return {
                "success": False,
                "message": "SMTP_AUTH_FAILED",
                "phase": fase,
                "detail": (
                    "O Gmail fechou a ligacao apos recusar a senha (535 BadCredentials). "
                    "SMTP_PASSWORD precisa ser uma senha de aplicativo real "
                    "(https://myaccount.google.com/apppasswords), nao o exemplo abcd efgh ijkl mnop "
                    "nem a senha normal da conta Google. "
                    f"Excecao={type(exc).__name__}: {exc}"
                ),
                "server": servidor,
                "port": porta,
                "mode": modo,
                "exception": type(exc).__name__,
            }
        fase = "envio da mensagem"
        recusados = smtp.sendmail(remetente, [destino, *copias_ok], mensagem.as_string())
        if recusados:
            raise smtplib.SMTPRecipientsRefused(recusados)
        fase = "encerramento da sessão"
        smtp.quit()
        smtp = None
    except smtplib.SMTPAuthenticationError as exc:
        return _falha("autenticação de utilizador/palavra-passe", "SMTP_AUTH_FAILED", exc, servidor=servidor, porta=porta, modo=modo)
    except smtplib.SMTPServerDisconnected as exc:
        return _falha(
            fase,
            "SMTP_DISCONNECTED",
            exc,
            servidor=servidor,
            porta=porta,
            modo=modo,
        )
    except (TimeoutError, socket.timeout, smtplib.SMTPConnectError) as exc:
        return _falha("conexão TCP/Socket", "SMTP_CONNECT_TIMEOUT", exc, servidor=servidor, porta=porta, modo=modo)
    except ssl.SSLError as exc:
        return _falha("negociação TLS/SSL (certificado ou handshake)", "SMTP_TLS_FAILED", exc, servidor=servidor, porta=porta, modo=modo)
    except smtplib.SMTPRecipientsRefused as exc:
        return _falha("envio da mensagem", "SMTP_RECIPIENT_REFUSED", exc, servidor=servidor, porta=porta, modo=modo)
    except smtplib.SMTPResponseException as exc:
        return _falha(fase, "SMTP_PROTOCOL", exc, servidor=servidor, porta=porta, modo=modo)
    except OSError as exc:
        return _falha("conexão TCP/Socket", "SMTP_SOCKET", exc, servidor=servidor, porta=porta, modo=modo)
    except smtplib.SMTPException as exc:
        return _falha(fase, "SMTP_PROTOCOL", exc, servidor=servidor, porta=porta, modo=modo)
    finally:
        if smtp is not None:
            try:
                smtp.close()
            except Exception:  # noqa: BLE001
                logger.debug("SMTP close ignorado apos falha", exc_info=True)
    logger.info("SMTP enviado com sucesso para %s via %s:%s (%s)", destino, servidor, porta, modo)
    return {
        "success": True,
        "message": "SENT",
        "detail": f"E-mail enviado para {destino} via {servidor}:{porta} ({modo}).",
        "phase": "envio da mensagem",
        "server": servidor,
        "port": porta,
        "mode": modo,
    }


def html_teste_smtp() -> str:
    return """
<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;border:1px solid #d7c39a;border-radius:12px;overflow:hidden">
  <div style="background:#1F4E45;color:#F7F1E3;padding:18px 22px">
    <div style="font-size:12px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.8">Grupo ESC</div>
    <h1 style="margin:6px 0 0 0;font-size:22px">Teste de Conectividade SMTP</h1>
  </div>
  <div style="padding:22px;background:#F7F1E3;color:#1F4E45">
    <p style="margin:0 0 12px 0">Selo: <strong>Grupo ESC - Teste de Conectividade SMTP</strong>.</p>
    <p style="margin:0 0 12px 0">O canal de alertas do Dashboard CTI respondeu com sucesso. Este e-mail nao e um alerta de risco.</p>
    <p style="margin:0;font-size:13px;opacity:0.8">Se voce nao solicitou este teste, ignore a mensagem.</p>
  </div>
</div>
"""


def html_alerta_risco(resumo: str, itens: list[str]) -> str:
    return html_alerta_consolidado(resumo, [], itens)


def _esc(valor: object) -> str:
    return html.escape("" if valor is None else str(valor), quote=True)


def _estado_geral(checks: list[dict[str, object]]) -> str:
    modelo = [str(item.get("status") or "") for item in checks if item.get("id") != "simulacao"]
    if "critico" in modelo:
        return "critico"
    extras = [str(item.get("status") or "") for item in checks]
    if "atencao" in extras or "critico" in extras:
        return "atencao"
    return "conforme"


def _badge_status(status: str) -> str:
    mapa = {
        "critico": ("CRÍTICO", "#8C2F2F", "#F8EAEA"),
        "atencao": ("ATENÇÃO", "#8A6A1F", "#F8F1D8"),
        "conforme": ("CONFORME", "#1F4E45", "#E8F0EC"),
    }
    rotulo, cor, fundo = mapa.get(status, mapa["conforme"])
    return (
        "<table role='presentation' cellpadding='0' cellspacing='0' style='display:inline-table'>"
        "<tr>"
        f"<td style='padding:4px 11px;background:{fundo};color:{cor};font-size:10px;"
        f"font-weight:700;letter-spacing:0.08em;border:1px solid {cor}'>{rotulo}</td>"
        "</tr></table>"
    )


def _barra_proximidade(proximidade: int, status: str) -> str:
    cor = {"critico": "#8C2F2F", "atencao": "#C4A15A", "conforme": "#1F4E45"}.get(status, "#1F4E45")
    largura = max(0, min(100, int(proximidade)))
    resto = 100 - largura
    return (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='background:#E8EEEA'>"
        "<tr>"
        f"<td width='{largura}%' style='height:8px;background:{cor};font-size:0;line-height:0'>&nbsp;</td>"
        f"<td width='{resto}%' style='height:8px;font-size:0;line-height:0'>&nbsp;</td>"
        "</tr></table>"
        f"<p style='margin:5px 0 0 0;font-size:11px;color:#5B6B66'>"
        f"Proximidade do limiar de risco:&nbsp;{largura}%</p>"
    )


def _cartao_metrica(item: dict[str, object]) -> str:
    status = str(item.get("status") or ("critico" if item.get("critical") else "conforme"))
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 14px 0;background:#ffffff;border:1px solid #D9E0DC">
  <tr>
    <td style="width:4px;background:{'#8C2F2F' if status == 'critico' else '#C4A15A' if status == 'atencao' else '#1F4E45'};font-size:0;line-height:0">&nbsp;</td>
    <td style="padding:16px 18px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-size:15px;font-weight:700;color:#1F4E45">{_esc(item.get("label"))}</td>
          <td align="right">{_badge_status(status)}</td>
        </tr>
      </table>
      <p style="margin:10px 0 0 0;font-size:22px;font-weight:800;color:#14352F">{_esc(item.get("value"))}</p>
      <p style="margin:2px 0 10px 0;font-size:12px;color:#5B6B66">Limiar de alerta:&nbsp;{_esc(item.get("threshold"))}</p>
      {_barra_proximidade(int(item.get("proximity") or 0), status)}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;font-size:12px;color:#2C3A37;line-height:1.5">
        <tr>
          <td style="padding:8px 0 6px 0;border-top:1px solid #EEF2F0">
            <strong>Localização exata no Dashboard:</strong><br>{_esc(item.get("location") or "—")}
          </td>
        </tr>
        <tr>
          <td style="padding:6px 0;border-top:1px solid #EEF2F0">
            <strong>Fórmula / lógica de cálculo:</strong><br>{_esc(item.get("formula") or item.get("note") or "—")}
          </td>
        </tr>
        <tr>
          <td style="padding:6px 0 0 0;border-top:1px solid #EEF2F0">
            <strong>Limiar crítico de alerta:</strong><br>{_esc(item.get("threshold_text") or item.get("threshold") or "—")}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""


def html_alerta_consolidado(
    resumo: str,
    checks: list[dict[str, object]],
    notas: list[str] | None = None,
) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    n_cenarios = next((item.get("value") for item in checks if item.get("id") == "n_cenarios"), "—")
    estado = _estado_geral(checks)
    rotulo_geral = {"critico": "Crítico", "atencao": "Atenção", "conforme": "Conforme"}.get(estado, "Conforme")
    linhas_resumo = []
    for item in checks:
        status = str(item.get("status") or ("critico" if item.get("critical") else "conforme"))
        linhas_resumo.append(
            "<tr>"
            f"<td style='padding:9px 10px;border-bottom:1px solid #E6EDE9;color:#1F4E45'>{_esc(item.get('label'))}</td>"
            f"<td style='padding:9px 10px;border-bottom:1px solid #E6EDE9;text-align:right;font-weight:700'>{_esc(item.get('value'))}</td>"
            f"<td style='padding:9px 10px;border-bottom:1px solid #E6EDE9;text-align:right;color:#5B6B66'>{_esc(item.get('threshold'))}</td>"
            f"<td style='padding:9px 10px;border-bottom:1px solid #E6EDE9'>{_badge_status(status)}</td>"
            "</tr>"
        )
    tabela = "".join(linhas_resumo) or (
        "<tr><td colspan='4' style='padding:12px'>Nenhuma métrica avaliada.</td></tr>"
    )
    cartoes = "".join(_cartao_metrica(item) for item in checks)
    notas_html = ""
    if notas:
        itens = "".join(f"<li style='margin:0 0 4px 0'>{_esc(nota)}</li>" for nota in notas if nota)
        if itens:
            notas_html = (
                "<p style='margin:14px 0 6px 0;font-size:11px;letter-spacing:0.12em;"
                "text-transform:uppercase;color:#C4A15A;font-weight:700'>Notas da varredura</p>"
                f"<ul style='margin:0 0 0 18px;padding:0;font-size:12px;color:#5B6B66'>{itens}</ul>"
            )
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F1EA;padding:24px 0">
  <tr>
    <td align="center">
      <table role="presentation" width="680" cellpadding="0" cellspacing="0" style="width:680px;max-width:680px;background:#ffffff;border:1px solid #D7C39A;font-family:Arial,Helvetica,sans-serif;color:#1F4E45">
        <tr>
          <td style="height:6px;background:#C4A15A;font-size:0;line-height:0">&nbsp;</td>
        </tr>
        <tr>
          <td style="padding:22px 28px 18px 28px;background:#1F4E45;color:#F7F1E3">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="58" valign="middle">
                  <table role="presentation" cellpadding="0" cellspacing="0">
                    <tr>
                      <td width="48" height="48" align="center" valign="middle" style="width:48px;height:48px;background:#C4A15A;color:#1F4E45;font-weight:800;letter-spacing:0.06em;font-size:14px">ESC</td>
                    </tr>
                  </table>
                </td>
                <td valign="middle" style="padding-left:12px">
                  <div style="font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:#E8C07A">Grupo&nbsp;ESC&nbsp;—&nbsp;Dashboard&nbsp;CTI</div>
                  <div style="font-size:24px;font-weight:800;margin-top:4px;line-height:1.25">Relatório&nbsp;executivo&nbsp;de&nbsp;risco</div>
                </td>
                <td align="right" valign="middle">{_badge_status(estado)}</td>
              </tr>
            </table>
            <p style="margin:14px 0 0 0;font-size:12px;color:#D7E3DE">Confidencial&nbsp;·&nbsp;uso&nbsp;interno&nbsp;·&nbsp;Gerado&nbsp;em&nbsp;{agora}&nbsp;·&nbsp;Universo:&nbsp;{_esc(n_cenarios)}&nbsp;cenários&nbsp;de&nbsp;Monte&nbsp;Carlo&nbsp;·&nbsp;Horizonte:&nbsp;12&nbsp;anos&nbsp;·&nbsp;Estado&nbsp;geral:&nbsp;{_esc(rotulo_geral)}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:22px 28px 8px 28px">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F1E3;border-left:4px solid #C4A15A">
              <tr>
                <td style="padding:16px 18px">
                  <div style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#8A6A1F;font-weight:700">Sumário&nbsp;executivo</div>
                  <p style="margin:8px 0 0 0;font-size:14px;line-height:1.65;color:#2C3A37">{_esc(resumo)}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 8px 28px">
            <div style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#C4A15A;font-weight:700;margin-bottom:8px">Visão&nbsp;consolidada</div>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #D9E0DC;font-size:13px">
              <tr style="background:#1F4E45;color:#F7F1E3">
                <th align="left" style="padding:10px">Métrica</th>
                <th align="right" style="padding:10px">Valor</th>
                <th align="right" style="padding:10px">Limiar</th>
                <th align="left" style="padding:10px">Estado</th>
              </tr>
              {tabela}
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:18px 28px 8px 28px">
            <div style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#C4A15A;font-weight:700;margin-bottom:10px">Detalhamento&nbsp;técnico&nbsp;e&nbsp;localização&nbsp;no&nbsp;Dashboard</div>
            {cartoes}
            {notas_html}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 28px 24px 28px;border-top:1px solid #E6EDE9">
            <p style="margin:16px 0 0 0;font-size:11px;line-height:1.6;color:#5B6B66">
              Este é um relatório gerado automaticamente pelo motor de risco CTI do Grupo ESC. Não responda a este e-mail.
              Para auditoria detalhada, aceda ao painel administrativo do Dashboard CTI (visão do stakeholder, Distribuição&nbsp;&amp;&nbsp;Probabilidades e Solvência&nbsp;&amp;&nbsp;Liquidez Geral).
              A decisão de investimento ou de reequilíbrio contratual deve cruzar este digest com a base Cti.csv e os logs de acesso.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""
