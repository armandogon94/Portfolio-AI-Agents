from pydantic import BaseModel, Field


class CrewRequest(BaseModel):
    topic: str = Field(..., max_length=500, description="The topic for the crew to research and analyze")
    domain: str | None = Field(
        None,
        description="Industry domain (healthcare, finance, real_estate). None for general.",
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


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
