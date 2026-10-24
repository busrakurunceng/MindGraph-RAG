"""Tests for synthetic CaseRecord validation contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from mindgraph_rag.core import (
    CaseRecord,
    DurationObservation,
    FunctionalImpactObservation,
    ObservationStatus,
    SymptomObservation,
    load_case_record,
)

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "SYN-001.json"


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "case_id": "SYN-001",
        "is_synthetic": True,
        "narrative": "Fictional note. Difficulty sleeping for about three weeks.",
        "symptoms": [
            {
                "concept": "sleep_disturbance",
                "status": "reported",
                "evidence_span": "Difficulty sleeping",
            }
        ],
        "duration": {
            "status": "reported",
            "value": 3,
            "unit": "weeks",
            "evidence_span": "about three weeks",
        },
        "functional_impact": {"status": "unknown"},
        "missing_information": ["functional_impact"],
    }
    payload.update(overrides)
    return payload


def test_fixture_is_a_valid_case_record() -> None:
    record = load_case_record(FIXTURE_PATH)
    assert record.case_id == "SYN-001"
    assert record.is_synthetic is True
    assert "fictional" in record.narrative.lower()
    reported = [
        item.concept
        for item in record.symptoms
        if item.status is ObservationStatus.REPORTED
    ]
    assert "sleep_disturbance" in reported
    assert record.functional_impact.status is ObservationStatus.UNKNOWN
    assert "diagnosis" not in record.model_dump()


def test_json_round_trip_preserves_unknown_and_absent() -> None:
    original = load_case_record(FIXTURE_PATH)
    restored = CaseRecord.model_validate_json(original.model_dump_json())
    panic = next(item for item in restored.symptoms if item.concept == "panic_attacks")
    assert panic.status is ObservationStatus.ABSENT
    assert panic.evidence_span == "have not had panic attacks"
    assert restored.functional_impact.status is ObservationStatus.UNKNOWN
    assert restored.functional_impact.evidence_span is None
    assert restored.functional_impact.description is None


def test_fixture_json_deserializes_from_disk_bytes() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    record = CaseRecord.model_validate(raw)
    assert record.duration.value == 3
    assert record.duration.unit == "weeks"


def test_invalid_observation_status_is_rejected() -> None:
    payload = _valid_payload(
        symptoms=[
            {
                "concept": "sleep_disturbance",
                "status": "denied",
                "evidence_span": "Difficulty sleeping",
            }
        ]
    )
    with pytest.raises(ValidationError):
        CaseRecord.model_validate(payload)


def test_missing_required_fields_are_rejected() -> None:
    payload = _valid_payload()
    del payload["case_id"]
    with pytest.raises(ValidationError):
        CaseRecord.model_validate(payload)


def test_unknown_is_not_treated_as_absent() -> None:
    unknown = FunctionalImpactObservation(status=ObservationStatus.UNKNOWN)
    absent = FunctionalImpactObservation(
        status=ObservationStatus.ABSENT,
        evidence_span="no effect on work",
    )
    assert unknown.status is not ObservationStatus.ABSENT
    assert absent.status is ObservationStatus.ABSENT
    with pytest.raises(ValidationError, match="must not include evidence_span"):
        FunctionalImpactObservation(
            status=ObservationStatus.UNKNOWN,
            evidence_span="no effect on work",
        )
    with pytest.raises(ValidationError, match="require evidence_span"):
        SymptomObservation(concept="panic_attacks", status=ObservationStatus.ABSENT)


def test_unknown_duration_cannot_carry_invented_quantity() -> None:
    with pytest.raises(ValidationError, match="must not include value or unit"):
        DurationObservation(status=ObservationStatus.UNKNOWN, value=3, unit="weeks")


def test_evidence_span_must_appear_in_narrative() -> None:
    payload = _valid_payload(
        symptoms=[
            {
                "concept": "sleep_disturbance",
                "status": "reported",
                "evidence_span": "nightmares every night",
            }
        ]
    )
    with pytest.raises(ValidationError, match="copied verbatim"):
        CaseRecord.model_validate(payload)


def test_extra_diagnosis_field_is_rejected() -> None:
    payload = _valid_payload(diagnosis="major depressive disorder")
    with pytest.raises(ValidationError):
        CaseRecord.model_validate(payload)
