"use client";

import { useEffect, useState } from "react";

type ResearchAssignment = {
  index: number;
  title: string;
  objective: string;
  search_queries: string[];
};

type ResearchJob = {
  id: string;
  question: string;
  max_sources: number;
  status: "queued" | "running" | "completed" | "failed";
  current_stage: "queued" | "supervisor" | "plan_ready" | "failed";
  assignments: ResearchAssignment[];
  error: string | null;
};

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const statusText = {
  queued: "Waiting to start",
  running: "Planning the investigation",
  completed: "Research plan ready",
  failed: "Planning stopped",
} as const;

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
      if (timer) {
        clearTimeout(timer);
      }
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

  const progress = job.status === "queued" ? 15 : job.status === "running" ? 55 : 100;

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">
              {statusText[job.status]}
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
            style={{ width: `${progress}%` }}
          />
        </div>

        {job.status === "running" || job.status === "queued" ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-slate-600">
            <span className="size-2 animate-pulse rounded-full bg-blue-600" />
            The supervisor is separating the question into three focused research tracks.
          </p>
        ) : null}

        {job.status === "failed" ? (
          <p className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {job.error ?? "The research plan could not be created. Please try again."}
          </p>
        ) : null}
      </section>

      {job.status === "completed" ? (
        <section>
          <div className="mb-4 flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                Supervisor output
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
                Three research tracks
              </h2>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {job.assignments.map((assignment) => (
              <article
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                key={assignment.index}
              >
                <span className="font-mono text-xs font-semibold text-blue-600">
                  0{assignment.index}
                </span>
                <h3 className="mt-3 text-lg font-semibold text-slate-950">
                  {assignment.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {assignment.objective}
                </p>
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
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
