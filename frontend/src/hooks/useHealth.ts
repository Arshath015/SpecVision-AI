import { useEffect, useState } from "react";
import { getHealth } from "../api/client";
import type { HealthResponse } from "../types/api";

export type HealthState =
  | { status: "checking" }
  | { status: "connected"; data: HealthResponse }
  | { status: "disconnected" };

export function useHealth(pollMs = 20_000): HealthState {
  const [state, setState] = useState<HealthState>({ status: "checking" });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const data = await getHealth();
        if (!cancelled) setState({ status: "connected", data });
      } catch {
        if (!cancelled) setState({ status: "disconnected" });
      }
    }

    check();
    const interval = setInterval(check, pollMs);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [pollMs]);

  return state;
}
