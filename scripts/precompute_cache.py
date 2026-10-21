"""Compatibilidade com builds Render executados na raiz do repositorio."""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "PI4" / "Backend" / "scripts" / "precompute_cache.py"
    if not target.is_file():
        raise FileNotFoundError(f"Script de precompute nao encontrado: {target}")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
