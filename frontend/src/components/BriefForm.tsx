import { ImagePlus, Loader2, Sparkles, Wand2, X } from "lucide-react";
import { useRef, useState } from "react";
import { EXAMPLE_BRIEFS } from "../data/examples";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
// Must track the backend's MAX_IMAGE_SIZE_BYTES for this deployment --
// local/Docker default is 8MB, but the Vercel deployment lowers this to
// stay under Vercel Functions' 4.5MB request body limit (see
// VITE_MAX_IMAGE_SIZE_MB in frontend/.env.production). Showing a limit
// the backend doesn't actually honor would let a user upload something
// that fails with a confusing platform-level error instead of this app's
// own clean message.
const MAX_IMAGE_MB = Number(import.meta.env.VITE_MAX_IMAGE_SIZE_MB ?? 8);
const MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024;

interface BriefFormProps {
  brief: string;
  onBriefChange: (v: string) => void;
  image: File | null;
  onImageChange: (f: File | null) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export function BriefForm({ brief, onBriefChange, image, onImageChange, onAnalyze, isLoading, disabled }: BriefFormProps) {
  const [imageError, setImageError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Drag events fire on every child element a dragged file passes over, so
  // a plain enter/leave pair flickers "isDragging" off whenever the cursor
  // crosses from the dropzone into one of its own children. A counter that
  // only clears the highlight once it's back to zero avoids that.
  const dragCounterRef = useRef(0);

  function handleDragEnter(e: React.DragEvent) {
    e.preventDefault();
    dragCounterRef.current += 1;
    if (e.dataTransfer.types.includes("Files")) setIsDragging(true);
  }

  function handleDragOver(e: React.DragEvent) {
    // Required for onDrop to fire at all -- browsers reject drops by default.
    e.preventDefault();
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    dragCounterRef.current = Math.max(0, dragCounterRef.current - 1);
    if (dragCounterRef.current === 0) setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    dragCounterRef.current = 0;
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSetImage(file);
  }

  function validateAndSetImage(file: File) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setImageError("Unsupported format. Use JPG, PNG, or WebP.");
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setImageError(`Image is too large (max ${MAX_IMAGE_BYTES / (1024 * 1024)}MB).`);
      return;
    }
    setImageError(null);
    onImageChange(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) validateAndSetImage(file);
  }

  function removeImage() {
    onImageChange(null);
    setPreviewUrl(null);
    setImageError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function loadExample(label: string, exampleBrief: string, sampleImage?: string) {
    onBriefChange(exampleBrief);
    if (sampleImage) {
      try {
        const res = await fetch(`/sample-images/${sampleImage}`);
        const blob = await res.blob();
        const file = new File([blob], sampleImage, { type: blob.type || "image/jpeg" });
        validateAndSetImage(file);
      } catch {
        setImageError(`Could not load bundled sample image for "${label}".`);
      }
    } else {
      removeImage();
    }
  }

  const briefTooLong = brief.length > 4000;
  const canAnalyze = brief.trim().length > 0 && !briefTooLong && !isLoading && !disabled;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <label htmlFor="brief" className="text-sm font-medium text-slate-700">
            Sales brief <span className="text-rose-500">*</span>
          </label>
          <span className={`text-xs ${briefTooLong ? "text-rose-600" : "text-slate-400"}`}>{brief.length} / 4000</span>
        </div>
        <textarea
          id="brief"
          value={brief}
          onChange={(e) => onBriefChange(e.target.value)}
          placeholder="Describe the custom jewelry piece, e.g. '18K yellow-gold engagement ring with an oval center diamond, six small stones on each side...'"
          rows={5}
          className="w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />
        {briefTooLong && <p className="mt-1 text-xs text-rose-600">Brief exceeds the 4000 character limit.</p>}
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Reference image (optional)</label>
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {previewUrl ? (
            <div
              className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                isDragging ? "border-brand-400 bg-brand-50" : "border-slate-200 bg-slate-50"
              }`}
            >
              <img src={previewUrl} alt="Reference preview" className="h-20 w-20 flex-none rounded-md border border-slate-200 object-cover" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-700">{image?.name}</p>
                <p className="text-xs text-slate-500">
                  {isDragging ? "Drop to replace" : image ? `${(image.size / 1024).toFixed(0)} KB` : ""}
                </p>
              </div>
              <div className="flex flex-none gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Replace
                </button>
                <button
                  type="button"
                  onClick={removeImage}
                  className="rounded-md border border-slate-300 bg-white p-1.5 text-slate-500 hover:bg-slate-50"
                  aria-label="Remove image"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`flex w-full flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed px-4 py-6 transition-colors ${
                isDragging
                  ? "border-brand-400 bg-brand-50 text-brand-600"
                  : "border-slate-300 bg-slate-50 text-slate-500 hover:border-brand-300 hover:bg-brand-50/40"
              }`}
            >
              <ImagePlus size={20} />
              <span className="text-sm font-medium">
                {isDragging ? "Drop image to upload" : "Click or drag a reference photo here"}
              </span>
              <span className="text-xs text-slate-400">JPG, PNG, or WebP · up to {MAX_IMAGE_MB}MB</span>
            </button>
          )}
        </div>
        <input ref={fileInputRef} type="file" accept={ACCEPTED_TYPES.join(",")} onChange={handleFileInput} className="hidden" />
        {imageError && <p className="mt-1 text-xs text-rose-600">{imageError}</p>}
      </div>

      <div>
        <p className="mb-1.5 flex items-center gap-1 text-xs font-medium text-slate-500">
          <Sparkles size={13} /> Load an example
        </p>
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_BRIEFS.map((ex) => (
            <button
              key={ex.label}
              type="button"
              onClick={() => loadExample(ex.label, ex.brief, ex.sampleImage)}
              className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={onAnalyze}
        disabled={!canAnalyze}
        className="flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />}
        {isLoading ? "Analyzing…" : "Analyze"}
      </button>
    </div>
  );
}
