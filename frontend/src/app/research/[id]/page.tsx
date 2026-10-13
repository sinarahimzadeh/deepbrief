import Link from "next/link";
import { Suspense } from "react";

import { ResearchProgress } from "@/components/research-progress";

async function ResearchJob({
  params,
}: {
  params: PageProps<"/research/[id]">["params"];
}) {
  const { id } = await params;
  return <ResearchProgress jobId={id} />;
}

function ResearchFallback() {
  return (
    <div className="space-y-4" aria-label="Loading research job">
      <div className="h-36 animate-pulse rounded-3xl bg-slate-200/70" />
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((item) => (
          <div className="h-52 animate-pulse rounded-2xl bg-slate-200/60" key={item} />
        ))}
      </div>
    </div>
  );
}

export default function ResearchPage(props: PageProps<"/research/[id]">) {
  return (
    <main className="min-h-screen bg-[#f7f9fc] px-5 py-6 text-slate-950 sm:px-10 sm:py-8">
      <div className="mx-auto max-w-7xl">
        <nav className="mb-10 flex items-center justify-between border-b border-slate-200 pb-5">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid size-10 place-items-center rounded-xl bg-slate-950 text-sm font-bold text-white shadow-lg shadow-slate-950/15">
              DB
            </span>
            <span>
              <span className="block text-lg font-semibold tracking-tight">DeepBrief</span>
              <span className="block text-xs text-slate-500">Research workspace</span>
            </span>
          </Link>
          <Link
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300"
            href="/"
          >
            New question
          </Link>
        </nav>

        <Suspense fallback={<ResearchFallback />}>
          <ResearchJob params={props.params} />
        </Suspense>
      </div>
    </main>
  );
}
