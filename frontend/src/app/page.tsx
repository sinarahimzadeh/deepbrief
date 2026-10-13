import { BackendStatus } from "@/components/backend-status";

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#eef7ff_0,#f7f9fc_38%,#ffffff_72%)] px-6 py-8 text-slate-950 sm:px-10">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col">
        <nav className="flex items-center justify-between border-b border-slate-200/80 pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-slate-950 text-sm font-bold text-white shadow-sm">
              DB
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight">DeepBrief</p>
              <p className="text-xs text-slate-500">Multi-agent research</p>
            </div>
          </div>
          <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-medium text-slate-600 shadow-sm">
            Foundation setup
          </span>
        </nav>

        <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="mb-5 inline-flex rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
              Step 1 of the build
            </p>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.05] tracking-[-0.045em] text-slate-950 sm:text-6xl">
              Research that shows its work.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              DeepBrief will coordinate a supervisor, parallel researchers, a
              writer, and a citation verifier to produce evidence-grounded
              reports with OpenAI or Gemini.
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white/85 p-7 shadow-[0_24px_70px_-32px_rgba(15,23,42,0.35)] backdrop-blur">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">
              System check
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">
              Frontend is running
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              This page now checks whether the FastAPI service is reachable.
            </p>
            <BackendStatus />
          </div>
        </section>

        <footer className="border-t border-slate-200/80 pt-5 text-sm text-slate-500">
          Next: provider switching, research agents, and grounded reports.
        </footer>
      </div>
    </main>
  );
}

