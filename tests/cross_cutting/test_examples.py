"""Run every example script end-to-end so the docs can't silently rot."""

from __future__ import annotations

import pathlib
import runpy

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
EXAMPLES = sorted((_REPO_ROOT / "examples").glob("*.py"))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_runs(path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    runpy.run_path(str(path), run_name="__main__")
    assert capsys.readouterr().out  # each example prints something
