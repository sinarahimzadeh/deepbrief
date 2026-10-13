"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const exampleQuestion =
  "Compare the best AI coding assistants for a small engineering team, including cost, privacy, and code quality.";

type ResearchJobResponse = {
  id: string;
};

export function ResearchForm() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [maxSources, setMaxSources] = useState(12);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = question.trim().length >= 10 && !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${apiBaseUrl}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim(), max_sources: maxSources }),
      });

      if (response.status === 429) {
        setError(
          "Today’s research limit has been reached. Please try again after the daily reset.",
        );
        return;
      }

      if (!response.ok) {
        setError("Research couldn’t start right now. Please try again shortly.");
        return;
      }

      const job = (await response.json()) as ResearchJobResponse;
      router.push(`/research/${job.id}`);
    } catch {
      setError("Research couldn’t start right now. Please try again shortly.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mt-7" onSubmit={handleSubmit}>
      <label className="block text-sm font-semibold text-slate-800" htmlFor="question">
        Research question
      </label>
      <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50/80 p-1.5 transition focus-within:border-blue-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-50">
        <textarea
          className="min-h-40 w-full resize-none bg-transparent px-3 py-3 text-[15px] leading-7 text-slate-900 outline-none placeholder:text-slate-400"
          id="question"
          maxLength={2000}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What do you want to understand, compare, or decide?"
          value={question}
        />
        <div className="flex items-center justify-between gap-3 border-t border-slate-200/80 px-3 py-2">
          <button
            className="text-xs font-semibold text-blue-700 transition hover:text-blue-900"
            onClick={() => setQuestion(exampleQuestion)}
            type="button"
          >
            Use an example
          </button>
          <span className="text-xs tabular-nums text-slate-400">
            {question.length}/2000
          </span>
        </div>
      </div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <label className="text-sm font-semibold text-slate-700" htmlFor="max-sources">
          Sources
          <select
            className="mt-2 block rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-medium text-slate-700 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-50"
            id="max-sources"
            onChange={(event) => setMaxSources(Number(event.target.value))}
            value={maxSources}
          >
            <option value={8}>Up to 8</option>
            <option value={12}>Up to 12</option>
            <option value={15}>Up to 15</option>
          </select>
        </label>

        <button
          className="group inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-slate-950/15 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
          disabled={!canSubmit}
          type="submit"
        >
          {isSubmitting ? "Starting…" : "Start research"}
          <svg
            aria-hidden="true"
            className="size-4 transition-transform group-hover:translate-x-0.5"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              d="M5 12h14m-5-5 5 5-5 5"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.8"
            />
          </svg>
        </button>
      </div>

      {error ? (
        <p
          aria-live="polite"
          className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700"
        >
          {error}
        </p>
      ) : null}

      <p className="mt-5 flex items-start gap-2 text-xs leading-5 text-slate-500">
        <svg
          aria-hidden="true"
          className="mt-0.5 size-4 shrink-0 text-emerald-600"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            d="m7 12 3 3 7-7"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
          />
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        You’ll see each researcher’s progress, evidence, and citations as they work.
      </p>
    </form>
  );
}
