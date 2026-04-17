import RunView from "@/components/RunView";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <main className="flex flex-1 flex-col px-4 py-8 sm:px-6">
      <div className="mx-auto w-full max-w-7xl">
        <RunView taskId={id} />
      </div>
    </main>
  );
}
