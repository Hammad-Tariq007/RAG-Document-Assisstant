import ReactMarkdown, { type Components } from "react-markdown";

/**
 * Renders the assistant's grounded answer as Markdown (the grounding prompt
 * asks the model to structure answers with headers/bullets/bold). [Source N]
 * citations are turned into inline code spans before parsing so Markdown's
 * own code-span mechanism can render them as pill badges below.
 */
export function MarkdownAnswer({ content }: { content: string }) {
  const withCitationSpans = content.replace(/\[Source (\d+)\]/g, "`[Source $1]`");

  return (
    <div className="space-y-2 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown components={components}>{withCitationSpans}</ReactMarkdown>
    </div>
  );
}

const components: Components = {
  h1: ({ children }) => (
    <h3 className="mt-3 mb-1 text-sm font-semibold text-zinc-900 dark:text-zinc-100">{children}</h3>
  ),
  h2: ({ children }) => (
    <h3 className="mt-3 mb-1 text-sm font-semibold text-zinc-900 dark:text-zinc-100">{children}</h3>
  ),
  h3: ({ children }) => (
    <h4 className="mt-3 mb-1 text-sm font-semibold text-zinc-900 dark:text-zinc-100">{children}</h4>
  ),
  p: ({ children }) => <p className="my-2 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  code: ({ children }) => (
    <span className="mx-0.5 inline-flex items-center rounded-md bg-violet-100 px-1.5 py-0.5 text-xs font-medium text-violet-800 dark:bg-violet-900/50 dark:text-violet-300">
      {children}
    </span>
  ),
};
