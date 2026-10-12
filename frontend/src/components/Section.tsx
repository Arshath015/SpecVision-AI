import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface SectionProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
}

export function Section({ icon: Icon, title, subtitle, children, action }: SectionProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <Icon size={17} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
        </div>
        {action}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}
