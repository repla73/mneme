from __future__ import annotations

import pytest
from pydantic import ValidationError

from mneme.models import RationaleClaim, RationaleStatus


def test_explicit_rationale_requires_evidence():
    with pytest.raises(ValidationError, match="evidence reference"):
        RationaleClaim(text="The user approved this.", status=RationaleStatus.EXPLICIT)


def test_inferred_rationale_cannot_claim_certainty():
    with pytest.raises(ValidationError, match="must not claim certainty"):
        RationaleClaim(
            text="This appears to be the reason.",
            status=RationaleStatus.INFERRED,
            confidence=1.0,
        )


def test_inferred_rationale_accepts_uncertainty():
    claim = RationaleClaim(
        text="This appears to be the reason.",
        status=RationaleStatus.INFERRED,
        confidence=0.6,
    )
    assert claim.confidence == 0.6


def test_event_privacy_must_cover_provenance():
    from mneme.models import ProvenanceRef
    from conftest import make_event

    event = make_event(privacy="project_internal")
    with pytest.raises(ValidationError, match="must cover"):
        event.provenance = [
            ProvenanceRef(ref_id="secret-source", kind="message", privacy_class="secret")
        ]
