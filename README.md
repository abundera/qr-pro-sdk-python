# abundera-qr-pro

Official Python SDK for [Abundera QR Pro](https://pro.qr.abundera.ai).

Dynamic QR codes that you actually own. Scan analytics. Webhooks. Privacy-safe by default.

## Install

```bash
pip install abundera-qr-pro
```

Requires Python 3.9+.

## Quickstart

```python
from abundera_qr_pro import Client

with Client(api_key="abnd_qrpro_...") as c:
    code = c.create_code(
        destination_url="https://example.com/launch",
        label="Spring launch poster",
        tags=["print", "q2"],
    )
    print(code.short_url)

    # Later: change where it points
    c.update_code(code.id, destination_url="https://example.com/launch/v2")

    # Pull analytics
    stats = c.get_analytics(code.id, from_="2026-04-01")
    print(stats.total_scans, stats.by_country)
```

## Webhook verification

```python
from abundera_qr_pro import verify_webhook_signature
from abundera_qr_pro.webhook import WebhookVerificationError

# In your Flask/FastAPI/Django handler:
signature = request.headers["X-Abundera-Signature"]
raw_body = request.body  # raw string/bytes, NOT parsed JSON

try:
    verify_webhook_signature(
        signature=signature,
        body=raw_body,
        secret=os.environ["ABUNDERA_WEBHOOK_SECRET"],
    )
except WebhookVerificationError:
    return "", 400

# Safe to parse and act on body after this line
```

## Configuration

| Option        | Default                              | Description                                |
| ------------- | ------------------------------------ | ------------------------------------------ |
| `api_key`     | **required**                         | API key from `/account/keys`               |
| `base_url`    | `https://pro.qr.abundera.ai`         | Override for self-hosted / staging         |
| `timeout`     | `30.0`                               | Per-request timeout in seconds             |
| `max_retries` | `3`                                  | Retries for 429/5xx (exponential backoff)  |
| `user_agent`  | `abundera-qr-pro-python/<version>`   | Sent on every request                      |
| `http_client` | internal `httpx.Client`              | Inject a preconfigured `httpx.Client`      |

## Error handling

All non-2xx responses (after retries) raise `AbunderaError`:

```python
from abundera_qr_pro import AbunderaError

try:
    c.create_code(destination_url="not a url")
except AbunderaError as e:
    print(e.status, e.code, e.message, e.request_id)
```

## Coverage

Supported surfaces: codes (CRUD + import + slug check), analytics (JSON + CSV), groups, webhooks, user. See [API docs](https://pro.qr.abundera.ai/docs/) for the full OpenAPI 3.1 spec.

## License

MIT © Abundera, Inc.
