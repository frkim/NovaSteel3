"""Conformance tests binding the Fabric loader notebook
(``fabric/notebooks/ns-load-analytical-gold.Notebook``) to the analytical
generator schema.

No Spark runs locally, so instead of executing the notebook these tests parse
its ``CASTS`` and ``IDEMPOTENCY_KEYS`` dict literals and assert they match the
generator's emitted columns (``EXPECTED_COLUMNS``) and idempotency keys
(``IDEMPOTENCY_KEYS``). This catches any schema drift between what the
simulator writes and what the loader would MERGE, which would otherwise only
surface as a failed load in Fabric.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.analytics import IDEMPOTENCY_KEYS as GEN_IDEMPOTENCY_KEYS
from simulator.validators.gold_contract import EXPECTED_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (REPO_ROOT / "fabric" / "notebooks" / "ns-load-analytical-gold.Notebook"
            / "notebook-content.py")


def _extract_dict_literal(source: str, name: str) -> dict:
    marker = f"{name} = {{"
    start = source.index(marker) + len(f"{name} = ")
    depth = 0
    for i in range(start, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return ast.literal_eval(source[start:i + 1])
    raise AssertionError(f"could not extract dict {name!r} from notebook")


class LoaderNotebookConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = NOTEBOOK.read_text(encoding="utf-8")
        cls.casts = _extract_dict_literal(cls.source, "CASTS")
        cls.keys = _extract_dict_literal(cls.source, "IDEMPOTENCY_KEYS")

    def test_notebook_exists(self):
        self.assertTrue(NOTEBOOK.exists())

    def test_idempotency_keys_match_generator(self):
        self.assertEqual(self.keys, GEN_IDEMPOTENCY_KEYS)

    def test_cast_columns_match_emitted_columns(self):
        self.assertEqual(set(self.casts), set(EXPECTED_COLUMNS))
        for table, columns in EXPECTED_COLUMNS.items():
            self.assertEqual(set(self.casts[table].keys()), set(columns),
                             msg=f"{table}: loader cast columns differ from emitted columns")

    def test_idempotency_keys_are_cast_columns(self):
        for table, keys in self.keys.items():
            for key in keys:
                self.assertIn(key, self.casts[table],
                              msg=f"{table}: idempotency key {key} not in loader casts")

    def test_environment_is_guarded(self):
        # Demo-data load must be hard-disabled outside dev/test/demo. Deployed
        # environment names are qualified (e.g. "novasteelv3-demo"), so the guard
        # accepts the bare token or a "-<token>" suffix and rejects anything else.
        self.assertIn('_ENV_ALLOWED_SUFFIXES = ("dev", "test", "demo")', self.source)
        self.assertIn(
            'if not any(_env_normalized == t or _env_normalized.endswith("-" + t)',
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
