import json
from pathlib import Path

import pytest

from fixtures.server_selection_samples import (
    BLOCKED_SELECTION_RESULT,
    COMPLETED_SELECTION_RESULT,
    FAILED_SELECTION_RESULT,
    PARTIAL_SELECTION_RESULT,
)

jsonschema = pytest.importorskip("jsonschema")


def _schema() -> dict:
    return json.loads(Path("specs/003-selecionar-servidor/contracts/selection-result.schema.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "sample",
    [
        COMPLETED_SELECTION_RESULT,
        FAILED_SELECTION_RESULT,
        PARTIAL_SELECTION_RESULT,
        BLOCKED_SELECTION_RESULT,
    ],
)
def test_selection_result_samples_match_schema(sample: dict) -> None:
    jsonschema.validate(sample, _schema())
