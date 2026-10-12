import type { AnalyzeResponse, ApiErrorBody, HealthResponse, InventoryItem } from "../types/api";

const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiErrorBody;
    return body.detail ?? `Request failed with status ${res.status}`;
  } catch {
    return `Request failed with status ${res.status}`;
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8_000);
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    if (!res.ok) throw new ApiError(res.status, await parseErrorBody(res));
    return (await res.json()) as HealthResponse;
  } finally {
    clearTimeout(timer);
  }
}

export async function listInventory(): Promise<InventoryItem[]> {
  const res = await fetch(`${API_BASE_URL}/inventory`);
  if (!res.ok) throw new ApiError(res.status, await parseErrorBody(res));
  return (await res.json()) as InventoryItem[];
}

export async function analyze(brief: string, image: File | null): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    // Always multipart/form-data -- the backend's single, documented request
    // contract (see backend/app/api/routes.py). A brief-only request is just
    // this same form with the "image" part omitted. Do NOT set a Content-Type
    // header here: the browser generates the multipart boundary itself, and
    // overriding it manually produces a malformed request the server can't parse.
    const form = new FormData();
    form.append("brief", brief);
    if (image) form.append("image", image);
    const res = await fetch(`${API_BASE_URL}/analyze`, { method: "POST", body: form, signal: controller.signal });
    if (!res.ok) throw new ApiError(res.status, await parseErrorBody(res));
    return (await res.json()) as AnalyzeResponse;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, "The request timed out. The backend may be unavailable or still starting up.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
