"""Compatibilidade publica das sub-abas por persona."""

from .admin_users import render_admin_usuarios
from .audit import render_ceo_auditoria
from .ceo import render_ceo_break_even, render_ceo_dre_operacional, render_ceo_ltv_cac, render_ceo_visao_geral
from .comparison import render_comparar_cenarios
from .concession import render_concedente_ativos, render_concedente_capex, render_concedente_solvencia
from .custom_analysis import render_custom_analysis
from .shareholders import render_acionistas_dividendos, render_acionistas_eva, render_acionistas_retorno

__all__ = [
    "render_admin_usuarios",
    "render_acionistas_dividendos",
    "render_acionistas_eva",
    "render_acionistas_retorno",
    "render_ceo_auditoria",
    "render_ceo_break_even",
    "render_ceo_dre_operacional",
    "render_ceo_ltv_cac",
    "render_ceo_visao_geral",
    "render_comparar_cenarios",
    "render_concedente_ativos",
    "render_concedente_capex",
    "render_concedente_solvencia",
    "render_custom_analysis",
]
