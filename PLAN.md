# AI Agent System
## CrewAI Multi-Agent Framework with RAG & Chainlit UI

---

## PROJECT OVERVIEW

Production-ready multi-agent system demonstrating:
- CrewAI framework (agent orchestration)
- Chainlit chat interface (user-friendly UI)
- Qdrant vector database (RAG/semantic search)
- Multiple specialized agents (research, analysis, writing)
- Industry-specific configurations (Healthcare, Finance, Real Estate, etc.)
- Tool integration (web search, document analysis, data retrieval)

**Why it matters:** Showcase of advanced AI capabilities. Demonstrates agentic AI patterns used in modern enterprise applications.

**Subdomain:** agents.305-ai.com

---

## TECH STACK

- **Agent Framework:** CrewAI 0.30+
- **Chat UI:** Chainlit 1.0+
- **Vector DB:** Qdrant 2.7+
- **Language Model:** Anthropic Claude (via API)
- **Backend:** FastAPI 0.104+
- **Vector Embeddings:** OpenAI or local model
- **Tools:** DuckDuckGo search, file reading, API calls

---

## ARCHITECTURE

```
User Interface (Chainlit)
        ↓
   CrewAI Agents
   ├── Research Agent (gather info)
   ├── Analysis Agent (process data)
   ├── Writing Agent (generate content)
   └── Validation Agent (quality check)
        ↓
   Tool Integration
   ├── Web Search (DuckDuckGo)
   ├── Document Retrieval (Qdrant RAG)
   ├── Data Analysis (Python)
   └── External APIs
        ↓
   Claude API (Intelligence)
```

---

## AGENT DEFINITIONS

### File: `agents/agents_config.py`

```python
from crewai import Agent, Task, Crew
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import ReadFileTool
from tools.document_retrieval import RagTool
from langchain.tools import Tool

# Initialize tools
search_tool = DuckDuckGoSearchRun()
read_file_tool = ReadFileTool()
rag_tool = RagTool()  # Custom Qdrant RAG

# RESEARCH AGENT
researcher = Agent(
    role="Research Analyst",
    goal="Find and summarize information about given topics",
    backstory="Expert researcher with deep knowledge across multiple domains",
    tools=[search_tool, rag_tool],
    verbose=True,
    allow_delegation=True
)

# ANALYSIS AGENT
analyst = Agent(
    role="Data Analyst",
    goal="Analyze information and extract key insights",
    backstory="Skilled analyst who uncovers patterns and trends",
    tools=[read_file_tool],
    verbose=True,
    allow_delegation=False
)

# WRITING AGENT
writer = Agent(
    role="Content Writer",
    goal="Create clear, engaging written content",
    backstory="Professional writer with strong communication skills",
    tools=[],
    verbose=True,
    allow_delegation=False
)

# VALIDATION AGENT
validator = Agent(
    role="Quality Assurance",
    goal="Ensure content accuracy and completeness",
    backstory="Meticulous reviewer focused on quality",
    tools=[],
    verbose=True,
    allow_delegation=False
)
```

### File: `agents/tasks_config.py`

```python
from crewai import Task

research_task = Task(
    description="Research the topic: {topic}",
    agent=researcher,
    expected_output="A comprehensive summary of findings with sources"
)

analysis_task = Task(
    description="Analyze the research findings and extract key insights",
    agent=analyst,
    expected_output="Key patterns, trends, and actionable insights"
)

writing_task = Task(
    description="Write a professional report based on the analysis",
    agent=writer,
    expected_output="Well-structured written report with clear recommendations"
)

validation_task = Task(
    description="Review the report for accuracy and completeness",
    agent=validator,
    expected_output="Quality assessment and any needed corrections"
)

# Create crew
crew = Crew(
    agents=[researcher, analyst, writer, validator],
    tasks=[research_task, analysis_task, writing_task, validation_task],
    verbose=True,
    process=Process.hierarchical,
    manager_agent=researcher
)
```

---

## RAG IMPLEMENTATION

### File: `tools/document_retrieval.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.tools import Tool
from typing import Optional

