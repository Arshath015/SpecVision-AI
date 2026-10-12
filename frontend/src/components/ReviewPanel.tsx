import { ShieldAlert } from "lucide-react";
import type { ConfidenceSummary, ProcessingMetadata } from "../types/api";
import { SeverityBadge, StatusBadge } from "./Badge";
import { Section } from "./Section";

export function ReviewPanel({ summary, metadata }: { summary: ConfidenceSummary; metadata: ProcessingMetadata }) {
  return (
    <Section icon={ShieldAlert} title="Confidence &amp; review" subtitle="Actionable warnings -- failures are never hidden behind a successful-looking result.">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <StatusBadge status={summary.overall_status} />
          {summary.low_confidence_fields.length > 0 && (
            <span className="text-xs text-slate-500">{summary.low_confidence_fields.length} low-confidence field(s)</span>
          )}
        </div>

        {summary.low_confidence_fields.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {summary.low_confidence_fields.map((f) => (
              <span key={f} className="rounded-full border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-700">
                {f.replace(/_/g, " ").replace(/\./g, " / ")}
              </span>
            ))}
          </div>
        )}

        {summary.review_flags.length === 0 ? (
          <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
            No review flags were raised for this analysis.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {summary.review_flags.map((flag) => (
              <div key={flag.code} className="rounded-lg border border-slate-200 px-3 py-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[11px] font-semibold text-slate-700">{flag.code}</span>
                  <SeverityBadge severity={flag.severity} />
                </div>
                <p className="mt-1 text-sm text-slate-700">{flag.message}</p>
                <p className="mt-0.5 text-xs text-slate-500">
                  <span className="font-medium text-slate-600">Recommended action: </span>
                  {flag.recommended_action}
                </p>
              </div>
            ))}
          </div>
        )}

        {metadata.recovery_events.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-slate-500">Recovery events during processing</p>
            <ul className="flex flex-col gap-1">
              {metadata.recovery_events.map((e, i) => (
                <li key={i} className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs text-slate-600">
                  <span className="font-medium text-slate-700">{e.action}:</span> {e.detail}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Section>
  );
}
