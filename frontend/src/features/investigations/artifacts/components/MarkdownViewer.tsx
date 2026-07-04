import { useMemo } from "react";

export interface MarkdownViewerProps {
  content: string;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderInline(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code class='rounded bg-surface-active px-1 text-xs text-accent-default'>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "<a href='$2' class='text-accent-default underline' target='_blank' rel='noopener noreferrer'>$1</a>");
}

export function MarkdownViewer({ content }: MarkdownViewerProps) {
  const html = useMemo(() => {
    const lines = content.split("\n");
    const result: string[] = [];
    let inList = false;
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();

      // Code blocks
      if (line.startsWith("```")) {
        if (inCodeBlock) {
          result.push(`<pre class="overflow-x-auto rounded-md bg-surface-active p-3 text-xs leading-relaxed"><code>${escapeHtml(codeBlockContent.join("\n"))}</code></pre>`);
          codeBlockContent = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      // Close list if needed
      if (inList && !line.startsWith("- ") && !line.startsWith("* ") && !/^\d+\.\s/.test(line)) {
        result.push("</ul>");
        inList = false;
      }

      // Empty line
      if (line === "") {
        result.push("<div class='h-2' />");
        continue;
      }

      // Headings
      if (line.startsWith("### ")) {
        result.push(`<h3 class="mt-4 mb-2 text-base font-semibold text-text-primary">${renderInline(line.slice(4))}</h3>`);
        continue;
      }
      if (line.startsWith("## ")) {
        result.push(`<h2 class="mt-5 mb-2 text-lg font-semibold text-text-primary">${renderInline(line.slice(3))}</h2>`);
        continue;
      }
      if (line.startsWith("# ")) {
        result.push(`<h1 class="mt-6 mb-3 text-xl font-bold text-text-primary">${renderInline(line.slice(2))}</h1>`);
        continue;
      }

      // Unordered list
      if (line.startsWith("- ") || line.startsWith("* ")) {
        if (!inList) {
          result.push("<ul class='list-disc pl-5 space-y-1 text-sm text-text-secondary'>");
          inList = true;
        }
        result.push(`<li>${renderInline(line.slice(2))}</li>`);
        continue;
      }

      // Ordered list
      if (/^\d+\.\s/.test(line)) {
        if (!inList) {
          result.push("<ol class='list-decimal pl-5 space-y-1 text-sm text-text-secondary'>");
          inList = true;
        }
        result.push(`<li>${renderInline(line.replace(/^\d+\.\s/, ""))}</li>`);
        continue;
      }

      // Horizontal rule
      if (/^-{3,}$/.test(line)) {
        result.push("<hr class='my-4 border-border' />");
        continue;
      }

      // Blockquote
      if (line.startsWith("> ")) {
        result.push(`<blockquote class="border-l-2 border-accent-default pl-3 text-sm italic text-text-secondary">${renderInline(line.slice(2))}</blockquote>`);
        continue;
      }

      // Paragraph
      result.push(`<p class="text-sm text-text-secondary leading-relaxed">${renderInline(line)}</p>`);
    }

    // Close open tags
    if (inList) result.push("</ul>");
    if (inCodeBlock) {
      result.push(`<pre class="overflow-x-auto rounded-md bg-surface-active p-3 text-xs leading-relaxed"><code>${escapeHtml(codeBlockContent.join("\n"))}</code></pre>`);
    }

    return result.join("\n");
  }, [content]);

  return (
    <div
      className="prose prose-sm max-w-none space-y-1"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
