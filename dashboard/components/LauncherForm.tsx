"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiClient } from "@/lib/api";
import type { WorkflowInfo } from "@/lib/types";

const DOMAINS = [
  "general",
  "healthcare",
  "finance",
  "real_estate",
  "legal",
  "education",
  "engineering",
];

export default function LauncherForm() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<WorkflowInfo[]>([]);
  const [workflow, setWorkflow] = useState<string>("research_report");
  const [domain, setDomain] = useState<string>("general");
  const [topic, setTopic] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    apiClient
      .listWorkflows()
      .then((list) => {
        if (!active) return;
        setWorkflows(list);
        if (list.length && !list.some((w) => w.name === workflow)) {
          setWorkflow(list[0].name);
        }
      })
      .catch((err) => {
        if (!active) return;
        setError(`Failed to load workflows: ${err.message}`);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedWorkflow = workflows.find((w) => w.name === workflow);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const trimmed = topic.trim();
    if (!trimmed) {
      setError("Topic is required.");
      return;
    }
    setSubmitting(true);
    try {
      const { task_id } = await apiClient.runCrew({
        topic: trimmed,
        domain: domain === "general" ? null : domain,
        workflow,
      });
      router.push(`/runs/${task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-2xl border-zinc-200/80 shadow-sm dark:border-zinc-800">
      <CardHeader className="border-b border-zinc-100 dark:border-zinc-800">
        <CardTitle className="text-lg">Launch a crew</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={onSubmit} className="flex flex-col gap-6" noValidate>
          <div className="flex flex-col gap-2">
            <Label htmlFor="workflow">Workflow</Label>
            <Select
              value={workflow}
              onValueChange={(v) => v && setWorkflow(v)}
            >
              <SelectTrigger id="workflow">
                <SelectValue placeholder="Pick a workflow" />
              </SelectTrigger>
              <SelectContent>
                {workflows.map((w) => (
                  <SelectItem key={w.name} value={w.name}>
                    <span className="font-medium">{w.name}</span>
                    <span className="ml-2 text-xs text-zinc-500">
                      {w.process}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedWorkflow ? (
              <motion.div
                layoutId={`wf-${selectedWorkflow.name}`}
                className="mt-1 rounded-md border border-zinc-100 bg-zinc-50/60 p-3 text-xs leading-relaxed text-zinc-600 dark:border-zinc-800 dark:bg-zinc-800/30 dark:text-zinc-400"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                    {selectedWorkflow.process}
                  </span>
                  <span className="text-[11px] text-zinc-400">
                    {selectedWorkflow.agent_roles.length} agents ·{" "}
                    {selectedWorkflow.task_names.length} tasks
                  </span>
                </div>
                {selectedWorkflow.description}
              </motion.div>
            ) : null}
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="domain">Domain</Label>
            <Select value={domain} onValueChange={(v) => v && setDomain(v)}>
              <SelectTrigger id="domain">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DOMAINS.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="topic">Topic</Label>
            <Input
              id="topic"
              placeholder="e.g. AI in healthcare"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          {error ? (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          ) : null}

          <Button type="submit" disabled={submitting} className="self-start">
            {submitting ? "Launching…" : "Launch"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
