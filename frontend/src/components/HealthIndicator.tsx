import { CircleAlert, CircleCheck, LoaderCircle } from "lucide-react";
import type { HealthState } from "../hooks/useHealth";

export function HealthIndicator({ health }: { health: HealthState }) {
  if (health.status === "checking") {
    return (
      <div className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
        <LoaderCircle size={13} className="animate-spin" />
        Checking backend…
      </div>
    );
  }
  if (health.status === "disconnected") {
    return (
      <div className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700">
        <CircleAlert size={13} />
        Backend unreachable
      </div>
    );
  }
  const modeLabel = health.data.app_mode === "live" ? "Live LLM" : "Offline demo";
  const modeStyle =
    health.data.app_mode === "live"
      ? "border-violet-200 bg-violet-50 text-violet-700"
      : "border-brand-200 bg-brand-50 text-brand-700";
  return (
    <div className="flex items-center gap-2">
      <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
        <CircleCheck size={13} />
        Backend connected
      </div>
      <div className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${modeStyle}`}>
        {modeLabel}
      </div>
    </div>
  );
}
