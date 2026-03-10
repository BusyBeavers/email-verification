from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.errors import ApiError


class HeybounceClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def validate_single(self, email: str) -> dict[str, Any]:
        api_key = self._require_api_key()

        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            # The public docs currently render the single-email endpoint in an
            # ambiguous way, so we try the most likely forms in order.
            candidates: list[tuple[str, dict[str, str] | None]] = [
                (f"{self._settings.heybounce_base_url}/validate", {"email": email, "api_key": api_key}),
                (f"{self._settings.heybounce_base_url}/{email}", {"api_key": api_key}),
                (f"{self._settings.heybounce_base_url}/{email}&api_key={api_key}", None),
            ]

            last_response: httpx.Response | None = None
            for url, params in candidates:
                response = await client.get(url, params=params)
                last_response = response
                if response.status_code in {404, 405}:
                    continue
                return self._parse_single_response(response)

        if last_response is None:
            raise ApiError("provider_unreachable", "Heybounce could not be reached.", 502)
        raise self._provider_error_from_response(last_response)

    async def validate_batch(self, emails: list[str]) -> list[dict[str, Any]]:
        api_key = self._require_api_key()
        url = f"{self._settings.heybounce_base_url}/validate_batch"
        async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
            response = await client.post(url, params={"api_key": api_key}, json={"emails": emails})
        self._raise_for_error(response)
        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise ApiError("provider_invalid_response", "Heybounce returned an unexpected batch payload.", 502)
        return data

    def _require_api_key(self) -> str:
        if not self._settings.heybounce_api_key:
            raise ApiError(
                error="service_not_configured",
                message="HEYBOUNCE_API_KEY is missing. Add it to your environment before calling this endpoint.",
                status_code=503,
            )
        return self._settings.heybounce_api_key

    def _parse_single_response(self, response: httpx.Response) -> dict[str, Any]:
        self._raise_for_error(response)
        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiError("provider_invalid_response", "Heybounce returned an unexpected single-email payload.", 502)
        return data

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        raise self._provider_error_from_response(response)

    def _provider_error_from_response(self, response: httpx.Response) -> ApiError:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        provider_message = payload.get("error_message") or payload.get("message") or response.text.strip() or "Provider request failed."

        if response.status_code == 401:
            return ApiError("provider_auth_error", provider_message, 502)
        if response.status_code == 402:
            return ApiError("provider_quota_exceeded", provider_message, 503)
        if response.status_code == 429:
            return ApiError("provider_rate_limited", provider_message, 503)
        if response.status_code >= 500:
            return ApiError("provider_server_error", provider_message, 502)
        return ApiError("provider_request_failed", provider_message, 502)
