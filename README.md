# Email Verification Microservice (MS5)

This microservice houses the Heybounce API that is used for email verification (single or batch).

## What it does

- `POST /email/verify` validates one email address.
- `POST /email/verify/batch` validates between 1 and 100 email addresses.
- Syntactically invalid emails return `400` with `{ "error": "invalid_email_format" }`.
- Batch requests above 100 items return `413` with `{ "error": "batch_limit_exceeded" }`.

For batch request. It can handle up to 100 emails. Gues how many a single request can do.
Heybounce's documented batch endpoint currently allows 25 emails per provider request. This service automatically chunks larger batches so the team can still call one microservice endpoint while the implementation stays inside the provider's documented limit.

## Upstream provider notes

- Heybounce docs: `https://docs.heybounce.io/`
- Single validation: documented as a `GET` endpoint that validates one email address.
- Batch validation: documented as `POST /validate_batch` with an `emails` array and a maximum of 25 emails per provider request.

Because the public Heybounce docs currently render the single-email URL a little ambiguously, the client tries a small set of likely endpoint shapes in order. That makes the wrapper more resilient without changing the public microservice contract.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Environment variables

- `HEYBOUNCE_API_KEY` - required for live requests.
- `HEYBOUNCE_BASE_URL` - defaults to `https://api.heybounce.io/v1`.
- `REQUEST_TIMEOUT_SECONDS` - defaults to `10`.
- `BATCH_MAX_EMAILS` - defaults to `100`.
- `PROVIDER_BATCH_MAX_EMAILS` - defaults to `25`.

## Example requests

### Single email

```bash
curl -X POST http://localhost:8000/email/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

Example response:

```json
{
  "email": "user@example.com",
  "isDeliverable": true,
  "reason": "safe",
  "isDisposable": false
}
```

### Batch email validation

Wrapped payload:

```bash
curl -X POST http://localhost:8000/email/verify/batch \
  -H "Content-Type: application/json" \
  -d '{"emails":["one@example.com","two@example.com"]}'
```

Raw array payload:

```bash
curl -X POST http://localhost:8000/email/verify/batch \
  -H "Content-Type: application/json" \
  -d '["one@example.com","two@example.com"]'
```

## Testing

```bash
pytest
```

## Notes for validation screenshots

Useful URLs for your Sprint 3 validation screenshots:

- `GET /docs`
- `GET /health`
- `GET /email/provider-status`
- `POST /email/verify`
- `POST /email/verify/batch`
