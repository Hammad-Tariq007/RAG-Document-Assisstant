export type DocumentSummary = {
  document_id: string;
  document_name: string;
  chunk_count: number;
  uploaded_at: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "streaming" | "done" | "error";
};
