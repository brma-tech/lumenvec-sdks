# SDK matrix

| SDK | Runtime | Local contract check |
|---|---|---|
| Go | Go modules | `go test ./pkg/client ./tests/integration` |
| Python | Python 3.10+ | `pytest -q sdks/python/test_client.py` |
| JavaScript | Node 18+ | `node sdks/javascript/index.test.mjs` |
| Rust | Rust 2021 | `cargo test --manifest-path sdks/rust/Cargo.toml` |

All clients target the same `/v1` HTTP contract and support metadata plus the
L2, cosine, and inner-product metrics where the runtime implementation is
available.

## Contract provenance

The canonical public contract is versioned by
`api/contracts/contract-manifest.json`. SDK release tooling must consume the
bundle produced by `scripts/build-public-contract-bundle.py`; importing server
implementation packages or generating from unreviewed source files is
forbidden. The unified gate verifies source digests, the v1 compatibility
baseline, and this dependency boundary before SDK publication.
