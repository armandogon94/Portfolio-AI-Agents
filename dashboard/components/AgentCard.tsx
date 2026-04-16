"use client";

import { motion, useReducedMotion } from "framer-motion";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateChip } from "@/components/StateChip";
import type { AgentRunState, AgentStateEvent } from "@/lib/types";

export interface AgentCardProps {
  role: string;
  state: AgentRunState;
  currentDetail: string;
  log: AgentStateEvent[];
}

export function AgentCard({ role, state, currentDetail, log }: AgentCardProps) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      layout
      transition={{ duration: reduced ? 0 : 0.2 }}
      data-testid={`agent-card-${role}`}
      className="w-full"
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-base font-semibold capitalize">
            {role}
          </CardTitle>
          <StateChip state={state} />
        </CardHeader>
        <CardContent className="space-y-2 pt-0">
          {currentDetail ? (
            <p className="text-sm text-zinc-700 dark:text-zinc-300">
              {currentDetail}
            </p>
          ) : null}
          {log.length > 0 ? (
            <details className="text-xs text-zinc-500">
              <summary className="cursor-pointer select-none">
                {log.length} step{log.length === 1 ? "" : "s"}
              </summary>
              <ul className="mt-2 space-y-1">
                {log.slice(-8).map((entry, idx) => (
                  <li key={`${entry.ts}-${idx}`}>
                    <span className="font-mono">{entry.state}</span>
                    {entry.detail ? ` — ${entry.detail}` : ""}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}
