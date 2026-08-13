# LumenVec Python SDK

The client uses the Python standard library and targets the versioned HTTP
API. It supports metadata ingestion, batch upserts, filtered search, and the
`l2`, `cosine`, and `inner_product` metrics.

```python
from lumenvec_client import LumenVecClient

client = LumenVecClient("http://localhost:19190")
client.upsert("doc-1", [1.0, 0.0], {"tenant": "acme"})
hits = client.search([1.0, 0.0], k=10, metadata={"tenant": "acme"}, metric="cosine")
print(hits)
```
