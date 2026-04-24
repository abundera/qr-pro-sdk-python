from __future__ import annotations

import time
from typing import Any, List, Optional

import httpx

from .models import Analytics, Code, CodeCreate, CodePatch, Group, ListResult, Webhook

DEFAULT_BASE_URL = "https://pro.qr.abundera.ai"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
RETRY_STATUS = {429, 500, 502, 503, 504}


class AbunderaError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"[{status} {code}] {message}")
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id


class Client:
    """Synchronous client for the Abundera QR Pro API.

    Example:
        >>> from abundera_qr_pro import Client
        >>> c = Client(api_key="abnd_qrpro_...")
        >>> code = c.create_code(destination_url="https://example.com")
        >>> code.short_url
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str = "abundera-qr-pro-python/0.1.0",
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self._http = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict] = None,
        raw: bool = False,
    ) -> Any:
        url = self.base_url + path
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self._http.request(
                    method, url, json=json, params=params, headers=headers
                )
            except httpx.RequestError as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise
                time.sleep(0.25 * (2**attempt))
                continue

            if r.is_success:
                if raw:
                    return r.text
                if not r.content:
                    return None
                return r.json()

            if r.status_code in RETRY_STATUS and attempt < self.max_retries:
                try:
                    retry_after = float(r.headers.get("retry-after", "0"))
                except ValueError:
                    retry_after = 0
                delay = retry_after if retry_after > 0 else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            code = "http_error"
            message = f"HTTP {r.status_code}"
            try:
                j = r.json()
                code = j.get("code", code)
                message = j.get("message", message)
            except ValueError:
                pass
            raise AbunderaError(
                r.status_code, code, message, r.headers.get("x-request-id")
            )
        if last_exc:
            raise last_exc
        raise RuntimeError("unreachable")

    # --- Codes --------------------------------------------------------

    def list_codes(
        self,
        *,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        tag: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> ListResult[Code]:
        params = {
            k: v
            for k, v in {
                "cursor": cursor,
                "limit": limit,
                "tag": tag,
                "group_id": group_id,
            }.items()
            if v is not None
        }
        r = self._request("GET", "/api/codes", params=params)
        return ListResult(
            data=[Code.from_dict(d) for d in r.get("data", [])],
            pagination=r.get("pagination", {}),
        )

    def get_code(self, code_id: str) -> Code:
        return Code.from_dict(self._request("GET", f"/api/codes/{code_id}"))

    def create_code(self, **fields: Any) -> Code:
        data = CodeCreate(**fields).to_dict()
        return Code.from_dict(self._request("POST", "/api/codes", json=data))

    def update_code(self, code_id: str, **fields: Any) -> Code:
        data = CodePatch(**fields).to_dict()
        return Code.from_dict(
            self._request("PATCH", f"/api/codes/{code_id}", json=data)
        )

    def delete_code(self, code_id: str) -> None:
        self._request("DELETE", f"/api/codes/{code_id}")

    def check_slug(self, slug: str) -> bool:
        return bool(
            self._request("GET", "/api/codes/check-slug", params={"slug": slug}).get(
                "available"
            )
        )

    def import_codes(self, rows: List[dict]) -> dict:
        return self._request("POST", "/api/codes/import", json={"rows": rows})

    # --- Analytics ----------------------------------------------------

    def get_analytics(
        self, code_id: str, *, from_: Optional[str] = None, to: Optional[str] = None
    ) -> Analytics:
        params = {k: v for k, v in {"from": from_, "to": to}.items() if v is not None}
        d = self._request("GET", f"/api/codes/{code_id}/analytics", params=params)
        return Analytics(
            **{k: d.get(k) for k in Analytics.__dataclass_fields__ if k in d}
        )

    def get_analytics_csv(
        self, code_id: str, *, from_: Optional[str] = None, to: Optional[str] = None
    ) -> str:
        params = {k: v for k, v in {"from": from_, "to": to}.items() if v is not None}
        return self._request(
            "GET", f"/api/codes/{code_id}/analytics.csv", params=params, raw=True
        )

    # --- Groups -------------------------------------------------------

    def list_groups(self) -> ListResult[Group]:
        r = self._request("GET", "/api/groups")
        return ListResult(
            data=[Group(**g) for g in r.get("data", [])],
            pagination=r.get("pagination", {}),
        )

    def create_group(self, name: str, description: Optional[str] = None) -> Group:
        body = {"name": name}
        if description is not None:
            body["description"] = description
        return Group(**self._request("POST", "/api/groups", json=body))

    def delete_group(self, group_id: str) -> None:
        self._request("DELETE", f"/api/groups/{group_id}")

    # --- Webhooks -----------------------------------------------------

    def list_webhooks(self) -> ListResult[Webhook]:
        r = self._request("GET", "/api/webhooks")
        return ListResult(
            data=[Webhook(**w) for w in r.get("data", [])],
            pagination=r.get("pagination", {}),
        )

    def create_webhook(self, url: str, events: List[str]) -> Webhook:
        """Create a webhook. The returned Webhook has ``secret`` populated — store it now."""
        return Webhook(
            **self._request(
                "POST", "/api/webhooks", json={"url": url, "events": events}
            )
        )

    def delete_webhook(self, webhook_id: str) -> None:
        self._request("DELETE", f"/api/webhooks/{webhook_id}")

    # --- User ---------------------------------------------------------

    def me(self) -> dict:
        return self._request("GET", "/api/user/me")

    def export_account(self) -> dict:
        return self._request("POST", "/api/user/export")
