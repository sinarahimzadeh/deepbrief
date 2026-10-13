import { ResearchForm } from "@/components/research-form";

const benefits = [
  {
    title: "Parallel investigation",
    description: "Three focused researchers explore different sides of the question at once.",
    icon: "01",
  },
  {
    title: "Evidence you can inspect",
    description: "Important claims stay connected to their original web sources.",
    icon: "02",
  },
  {
    title: "A final verification pass",
    description: "A dedicated verifier checks citation coverage before the brief is finished.",
    icon: "03",
  },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#f7f9fc] px-5 py-6 text-slate-950 sm:px-10 sm:py-8">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[36rem] bg-[radial-gradient(circle_at_18%_5%,rgba(191,219,254,0.5),transparent_36%),radial-gradient(circle_at_88%_18%,rgba(224,231,255,0.55),transparent_32%)]" />
      <div className="relative mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl flex-col">
        <nav className="flex items-center justify-between border-b border-slate-200/80 pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-slate-950 text-sm font-bold text-white shadow-lg shadow-slate-950/15">
              DB
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight">DeepBrief</p>
              <p className="text-xs text-slate-500">Multi-agent research</p>
            </div>
          </div>
          <span className="rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur">
            Evidence-first research
          </span>
        </nav>

        <section className="grid flex-1 items-center gap-12 py-14 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
          <div className="max-w-2xl">
            <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-white/70 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm backdrop-blur">
              <span className="size-2 rounded-full bg-blue-600" />
              Multi-agent research workspace
            </p>
            <h1 className="text-5xl font-semibold leading-[1.03] tracking-[-0.05em] text-slate-950 sm:text-6xl lg:text-7xl">
              Multi-agent research with verifiable sources.
            </h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-slate-600">
              DeepBrief plans the investigation, sends three researchers in
              parallel, and returns one clear brief with evidence behind every
              important claim.
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {benefits.map((benefit) => (
                <div
                  className="rounded-2xl border border-white/80 bg-white/55 p-4 shadow-sm backdrop-blur"
                  key={benefit.title}
                >
                  <span className="font-mono text-xs font-semibold text-blue-600">
                    {benefit.icon}
                  </span>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    {benefit.title}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {benefit.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-white bg-white/90 p-6 shadow-[0_32px_90px_-38px_rgba(15,23,42,0.4)] backdrop-blur sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">
              New research brief
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-[-0.025em] sm:text-3xl">
              What do you want to investigate?
            </h2>
            <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
              Be specific about the decision, comparison, or topic you need to
              understand.
            </p>
            <ResearchForm />
          </div>
        </section>

        <footer className="flex flex-col gap-2 border-t border-slate-200/80 py-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>DeepBrief · Research that shows its work</span>
          <span>Plan · Investigate · Verify</span>
        </footer>
      </div>
    </main>
  );
}

