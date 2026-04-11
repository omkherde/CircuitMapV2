"""
models/responses.py — Pydantic SSE event models and response shapes.
"""
from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class TraceEventType(str, Enum):
    agent_thought = "agent_thought"
    tool_call = "tool_call"
    tool_result = "tool_result"
    brain_map = "brain_map"
    overlap_score = "overlap_score"
    confidence_update = "confidence_update"
    report_ready = "report_ready"
    pdf_ready = "pdf_ready"
    error = "error"


class ValidateResponse(BaseModel):
    session_id: str
    stream_url: str
    mode: str = "live"


class HealthResponse(BaseModel):
    status: str = "ok"
    ahba_loaded: bool = False
    chroma_loaded: bool = False
    neurosynth_loaded: bool = False


class DemoResponse(BaseModel):
    session_id: str
    mode: str = "demo"
    events: list
    expression_map_url: str
    disease_map_url: str
