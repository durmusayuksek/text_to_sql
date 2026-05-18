import { useEffect, useState } from "react";
import { getHealthStatus } from "../api/client";
import type { HealthResponse } from "../types/api";

type RequestState = "idle" | "loading" | "success" | "error";

export function HealthStatus() {
  const [status, setStatus] = useState<RequestState>("idle");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadHealthStatus() {
      setStatus("loading");

      try {
        const data = await getHealthStatus();

        if (isMounted) {
          setHealth(data);
          setStatus("success");
        }
      } catch {
        if (isMounted) {
          setStatus("error");
        }
      }
    }

    void loadHealthStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  const label = health ? `${health.appName}: ${health.status}` : "Checking API";

  return (
    <div className="inline-flex w-fit items-center gap-3 rounded-2xl border border-[rgba(var(--brand-teal-rgb),0.16)] bg-white/80 px-4 py-3 text-sm font-medium text-slate-700 shadow-sm">
      <span
        className="h-2.5 w-2.5 rounded-full bg-slate-400 data-[state=success]:bg-[rgb(var(--brand-teal-rgb))] data-[state=error]:bg-rose-500 data-[state=loading]:bg-amber-400"
        data-state={status}
      />
      <span>{status === "error" ? "Backend unavailable" : label}</span>
    </div>
  );
}
