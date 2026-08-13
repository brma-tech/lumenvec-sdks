"""Small dependency-free Python client for the LumenVec HTTP API.

The client intentionally uses only the standard library so examples can run
in constrained environments. It targets the versioned ``/v1`` endpoints.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LumenVecError(RuntimeError):
    """Raised when the server rejects a request or cannot be reached."""


class LumenVecClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict | None = None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                if not raw:
                    return None
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw.decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError):
                detail = exc.read().decode("utf-8", errors="replace")
                raise LumenVecError(f"HTTP {exc.code}: {detail}") from exc
            raise LumenVecError(str(exc)) from exc

    def health(self):
        return self._request("GET", "/v1/health")

    def upsert(self, vector_id: str, values: list[float], metadata: dict[str, str] | None = None, *, namespace: str | None = None):
        payload = {"id": vector_id, "values": values}
        if metadata:
            payload["metadata"] = metadata
        if namespace:
            payload["namespace"] = namespace
        return self._request("POST", "/v1/vectors", payload)

    def upsert_batch(self, vectors: list[dict], *, namespace: str | None = None):
        if namespace:
            vectors = [{**vector, "namespace": namespace} for vector in vectors]
        return self._request("POST", "/v1/vectors/batch", {"vectors": vectors})

    def upsert_stream(self, records, *, namespace: str | None = None):
        """Upload an iterable of vector dictionaries as newline-delimited JSON."""
        import json as _json
        from urllib.request import Request, urlopen as _urlopen
        lines = []
        for record in records:
            item = dict(record)
            if namespace:
                item["namespace"] = namespace
            lines.append(_json.dumps(item))
        headers = {"Content-Type": "application/x-ndjson", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.base_url + "/v1/vectors/stream", data=("\n".join(lines) + "\n").encode(), headers=headers, method="POST")
        with _urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
            return _json.loads(raw) if raw else None

    def get(self, vector_id: str):
        return self._request("GET", f"/v1/vectors/{vector_id}")

    def search(self, values: list[float], k: int = 10, *, filter_ids=None,
               text_query: str | None = None, metadata=None, metric: str | None = None, namespace: str | None = None):
        payload = {"values": values, "k": k}
        if filter_ids:
            payload["filter_ids"] = list(filter_ids)
        if text_query:
            payload["text_query"] = text_query
        if metadata:
            payload["metadata"] = metadata
        if metric:
            payload["metric"] = metric
        if namespace:
            payload["namespace"] = namespace
        return self._request("POST", "/v1/vectors/search", payload)


__all__ = ["LumenVecClient", "LumenVecError"]
