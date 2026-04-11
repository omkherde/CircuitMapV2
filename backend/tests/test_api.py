"""
tests/test_api.py — FastAPI endpoint tests using TestClient.

Tests cover:
  - Health check
  - /api/validate returns session_id and stream_url
  - /api/demo/{scenario} validation (bad scenario → 422, missing cache → 404)
  - /api/maps path-traversal guard
  - /api/stream duplicate-consumer guard
  - /api/report path-traversal guard
"""
import os
import sys

# Ensure the backend package root is on the path when running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-placeholder")

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_returns_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "ahba_loaded" in body
    assert "chroma_loaded" in body
    assert "neurosynth_loaded" in body


# ── /api/validate ──────────────────────────────────────────────────────────────

def test_validate_returns_session_id(monkeypatch):
    """POST /api/validate should immediately return a session_id without running the agent."""
    import asyncio

    async def _fake_run(*args, **kwargs):
        pass

    monkeypatch.setattr("main._run_agent_for_session", _fake_run)

    resp = client.post(
        "/api/validate",
        json={"drug_query": "Donepezil", "query_type": "name", "indication": "Alzheimer's disease"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["stream_url"].startswith("/api/stream/")
    assert body["mode"] == "live"


def test_validate_rejects_short_query():
    resp = client.post(
        "/api/validate",
        json={"drug_query": "A", "query_type": "name", "indication": "Alzheimer's disease"},
    )
    assert resp.status_code == 422  # Pydantic min_length=2


def test_validate_rejects_empty_indication():
    resp = client.post(
        "/api/validate",
        json={"drug_query": "Donepezil", "query_type": "name", "indication": ""},
    )
    assert resp.status_code == 422


# ── /api/demo ──────────────────────────────────────────────────────────────────

def test_demo_invalid_scenario():
    """An unknown scenario should return 422 (FastAPI enum validation)."""
    resp = client.get("/api/demo/nonexistent")
    assert resp.status_code == 422


def test_demo_missing_cache(tmp_path, monkeypatch):
    """A valid scenario with no precomputed cache file should return 404."""
    monkeypatch.setenv("DEMO_CACHE_DIR", str(tmp_path))
    # Re-import to pick up the new env var inside the route handler
    import importlib
    import main as m
    monkeypatch.setattr(m, "DEMO_CACHE_DIR", str(tmp_path))

    resp = client.get("/api/demo/alzheimers")
    assert resp.status_code == 404


# ── /api/maps path-traversal guard ─────────────────────────────────────────────

def test_maps_rejects_traversal_session_id():
    resp = client.get("/api/maps/../etc/passwd/expression.png")
    # FastAPI will match the literal route or 404; what it must NOT do is serve a file
    assert resp.status_code in (400, 404, 422)


def test_maps_rejects_bad_map_type():
    resp = client.get("/api/maps/valid-session-id/secrets.png")
    # map_type is extracted from path before .png; "secrets" is not allowed
    assert resp.status_code == 400


def test_maps_rejects_invalid_session_id_chars():
    resp = client.get("/api/maps/../../expression.png")
    assert resp.status_code in (400, 404, 422)


# ── /api/stream duplicate consumer guard ───────────────────────────────────────

def test_stream_rejects_second_consumer(monkeypatch):
    """A session already being streamed should reject a second consumer with 409."""
    import asyncio

    async def _fake_run(*args, **kwargs):
        pass

    monkeypatch.setattr("main._run_agent_for_session", _fake_run)

    # Create a session
    resp = client.post(
        "/api/validate",
        json={"drug_query": "Tolcapone", "query_type": "name", "indication": "schizophrenia"},
    )
    session_id = resp.json()["session_id"]

    # Simulate a consumer already active
    from main import sessions
    sessions[session_id]["consumers"] = 1

    # Second consumer should be rejected
    resp2 = client.get(f"/api/stream/{session_id}")
    assert resp2.status_code == 409


# ── /api/report path-traversal guard ───────────────────────────────────────────

def test_report_rejects_traversal_session_id():
    resp = client.get("/api/report/../../../etc/passwd/download")
    assert resp.status_code in (400, 404, 422)


# ── correlation_service ────────────────────────────────────────────────────────

def test_correlation_cleanup():
    """cleanup_session_maps should only remove maps for the given session."""
    from services.correlation_service import store_parcellated_map, get_parcellated_map, cleanup_session_maps

    store_parcellated_map("sess_A_expression_HIF1A", {"hippocampus_L": 0.9})
    store_parcellated_map("sess_A_disease_alzheimer", {"hippocampus_L": 0.8})
    store_parcellated_map("sess_B_expression_SUV39H1", {"hippocampus_L": 0.5})

    cleanup_session_maps("sess_A")

    assert get_parcellated_map("sess_A_expression_HIF1A") is None
    assert get_parcellated_map("sess_A_disease_alzheimer") is None
    # sess_B maps must survive
    assert get_parcellated_map("sess_B_expression_SUV39H1") is not None


# ── chembl_service local fallbacks ─────────────────────────────────────────────

def test_chaetocin_primary_target_is_suv39h1():
    """Chaetocin's primary target must be SUV39H1 per PRD §4 Scenario 1."""
    from services.chembl_service import LOCAL_TARGET_FALLBACKS
    entry = LOCAL_TARGET_FALLBACKS["chaetocin"]
    assert entry["primary_target"] == "SUV39H1", (
        f"Expected SUV39H1 but got {entry['primary_target']}. "
        "PRD §4 Scenario 1 specifies SUV39H1 as the canonical Chaetocin target."
    )
    # HIF1A should be an off-target, not the primary
    off_target_genes = [ot["gene_name"] for ot in entry.get("off_targets", [])]
    assert "HIF1A" in off_target_genes, "HIF1A should appear as an off-target for Chaetocin"
