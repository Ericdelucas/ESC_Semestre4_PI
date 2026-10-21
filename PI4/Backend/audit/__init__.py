"""Auditoria, validacao e reconciliacao de bases CTI."""
# isso serve para evitar importacoes circulares, pois o runner importa o config
from .runner import run_audit
# e para evitar que o runner importe o config antes de ser importado, o que causaria erro de importacao circular
__all__ = ["run_audit"]

