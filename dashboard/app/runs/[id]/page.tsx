import RunView from "@/components/RunView";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <main className="flex flex-1 flex-col bg-zinc-50 px-6 py-10 font-sans dark:bg-zinc-950">
      <div className="mx-auto w-full max-w-6xl">
        <RunView taskId={id} />
      </div>
    </main>
  );
}
