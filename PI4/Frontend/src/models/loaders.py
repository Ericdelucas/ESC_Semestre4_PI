"""Compatibilidade: carregamento de dados agora vive no Backend."""

from __future__ import annotations

import sys
from pathlib import Path


PI4_ROOT = Path(__file__).resolve().parents[3]
if str(PI4_ROOT) not in sys.path:
    sys.path.insert(0, str(PI4_ROOT))

from Backend.data_loader import (  # noqa: E402
    load_cti_csv,
    magnitude,
    normalizar_conta,
    otimizar_base_cti,
    parse_valor_br,
    separar_demonstrativos,
    soma_contas,
)

__all__ = [
    "load_cti_csv",
    "magnitude",
    "normalizar_conta",
    "otimizar_base_cti",
    "parse_valor_br",
    "separar_demonstrativos",
    "soma_contas",
]
