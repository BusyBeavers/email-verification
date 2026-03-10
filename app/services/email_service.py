from __future__ import annotations

import asyncio
from itertools import islice
from typing import Any, Iterable

from app.config import Settings
from app.errors import ApiError
from app.models import VerificationResult
from app.services.heybounce_client import HeybounceClient
from app.services.validation import (
    is_deliverable_status,
    is_disposable_email,
    normalize_email_or_raise,
)


class EmailVerificationService:
    def __init__(self, client: HeybounceClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def verify_single(self, email: str) -> VerificationResult:
        normalized_email = normalize_email_or_raise(email)
        provider_result = await self._client.validate_single(normalized_email)
        return self._map_provider_record(provider_result, fallback_email=normalized_email)

    async def verify_batch(self, emails: list[str]) -> list[VerificationResult]:
        if not emails:
            raise ApiError("invalid_request", "At least one email address must be provided.", 400)
        if len(emails) > self._settings.batch_max_emails:
            raise ApiError(
                "batch_limit_exceeded",
                f"This endpoint accepts at most {self._settings.batch_max_emails} email addresses per request.",
                413,
            )

        normalized_valid_emails: list[str] = []
        invalid_results_by_email: dict[str, VerificationResult] = {}
        original_order: list[str] = []

        for raw_email in emails:
            original_order.append(raw_email)
            try:
                normalized_valid_emails.append(normalize_email_or_raise(raw_email))
            except ApiError:
                invalid_results_by_email[raw_email] = VerificationResult(
                    email=raw_email,
                    isDeliverable=False,
                    reason="invalid_email_format",
                    isDisposable=False,
                )

        unique_valid_emails = list(dict.fromkeys(normalized_valid_emails))
        valid_results_by_email: dict[str, VerificationResult] = {}
        tasks = [
            self._client.validate_batch(chunk)
            for chunk in self._chunked(unique_valid_emails, self._settings.provider_batch_max_emails)
        ]
        if tasks:
            chunk_results = await asyncio.gather(*tasks)
            for chunk in chunk_results:
                for item in chunk:
                    mapped = self._map_provider_record(item)
                    valid_results_by_email[mapped.email] = mapped

        combined_results: list[VerificationResult] = []
        for original_email in original_order:
            if original_email in invalid_results_by_email:
                combined_results.append(invalid_results_by_email[original_email])
                continue

            normalized_email = normalize_email_or_raise(original_email)
            mapped_result = valid_results_by_email.get(normalized_email)
            if mapped_result is None:
                combined_results.append(
                    VerificationResult(
                        email=normalized_email,
                        isDeliverable=False,
                        reason="provider_no_result",
                        isDisposable=False,
                    )
                )
            else:
                combined_results.append(mapped_result)
        return combined_results

    @staticmethod
    def _chunked(values: list[str], chunk_size: int) -> Iterable[list[str]]:
        iterator = iter(values)
        while chunk := list(islice(iterator, chunk_size)):
            yield chunk

    def _map_provider_record(self, item: dict[str, Any], fallback_email: str | None = None) -> VerificationResult:
        address = str(item.get("normalized") or item.get("address") or fallback_email or "")
        status = item.get("status")
        reason = str(item.get("reason") or status or "unknown")
        domain = str(item.get("domain") or address.split("@")[-1] if "@" in address else "")

        return VerificationResult(
            email=address,
            isDeliverable=is_deliverable_status(status),
            reason=reason,
            isDisposable=is_disposable_email(domain=domain, status=status, reason=reason),
        )
