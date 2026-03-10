from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import ApiError
from app.services.email_service import EmailVerificationService


class StubHeybounceClient:
    async def validate_single(self, email: str) -> dict:
        return {
            "address": email,
            "normalized": email,
            "status": "safe",
            "reason": "safe",
            "domain": email.split("@", 1)[1],
        }

    async def validate_batch(self, emails: list[str]) -> list[dict]:
        return [
            {
                "address": email,
                "normalized": email,
                "status": "safe",
                "reason": "safe",
                "domain": email.split("@", 1)[1],
            }
            for email in emails
        ]


@pytest.mark.anyio
async def test_invalid_single_email_returns_assignment_error() -> None:
    service = EmailVerificationService(StubHeybounceClient(), Settings(heybounce_api_key="fake"))
    with pytest.raises(ApiError) as exc:
        await service.verify_single("not-an-email")
    assert exc.value.error == "invalid_email_format"
    assert exc.value.status_code == 400


@pytest.mark.anyio
async def test_batch_limit_exceeded() -> None:
    service = EmailVerificationService(StubHeybounceClient(), Settings(heybounce_api_key="fake"))
    emails = [f"user{i}@example.com" for i in range(101)]
    with pytest.raises(ApiError) as exc:
        await service.verify_batch(emails)
    assert exc.value.error == "batch_limit_exceeded"
    assert exc.value.status_code == 413


@pytest.mark.anyio
async def test_batch_invalid_email_is_reported_per_item() -> None:
    service = EmailVerificationService(StubHeybounceClient(), Settings(heybounce_api_key="fake"))
    result = await service.verify_batch(["valid@example.com", "not-an-email"])
    assert result[0].isDeliverable is True
    assert result[1].reason == "invalid_email_format"
    assert result[1].isDeliverable is False
