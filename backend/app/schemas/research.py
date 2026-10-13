from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ResearchJobStatus = Literal["queued", "running", "completed", "failed"]
ResearchStage = Literal["queued", "supervisor", "plan_ready", "failed"]


class ResearchRequest(BaseModel):
    question: str = Field(min_length=10, max_length=2000)
    max_sources: int = Field(default=12, ge=3, le=15)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        question = " ".join(value.split())
        if len(question) < 10:
            raise ValueError("Question must contain at least 10 characters")
        return question


class ResearchAssignment(BaseModel):
    index: int = Field(ge=1, le=3)
    title: str = Field(min_length=3, max_length=100)
    objective: str = Field(min_length=10, max_length=600)
    search_queries: list[str] = Field(min_length=2, max_length=4)

    @field_validator("title", "objective")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("search_queries")
    @classmethod
    def normalize_queries(cls, value: list[str]) -> list[str]:
        queries = [" ".join(query.split()) for query in value if query.strip()]
        if len(queries) < 2:
            raise ValueError("Each assignment requires at least two search queries")
        return queries


class ResearchPlan(BaseModel):
    assignments: list[ResearchAssignment] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_assignments(self) -> "ResearchPlan":
        indexes = {assignment.index for assignment in self.assignments}
        if indexes != {1, 2, 3}:
            raise ValueError("Assignments must use indexes 1, 2, and 3")

        titles = {assignment.title.casefold() for assignment in self.assignments}
        if len(titles) != 3:
            raise ValueError("Assignment titles must be unique")
        return self


class ResearchJobCreated(BaseModel):
    id: str
    status: ResearchJobStatus
    created_at: datetime


class ResearchJobDetail(BaseModel):
    id: str
    question: str
    max_sources: int
    status: ResearchJobStatus
    current_stage: ResearchStage
    assignments: list[ResearchAssignment] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