class RagTool:
    def __init__(self, collection_name: str = "documents"):
        self.client = QdrantClient(url="http://qdrant:6333")
        self.embeddings = OpenAIEmbeddings()
        self.collection_name = collection_name

    def ingest_document(self, doc_id: str, content: str):
        """Add document to vector database"""
        # Create embedding
        embedding = self.embeddings.embed_query(content)

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=hash(doc_id),
                    vector=embedding,
                    payload={"content": content, "doc_id": doc_id}
                )
            ]
        )

    def retrieve_similar(self, query: str, limit: int = 5) -> list:
        """Retrieve similar documents"""
        query_embedding = self.embeddings.embed_query(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )

        return [
            {
                "doc_id": hit.payload["doc_id"],
                "content": hit.payload["content"],
                "score": hit.score
            }
            for hit in results
        ]

    def to_tool(self) -> Tool:
        """Convert to LangChain tool"""
        return Tool(
            name="document_search",
            func=lambda query: str(self.retrieve_similar(query)),
            description="Search documents using semantic similarity"
        )
```

---

## CHAINLIT INTERFACE

### File: `chainlit_app.py`

```python
import chainlit as cl
from crewai import Crew
from agents.agents_config import researcher, analyst, writer, validator
from agents.tasks_config import crew

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("crew", crew)
    cl.user_session.set("messages", [])

@cl.on_message
async def on_message(message: cl.Message):
    crew = cl.user_session.get("crew")
    messages = cl.user_session.get("messages")

    # Append user message
    messages.append({"role": "user", "content": message.content})

    # Show thinking process
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Execute crew
        result = crew.kickoff(inputs={"topic": message.content})

        # Send final response
        msg.content = result
        await msg.update()

        # Store in session
        messages.append({"role": "assistant", "content": result})
        cl.user_session.set("messages", messages)

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()

@cl.on_chat_end
def on_chat_end():
    print("Chat ended")
```

---

## INDUSTRY-SPECIFIC CONFIGURATIONS

### File: `configs/healthcare_config.py`

```python
healthcare_system_prompt = """
You are an expert healthcare analyst with knowledge of:
- Medical terminology and diagnoses
- Healthcare regulations (HIPAA, FDA)
- Clinical research methodologies
- Healthcare data analysis
- Treatment protocols and best practices

When analyzing healthcare topics, consider:
- Evidence-based medicine
- Patient safety and ethics
- Regulatory compliance
- Cost-effectiveness
"""

healthcare_tools = [
    DuckDuckGoSearchRun(),  # Medical research
    RagTool(),  # Internal healthcare documents
    # Custom clinical data retrieval tool
]
```

### File: `configs/finance_config.py`

```python
finance_system_prompt = """
You are an expert financial analyst with knowledge of:
- Investment strategies and portfolio management
- Financial modeling and valuation
- Risk analysis and compliance
- Market trends and economic indicators
- Financial reporting standards

When analyzing financial topics, consider:
- Regulatory requirements (SEC, FINRA)
- Tax implications
- Market volatility
- Return on investment metrics
"""
```

### File: `configs/real_estate_config.py`

```python
real_estate_system_prompt = """
You are an expert real estate analyst with knowledge of:
- Property valuation and appraisal
- Market analysis and trends
- Investment strategies
- Construction and development
- Real estate law and regulations

When analyzing real estate topics, consider:
- Comparable market analysis (CMA)
- Property condition assessment
- Financing options
- Market cycles and timing
"""
```

---

## DOCKER COMPOSE

```yaml
qdrant:
  image: qdrant/qdrant:latest
  container_name: qdrant
  ports:
    - "127.0.0.1:6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
  networks:
    - backend
  restart: unless-stopped

agents-api:
  image: ghcr.io/armando/agents-api:latest
  depends_on:
    - qdrant
  environment:
    QDRANT_HOST: qdrant
    QDRANT_PORT: 6333
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  networks:
    - backend
    - frontend
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
  restart: unless-stopped
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.agents.rule=Host(`agents.305-ai.com`)"
    - "traefik.http.routers.agents.entrypoints=websecure"
    - "traefik.http.routers.agents.tls.certresolver=letsencrypt"
    - "traefik.http.services.agents.loadbalancer.server.port=8000"
```

---

## ESTIMATED TIMELINE

- **Agent Setup:** 3 hours
- **RAG Implementation:** 2.5 hours
- **Chainlit UI:** 2 hours
- **Industry Configs:** 2 hours
- **Testing:** 1.5 hours

**Total:** ~11 hours

---

**Agent System Version:** 1.0
**Status:** Production-ready
