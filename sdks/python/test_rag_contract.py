import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from probe_rag_contract import CONTENT_KEY, METADATA_KEY, can_restore_document


@pytest.mark.parametrize("payload", [None, [], {}, {"id": "x", "distance": 0}, {"metadata": None}])
def test_vectors_and_ids_are_not_documents(payload):
    assert not can_restore_document(payload, "body", {"page": 1})


def test_document_restores_nested_metadata_and_unicode():
    metadata = {"source": "informações.md", "page": 2, "tags": ["a"], "nested": {"ok": True}}
    payload = {"metadata": {CONTENT_KEY: "conteúdo", METADATA_KEY: json.dumps(metadata)}}
    assert can_restore_document(payload, "conteúdo", metadata)


@pytest.mark.parametrize("encoded", [None, "broken-json", "{}", "[]"])
def test_missing_or_corrupted_metadata_is_not_success(encoded):
    payload = {"metadata": {CONTENT_KEY: "body", METADATA_KEY: encoded}}
    assert not can_restore_document(payload, "body", {"page": 1})


def test_wrong_document_content_is_not_success():
    payload = {"metadata": {CONTENT_KEY: "wrong", METADATA_KEY: '{"page": 1}'}}
    assert not can_restore_document(payload, "body", {"page": 1})
