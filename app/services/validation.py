from __future__ import annotations

from email_validator import EmailNotValidError, validate_email

from app.errors import ApiError

# A lightweight fallback set of well-known disposable providers to make
# the microservice's "isDisposable" field deterministic even if the upstream
# API response does not expose a dedicated disposable flag.
COMMON_DISPOSABLE_DOMAINS = {
    "10minutemail.com",
    "10minutemail.net",
    "20minutemail.com",
    "dispostable.com",
    "fakeinbox.com",
    "guerrillamail.com",
    "maildrop.cc",
    "mailinator.com",
    "mintemail.com",
    "sharklasers.com",
    "temp-mail.org",
    "tempail.com",
    "tempmail.dev",
    "trashmail.com",
    "yopmail.com",
}

DELIVERABLE_STATUSES = {
    "safe",
    "valid",
    "deliverable",
    "accept_all",
    "catch-all",
    "catch_all",
}

DISPOSABLE_MARKERS = {
    "disposable",
    "temporary",
    "temp",
    "burner",
}


def normalize_email_or_raise(email: str) -> str:
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ApiError(
            error="invalid_email_format",
            message="The provided email address is not syntactically valid.",
            status_code=400,
        ) from exc


def is_disposable_email(domain: str, status: str | None, reason: str | None) -> bool:
    normalized_domain = domain.lower().strip()
    status_text = (status or "").lower()
    reason_text = (reason or "").lower()

    if normalized_domain in COMMON_DISPOSABLE_DOMAINS:
        return True

    return any(marker in status_text or marker in reason_text for marker in DISPOSABLE_MARKERS)


def is_deliverable_status(status: str | None) -> bool:
    if not status:
        return False
    return status.lower().strip() in DELIVERABLE_STATUSES
