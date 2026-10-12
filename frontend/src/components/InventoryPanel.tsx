import { ChevronDown, Gem } from "lucide-react";
import { useState } from "react";
import type { InventoryCandidate, InventoryMatchResult } from "../types/api";
import { Section } from "./Section";

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.72 ? "bg-emerald-500" : score >= 0.5 ? "bg-amber-500" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-600">{pct}%</span>
    </div>
  );
}

function CandidateCard({ candidate, rank }: { candidate: InventoryCandidate; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
            #{rank}
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">{candidate.name}</p>
            <p className="text-xs text-slate-500">
              {candidate.product_id} &middot; {candidate.item.metal_purity.replace(/_/g, " ")} {candidate.item.metal_color}{" "}
              {candidate.item.metal_type} &middot; {candidate.item.center_stone_type} {candidate.item.center_stone_shape}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">
              {candidate.currency} {candidate.unit_price.toLocaleString()}
            </p>
            <p className="text-[11px] text-slate-400">unit price</p>
          </div>
          <ScoreBar score={candidate.match_score} />
          <span
            className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${
              candidate.passed_threshold
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : "border-slate-200 bg-slate-50 text-slate-500"
            }`}
          >
            {candidate.passed_threshold ? "Passed threshold" : "Below threshold"}
          </span>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Toggle attribute explanations"
          >
            <ChevronDown size={16} className={`transition-transform ${expanded ? "rotate-180" : ""}`} />
          </button>
        </div>
      </div>
      {expanded && (
        <div className="border-t border-slate-100 px-4 py-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-400">
                <th className="pb-1.5 font-medium">Attribute</th>
                <th className="pb-1.5 font-medium">Extracted</th>
                <th className="pb-1.5 font-medium">Catalog</th>
                <th className="pb-1.5 font-medium">Weight</th>
                <th className="pb-1.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {candidate.attribute_explanations.map((exp) => (
                <tr key={exp.attribute} className="border-t border-slate-50">
                  <td className="py-1.5 pr-2 font-medium text-slate-700">{exp.attribute.replace(/_/g, " ")}</td>
                  <td className="py-1.5 pr-2 text-slate-600">{exp.extracted_value}</td>
                  <td className="py-1.5 pr-2 text-slate-600">{exp.inventory_value}</td>
                  <td className="py-1.5 pr-2 text-slate-500">{exp.weight.toFixed(2)}</td>
                  <td className="py-1.5">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        exp.status === "exact_match"
                          ? "bg-emerald-50 text-emerald-700"
                          : exp.status === "partial_match"
                            ? "bg-amber-50 text-amber-700"
                            : exp.status === "contradiction"
                              ? "bg-rose-50 text-rose-700"
                              : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {exp.status.replace(/_/g, " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function InventoryPanel({ match }: { match: InventoryMatchResult }) {
  return (
    <Section
      icon={Gem}
      title="Inventory matching"
      subtitle={`Deterministic weighted scoring against the catalog (auto-select threshold: ${Math.round(match.threshold_used * 100)}%).`}
    >
      <div className="flex flex-col gap-3">
        {match.candidates.length === 0 ? (
          <p className="text-sm text-slate-500">No candidates were available to score.</p>
        ) : (
          match.candidates.map((c, i) => <CandidateCard key={c.product_id} candidate={c} rank={i + 1} />)
        )}
        <div
          className={`rounded-lg border px-3 py-2.5 text-xs ${
            match.reliable_match_found
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-amber-200 bg-amber-50 text-amber-800"
          }`}
        >
          {match.explanation}
        </div>
        {match.reliable_match_found && (
          <p className="text-[11px] italic text-slate-400">
            A high similarity score indicates the closest catalog reference -- it is not a claim of exact product equivalence.
          </p>
        )}
      </div>
    </Section>
  );
}
