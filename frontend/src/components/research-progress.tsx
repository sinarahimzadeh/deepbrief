"use client";

import { useEffect, useState } from "react";

type ResearchAssignment = {
  index: number;
  title: string;
  objective: string;
  search_queries: string[];
};

type ResearchAgent = {
  index: number;
  title: string;
  status: "waiting" | "searching" | "analyzing" | "completed" | "failed";
  progress_message: string;
  sources_found: number;
};

type ResearchSource = {
  source_key: string;
  title: string;
  url: string;
  domain: string;
  snippet: string;
};

type ResearcherResult = {
  index: number;
  title: string;
  summary: string;
  findings: { statement: string; source_keys: string[] }[];
  sources: ResearchSource[];
};

type ResearchJob = {
  id: string;
  question: string;
  max_sources: number;
  status: "queued" | "running" | "completed" | "failed";
  current_stage:
    | "queued"
    | "supervisor"
    | "researchers"
    | "research_complete"
    | "failed";
  assignments: ResearchAssignment[];
  agents: ResearchAgent[];
  researcher_results: ResearcherResult[];
  error: string | null;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const agentStatusStyles = {
  waiting: "bg-slate-100 text-slate-500",
  searching: "bg-blue-50 text-blue-700",
  analyzing: "bg-amber-50 text-amber-700",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-rose-50 text-rose-700",
} as const;

function getProgress(job: ResearchJob) {
  if (job.status === "queued") return 10;
  if (job.status === "failed" || job.status === "completed") return 100;
  if (job.current_stage === "supervisor") return 25;

  const completedResearchers = job.agents.filter(
    (agent) => agent.status === "completed",
  ).length;
  return 40 + completedResearchers * 20;
}

function getStatusText(job: ResearchJob) {
  if (job.status === "failed") return "Research stopped";
  if (job.status === "completed") return "Research complete";
  if (job.current_stage === "researchers") return "Researchers are working";
  if (job.current_stage === "supervisor") return "Creating the research plan";
  return "Waiting to start";
}

export function ResearchProgress({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const response = await fetch(`${apiBaseUrl}/research/${jobId}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Research request failed: ${response.status}`);
        }

        const nextJob = (await response.json()) as ResearchJob;
        setJob(nextJob);
        setLoadError(null);

        if (nextJob.status === "queued" || nextJob.status === "running") {
          timer = setTimeout(poll, 1500);
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setLoadError("This research job could not be loaded.");
        }
      }
    }

    void poll();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  if (loadError) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">
        {loadError}
      </div>
    );
  }

  if (!job) {
    return (
      <div className="space-y-4" aria-label="Loading research job">
        <div className="h-28 animate-pulse rounded-2xl bg-slate-200/70" />
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div className="h-52 animate-pulse rounded-2xl bg-slate-200/60" key={item} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">
              {getStatusText(job)}
            </p>
            <h1 className="mt-3 max-w-3xl text-2xl font-semibold leading-9 tracking-[-0.025em] text-slate-950 sm:text-3xl">
              {job.question}
            </h1>
          </div>
          <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
            Up to {job.max_sources} sources
          </span>
        </div>

        <div className="mt-7 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              job.status === "failed" ? "bg-rose-500" : "bg-blue-600"
            }`}
            style={{ width: `${getProgress(job)}%` }}
          />
        </div>

        {job.status === "running" || job.status === "queued" ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-slate-600">
            <span className="size-2 animate-pulse rounded-full bg-blue-600" />
            {job.current_stage === "researchers"
              ? "Three researchers are searching and analyzing sources in parallel."
              : "The supervisor is dividing the question into three research tracks."}
          </p>
        ) : null}

        {job.status === "failed" ? (
          <p className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {job.error ?? "The research run could not be completed. Please try again."}
          </p>
        ) : null}
      </section>

      {job.assignments.length > 0 ? (
        <section>
          <div className="mb-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Research team
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              Three research tracks
            </h2>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {job.assignments.map((assignment) => {
              const agent = job.agents.find((item) => item.index === assignment.index);
              const result = job.researcher_results.find(
                (item) => item.index === assignment.index,
              );

              return (
                <article
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                  key={assignment.index}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs font-semibold text-blue-600">
                      Researcher {assignment.index}
                    </span>
                    {agent ? (
                      <span
                        className={`rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize ${agentStatusStyles[agent.status]}`}
                      >
                        {agent.status}
                      </span>
                    ) : null}
                  </div>

                  <h3 className="mt-3 text-lg font-semibold text-slate-950">
                    {assignment.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {result?.summary ?? assignment.objective}
                  </p>

                  {agent ? (
                    <p className="mt-4 text-xs font-medium text-slate-500">
                      {agent.progress_message}
                    </p>
                  ) : null}

                  {result ? (
                    <div className="mt-5 space-y-5 border-t border-slate-100 pt-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                          Findings
                        </p>
                        <ul className="mt-3 space-y-3">
                          {result.findings.map((finding) => (
                            <li
                              className="text-sm leading-6 text-slate-700"
                              key={`${finding.statement}-${finding.source_keys.join("-")}`}
                            >
                              {finding.statement}{" "}
                              <span className="whitespace-nowrap text-xs font-semibold text-blue-700">
                                [{finding.source_keys.join(", ")}]
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                          Sources
                        </p>
                        <ul className="mt-3 space-y-2">
                          {result.sources.map((source) => (
                            <li key={source.source_key}>
                              <a
                                className="block text-xs leading-5 text-blue-700 underline decoration-blue-200 underline-offset-2 hover:text-blue-900"
                                href={source.url}
                                rel="noreferrer noopener"
                                target="_blank"
                              >
                                {source.source_key} · {source.title}
                              </a>
                              <span className="text-[11px] text-slate-400">
                                {source.domain}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-5 border-t border-slate-100 pt-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                        Planned searches
                      </p>
                      <ul className="mt-3 space-y-2">
                        {assignment.search_queries.map((query) => (
                          <li className="text-xs leading-5 text-slate-600" key={query}>
                            {query}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}
