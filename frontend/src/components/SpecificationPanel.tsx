import { FileText } from "lucide-react";
import type { ProductSpecification } from "../types/api";
import { AttributedField } from "./AttributedField";
import { Section } from "./Section";

export function SpecificationPanel({ spec }: { spec: ProductSpecification }) {
  return (
    <Section
      icon={FileText}
      title="Structured specification"
      subtitle="Values are distinguished by source and confidence -- unknown fields are shown honestly, never guessed."
    >
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <AttributedField label="Product type" field={spec.product_type} />
        <AttributedField label="Design category" field={spec.design_category} />
        <AttributedField label="Metal type" field={spec.metal_type} />
        <AttributedField label="Metal purity" field={spec.metal_purity} />
        <AttributedField label="Metal color" field={spec.metal_color} />
        <AttributedField label="Setting type" field={spec.setting_type} />
        <AttributedField label="Ring size (US)" field={spec.dimensions.ring_size_us} />
        <AttributedField label="Band width" field={spec.dimensions.band_width_mm} unit="mm" />
        <AttributedField label="Center stone type" field={spec.center_stone.gemstone_type} />
        <AttributedField label="Center stone shape" field={spec.center_stone.shape} />
        <AttributedField label="Center stone carat" field={spec.center_stone.carat} unit="ct" />
        <AttributedField label="Side stone type" field={spec.side_stones.gemstone_type} />
        <AttributedField label="Side stone count" field={spec.side_stones.count_total} />
        <AttributedField label="Side stones total carat" field={spec.side_stones.total_carat} unit="ct" />
      </div>
      {spec.notes && (
        <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
          <span className="font-medium text-slate-600">Extractor notes: </span>
          {spec.notes}
        </p>
      )}
    </Section>
  );
}
