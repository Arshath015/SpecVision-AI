import { Receipt } from "lucide-react";
import type { PriceEstimate } from "../types/api";
import { Section } from "./Section";

export function PricingPanel({ price }: { price: PriceEstimate }) {
  if (!price.available) {
    return (
      <Section icon={Receipt} title="Price estimate" subtitle="Indicative pricing derived from the selected inventory reference.">
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
          <p className="text-sm font-medium text-slate-500">No indicative price available</p>
          <p className="mt-1 text-xs text-slate-400">{price.reason}</p>
        </div>
      </Section>
    );
  }

  return (
    <Section icon={Receipt} title="Price estimate" subtitle="Indicative only -- not a confirmed commercial quote.">
      <div className="flex flex-col gap-4">
        <div className="flex items-end justify-between rounded-lg bg-brand-50 px-4 py-3">
          <div>
            <p className="text-xs text-brand-600">Indicative total</p>
            <p className="text-2xl font-bold text-brand-800">
              {price.currency} {price.indicative_total?.toLocaleString()}
            </p>
          </div>
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800">
            Indicative estimate, not a confirmed quote
          </span>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-slate-500">Breakdown</p>
          <table className="w-full text-xs">
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="py-1.5 text-slate-600">Catalog base price</td>
                <td className="py-1.5 text-right font-medium text-slate-800">
                  {price.currency} {price.base_unit_price?.toLocaleString()}
                </td>
              </tr>
              {price.adjustments.map((adj, i) => (
                <tr key={i} className="border-b border-slate-100">
                  <td className="py-1.5 text-slate-600">
                    {adj.label}
                    <span className="block text-[10px] text-slate-400">{adj.detail}</span>
                  </td>
                  <td className="py-1.5 text-right font-medium text-slate-800">
                    + {price.currency} {adj.amount.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-slate-500">Formula</p>
          <p className="rounded-lg bg-slate-50 px-3 py-2 font-mono text-[11px] text-slate-600">{price.formula_description}</p>
        </div>

        {price.assumptions.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-slate-500">Assumptions &amp; missing inputs</p>
            <ul className="flex flex-col gap-1">
              {price.assumptions.map((a) => (
                <li key={a.code} className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs text-slate-600">
                  <span className="font-medium text-slate-700">{a.code}:</span> {a.description}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Section>
  );
}
