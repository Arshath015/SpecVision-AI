import { AlertTriangle, ScanSearch } from "lucide-react";
import { useState } from "react";
import type { CVEstimate } from "../types/api";
import { ConfidenceBadge } from "./Badge";
import { Section } from "./Section";

export function CVPanel({ cv, previewUrl }: { cv: CVEstimate; previewUrl: string | null }) {
  const [showAnnotated, setShowAnnotated] = useState(true);

  if (!cv.available) {
    return (
      <Section icon={ScanSearch} title="Computer vision" subtitle="Classical OpenCV baseline for visible gemstone detection.">
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-slate-300 bg-slate-50 py-8 text-center">
          <ScanSearch size={22} className="text-slate-300" />
          <p className="text-sm font-medium text-slate-500">No visible-stone estimate available</p>
          <p className="max-w-sm text-xs text-slate-400">{cv.reason}</p>
        </div>
      </Section>
    );
  }

  const annotatedSrc = cv.annotated_image_base64 ? `data:image/png;base64,${cv.annotated_image_base64}` : null;

  return (
    <Section icon={ScanSearch} title="Computer vision" subtitle="Classical OpenCV baseline (Hough-circle + contour hybrid) -- no paid vision API.">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-[minmax(0,260px)_1fr]">
        <div>
          <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
            <img
              src={showAnnotated && annotatedSrc ? annotatedSrc : (previewUrl ?? annotatedSrc ?? undefined)}
              alt="Reference"
              className="h-56 w-full object-contain"
            />
          </div>
          {annotatedSrc && previewUrl && (
            <button
              type="button"
              onClick={() => setShowAnnotated((v) => !v)}
              className="mt-2 w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              {showAnnotated ? "Show original" : "Show detections"}
            </button>
          )}
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-lg bg-brand-50 px-3 py-2 text-center">
              <p className="text-2xl font-bold text-brand-700">{cv.estimated_visible_count}</p>
              <p className="text-[11px] text-brand-600">visible components</p>
            </div>
            <ConfidenceBadge level={cv.confidence} />
            <span
              className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${
                cv.suitable_for_automatic_use
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-amber-200 bg-amber-50 text-amber-700"
              }`}
            >
              {cv.suitable_for_automatic_use ? "Suitable for automatic use" : "Needs human review"}
            </span>
          </div>

          <p className="text-xs text-slate-600">{cv.reason}</p>

          <p className="rounded-lg bg-slate-50 px-3 py-2 text-[11px] italic text-slate-500">
            A visible-stone count reflects only what is distinguishable in this one photo -- it is not necessarily the total
            number of stones in the finished product (occlusion, angle, and resolution all limit what can be seen).
          </p>

          {cv.image_quality_warnings.length > 0 && (
            <div className="flex flex-col gap-1.5">
              {cv.image_quality_warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs text-amber-800">
                  <AlertTriangle size={13} className="mt-0.5 flex-none" />
                  {w}
                </div>
              ))}
            </div>
          )}

          {cv.brief_claimed_count !== null && (
            <div
              className={`rounded-lg border px-2.5 py-1.5 text-xs ${
                cv.disagreement_with_brief
                  ? "border-rose-200 bg-rose-50 text-rose-700"
                  : "border-slate-200 bg-slate-50 text-slate-600"
              }`}
            >
              Brief implies {cv.brief_claimed_count} side stone(s) vs. {cv.estimated_visible_count} visibly detected
              {cv.disagreement_ratio !== null && ` (${Math.round(cv.disagreement_ratio * 100)}% relative difference)`}.
              {cv.disagreement_with_brief ? " Flagged as a disagreement." : " Within the agreement threshold."}
            </div>
          )}

          <p className="text-[11px] text-slate-400">Processed in {cv.processing_time_ms.toFixed(1)}ms</p>
        </div>
      </div>
    </Section>
  );
}
