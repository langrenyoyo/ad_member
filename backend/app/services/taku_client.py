import hashlib
import json
import time

import requests


class TakuClient:
    def __init__(self, publisher_key: str, base_url: str, timeout: int = 30):
        self.publisher_key = publisher_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_placements(self, app_ids: list[str] | None = None, start: int = 0, limit: int = 100):
        path = "/v1/placements"
        body = {"start": start, "limit": limit}
        if app_ids:
            body["app_ids"] = app_ids
        body_text = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        timestamp = int(time.time() * 1000)
        content_md5 = hashlib.md5(body_text.encode("utf-8")).hexdigest().upper()
        header_text = f"X-Up-Key:{self.publisher_key}\nX-Up-Timestamp:{timestamp}"
        sign_text = f"POST\n{content_md5}\napplication/json\n{header_text}\n{path}"
        signature = hashlib.md5(sign_text.encode("utf-8")).hexdigest().upper()
        response = requests.post(
            f"{self.base_url}{path}",
            data=body_text,
            headers={
                "X-Up-Key": self.publisher_key,
                "X-Up-Timestamp": str(timestamp),
                "X-Up-Signature": signature,
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
