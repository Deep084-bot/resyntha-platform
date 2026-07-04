import { useState, useMemo } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

export interface JsonViewerProps {
  data: unknown;
  depth?: number;
  keyName?: string;
}

function JsonLeaf({
  value,
  keyName,
  depth = 0,
}: {
  value: unknown;
  keyName?: string;
  depth?: number;
}) {
  let display: string;
  let color: string;

  if (value === null) {
    display = "null";
    color = "text-destructive";
  } else if (typeof value === "string") {
    display = `"${value}"`;
    color = "text-success";
  } else if (typeof value === "number") {
    display = String(value);
    color = "text-accent-default";
  } else if (typeof value === "boolean") {
    display = String(value);
    color = "text-warning";
  } else {
    display = String(value);
    color = "text-text-secondary";
  }

  return (
    <div className="flex items-baseline gap-1" style={{ paddingLeft: depth * 16 }}>
      {keyName !== undefined && (
        <span className="shrink-0 text-text-primary">&quot;{keyName}&quot;: </span>
      )}
      <span className={cn("font-mono text-xs", color)}>{display}</span>
    </div>
  );
}

function JsonBranch({
  data,
  keyName,
  depth = 0,
}: JsonViewerProps) {
  const [collapsed, setCollapsed] = useState(depth >= 3);
  const isArray = Array.isArray(data);
  const entries = useMemo(
    () =>
      isArray
        ? data.map((v, i) => [String(i), v] as [string, unknown])
        : Object.entries(data as Record<string, unknown>),
    [data, isArray],
  );
  const isEmpty = entries.length === 0;
  const bracket = isArray ? ["[", "]"] : ["{", "}"];

  return (
    <div style={{ paddingLeft: depth * 16 }}>
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-1 hover:text-text-primary transition-colors"
        aria-expanded={!collapsed}
        aria-label={
          keyName !== undefined
            ? `Collapse ${keyName}`
            : `Collapse ${isArray ? "array" : "object"}`
        }
      >
        {isEmpty ? (
          <span className="w-3" />
        ) : collapsed ? (
          <ChevronRight className="h-3 w-3 shrink-0 text-text-muted" />
        ) : (
          <ChevronDown className="h-3 w-3 shrink-0 text-text-muted" />
        )}
        {keyName !== undefined && (
          <span className="text-xs text-text-primary font-mono">
            &quot;{keyName}&quot;:{" "}
          </span>
        )}
        <span className="text-xs text-text-muted font-mono">
          {collapsed
            ? `${bracket[0]} ${entries.length} ${entries.length === 1 ? "item" : "items"} ${bracket[1]}`
            : bracket[0]}
        </span>
      </button>

      {!collapsed && !isEmpty && (
        <div className="border-l border-border ml-1.5">
          {entries.map(([k, v]) =>
            v !== null && typeof v === "object" ? (
              <JsonBranch key={k} data={v} keyName={k} depth={depth + 1} />
            ) : (
              <JsonLeaf key={k} value={v} keyName={k} depth={depth + 1} />
            ),
          )}
          <div
            className="text-xs text-text-muted font-mono"
            style={{ paddingLeft: (depth + 1) * 16 }}
          >
            {bracket[1]}
          </div>
        </div>
      )}
    </div>
  );
}

export function JsonViewer({ data, depth = 0, keyName }: JsonViewerProps) {
  if (data === null || typeof data !== "object") {
    return <JsonLeaf value={data} keyName={keyName} depth={depth} />;
  }

  return <JsonBranch data={data} keyName={keyName} depth={depth} />;
}
