"""Structured contracts for synthetic psychological case records.

This module validates already-authored data. It does not extract, classify,
or diagnose.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObservationStatus(StrEnum):
    """How a field relates to the source narrative."""

    REPORTED = "reported"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SymptomObservation(_StrictModel):
    """One symptom concept grounded in the case narrative when known."""

    concept: str = Field(min_length=1)
    status: ObservationStatus
    evidence_span: str | None = None

    @model_validator(mode="after")
    def evidence_matches_status(self) -> SymptomObservation:
        return _apply_evidence_rule(self)


class DurationObservation(_StrictModel):
    """Time course of the described difficulties, if the narrative states it."""

    status: ObservationStatus
    value: float | None = None
    unit: Literal["days", "weeks", "months"] | None = None
    evidence_span: str | None = None

    @model_validator(mode="after")
    def fields_match_status(self) -> DurationObservation:
        _apply_evidence_rule(self)
        has_quantity = self.value is not None or self.unit is not None
        if self.status is ObservationStatus.REPORTED:
            if self.value is None or self.unit is None:
                raise ValueError("reported duration requires both value and unit")
        elif has_quantity:
            raise ValueError("absent and unknown duration must not include value or unit")
        return self


class FunctionalImpactObservation(_StrictModel):
    """Effect on daily functioning, only when the narrative supports it."""

    status: ObservationStatus
    description: str | None = None
    evidence_span: str | None = None

    @model_validator(mode="after")
    def fields_match_status(self) -> FunctionalImpactObservation:
        _apply_evidence_rule(self)
        if self.status is ObservationStatus.UNKNOWN and self.description is not None:
            raise ValueError("unknown functional impact must not include a description")
        if self.status is ObservationStatus.REPORTED and not self.description:
            raise ValueError("reported functional impact requires a description")
        return self


class CaseRecord(_StrictModel):
    """Versioned, diagnosis-free record of a synthetic case narrative."""

    case_id: str = Field(pattern=r"^SYN-[A-Z0-9-]+$")
    is_synthetic: Literal[True] = True
    narrative: str = Field(min_length=1)
    symptoms: list[SymptomObservation] = Field(min_length=1)
    duration: DurationObservation
    functional_impact: FunctionalImpactObservation
    missing_information: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def evidence_spans_come_from_narrative(self) -> CaseRecord:
        spans = [item.evidence_span for item in self.symptoms]
        spans.append(self.duration.evidence_span)
        spans.append(self.functional_impact.evidence_span)
        for span in spans:
            if span is not None and span not in self.narrative:
                raise ValueError(
                    "evidence_span must be copied verbatim from narrative; "
                    f"not found: {span!r}"
                )
        return self


def load_case_record(path: Path | str) -> CaseRecord:
    """Load and validate a CaseRecord from a UTF-8 JSON file."""
    return CaseRecord.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _apply_evidence_rule(
    observation: SymptomObservation | DurationObservation | FunctionalImpactObservation,
) -> SymptomObservation | DurationObservation | FunctionalImpactObservation:
    if observation.status is ObservationStatus.UNKNOWN:
        if observation.evidence_span is not None:
            raise ValueError("unknown observations must not include evidence_span")
    elif not observation.evidence_span:
        raise ValueError("reported and absent observations require evidence_span")
    return observation
