"""Tests for EnableBanking auth-state tracking."""

import time

import pytest

from leggen.services import enablebanking_service as ebs
from leggen.services.enablebanking_service import EnableBankingService


@pytest.fixture(autouse=True)
def clear_states():
    ebs._pending_auth_states.clear()
    yield
    ebs._pending_auth_states.clear()


@pytest.mark.unit
class TestAuthStateTracking:
    def test_unknown_state_is_rejected(self):
        service = EnableBankingService()
        assert service.claim_auth_state("never-issued") is None

    def test_issued_state_is_claimable(self):
        service = EnableBankingService()
        service._register_auth_state("s1")

        record = service.claim_auth_state("s1")
        assert record is not None
        assert record.session_id is None

    def test_claim_is_repeatable_and_returns_redeemed_session(self):
        service = EnableBankingService()
        service._register_auth_state("s1")
        service.claim_auth_state("s1")
        service.mark_auth_state_redeemed("s1", "sess-1")

        record = service.claim_auth_state("s1")
        assert record is not None
        assert record.session_id == "sess-1"

    def test_expired_state_is_rejected_and_dropped(self):
        service = EnableBankingService()
        service._register_auth_state("s1")
        ebs._pending_auth_states["s1"].issued_at = (
            time.time() - EnableBankingService.AUTH_STATE_TTL_SECONDS - 1
        )

        assert service.claim_auth_state("s1") is None
        assert "s1" not in ebs._pending_auth_states

    def test_registering_prunes_aged_out_states(self):
        service = EnableBankingService()
        service._register_auth_state("old")
        ebs._pending_auth_states["old"].issued_at = (
            time.time() - EnableBankingService.AUTH_STATE_TTL_SECONDS - 1
        )

        service._register_auth_state("new")

        assert "old" not in ebs._pending_auth_states
        assert "new" in ebs._pending_auth_states

    def test_states_are_shared_across_service_instances(self):
        EnableBankingService()._register_auth_state("s1")
        assert EnableBankingService().claim_auth_state("s1") is not None
