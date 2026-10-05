# SDK matrix

| SDK | Runtime | Contract check |
| --- | --- | --- |
| Go | Go 1.26.6+ | `go test ./...` from repository root |
| Python | Python 3.10+ | `python -m pytest sdks/python/test_client.py` |
| JavaScript | Node 18+ | `node sdks/javascript/index.test.mjs` |
| Rust | Rust 2021 | `cargo test --locked --manifest-path sdks/rust/Cargo.toml` |

Python, JavaScript and Rust target the versioned HTTP API. Go provides HTTP and gRPC clients. See each client README for method signatures.

The protobuf snapshot is copied without modifying its wire descriptor from Community revision `ee2052930f95024305fb6be19a74acb34049893d` (`v0.3.0-rc.1`). The Go module is independently buildable and contains no server runtime dependencies. Future updates must preserve wire compatibility and rerun all client tests.

Go clients should use a patched Go toolchain (1.26.6 or later in the 1.26 series). Rust's locked `h2` and `rustls` dependencies are updated to versions without current RustSec advisories; `cargo audit` reports a yanked `chacha20` crate warning but no known vulnerabilities.
