# LumenVec SDKs

Public HTTP and gRPC clients for [LumenVec Community](https://github.com/brma-tech/lumenvec-community). This repository contains client libraries, not the database server.

This update targets Community `v0.3.0-rc.1` (engine revision `ee2052930f95024305fb6be19a74acb34049893d`). The engine is a prerelease; compatibility here does not certify production upgrades or retrieval quality.

| Client | Location | Validation |
| --- | --- | --- |
| Go HTTP/gRPC | `pkg/client` | `go test ./...` |
| Python HTTP | `sdks/python` | `python -m pytest sdks/python/test_client.py` |
| JavaScript HTTP | `sdks/javascript` | `node sdks/javascript/index.test.mjs` |
| Rust HTTP | `sdks/rust` | `cargo test --locked --manifest-path sdks/rust/Cargo.toml` |

Import `github.com/brma-tech/lumenvec-sdks/pkg/client` in Go. The independent module uses patched gRPC 1.83.2. Generated protobuf contracts live in `api/proto` and retain upstream descriptor metadata; clients do not import server implementation packages.

HTTP defaults to port 19190; gRPC uses 19191 when enabled by the server. Configure API credentials in your client and use TLS for remote connections. See the individual [SDK guides](sdks/README.md).

Contract tests use fixtures. Validate your integration before upgrading a deployed application. Updating this repository does not publish packages to npm, PyPI or crates.io.
