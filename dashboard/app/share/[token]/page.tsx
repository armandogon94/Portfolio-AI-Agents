/**
 * Public read-only share page (slice-27).
 *
 * Server-renders the FastAPI /share/{token} response so the prospect
 * gets a single fetch without CORS or client-side EventSource.
 * The backend enforces HMAC verification + 7-day TTL.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";

export default async function SharePage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const resp = await fetch(`${API_URL}/share/${token}`, { cache: "no-store" });

  if (resp.status === 410) {
    return <Expired />;
  }
  if (resp.status === 403) {
    return <Forbidden />;
  }
  if (resp.status === 404) {
    return <Missing />;
  }
  if (!resp.ok) {
    return <Failed status={resp.status} />;
  }

  const html = await resp.text();
  return (
    <main className="flex flex-1 flex-col bg-zinc-50 px-6 py-10 font-sans dark:bg-zinc-950">
      <div
        className="mx-auto w-full max-w-4xl rounded-md border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
        // The backend HTML is trusted (it's our own template, server-rendered
        // with autoescape). CSP on the backend route forbids scripts anyway.
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </main>
  );
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
