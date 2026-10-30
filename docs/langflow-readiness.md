# Langflow integration readiness — 2026-10-30

## Coordination

Upstream proposal: https://github.com/langflow-ai/langflow/issues/16070

The proposal asks maintainers about acceptance, bundle placement, dependencies
and the active release-candidate target. No Langflow implementation PR, official
integration or default-install availability is claimed.

## Reproducible contract probe

The Python SDK was exercised against the published Windows AMD64 Community
v0.3.0-rc.1 executable. The downloaded archive was verified against the release's
SHA256SUMS.txt. This is an actual HTTP test, not a mocked server or model call.

The test started its own engine process with a fresh temporary working directory,
separate snapshot/WAL paths, a free port, exact search and a randomly generated
API key. It inserted a synthetic document containing Unicode text and JSON-encoded
structured source metadata. Existing application data and running services were
not used. The probe cleans up its process and temporary storage.

Observed result:

```json
{
  "vector_round_trip": true,
  "search_returns_expected_id": true,
  "namespace_excludes_other_documents": true,
  "get_response_keys": ["id", "values"],
  "search_hit_keys": ["distance", "id"],
  "document_restorable_via_get": false,
  "document_restorable_via_search": false,
  "document_round_trip_supported": false
}
```

Accepting metadata in an upsert does not prove that a document can be recovered.
The inspected tagged `GetVectorHandler` returns ID/values, and the measured
search response returns ID/distance. Neither exposes stored text/source metadata
to this SDK. Therefore an engine-only document adapter is not ready for Langflow.
Restart durability of document recovery was not tested because the payload cannot
be retrieved even before restart. Namespace filtering is not an authorization or
tenant-isolation guarantee.

## Recommended next dependency

Agree an additive document-payload retrieval contract in the engine, for example
an opt-in metadata field on vector retrieval/search. Review authentication,
response-size limits, namespace behavior and compatibility before implementation.
The integration should then serialize document text and structured metadata in a
documented string-valued envelope and verify recovery after restart.

An explicitly managed external document store is an alternative design, but adds
deployment, persistence and synchronization requirements. Do not silently use a
process-local dictionary or developer-local JSON file as a replacement: flows
running in a different process or container would lose access to the documents.

After that prerequisite, proceed with SDK packaging, a LangChain-compatible
adapter and the Langflow bundle/component at the location agreed upstream. Follow
Langflow connector URL protections rather than bypassing them for local endpoints.

## Run locally

Download a release executable and verify its archive checksum first. Do not use
an executable from an untrusted source. Python 3.10+ is sufficient for the probe;
no LangChain dependency or paid model API is required.

```bash
python -m pip install pytest
python -m pytest sdks/python
python sdks/python/probe_rag_contract.py --binary /path/to/lumenvec
```

Exit code 0 means the checked document contract is available. Exit code 2 means
basic vector/namespace checks succeeded but text/metadata recovery is missing.
Other errors fail the probe instead of reporting a successful integration.

The unit suite checks rejection of ID-only results, malformed/missing metadata,
wrong text and successful Unicode/nested-metadata reconstruction. CI runs these
offline tests. The real-engine probe is an explicit operator-run check, not part
of the default CI job and not an assertion that a Langflow component was tested.

## Source references

- https://github.com/langflow-ai/langflow/blob/main/CONTRIBUTING.md
- https://github.com/langflow-ai/langflow/blob/main/docs/docs/Contributing/contributing-bundles.mdx
- https://github.com/langflow-ai/langflow/blob/main/src/bundles/lfx-bundles/src/lfx_bundles/qdrant/qdrant.py
- https://github.com/langflow-ai/langflow/blob/main/docs/docs/Contributing/contributing-component-tests.mdx
- https://github.com/brma-tech/lumenvec-community/blob/v0.3.0-rc.1/internal/api/server.go
- https://github.com/brma-tech/lumenvec-community/releases/tag/v0.3.0-rc.1
