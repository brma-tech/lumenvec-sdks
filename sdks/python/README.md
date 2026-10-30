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

## Langflow preparation

An optional Langflow provider integration is proposed in
[langflow#16070](https://github.com/langflow-ai/langflow/issues/16070).
It is not yet an available or approved Langflow component.

The isolated [RAG document contract probe](probe_rag_contract.py) verifies whether
a server can return document text and structured metadata, not just vector IDs.
The published Community v0.3.0-rc.1 Windows binary currently fails that document
recovery requirement. See [readiness findings and next steps](../../../docs/langflow-readiness.md).
No paid embedding provider is needed for the probe or its unit tests.
