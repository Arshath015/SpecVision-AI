import { Cpu } from "lucide-react";
import type { ProcessingMetadata } from "../types/api";
import { Section } from "./Section";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

export function DiagnosticsPanel({ metadata }: { metadata: ProcessingMetadata }) {
  return (
    <Section icon={Cpu} title="Technical diagnostics" subtitle="Processing metadata for this request. No credentials are ever exposed here.">
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <Stat label="Mode" value={metadata.app_mode === "live" ? "Live LLM" : "Offline demo"} />
        <Stat label="Extraction method" value={metadata.extraction_method.replace(/_/g, " ")} />
        <Stat label="Provider" value={metadata.provider ?? "n/a (offline)"} />
        <Stat label="Model" value={metadata.model_used ?? "n/a (offline)"} />
        <Stat label="Total latency" value={`${metadata.total_latency_ms.toFixed(0)}ms`} />
        <Stat label="Extraction latency" value={`${metadata.extraction_latency_ms.toFixed(0)}ms`} />
        <Stat label="CV latency" value={`${metadata.cv_latency_ms.toFixed(0)}ms`} />
        <Stat label="Matching latency" value={`${metadata.matching_latency_ms.toFixed(0)}ms`} />
      </div>
      <p className="mt-2.5 text-[11px] text-slate-400">
        Request ID: <span className="font-mono">{metadata.request_id}</span>
        {metadata.estimated_llm_cost_usd !== null && (
          <> &middot; Estimated LLM cost: ${metadata.estimated_llm_cost_usd.toFixed(4)}</>
        )}
      </p>
    </Section>
  );
}
