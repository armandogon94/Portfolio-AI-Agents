/**
 * Public read-only share page (slice-27, slice-29d).
 *
 * Fetches GET /share/{token}?format=json on the client, hands the typed
 * payload to <ShareRunView/> (dual-pane graph + transcript with scrubber).
 * The HTML variant of /share/{token} still exists on the backend for curl
 * users / PDF rendering — this page opts into the JSON branch.
 *
 * Client-side fetch (vs RSC) is deliberate: the scrubber is purely
 * interactive, no SEO surface, and testing with Playwright route
 * interception only works when the request originates from the browser.
 */
"use client";

import { use, useEffect, useState } from "react";

import { ShareRunView, type SharePayload } from "@/components/ShareRunView";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";

type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; payload: SharePayload }
  | { kind: "error"; status: number };

export default function SharePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/share/${token}?format=json`, { cache: "no-store" })
      .then(async (resp) => {
        if (!active) return;
        if (!resp.ok) {
          setState({ kind: "error", status: resp.status });
          return;
        }
        const payload = (await resp.json()) as SharePayload;
        setState({ kind: "ok", payload });
      })
      .catch(() => {
        if (!active) return;
        setState({ kind: "error", status: 0 });
      });
    return () => {
      active = false;
    };
  }, [token]);

  if (state.kind === "loading") {
    return (
      <StatusCard title="Loading shared run…">
        Fetching the replay payload from the backend.
      </StatusCard>
    );
  }
  if (state.kind === "error") {
    if (state.status === 410) return <Expired />;
    if (state.status === 403) return <Forbidden />;
    if (state.status === 404) return <Missing />;
    return <Failed status={state.status} />;
  }
  return <ShareRunView payload={state.payload} />;
}

function Expired() {
  return (
    <StatusCard title="Share link expired">
      This link is older than 7 days. Ask the sender for a fresh one.
    </StatusCard>
  );
}

function Forbidden() {
  return (
    <StatusCard title="Invalid share link">
      The token doesn't match — it may have been altered, or the server's
      share secret was rotated.
    </StatusCard>
  );
}

function Missing() {
  return (
    <StatusCard title="Run not found">
      The run this link pointed to isn't available anymore.
    </StatusCard>
  );
}

function Failed({ status }: { status: number }) {
  return (
    <StatusCard title="Unable to load the share page">
      Backend returned HTTP {status}. Try again, or contact the sender.
    </StatusCard>
  );
}

function StatusCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-10">
      <div className="max-w-md rounded-md border border-zinc-200 bg-white p-6 text-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          {title}
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">{children}</p>
      </div>
    </main>
  );
}
