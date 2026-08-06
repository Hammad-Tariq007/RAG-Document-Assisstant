"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { askQuestion } from "@/lib/api";
import type { ChatMessage, DocumentSummary } from "@/lib/types";

import { MarkdownAnswer } from "./MarkdownAnswer";
import { useToast } from "./ToastProvider";

type Props = {
  selectedDocument: DocumentSummary | null;
  hasDocuments: boolean;
};

export function ChatPanel({ selectedDocument, hasDocuments }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const showToast = useToast();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const question = input.trim();
      if (!question || isAsking) return;

      if (!hasDocuments) {
        showToast("error", "Upload a document before asking a question.");
        return;
      }

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
        status: "done",
      };
      const assistantId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        status: "streaming",
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInput("");
      setIsAsking(true);

      try {
        await askQuestion(question, selectedDocument?.document_id ?? null, (text) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + text } : m)),
          );
        });
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, status: "done" } : m)),
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : "Something went wrong.";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, status: "error", content: m.content || message }
              : m,
          ),
        );
        showToast("error", message);
      } finally {
        setIsAsking(false);
      }
    },
    [hasDocuments, input, isAsking, selectedDocument, showToast],
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <p className="text-lg font-medium text-zinc-700 dark:text-zinc-300">
              Ask about your documents
            </p>
            <p className="max-w-sm text-sm text-zinc-400">
              {hasDocuments
                ? "Answers are grounded in your uploaded documents, with citations."
                : "Upload a PDF or text file to get started."}
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-6">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                    m.role === "user"
                      ? "whitespace-pre-wrap bg-indigo-600 text-white"
                      : "bg-zinc-50 text-zinc-800 dark:bg-zinc-900 dark:text-zinc-100"
                  }`}
                >
                  {m.role === "assistant" ? (
                    <>
                      <MarkdownAnswer content={m.content} />
                      {m.status === "streaming" && (
                        <span className="ml-1 inline-block h-3 w-1.5 animate-pulse bg-zinc-400 align-middle" />
                      )}
                    </>
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-zinc-100 p-4 dark:border-zinc-800 sm:px-8">
        <div className="mx-auto flex max-w-2xl items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={
              selectedDocument ? `Ask about ${selectedDocument.document_name}…` : "Ask a question…"
            }
            rows={1}
            className="flex-1 resize-none rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:ring-indigo-950"
          />
          <button
            type="submit"
            disabled={isAsking || !input.trim()}
            className="shrink-0 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isAsking ? "Asking…" : "Ask"}
          </button>
        </div>
      </form>
    </div>
  );
}
