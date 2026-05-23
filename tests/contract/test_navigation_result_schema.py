import json
from pathlib import Path

import pytest

from fixtures.navigation_result_samples import (
    BLOCKED_NAVIGATION_RESULT,
    COMPLETED_NAVIGATION_RESULT,
    FAILED_NAVIGATION_RESULT,
    PARTIAL_NAVIGATION_RESULT,
)

jsonschema = pytest.importorskip("jsonschema")


def _schema() -> dict:
    return json.loads(Path("specs/002-navegar-espelho-ponto/contracts/navigation-result.schema.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "sample",
    [
        COMPLETED_NAVIGATION_RESULT,
        FAILED_NAVIGATION_RESULT,
        PARTIAL_NAVIGATION_RESULT,
        BLOCKED_NAVIGATION_RESULT,
    ],
)
def test_navigation_result_samples_match_schema(sample: dict) -> None:
    jsonschema.validate(sample, _schema())
