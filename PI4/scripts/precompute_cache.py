"""Encaminha o precompute do build da Render para o script em Backend."""

from __future__ import annotations

import runpy
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
CANDIDATES = (
    ROOT / "Backend" / "scripts" / "precompute_cache.py",
    ROOT / "PI4" / "Backend" / "scripts" / "precompute_cache.py",
)

for candidate in CANDIDATES:
    if candidate.exists() and candidate.resolve() != HERE:
        runpy.run_path(str(candidate), run_name="__main__")
        break
else:
    raise FileNotFoundError(
        "Script real nao encontrado. Esperado em Backend/scripts/precompute_cache.py"
    )
