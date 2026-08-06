import type { DocumentSummary } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function readErrorDetail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail ?? res.statusText;
  } catch {
    return res.statusText || "Request failed.";
  }
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const res = await fetch(`${API_URL}/documents`);
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);

  const data = await res.json();
  return {
    document_id: data.document_id,
    document_name: data.document_name,
    chunk_count: data.chunk_count,
    uploaded_at: new Date().toISOString(),
  };
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${documentId}`, { method: "DELETE" });
  if (!res.ok) throw new ApiError(await readErrorDetail(res), res.status);
}

/**
 * Streams the answer token-by-token, calling onToken for each chunk of text
 * as it arrives from the backend's StreamingResponse.
 */
export async function askQuestion(
  question: string,
  documentId: string | null,
  onToken: (text: string) => void,
): Promise<void> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId }),
  });

  if (!res.ok) {
    throw new ApiError(await readErrorDetail(res), res.status);
  }
  if (!res.body) {
    throw new ApiError("No response body received from the server.", 500);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}
