"""Probe an isolated engine for the document contract required by RAG adapters.

No model credentials are used. The engine is always started with fresh temporary
storage, a random API key and a free port. Existing services are never contacted.
Exit 2 means vector operations worked but a complete document cannot be recovered.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time

from lumenvec_client import LumenVecClient, LumenVecError


CONTENT_KEY = "langchain_page_content"
METADATA_KEY = "langchain_metadata_json"


def can_restore_document(payload: object, text: str, metadata: dict) -> bool:
    """Require both text and structured metadata, not just vector coordinates."""
    if not isinstance(payload, dict):
        return False
    stored = payload.get("metadata")
    if not isinstance(stored, dict) or stored.get(CONTENT_KEY) != text:
        return False
    try:
        return json.loads(stored.get(METADATA_KEY, "")) == metadata
    except (TypeError, ValueError):
        return False


def stop_engine(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def start_engine(binary: Path, directory: Path, port: int, api_key: str, log):
    environment = os.environ.copy()
    # Do not inherit cluster membership, telemetry, TLS or production storage
    # overrides from a developer's shell. This probe owns its complete config.
    for key in list(environment):
        if key.startswith("VECTOR_DB_"):
            del environment[key]
    environment.update({
        "VECTOR_DB_PROTOCOL": "http",
        "VECTOR_DB_PORT": str(port),
        "VECTOR_DB_SNAPSHOT_PATH": str(directory / "snapshot.json"),
        "VECTOR_DB_WAL_PATH": str(directory / "wal.log"),
        "VECTOR_DB_VECTOR_PATH": str(directory / "vectors"),
        "VECTOR_DB_VECTOR_STORE": "memory",
        "VECTOR_DB_SEARCH_MODE": "exact",
        "VECTOR_DB_API_KEY": api_key,
        "VECTOR_DB_SECURITY_AUTH_ENABLED": "true",
        "VECTOR_DB_SECURITY_API_KEY": api_key,
    })
    process = subprocess.Popen(
        [str(binary)], cwd=directory, env=environment, stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    client = LumenVecClient(f"http://127.0.0.1:{port}", api_key, timeout=2)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("Probe engine exited before readiness")
            try:
                client.health()
                return process, client
            except LumenVecError:
                time.sleep(0.1)
        raise RuntimeError("Probe engine readiness timed out")
    except BaseException:
        stop_engine(process)
        raise


def probe(binary: Path) -> dict:
    binary = binary.resolve(strict=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="lumenvec-rag-contract-") as temporary:
        directory = Path(temporary)
        with (directory / "engine.log").open("wb") as log:
            process, client = start_engine(binary, directory, port, secrets.token_hex(24), log)
            try:
                document_id = "langflow-contract-document"
                namespace = "langflow-contract-a"
                text = "LumenVec document contract: informações com fontes."
                metadata = {"source": "contract.md", "page": 2, "tags": ["rag", "test"]}
                values = [1.0, 0.0, 0.0]
                client.upsert(document_id, values, {
                    CONTENT_KEY: text,
                    METADATA_KEY: json.dumps(metadata, ensure_ascii=False),
                }, namespace=namespace)
                fetched = client.get(document_id)
                hits = client.search(values, k=1, namespace=namespace, metric="l2")
                other_hits = client.search(values, k=1, namespace="langflow-contract-b", metric="l2")
                hit = hits[0] if isinstance(hits, list) and hits else None
                vector_ok = isinstance(fetched, dict) and fetched.get("id") == document_id
                search_ok = isinstance(hit, dict) and hit.get("id") == document_id
                result = {
                    "vector_round_trip": vector_ok,
                    "search_returns_expected_id": search_ok,
                    "namespace_excludes_other_documents": not other_hits,
                    "get_response_keys": sorted(fetched) if isinstance(fetched, dict) else [],
                    "search_hit_keys": sorted(hit) if isinstance(hit, dict) else [],
                    "document_restorable_via_get": can_restore_document(fetched, text, metadata),
                    "document_restorable_via_search": can_restore_document(hit, text, metadata),
                }
                result["document_round_trip_supported"] = bool(
                    vector_ok and search_ok and not other_hits and (
                        result["document_restorable_via_get"] or result["document_restorable_via_search"]
                    )
                )
                if not vector_ok or not search_ok or other_hits:
                    raise RuntimeError(f"Basic vector/namespace contract failed: {result}")
                return result
            finally:
                stop_engine(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.binary)
    print(json.dumps(result, indent=2))
    return 0 if result["document_round_trip_supported"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
