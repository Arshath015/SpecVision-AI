import type { ConfidenceLevel, ReviewSeverity, SourceType } from "../types/api";

const CONFIDENCE_STYLES: Record<ConfidenceLevel, string> = {
  high: "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low: "bg-rose-50 text-rose-700 border-rose-200",
};

const SEVERITY_STYLES: Record<ReviewSeverity, string> = {
  info: "bg-slate-100 text-slate-700 border-slate-300",
  warning: "bg-amber-50 text-amber-800 border-amber-300",
  critical: "bg-rose-50 text-rose-800 border-rose-300",
};

const SOURCE_LABELS: Record<SourceType, string> = {
  user_provided: "From brief",
  model_inferred: "Model inferred",
  image_estimated: "From image",
  default_assumption: "Assumed",
  unknown: "Unknown",
};

const SOURCE_STYLES: Record<SourceType, string> = {
  user_provided: "bg-brand-50 text-brand-700 border-brand-200",
  model_inferred: "bg-violet-50 text-violet-700 border-violet-200",
  image_estimated: "bg-cyan-50 text-cyan-700 border-cyan-200",
  default_assumption: "bg-slate-100 text-slate-700 border-slate-300",
  unknown: "bg-slate-100 text-slate-500 border-slate-300",
};

function baseClasses(extra?: string) {
  return `inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${extra ?? ""}`;
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  return <span className={baseClasses(CONFIDENCE_STYLES[level])}>{level}</span>;
}

export function SeverityBadge({ severity }: { severity: ReviewSeverity }) {
  return <span className={baseClasses(SEVERITY_STYLES[severity])}>{severity}</span>;
}

export function SourceBadge({ source }: { source: SourceType }) {
  return <span className={baseClasses(SOURCE_STYLES[source])}>{SOURCE_LABELS[source]}</span>;
}

export function StatusBadge({ status }: { status: "auto_approved" | "needs_review" | "failed" }) {
  const styles: Record<string, string> = {
    auto_approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
    needs_review: "bg-amber-50 text-amber-800 border-amber-300",
    failed: "bg-rose-50 text-rose-800 border-rose-300",
  };
  const labels: Record<string, string> = {
    auto_approved: "Auto-approved",
    needs_review: "Needs review",
    failed: "Failed",
  };
  return <span className={baseClasses(`${styles[status]} text-sm px-3 py-1`)}>{labels[status]}</span>;
}
