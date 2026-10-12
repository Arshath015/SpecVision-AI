import { AlertCircle, Gem, Sparkles } from "lucide-react";
import { useState } from "react";
import { analyze, ApiError } from "./api/client";
import { BriefForm } from "./components/BriefForm";
import { CVPanel } from "./components/CVPanel";
import { DiagnosticsPanel } from "./components/DiagnosticsPanel";
import { HealthIndicator } from "./components/HealthIndicator";
import { InventoryPanel } from "./components/InventoryPanel";
import { PricingPanel } from "./components/PricingPanel";
import { ReviewPanel } from "./components/ReviewPanel";
import { SpecificationPanel } from "./components/SpecificationPanel";
import { useHealth } from "./hooks/useHealth";
import type { AnalyzeResponse } from "./types/api";

export default function App() {
  const health = useHealth();
  const [brief, setBrief] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleImageChange(file: File | null) {
    setImage(file);
    setPreviewUrl(file ? URL.createObjectURL(file) : null);
  }

  async function handleAnalyze() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await analyze(brief.trim(), image);
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred while contacting the backend.");
      }
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  const backendDown = health.status === "disconnected";

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Gem size={18} />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900">SpecVision AI</h1>
              <p className="text-xs text-slate-500">AI-powered product specification &amp; cost estimation for custom jewelry</p>
            </div>
          </div>
          <HealthIndicator health={health} />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 py-6 lg:grid-cols-[380px_1fr]">
        <div className="lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <BriefForm
              brief={brief}
              onBriefChange={setBrief}
              image={image}
              onImageChange={handleImageChange}
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
              disabled={backendDown}
            />
            {backendDown && (
              <p className="mt-3 flex items-start gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                <AlertCircle size={14} className="mt-0.5 flex-none" />
                The backend is unreachable. Start it with <code className="font-mono">uvicorn app.main:app --reload</code> and
                confirm <code className="font-mono">VITE_API_URL</code> is correct.
              </p>
            )}
            {error && (
              <p className="mt-3 flex items-start gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                <AlertCircle size={14} className="mt-0.5 flex-none" />
                {error}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-5">
          {!result && !isLoading && (
            <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white py-20 text-center">
              <Sparkles size={26} className="text-slate-300" />
              <p className="text-sm font-medium text-slate-500">Enter a brief and click Analyze to see results</p>
              <p className="max-w-sm text-xs text-slate-400">
                Try one of the bundled examples on the left to see a full specification, inventory match, computer-vision
                estimate, price, and review summary.
              </p>
            </div>
          )}

          {isLoading && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-20 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
              <p className="text-sm font-medium text-slate-500">Running the analysis pipeline…</p>
            </div>
          )}

          {result && !isLoading && (
            <>
              <SpecificationPanel spec={result.specification} />
              <InventoryPanel match={result.inventory_match} />
              <CVPanel cv={result.cv_estimate} previewUrl={previewUrl} />
              <PricingPanel price={result.price_estimate} />
              <ReviewPanel summary={result.confidence_summary} metadata={result.processing_metadata} />
              <DiagnosticsPanel metadata={result.processing_metadata} />
            </>
          )}
        </div>
      </main>

      <footer className="mx-auto max-w-7xl px-6 py-6 text-center text-xs text-slate-400">
        SpecVision AI is a local evaluation project. Pricing shown is indicative only, not a confirmed commercial quote.
      </footer>
    </div>
  );
}
