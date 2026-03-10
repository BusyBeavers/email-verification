from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app, get_email_service
from app.models import VerificationResult


class StubEmailService:
    async def verify_single(self, email: str) -> VerificationResult:
        return VerificationResult(email=email, isDeliverable=True, reason="safe", isDisposable=False)

    async def verify_batch(self, emails: list[str]) -> list[VerificationResult]:
        return [VerificationResult(email=email, isDeliverable=True, reason="safe", isDisposable=False) for email in emails]


@pytest.fixture()
def override_service() -> None:
    app.dependency_overrides[get_email_service] = lambda: StubEmailService()
    yield
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_single_verify_success(override_service: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/email/verify", json={"email": "user@example.com"})
    assert response.status_code == 200
    assert response.json()["isDeliverable"] is True


@pytest.mark.anyio
async def test_batch_verify_accepts_wrapped_payload(override_service: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/email/verify/batch", json={"emails": ["a@example.com", "b@example.com"]})
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.anyio
async def test_batch_verify_accepts_raw_array(override_service: None) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/email/verify/batch", json=["a@example.com", "b@example.com"])
    assert response.status_code == 200
    assert response.json()[0]["email"] == "a@example.com"
