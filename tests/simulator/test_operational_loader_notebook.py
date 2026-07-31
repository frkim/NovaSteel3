"""Conformance tests binding the operational loader notebook
(``fabric/notebooks/ns-load-operational-envelopes.Notebook``) to the
simulator's operational shaping and the BFF's expectations.

No Spark runs locally, so instead of executing the notebook these tests parse
its dataset list and schema declarations and assert they match
``simulator.fabric_operational`` (and, transitively, the BFF's
``KNOWN_DATASETS`` via the round-trip test). This catches drift between what the
simulator writes and what the loader would land.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulator.fabric_operational import (
    ENVELOPE_COLUMN,
    EVENT_ID_COLUMN,
    MANIFEST_TABLE,
    OPERATIONAL_DATASETS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = (REPO_ROOT / "fabric" / "notebooks" / "ns-load-operational-envelopes.Notebook"
            / "notebook-content.py")


def _extract_list_literal(source: str, name: str) -> list:
    marker = f"{name} = ["
    start = source.index(marker) + len(f"{name} = ")
    depth = 0
    for i in range(start, len(source)):
        ch = source[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return ast.literal_eval(source[start:i + 1])
    raise AssertionError(f"could not extract list {name!r} from notebook")


class OperationalLoaderNotebookConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = NOTEBOOK.read_text(encoding="utf-8")

    def test_notebook_exists(self):
        self.assertTrue(NOTEBOOK.exists())

    def test_dataset_list_matches_generator(self):
        datasets = _extract_list_literal(self.source, "OPERATIONAL_DATASETS")
        self.assertEqual(tuple(datasets), tuple(OPERATIONAL_DATASETS))

    def test_column_and_table_names_match(self):
        self.assertIn(f'EVENT_ID_COLUMN = "{EVENT_ID_COLUMN}"', self.source)
        self.assertIn(f'ENVELOPE_COLUMN = "{ENVELOPE_COLUMN}"', self.source)
        self.assertIn(f'MANIFEST_TABLE = "{MANIFEST_TABLE}"', self.source)

    def test_envelope_is_kept_as_string(self):
        # The BFF requires the envelope column to be a JSON *string* to
        # json.loads it; the notebook must read it with an explicit StringType
        # schema rather than letting Spark infer a struct.
        self.assertIn("StructField(ENVELOPE_COLUMN, StringType(), False)", self.source)
        self.assertNotIn("inferSchema", self.source)

    def test_merge_is_on_event_id(self):
        self.assertIn("dropDuplicates([EVENT_ID_COLUMN])", self.source)
        self.assertIn("target.`{EVENT_ID_COLUMN}` = source.`{EVENT_ID_COLUMN}`", self.source)

    def test_environment_is_guarded(self):
        # Deployed environment names are qualified (e.g. "novasteelv3-demo"), so
        # the guard accepts the bare token or a "-<token>" suffix, nothing else.
        self.assertIn('_ENV_ALLOWED_SUFFIXES = ("dev", "test", "demo")', self.source)
        self.assertIn(
            'if not any(_env_normalized == t or _env_normalized.endswith("-" + t)',
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
