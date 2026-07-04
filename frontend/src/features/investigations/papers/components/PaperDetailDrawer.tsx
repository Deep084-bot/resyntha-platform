import React, { useCallback, useEffect, useRef, useState } from "react";
import { X, ExternalLink, Copy, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Paper } from "@/types";
import { cn } from "@/lib/utils";

export interface PaperDetailDrawerProps {
  paper: Paper | null;
  onClose: () => void;
}

function useCopyToClipboard(text: string) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard not available
    }
  }, [text]);

  return { copied, copy };
}

export function PaperDetailDrawer({ paper, onClose }: PaperDetailDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const doiCopied = useCopyToClipboard(paper?.doi ?? "");
  const titleCopied = useCopyToClipboard(paper?.title ?? "");

  // Store previous focus on open
  useEffect(() => {
    if (paper) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      const timer = setTimeout(() => {
        drawerRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [paper]);

  // Handle Escape to close
  useEffect(() => {
    if (!paper) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [paper, onClose]);

  // Restore focus on close
  useEffect(() => {
    if (!paper) {
      previousFocusRef.current?.focus();
      previousFocusRef.current = null;
    }
  }, [paper]);

  // Focus trap
  useEffect(() => {
    if (!paper) return;
    const drawer = drawerRef.current;
    if (!drawer) return;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const focusableEls = drawer.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusableEls.length === 0) return;
      const first = focusableEls[0];
      const last = focusableEls[focusableEls.length - 1];

      if (!first || !last) return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleTabKey);
    return () => document.removeEventListener("keydown", handleTabKey);
  }, [paper]);

  if (!paper) return null;

  const hasAbstract = paper.abstract != null && paper.abstract.length > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Paper details: ${paper.title}`}
        tabIndex={-1}
        className={cn(
          "fixed inset-y-0 right-0 z-50 w-full max-w-lg border-l border-border bg-surface shadow-xl",
          "flex flex-col overflow-y-auto",
          "transition-transform duration-300",
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border p-4">
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-semibold text-text-primary leading-snug">
              {paper.title}
            </h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close paper details"
            className="shrink-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-4 p-4">
          {/* Authors */}
          <Section label="Authors">
            <p className="text-sm text-text-primary">
              {paper.authors.length > 0
                ? paper.authors.join(", ")
                : "Unknown authors"}
            </p>
          </Section>

          {/* Venue & Year */}
          <div className="grid grid-cols-2 gap-4">
            {paper.venue && (
              <Section label="Venue">
                <p className="text-sm text-text-primary">{paper.venue}</p>
              </Section>
            )}
            {paper.year && (
              <Section label="Year">
                <p className="text-sm text-text-primary">{paper.year}</p>
              </Section>
            )}
          </div>

          {/* Citations & Source */}
          <div className="grid grid-cols-2 gap-4">
            {paper.citation_count != null && (
              <Section label="Citations">
                <p className="text-sm text-text-primary">
                  {paper.citation_count}
                </p>
              </Section>
            )}
            <Section label="Source">
              <p className="text-sm text-text-primary capitalize">
                {paper.source}
              </p>
            </Section>
          </div>

          {/* Score */}
          {paper.score != null && (
            <Section label="Relevance Score">
              <p className="text-sm text-text-primary">
                {paper.score.toFixed(2)}
              </p>
            </Section>
          )}

          {/* DOI */}
          {paper.doi && (
            <Section label="DOI">
              <div className="flex items-center gap-2">
                <code className="flex-1 truncate text-xs text-text-secondary">
                  {paper.doi}
                </code>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={doiCopied.copy}
                  aria-label="Copy DOI to clipboard"
                >
                  {doiCopied.copied ? (
                    <Check className="h-3 w-3 text-success" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>
            </Section>
          )}

          {/* Abstract */}
          {hasAbstract && (
            <Section label="Abstract">
              <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
                {paper.abstract}
              </p>
            </Section>
          )}

          {/* External links */}
          <div className="flex flex-wrap gap-2 pt-2">
            {paper.doi && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={`https://doi.org/${paper.doi}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open DOI in new tab"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open DOI
                </a>
              </Button>
            )}
            {paper.url && (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open PDF in new tab"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open PDF
                </a>
              </Button>
            )}
            {paper.title && (
              <Button
                variant="outline"
                size="sm"
                onClick={titleCopied.copy}
                aria-label="Copy title to clipboard"
              >
                {titleCopied.copied ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
                Copy title
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
        {label}
      </h3>
      <div className="mt-1">{children}</div>
    </div>
  );
}
