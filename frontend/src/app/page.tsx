"use client";

import { useCallback, useEffect, useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { DocumentPanel } from "@/components/DocumentPanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useToast } from "@/components/ToastProvider";
import { listDocuments } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const showToast = useToast();

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      showToast("error", err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      setIsLoadingDocuments(false);
    }
  }, [showToast]);

  useEffect(() => {
    // Initial fetch on mount — the setState happens after the await inside
    // refreshDocuments, not synchronously, so this isn't a cascading render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshDocuments();
  }, [refreshDocuments]);

  const selectedDocument = documents.find((d) => d.document_id === selectedDocumentId) ?? null;

  return (
    <div className="flex h-screen flex-col bg-zinc-50 dark:bg-zinc-950">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-zinc-100 px-4 dark:border-zinc-800 sm:px-6">
        <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Document Assistant
        </span>
        <ThemeToggle />
      </header>

      <div className="flex flex-1 flex-col overflow-hidden md:flex-row">
        <aside className="shrink-0 overflow-y-auto border-b border-zinc-100 dark:border-zinc-800 md:h-full md:w-72 md:border-b-0 md:border-r">
          {isLoadingDocuments ? (
            <div className="p-4 text-sm text-zinc-400">Loading documents…</div>
          ) : (
            <DocumentPanel
              documents={documents}
              selectedDocumentId={selectedDocumentId}
              onSelectDocument={setSelectedDocumentId}
              onDocumentsChange={refreshDocuments}
            />
          )}
        </aside>

        <main className="flex-1 overflow-hidden">
          <ChatPanel selectedDocument={selectedDocument} hasDocuments={documents.length > 0} />
        </main>
      </div>
    </div>
  );
}
