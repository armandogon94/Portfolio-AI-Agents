/**
 * Browser-side client for the FastAPI backend (slice-20b, DEC-26b).
 * Calls FastAPI directly — no BFF. API key is optional and only attached
 * when NEXT_PUBLIC_API_KEY is set at build time.
 */

import type {
  CrewRunRequest,
  CrewRunResponse,
  RunHistoryResponse,
  WorkflowInfo,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

function headers(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  return h;
}

async function asJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const detail = await resp.text().catch(() => resp.statusText);
    throw new Error(`API ${resp.status}: ${detail}`);
  }
  return (await resp.json()) as T;
}

export const apiClient = {
  apiUrl: API_URL,

  async listWorkflows(): Promise<WorkflowInfo[]> {
    const resp = await fetch(`${API_URL}/workflows`, { headers: headers() });
    return asJson<WorkflowInfo[]>(resp);
  },

  async listHistory(limit = 20): Promise<RunHistoryResponse> {
    const resp = await fetch(
      `${API_URL}/crew/history?limit=${limit}`,
      { headers: headers() },
    );
    return asJson<RunHistoryResponse>(resp);
  },

  async runCrew(body: CrewRunRequest): Promise<CrewRunResponse> {
    const resp = await fetch(`${API_URL}/crew/run`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    return asJson<CrewRunResponse>(resp);
  },
};
