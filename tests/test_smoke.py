"""Smoke tests for the installable package foundation."""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

import mindgraph_rag


def test_package_import_exposes_version() -> None:
    assert mindgraph_rag.__version__ == "0.1.0"
    assert mindgraph_rag.MIN_PYTHON == (3, 11)


def test_runtime_meets_declared_python_requirement() -> None:
    assert sys.version_info >= mindgraph_rag.MIN_PYTHON


def test_package_is_loaded_from_src_layout() -> None:
    package_file = Path(mindgraph_rag.__file__).resolve()
    assert package_file.parent.name == "mindgraph_rag"
    assert package_file.parents[1].name == "src"


def test_installed_distribution_metadata() -> None:
    dist = metadata.distribution("mindgraph_rag")
    requires_python = dist.metadata["Requires-Python"]
    assert requires_python == ">=3.11"
    assert dist.version == mindgraph_rag.__version__
