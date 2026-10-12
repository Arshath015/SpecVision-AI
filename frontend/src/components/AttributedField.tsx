import { HelpCircle } from "lucide-react";
import type { AttributedValue } from "../types/api";
import { ConfidenceBadge, SourceBadge } from "./Badge";

function formatValue(value: unknown, unit?: string): string {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "string") return value.replace(/_/g, " ");
  if (typeof value === "number") return unit ? `${value}${unit}` : String(value);
  return String(value);
}

export function AttributedField({
  label,
  field,
  unit,
}: {
  label: string;
  field: AttributedValue<unknown>;
  unit?: string;
}) {
  const isUnknown = field.value === null || field.value === undefined;
  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <ConfidenceBadge level={field.confidence} />
      </div>
      <div className={`text-sm font-semibold ${isUnknown ? "text-slate-400 italic font-normal" : "text-slate-900"}`}>
        {formatValue(field.value, unit)}
      </div>
      <div className="flex items-start gap-1.5">
        <SourceBadge source={field.source} />
      </div>
      <div className="flex items-start gap-1 text-xs text-slate-500">
        <HelpCircle size={12} className="mt-0.5 flex-none text-slate-400" />
        <span>{field.reason}</span>
      </div>
    </div>
  );
}
