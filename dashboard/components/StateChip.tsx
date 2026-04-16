import { Badge } from "@/components/ui/badge";
import type { AgentRunState } from "@/lib/types";

const LABELS: Record<AgentRunState, string> = {
  queued: "Queued",
  active: "Active",
  waiting_on_tool: "Tool",
  waiting_on_agent: "Waiting",
  completed: "Done",
  failed: "Failed",
};

const VARIANTS: Record<AgentRunState, "default" | "secondary" | "destructive" | "outline"> = {
  queued: "outline",
  active: "default",
  waiting_on_tool: "secondary",
  waiting_on_agent: "secondary",
  completed: "default",
  failed: "destructive",
};

export function StateChip({ state }: { state: AgentRunState }) {
  return <Badge variant={VARIANTS[state]}>{LABELS[state]}</Badge>;
}
