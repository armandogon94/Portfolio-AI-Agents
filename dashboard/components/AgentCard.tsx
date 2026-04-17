"use client";

import { motion, useReducedMotion } from "framer-motion";

import { AgentIcon } from "@/components/AgentIcon";
import { StateChip } from "@/components/StateChip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentRunState, AgentStateEvent } from "@/lib/types";

export interface AgentCardProps {
  role: string;
  state: AgentRunState;
  currentDetail: string;
  log: AgentStateEvent[];
}

function prettyRole(role: string): string {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function AgentCard({ role, state, currentDetail, log }: AgentCardProps) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      layout
      transition={{ duration: reduced ? 0 : 0.2, ease: "easeOut" }}
      data-testid={`agent-card-${role}`}
      className="w-full"
    >
      <Card className="border-zinc-200/80 shadow-sm transition-shadow hover:shadow dark:border-zinc-800">
        <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/15 to-violet-500/15 text-indigo-700 ring-1 ring-indigo-200/60 dark:text-indigo-300 dark:ring-indigo-500/30">
              <AgentIcon role={role} className="h-4 w-4" />
            </span>
            <CardTitle className="truncate text-sm font-semibold">
              {prettyRole(role)}
            </CardTitle>
          </div>
          <StateChip state={state} />
        </CardHeader>
        <CardContent className="space-y-2 pt-0">
          {currentDetail ? (
            <p className="line-clamp-2 text-xs text-zinc-600 dark:text-zinc-400">
              {currentDetail}
            </p>
          ) : null}
          {log.length > 0 ? (
            <details className="text-[11px] text-zinc-500">
              <summary className="cursor-pointer select-none font-medium uppercase tracking-wide text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
                {log.length} step{log.length === 1 ? "" : "s"}
              </summary>
              <ul className="mt-2 space-y-1 border-l border-zinc-200 pl-2 dark:border-zinc-800">
                {log.slice(-8).map((entry, idx) => (
                  <li key={`${entry.ts}-${idx}`} className="flex gap-1.5">
                    <span className="font-mono text-[10px] text-zinc-400">
                      {entry.state}
                    </span>
                    {entry.detail ? (
                      <span className="truncate">— {entry.detail}</span>
                    ) : null}
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
