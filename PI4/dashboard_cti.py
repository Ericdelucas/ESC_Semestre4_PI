"""
Compatibilidade: mantém `streamlit run dashboard_cti.py` / `python dashboard_cti.py`.

A lógica vive em `app.py` + `src/`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VENV_PY = BASE / ".venv" / "bin" / "python"


def _usar_venv_se_preciso() -> None:
    if not VENV_PY.exists():
        return
    if Path(sys.prefix).resolve() == (BASE / ".venv").resolve():
        return
    try:
        import numpy  # noqa: F401
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        os.execv(str(VENV_PY), [str(VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]])


_usar_venv_se_preciso()

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    from streamlit.web import cli as stcli
except ModuleNotFoundError as exc:
    print(
        "Dependências não encontradas. No diretório PI4:\n"
        f"  py -m pip install -r requirements_dashboard.txt\n"
        f"Detalhe: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _assegurar_streamlit() -> None:
    if get_script_run_ctx() is not None:
        return
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    raise SystemExit(stcli.main())


_assegurar_streamlit()

# Delega ao app modular (roteamento + views).
import app  # noqa: E402,F401
