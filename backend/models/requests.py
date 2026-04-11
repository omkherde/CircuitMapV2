"""
models/requests.py — Pydantic input models for CircuitMap API.
"""
from pydantic import BaseModel, field_validator
from enum import Enum


class QueryType(str, Enum):
    name = "name"
    smiles = "smiles"


class DemoScenario(str, Enum):
    alzheimers = "alzheimers"
    schizophrenia = "schizophrenia"
    depression = "depression"


class ValidateRequest(BaseModel):
    drug_query: str
    query_type: QueryType
    indication: str

    @field_validator('drug_query')
    @classmethod
    def drug_query_not_empty(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('drug_query must be at least 2 characters')
        return v

    @field_validator('indication')
    @classmethod
    def indication_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('indication must not be empty')
        return v
