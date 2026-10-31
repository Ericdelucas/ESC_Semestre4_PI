"""Valida os caminhos de build sem sobrescrever o cache de producao."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]


class PrecomputeEntrypointTests(unittest.TestCase):
    def test_render_commands_from_repository_root_and_pi4(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("scripts/precompute_cache.py", "PI4/scripts/precompute_cache.py"):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / relative, target)
            real_script = root / "PI4/Backend/scripts/precompute_cache.py"
            real_script.parent.mkdir(parents=True)
            real_script.write_text("if __name__ == '__main__':\n    print('PRECOMPUTE_OK')\n")
            for cwd, command in (
                (root, "scripts/precompute_cache.py"),
                (root / "PI4", "scripts/precompute_cache.py"),
                (root / "PI4", "Backend/scripts/precompute_cache.py"),
            ):
                with self.subTest(cwd=cwd, command=command):
                    result = subprocess.run([sys.executable, command], cwd=cwd,
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), "PRECOMPUTE_OK")

    def test_root_entrypoint_uses_actual_backend_script(self):
        import runpy
        from unittest.mock import patch

        module = runpy.run_path(str(REPO / "scripts/precompute_cache.py"))
        with patch("runpy.run_path") as delegate:
            module["main"]()
        delegate.assert_called_once_with(
            str(REPO / "PI4/Backend/scripts/precompute_cache.py"), run_name="__main__"
        )


if __name__ == "__main__":
    unittest.main()
