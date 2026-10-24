"""Pydantic schemas for the Existing Project Research Agent findings."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class RepositoryDetails(BaseModel):
    stars: int | str = "not found"
    license: str = "not found"
    language: str = "not found"
    last_update: str = "not found"
    archived: bool | str = "not found"


class Finding(BaseModel):
    name: str
    url: str
    platform: Literal["github", "huggingface"]
    kind: Literal["repository", "model", "dataset", "space"]
    problem_solved: str
    input_output: str
    dataset: str
    model_and_architecture: str
    method: str
    evaluation_and_results: str
    repository_details: RepositoryDetails
    reproducibility: str
    known_limitations: str
    field_sources: dict[str, str] = Field(
        default_factory=dict,
        description="Maps each field name to its source tag or 'not found'",
    )


class ProjectResearchFindings(BaseModel):
    session_id: str
    search_queries_run: list[str]
    findings: list[Finding] = Field(..., max_length=10)
    notes: str = ""
