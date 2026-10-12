// Mirrors backend/app/models/schemas.py and enums.py. Kept in one file so
// the frontend never has to guess at the response shape.

export type SourceType =
  | "user_provided"
  | "model_inferred"
  | "image_estimated"
  | "default_assumption"
  | "unknown";

export type ConfidenceLevel = "high" | "medium" | "low";
export type ReviewSeverity = "info" | "warning" | "critical";

export type ExtractionMethod =
  | "llm_live"
  | "llm_live_fallback_model"
  | "llm_repaired"
  | "offline_fixture"
  | "safe_degradation";

export type CVMethod = "contour_and_hough_hybrid" | "unavailable";

export interface AttributedValue<T> {
  value: T | null;
  source: SourceType;
  confidence: ConfidenceLevel;
  reason: string;
}

export interface DimensionSpec {
  ring_size_us: AttributedValue<number>;
  band_width_mm: AttributedValue<number>;
}

export interface CenterStoneSpec {
  gemstone_type: AttributedValue<string>;
  shape: AttributedValue<string>;
  carat: AttributedValue<number>;
}

export interface SideStoneSpec {
  gemstone_type: AttributedValue<string>;
  shape: AttributedValue<string>;
  count_total: AttributedValue<number>;
  total_carat: AttributedValue<number>;
}

export interface ProductSpecification {
  product_type: AttributedValue<string>;
  design_category: AttributedValue<string>;
  metal_type: AttributedValue<string>;
  metal_purity: AttributedValue<string>;
  metal_color: AttributedValue<string>;
  setting_type: AttributedValue<string>;
  dimensions: DimensionSpec;
  center_stone: CenterStoneSpec;
  side_stones: SideStoneSpec;
  notes: string | null;
}

export interface InventoryItem {
  product_id: string;
  name: string;
  product_type: string;
  design_category: string;
  metal_type: string;
  metal_purity: string;
  metal_color: string;
  setting_type: string;
  center_stone_type: string;
  center_stone_shape: string;
  center_stone_carat_min: number;
  center_stone_carat_max: number;
  side_stone_type: string;
  side_stone_count: number;
  band_width_mm: number;
  unit_price: number;
  currency: string;
}

export interface AttributeMatchExplanation {
  attribute: string;
  extracted_value: string;
  inventory_value: string;
  weight: number;
  attribute_score: number;
  status: "exact_match" | "partial_match" | "contradiction" | "missing_data";
  explanation: string;
}

export interface InventoryCandidate {
  product_id: string;
  name: string;
  unit_price: number;
  currency: string;
  match_score: number;
  passed_threshold: boolean;
  attribute_explanations: AttributeMatchExplanation[];
  item: InventoryItem;
}

export interface InventoryMatchResult {
  candidates: InventoryCandidate[];
  selected: InventoryCandidate | null;
  threshold_used: number;
  reliable_match_found: boolean;
  explanation: string;
}

export interface CVDetection {
  x: number;
  y: number;
  radius: number;
  detection_source: "hough_circle" | "contour";
}

export interface CVEstimate {
  method: CVMethod;
  available: boolean;
  estimated_visible_count: number | null;
  detections: CVDetection[];
  confidence: ConfidenceLevel;
  reason: string;
  image_quality_warnings: string[];
  suitable_for_automatic_use: boolean;
  annotated_image_base64: string | null;
  processing_time_ms: number;
  brief_claimed_count: number | null;
  disagreement_with_brief: boolean;
  disagreement_ratio: number | null;
}

export interface PriceAssumption {
  code: string;
  description: string;
}

export interface PriceAdjustment {
  label: string;
  detail: string;
  amount: number;
}

export interface PriceEstimate {
  available: boolean;
  currency: string;
  base_unit_price: number | null;
  adjustments: PriceAdjustment[];
  indicative_total: number | null;
  formula_description: string;
  assumptions: PriceAssumption[];
  is_confirmed_quote: boolean;
  reason: string;
}

export interface ReviewFlag {
  code: string;
  severity: ReviewSeverity;
  message: string;
  recommended_action: string;
}

export interface ConfidenceSummary {
  overall_status: "auto_approved" | "needs_review" | "failed";
  low_confidence_fields: string[];
  review_flags: ReviewFlag[];
}

export interface RecoveryEvent {
  stage: string;
  action: string;
  detail: string;
}

export interface ProcessingMetadata {
  request_id: string;
  app_mode: "offline" | "live";
  extraction_method: ExtractionMethod;
  provider: string | null;
  model_used: string | null;
  total_latency_ms: number;
  extraction_latency_ms: number;
  cv_latency_ms: number;
  matching_latency_ms: number;
  recovery_events: RecoveryEvent[];
  estimated_llm_cost_usd: number | null;
}

export interface AnalyzeResponse {
  specification: ProductSpecification;
  inventory_match: InventoryMatchResult;
  cv_estimate: CVEstimate;
  price_estimate: PriceEstimate;
  confidence_summary: ConfidenceSummary;
  processing_metadata: ProcessingMetadata;
}

export interface HealthResponse {
  status: string;
  app_mode: "offline" | "live";
  llm_provider: string | null;
  primary_model: string | null;
  live_mode_ready: boolean;
  inventory_items_loaded: number;
}

export interface ApiErrorBody {
  detail: string;
}
