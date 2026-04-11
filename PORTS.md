# Port Allocation — Project 06: Portfolio AI Agents

> All host-exposed ports are globally unique across all 16 projects so every project can run simultaneously. See `../PORT-MAP.md` for the full map.

## Current Assignments

| Service | Host Port | Container Port | File |
|---------|-----------|---------------|------|
| Chainlit UI | **3060** | 3060 | docker-compose.dev.yml |
| Agent API (FastAPI) | **8060** | 8000 | docker-compose.dev.yml |
| Qdrant HTTP | **6333** | 6333 | docker-compose.dev.yml |
| Qdrant gRPC | **6334** | 6334 | docker-compose.dev.yml |

> Note: Chainlit runs on port 3060 inside the container (configured via `--port 3060` in the start command). This is intentional — do not change to 3000.

## Allowed Range for New Services

If you need to add a new service to this project, pick from these ranges **only**:

| Type | Allowed Host Ports |
|------|--------------------|
| Frontend / UI | `3060 – 3069` |
| Backend / API | `8060 – 8069` |
| PostgreSQL | Not assigned. If needed, request an assignment in `../PORT-MAP.md`. |
| Redis | Not assigned. If needed, request an assignment in `../PORT-MAP.md`. |

Available slots: `3061-3069`, `8061-8069`.

## Do Not Use

Every port outside the ranges above is reserved by another project. Always check `../PORT-MAP.md` before picking a port.

Key ranges already taken:
- `3050-3059 / 8050-8059` → Project 05
- `3070-3079 / 8070-8079` → Project 07
- `6333-6334` → Qdrant (this project)
- `6379-6385` → Projects 02, 05, 10, 12, 13, 15, 16 Redis
- `5432-5439` → Projects 02-05, 11-13, 15 PostgreSQL
