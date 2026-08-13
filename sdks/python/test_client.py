import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lumenvec_client


class Response:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return b'{"ok": true}'


def test_search_contract(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.data.decode("utf-8"))
        assert timeout == 3
        return Response()

    monkeypatch.setattr(lumenvec_client, "urlopen", fake_urlopen)
    client = lumenvec_client.LumenVecClient("http://example.test", api_key="secret", timeout=3)
    assert client.search([1, 0], k=3, metadata={"tenant": "acme"}, metric="cosine") == {"ok": True}
    assert seen["url"] == "http://example.test/v1/vectors/search"
    assert seen["headers"]["Authorization"] == "Bearer secret"
    assert seen["body"]["metadata"] == {"tenant": "acme"}
    assert seen["body"]["metric"] == "cosine"


def test_health_accepts_plain_text_response(monkeypatch):
    class HealthResponse(Response):
        def read(self): return b"ok"

    monkeypatch.setattr(lumenvec_client, "urlopen", lambda request, timeout: HealthResponse())
    assert lumenvec_client.LumenVecClient("http://example.test").health() == "ok"
