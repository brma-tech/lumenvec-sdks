## Feature Request

Add a LumenVec vector-store integration as an optional provider bundle, subject
to the maintainers' preferred extension and packaging model.

I maintain LumenVec, an MIT-licensed vector database written in Go:

- Engine: https://github.com/brma-tech/lumenvec-community
- SDKs: https://github.com/brma-tech/lumenvec-sdks
- Current public engine prerelease: v0.3.0-rc.1

The proposed initial scope is document ingestion and similarity retrieval over
the HTTP API, using an externally managed LumenVec service and an embeddings
component supplied by the Langflow user. It would preserve document text and
source metadata, expose endpoint/API key/namespace/top-k, and provide explicit
timeouts and useful errors. It would not bundle the server executable or depend
on our separate LumenRAG application.

## Motivation

This would let users evaluate LumenVec as a self-hosted retrieval backend within
their existing Langflow flows, without replacing their document loaders,
embedding models or chat models. This request is for a usable integration, not
for a promotional listing or default installation requirement.

I did not find an existing LumenVec component or matching issue/PR in the current
repository search. I am validating the SDK and document round-trip contract
before proposing implementation: accepting metadata on ingestion is not enough
unless retrieval can also recover text and sources after a service restart.

## Your Contribution

I can implement and maintain the client/adapter, component, tests and
documentation. The planned verification includes deterministic offline
embeddings, an isolated engine integration test, namespace behavior, auth/error
handling, persistence/restart and a reproducible RAG example. No paid model API
would be needed for the basic integration tests.

Before opening an implementation PR, could you confirm:

1. Is a new optional vector-store provider integration welcome in the project?
2. Should it live in `lfx-bundles`, a standalone extension package, or another
   location? The bundle guide mentions `src/lfx/src/lfx/components`, while the
   current Qdrant implementation is under `src/bundles/lfx-bundles`.
3. Which active release-candidate branch should the PR target? I have read the
   contribution guide's instruction not to target `main`.
4. Are there additional dependency, compatibility or maintenance requirements
   for accepting a new vector-store provider?

I will follow the repository's vector-store component contracts, connector URL
security controls and component-test conventions, and keep the first PR focused.
