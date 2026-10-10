"""Cria tabelas e insere os usuarios padrao de teste."""

from __future__ import annotations

import sys
from pathlib import Path

_PI4 = Path(__file__).resolve().parents[2]
if str(_PI4) not in sys.path:
    sys.path.insert(0, str(_PI4))

from Backend.db import seed_usuarios


if __name__ == "__main__":
    seed_usuarios()
    print("Usuarios padrao sincronizados.")
