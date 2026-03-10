from __future__ import annotations

from typing import Annotated

from fastapi import Body, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.errors import ApiError
from app.models import (
    BatchEmailRequest,
    BatchEmailRequestRoot,
    ErrorResponse,
    ProviderStatusResponse,
    SingleEmailRequest,
    VerificationResult,
)
from app.services.email_service import EmailVerificationService
from app.services.heybounce_client import HeybounceClient

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Wraps Heybounce so the team can call simple, assignment-aligned endpoints.",
)


def get_email_service() -> EmailVerificationService:
    return EmailVerificationService(HeybounceClient(settings), settings)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error, message=exc.message).model_dump(exclude_none=True),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="invalid_request", message=str(exc)).model_dump(exclude_none=True),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/email/provider-status", response_model=ProviderStatusResponse)
async def provider_status() -> ProviderStatusResponse:
    return ProviderStatusResponse(
        configured=bool(settings.heybounce_api_key),
        batchProviderLimit=settings.provider_batch_max_emails,
        batchMicroserviceLimit=settings.batch_max_emails,
    )


@app.post("/email/verify", response_model=VerificationResult, responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def verify_email(
    payload: SingleEmailRequest,
    service: Annotated[EmailVerificationService, Depends(get_email_service)],
) -> VerificationResult:
    return await service.verify_single(payload.email)


@app.post(
    "/email/verify/batch",
    response_model=list[VerificationResult],
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def verify_batch(
    payload: Annotated[BatchEmailRequest | BatchEmailRequestRoot, Body(...)],
    service: Annotated[EmailVerificationService, Depends(get_email_service)],
) -> list[VerificationResult]:
    emails = payload.emails if isinstance(payload, BatchEmailRequest) else payload.root
    return await service.verify_batch(emails)
