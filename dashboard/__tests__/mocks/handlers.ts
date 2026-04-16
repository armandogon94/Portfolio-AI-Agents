import { http, HttpResponse } from "msw";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";

export const handlers = [
  http.get(`${API}/workflows`, () =>
    HttpResponse.json([
      {
        name: "research_report",
        description: "Classic 4-agent research pipeline",
        process: "sequential",
        agent_roles: ["researcher", "analyst", "writer", "validator"],
        task_names: ["research", "analysis", "writing", "validation"],
        parallel_tasks: null,
        inputs_schema: { topic: "The subject to research" },
      },
    ]),
  ),

  http.get(`${API}/crew/history`, () =>
    HttpResponse.json({
      runs: [
        {
          task_id: "00000000-0000-0000-0000-000000000001",
          topic: "AI in healthcare",
          domain: "healthcare",
          result: "Final report...",
          duration_seconds: 42.1,
          created_at: "2026-04-16T10:00:00Z",
        },
        {
          task_id: "00000000-0000-0000-0000-000000000002",
          topic: "Renewable energy 2025",
          domain: null,
          result: "Another report...",
          duration_seconds: 31.4,
          created_at: "2026-04-16T09:00:00Z",
        },
        {
          task_id: "00000000-0000-0000-0000-000000000003",
          topic: "Crypto regulation",
          domain: "finance",
          result: "Regulatory summary...",
          duration_seconds: 55.0,
          created_at: "2026-04-16T08:00:00Z",
        },
      ],
      count: 3,
    }),
  ),

  http.post(`${API}/crew/run`, async () =>
    HttpResponse.json(
      { task_id: "new-task-id-from-msw", status: "pending" },
      { status: 202 },
    ),
  ),
];

export const emptyHistoryHandler = http.get(`${API}/crew/history`, () =>
  HttpResponse.json({ runs: [], count: 0 }),
);
