from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel


class SingleEmailRequest(BaseModel):
    email: Annotated[str, Field(min_length=3, max_length=320)]


class BatchEmailRequest(BaseModel):
    emails: Annotated[list[str], Field(min_length=1, max_length=100)]


class BatchEmailRequestRoot(RootModel[list[str]]):
    root: Annotated[list[str], Field(min_length=1, max_length=100)]


class VerificationResult(BaseModel):
    email: str
    isDeliverable: bool
    reason: str
    isDisposable: bool = False


class ErrorResponse(BaseModel):
    error: str
    message: str | None = None


class ProviderStatusResponse(BaseModel):
    provider: Literal["heybounce"] = "heybounce"
    configured: bool
    batchProviderLimit: int
    batchMicroserviceLimit: int
