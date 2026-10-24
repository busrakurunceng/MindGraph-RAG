"""Dataset provenance manifest loading and validation.

Parses TOML with the standard-library ``tomllib``. This tracks source and
allowed use; it does not ingest documents or extract case content.
"""

from __future__ import annotations

import tomllib
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceType(StrEnum):
    """High-level origin of a dataset file or corpus."""

    SYNTHETIC = "synthetic"
    LITERATURE = "literature"


class DatasetEntry(BaseModel):
    """One versioned dataset referenced by the project."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    source_type: SourceType
    path: str = Field(min_length=1)
    version: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    license: str = Field(min_length=1)
    is_fictional: bool
    is_real_patient_data: bool
    notes: str | None = None

    @model_validator(mode="after")
    def synthetic_data_is_not_patient_data(self) -> DatasetEntry:
        if self.source_type is SourceType.SYNTHETIC:
            if not self.is_fictional:
                raise ValueError("synthetic datasets must set is_fictional = true")
            if self.is_real_patient_data:
                raise ValueError("synthetic datasets must set is_real_patient_data = false")
        if self.is_real_patient_data:
            raise ValueError("real patient data is not permitted in this prototype")
        return self

    def resolve_path(self, root: Path) -> Path:
        """Resolve ``path`` against the repository root."""
        return (root / self.path).resolve()


class DatasetManifest(BaseModel):
    """Collection of dataset provenance records."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(ge=1)
    datasets: list[DatasetEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def dataset_ids_are_unique(self) -> DatasetManifest:
        ids = [entry.id for entry in self.datasets]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ValueError(f"duplicate dataset ids: {duplicates}")
        return self


def load_dataset_manifest(path: Path | str, *, root: Path | str) -> DatasetManifest:
    """Load a manifest, validate metadata, and confirm local files exist."""
    manifest_path = Path(path)
    repo_root = Path(root)
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = DatasetManifest.model_validate(payload)
    _require_local_files(manifest, repo_root)
    return manifest


def _require_local_files(manifest: DatasetManifest, root: Path) -> None:
    missing: list[str] = []
    for entry in manifest.datasets:
        resolved = entry.resolve_path(root)
        if not resolved.is_file():
            missing.append(f"{entry.id}: {entry.path}")
    if missing:
        raise FileNotFoundError(
            "manifest references files that do not exist: " + "; ".join(missing)
        )
