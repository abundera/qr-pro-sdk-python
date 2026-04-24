"""Minimal quickstart: create, update, analytics, webhook verification.

Run: ABUNDERA_API_KEY=... python examples/quickstart.py
"""

import hashlib
import hmac
import os
import time

from abundera_qr_pro import Client, verify_webhook_signature


def main() -> None:
    api_key = os.environ.get("ABUNDERA_API_KEY")
    if not api_key:
        raise SystemExit("ABUNDERA_API_KEY not set")

    with Client(api_key=api_key) as c:
        code = c.create_code(
            destination_url="https://example.com/launch",
            label="Quickstart example",
            tags=["example"],
        )
        print("created:", code.short_url)

        updated = c.update_code(
            code.id, destination_url="https://example.com/launch/v2"
        )
        print("updated:", updated.destination_url)

        stats = c.get_analytics(code.id)
        print("scans:", stats.total_scans)

        # Webhook verification (offline — synthesized signature).
        secret = "whsec_example"
        body = f'{{"event":"code.scanned","code_id":"{code.id}"}}'
        ts = str(int(time.time()))
        v1 = hmac.new(
            secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256
        ).hexdigest()
        verify_webhook_signature(signature=f"t={ts},v1={v1}", body=body, secret=secret)
        print("webhook signature verified")

        c.delete_code(code.id)


if __name__ == "__main__":
    main()
