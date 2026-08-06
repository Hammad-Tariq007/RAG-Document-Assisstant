"use client";

import { useCallback, useRef, useState } from "react";

import { deleteDocument, uploadDocument } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";

import { useToast } from "./ToastProvider";

type Props = {
  documents: DocumentSummary[];
  selectedDocumentId: string | null;
  onSelectDocument: (id: string | null) => void;
  onDocumentsChange: () => void;
};

export function DocumentPanel({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onDocumentsChange,
}: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingNames, setUploadingNames] = useState<string[]>([]);
  const [deletingIds, setDeletingIds] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const showToast = useToast();

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      for (const file of Array.from(files)) {
        setUploadingNames((prev) => [...prev, file.name]);
        try {
          await uploadDocument(file);
          showToast("success", `${file.name} uploaded.`);
          onDocumentsChange();
        } catch (err) {
          showToast("error", err instanceof Error ? err.message : `Failed to upload ${file.name}.`);
        } finally {
          setUploadingNames((prev) => prev.filter((n) => n !== file.name));
        }
      }
    },
    [onDocumentsChange, showToast],
  );

  const handleDelete = useCallback(
    async (id: string) => {
      setDeletingIds((prev) => [...prev, id]);
      try {
        await deleteDocument(id);
        if (selectedDocumentId === id) onSelectDocument(null);
        onDocumentsChange();
      } catch (err) {
        showToast("error", err instanceof Error ? err.message : "Failed to delete document.");
      } finally {
        setDeletingIds((prev) => prev.filter((d) => d !== id));
      }
    },
    [onDocumentsChange, onSelectDocument, selectedDocumentId, showToast],
  );

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Documents</h2>

      <label
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${
          isDragging
            ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-950/30"
            : "border-zinc-200 hover:border-zinc-300 dark:border-zinc-800 dark:hover:border-zinc-700"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Drop files here or click to upload
        </span>
        <span className="text-xs text-zinc-400">PDF, Word, or TXT</span>
      </label>

      {uploadingNames.length > 0 && (
        <ul className="space-y-1.5">
          {uploadingNames.map((name) => (
            <li key={name} className="flex items-center gap-2 text-xs text-zinc-500">
              <span className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-zinc-300 border-t-indigo-500" />
              <span className="truncate">Uploading {name}…</span>
            </li>
          ))}
        </ul>
      )}

      <div className="flex-1 space-y-1 overflow-y-auto">
        {documents.length === 0 && uploadingNames.length === 0 ? (
          <p className="px-1 text-sm text-zinc-400">No documents yet.</p>
        ) : (
          <>
            <button
              onClick={() => onSelectDocument(null)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                selectedDocumentId === null
                  ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                  : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-900"
              }`}
            >
              All documents
            </button>

            {documents.map((doc) => (
              <div key={doc.document_id} className="flex items-center gap-1">
                <button
                  onClick={() => onSelectDocument(doc.document_id)}
                  className={`min-w-0 flex-1 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    selectedDocumentId === doc.document_id
                      ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300"
                      : "text-zinc-700 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-zinc-900"
                  }`}
                >
                  <span className="block truncate">{doc.document_name}</span>
                  <span className="block text-xs text-zinc-400">{doc.chunk_count} chunks</span>
                </button>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  disabled={deletingIds.includes(doc.document_id)}
                  aria-label={`Delete ${doc.document_name}`}
                  className="shrink-0 rounded-md p-2 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:hover:bg-red-950/30"
                >
                  {deletingIds.includes(doc.document_id) ? (
                    <span className="block h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-red-500" />
                  ) : (
                    <TrashIcon />
                  )}
                </button>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function TrashIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}
