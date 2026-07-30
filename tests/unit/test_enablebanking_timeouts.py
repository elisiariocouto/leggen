"""Tests for exception descriptions and EnableBanking request timeouts.

Both cover a sync failure mode that was silent: a paginated transactions fetch
timing out produced the log line "Failed to sync account <id>: " with no cause,
because httpx timeout exceptions carry an empty message.
"""

import httpx
import pytest

from leggen.errors import NotFoundError, describe_exception
from leggen.services.enablebanking_service import EnableBankingService
from leggen.utils.config import Config


@pytest.mark.unit
class TestDescribeException:
    """Test human-readable exception descriptions."""

    @pytest.mark.parametrize(
        "exc",
        [
            httpx.ReadTimeout(""),
            httpx.ConnectTimeout(""),
            httpx.PoolTimeout(""),
        ],
    )
    def test_empty_message_falls_back_to_class_name(self, exc):
        """Timeouts have no message, so the class name must identify them."""
        assert describe_exception(exc) == type(exc).__name__

    def test_whitespace_only_message_falls_back_to_class_name(self):
        assert describe_exception(RuntimeError("   ")) == "RuntimeError"

    def test_message_is_qualified_with_class_name(self):
        assert describe_exception(ValueError("boom")) == "ValueError: boom"

    def test_domain_error_detail_is_preserved(self):
        assert describe_exception(NotFoundError("account missing")) == (
            "NotFoundError: account missing"
        )

    def test_description_is_never_empty(self):
        """The formatted sync error must always name a cause."""
        account_id = "909c2d3b-728d-4af7-b7cc-d94b91f565b7"
        msg = f"Failed to sync account {account_id}: {describe_exception(httpx.ReadTimeout(''))}"
        assert msg.endswith("ReadTimeout")
        assert not msg.endswith(": ")


@pytest.mark.unit
class TestEnableBankingTimeouts:
    """Test that request timeouts are granular and configurable."""

    def test_default_timeouts(self):
        config = Config()
        config._config = {"enablebanking": {}}

        timeout = EnableBankingService().timeout
        assert timeout.connect == 10.0
        assert timeout.read == 60.0

    def test_read_timeout_exceeds_connect_timeout_by_default(self):
        """Slow transaction pages need a longer read budget than connect."""
        config = Config()
        config._config = {"enablebanking": {}}

        timeout = EnableBankingService().timeout
        assert timeout.read > timeout.connect

    def test_configured_timeouts_are_used(self):
        config = Config()
        config._config = {
            "enablebanking": {"connect_timeout": 5, "read_timeout": 120},
        }

        timeout = EnableBankingService().timeout
        assert timeout.connect == 5.0
        assert timeout.read == 120.0

    def test_client_is_rebuilt_when_timeout_changes(self):
        """Settings edits apply without a server restart."""
        config = Config()
        config._config = {"enablebanking": {"read_timeout": 60}}

        service = EnableBankingService()
        first = service._get_client()

        config._config = {"enablebanking": {"read_timeout": 120}}
        second = service._get_client()

        assert first is not second
        assert second.timeout.read == 120.0

    def test_client_is_reused_when_timeout_is_unchanged(self):
        config = Config()
        config._config = {"enablebanking": {"read_timeout": 60}}

        service = EnableBankingService()
        assert service._get_client() is service._get_client()
