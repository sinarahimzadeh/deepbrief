from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ResearchJobStatus = Literal["queued", "running", "completed", "failed"]
ResearchStage = Literal[
    "queued",
    "supervisor",
    "researchers",
    "writing",
    "verifying",
    "completed",
    "failed",
]
ResearchAgentStatus = Literal["waiting", "searching", "analyzing", "completed", "failed"]
WorkflowStepStatus = Literal[
    "waiting",
    "working",
    "completed",
    "completed_with_warnings",
    "failed",
]


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


class ResearchSource(BaseModel):
    source_key: str = Field(pattern=r"^R[1-3]S[1-5]$")
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=8, max_length=2000)
    domain: str = Field(min_length=1, max_length=255)
    snippet: str = Field(min_length=1, max_length=4000)
    query: str = Field(min_length=1, max_length=300)
    score: float | None = Field(default=None, ge=0, le=1)
    published_date: str | None = None


class ResearchFinding(BaseModel):
    statement: str = Field(min_length=10, max_length=1000)
    source_keys: list[str] = Field(min_length=1, max_length=5)

    @field_validator("statement")
    @classmethod
    def normalize_statement(cls, value: str) -> str:
        return " ".join(value.split())


class ResearcherSynthesis(BaseModel):
    summary: str = Field(min_length=20, max_length=1500)
    findings: list[ResearchFinding] = Field(min_length=1, max_length=8)


class ResearcherResult(BaseModel):
    index: int = Field(ge=1, le=3)
    title: str = Field(min_length=3, max_length=100)
    summary: str = Field(min_length=20, max_length=1500)
    findings: list[ResearchFinding] = Field(min_length=1, max_length=8)
    sources: list[ResearchSource] = Field(min_length=1, max_length=5)


class ReportSection(BaseModel):
    heading: str = Field(min_length=3, max_length=120)
    content: str = Field(min_length=40, max_length=5000)


class ReportDraft(BaseModel):
    title: str = Field(min_length=5, max_length=160)
    executive_summary: str = Field(min_length=50, max_length=2000)
    sections: list[ReportSection] = Field(min_length=2, max_length=6)
    conclusion: str = Field(min_length=40, max_length=2000)


ClaimSupport = Literal["supported", "weak", "unsupported"]


class ClaimVerification(BaseModel):
    claim: str = Field(min_length=10, max_length=1000)
    source_keys: list[str] = Field(min_length=1, max_length=5)
    status: ClaimSupport
    explanation: str = Field(min_length=10, max_length=1000)


class VerificationResult(BaseModel):
    overall_status: Literal["passed", "completed_with_warnings"]
    summary: str = Field(min_length=20, max_length=1000)
    claims: list[ClaimVerification] = Field(min_length=1, max_length=20)
    warnings: list[str] = Field(default_factory=list, max_length=10)


class WorkflowStepProgress(BaseModel):
    status: WorkflowStepStatus = "waiting"
    progress_message: str


class ResearchAgentProgress(BaseModel):
    index: int = Field(ge=1, le=3)
    title: str = Field(min_length=3, max_length=100)
    status: ResearchAgentStatus = "waiting"
    progress_message: str = "Waiting for the supervisor"
    sources_found: int = Field(default=0, ge=0, le=5)


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
    agents: list[ResearchAgentProgress] = Field(default_factory=list)
    researcher_results: list[ResearcherResult] = Field(default_factory=list)
    writer: WorkflowStepProgress = Field(
        default_factory=lambda: WorkflowStepProgress(
            progress_message="Waiting for the researchers"
        )
    )
    verifier: WorkflowStepProgress = Field(
        default_factory=lambda: WorkflowStepProgress(
            progress_message="Waiting for the report"
        )
    )
    report: ReportDraft | None = None
    verification: VerificationResult | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
