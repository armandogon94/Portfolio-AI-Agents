from enum import Enum

from pydantic import BaseModel, Field


class AgentRunState(str, Enum):
    """Lifecycle states for an agent within a crew run (slice-19, DEC-16)."""

    QUEUED = "queued"
    ACTIVE = "active"
    WAITING_ON_TOOL = "waiting_on_tool"
    WAITING_ON_AGENT = "waiting_on_agent"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStateEvent(BaseModel):
    """A single state event for a crew run, streamed via SSE (slice-19)."""

    task_id: str = Field(..., description="Task ID this event belongs to")
    agent_role: str = Field(..., description="Role name of the agent emitting the event")
    state: str = Field(..., description="Current state (AgentRunState value)")
    detail: str = Field("", description="Human-readable detail (e.g., tool name)")
    ts: str = Field(..., description="ISO 8601 timestamp")


class CrewRequest(BaseModel):
    topic: str = Field(..., max_length=500, description="The topic for the crew to research and analyze")
    domain: str | None = Field(
        None,
        description="Industry domain (healthcare, finance, real_estate). None for general.",
    )
    workflow: str = Field(
        "research_report",
        max_length=64,
        description=(
            "Workflow name from GET /workflows. Defaults to 'research_report' "
            "for backward compat with v1-v3 callers (slice-21)."
        ),
    )
    webhook_url: str | None = Field(
        None,
        max_length=2048,
        description="Optional HTTPS URL to POST the result to when the task completes.",
    )


class CrewResponse(BaseModel):
    topic: str
    domain: str | None
    result: str
    status: str = "completed"


class HealthResponse(BaseModel):
    # Only expose status — provider/environment details are operational intelligence (I11)
    status: str = "healthy"


class IngestRequest(BaseModel):
    doc_id: str = Field(..., max_length=255, description="Unique document identifier")
    content: str = Field(..., max_length=100_000, description="Document content to ingest")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")


class IngestResponse(BaseModel):
    doc_id: str
    status: str = "ingested"


class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500, description="Search query")
    limit: int = Field(5, ge=1, le=20, description="Max results to return")


class SearchResponse(BaseModel):
    query: str
    results: list[dict]
    count: int


class CrewAsyncResponse(BaseModel):
    task_id: str
    status: str = "pending"


class TaskStatusResponse(BaseModel):
    task_id: str
    topic: str
    domain: str | None
    status: str
    result: str | None


class UrlIngestRequest(BaseModel):
    url: str = Field(..., max_length=2048, description="URL to fetch and ingest into RAG")
    doc_id: str | None = Field(None, max_length=255, description="Override doc ID (default: URL)")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")


class UrlIngestResponse(BaseModel):
    doc_id: str
    status: str = "ingested"
    char_count: int


class RunHistoryEntry(BaseModel):
    task_id: str
    topic: str
    domain: str | None
    result: str
    duration_seconds: float
    created_at: str


class RunHistoryResponse(BaseModel):
    runs: list[RunHistoryEntry]
    count: int


class WorkflowInfo(BaseModel):
    """Public shape of a registered workflow returned by GET /workflows (slice-21)."""

    name: str
    description: str
    process: str
    agent_roles: list[str]
    task_names: list[str]
    parallel_tasks: list[list[str]] | None = None
    inputs_schema: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
