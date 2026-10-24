"""Tests for dataset provenance manifests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mindgraph_rag.core import (
    DatasetManifest,
    SourceType,
    load_case_record,
    load_dataset_manifest,
)
from mindgraph_rag.core.manifest import DatasetEntry

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "datasets.toml"


def _entry_toml(**overrides: object) -> str:
    fields: dict[str, object] = {
        "id": "SYN-TEST",
        "source_type": "synthetic",
        "path": "data/synthetic/item.json",
        "version": "1.0.0",
        "purpose": "unit test",
        "license": "project-created",
        "is_fictional": True,
        "is_real_patient_data": False,
    }
    fields.update(overrides)
    lines = ["schema_version = 1", "", "[[datasets]]"]
    for key, value in fields.items():
        lines.append(f"{key} = {_toml_value(value)}")
    return "\n".join(lines) + "\n"


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return '"' + str(value).replace('"', '\\"') + '"'


def _write_manifest(tmp_path: Path, body: str, *, create_target: bool = True) -> Path:
    data_dir = tmp_path / "data" / "synthetic"
    data_dir.mkdir(parents=True)
    if create_target:
        (data_dir / "item.json").write_text("{}", encoding="utf-8")
    manifest_path = tmp_path / "datasets.toml"
    manifest_path.write_text(body, encoding="utf-8")
    return manifest_path


def test_project_manifest_lists_syn_001_as_fictional() -> None:
    manifest = load_dataset_manifest(MANIFEST_PATH, root=REPO_ROOT)
    assert manifest.schema_version == 1
    entry = next(item for item in manifest.datasets if item.id == "SYN-001")
    assert entry.source_type is SourceType.SYNTHETIC
    assert entry.is_fictional is True
    assert entry.is_real_patient_data is False
    assert entry.resolve_path(REPO_ROOT).is_file()
    case = load_case_record(entry.resolve_path(REPO_ROOT))
    assert case.case_id == "SYN-001"


def test_missing_required_metadata_is_rejected() -> None:
    payload = {
        "schema_version": 1,
        "datasets": [
            {
                "id": "SYN-TEST",
                "source_type": "synthetic",
                "path": "data/synthetic/item.json",
                "version": "1.0.0",
                "purpose": "unit test",
                "is_fictional": True,
                "is_real_patient_data": False,
            }
        ],
    }
    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(payload)


def test_invalid_source_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DatasetEntry.model_validate(
            {
                "id": "SYN-TEST",
                "source_type": "clinical_records",
                "path": "data/synthetic/item.json",
                "version": "1.0.0",
                "purpose": "unit test",
                "license": "project-created",
                "is_fictional": True,
                "is_real_patient_data": False,
            }
        )


def test_nonexistent_path_raises_file_not_found(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, _entry_toml(), create_target=False)
    with pytest.raises(FileNotFoundError, match="do not exist"):
        load_dataset_manifest(manifest_path, root=tmp_path)


def test_literature_source_type_is_accepted_when_file_exists(tmp_path: Path) -> None:
    body = _entry_toml(
        id="LIT-TEST",
        source_type="literature",
        is_fictional=False,
        is_real_patient_data=False,
        license="CC-BY-4.0",
        purpose="placeholder for a future open literature snippet",
    )
    manifest_path = _write_manifest(tmp_path, body)
    manifest = load_dataset_manifest(manifest_path, root=tmp_path)
    assert manifest.datasets[0].source_type is SourceType.LITERATURE
