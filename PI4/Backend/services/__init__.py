"""Servicos de aplicacao do backend CTI."""

from .dashboard_pipeline import build_context_metrics, prepare_dashboard_data

__all__ = ["build_context_metrics", "prepare_dashboard_data"]

