"use client";

import { useEffect, useState } from "react";

type ConnectionState = "checking" | "connected" | "offline";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function BackendStatus() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, {
          cache: "no-store",
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Health check failed with ${response.status}`);
        }

        const body = (await response.json()) as { status?: string };
        setConnectionState(body.status === "ok" ? "connected" : "offline");
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setConnectionState("offline");
        }
      }
    }

    void checkBackend();
    return () => controller.abort();
  }, []);

  const styles = {
    checking: "border-amber-200 bg-amber-50 text-amber-800",
    connected: "border-emerald-200 bg-emerald-50 text-emerald-800",
    offline: "border-rose-200 bg-rose-50 text-rose-800",
  } satisfies Record<ConnectionState, string>;

  const labels = {
    checking: "Checking FastAPI...",
    connected: "Backend connected",
    offline: "Backend is not running",
  } satisfies Record<ConnectionState, string>;

  return (
    <div
      className={`mt-6 flex items-center gap-3 rounded-2xl border px-4 py-4 text-sm font-semibold ${styles[connectionState]}`}
      role="status"
    >
      <span
        className={`size-2.5 rounded-full ${
          connectionState === "connected"
            ? "bg-emerald-500"
            : connectionState === "offline"
              ? "bg-rose-500"
              : "animate-pulse bg-amber-500"
        }`}
      />
      {labels[connectionState]}
    </div>
  );
}

