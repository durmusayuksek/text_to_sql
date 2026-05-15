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
    <div className="inline-flex items-center gap-3 rounded-md border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200">
      <span
        className="h-2.5 w-2.5 rounded-full bg-slate-500 data-[state=success]:bg-emerald-400 data-[state=error]:bg-rose-400 data-[state=loading]:bg-amber-300"
        data-state={status}
      />
      <span>{status === "error" ? "Backend unavailable" : label}</span>
    </div>
  );
}

