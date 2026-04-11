from pydantic import BaseModel, Field


class CrewRequest(BaseModel):
    topic: str = Field(..., description="The topic for the crew to research and analyze")
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
    status: str = "healthy"
    llm_provider: str
    embedding_mode: str
    environment: str


class IngestRequest(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content to ingest")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")


class IngestResponse(BaseModel):
    doc_id: str
    status: str = "ingested"


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=20, description="Max results to return")


class SearchResponse(BaseModel):
    query: str
    results: list[dict]
    count: int


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
