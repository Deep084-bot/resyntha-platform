import { memo } from "react";
import type { NodeProps } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";

import { cn } from "@/lib/utils";
import type { NodeType } from "../types/graph";

const NODE_COLORS: Record<NodeType, { bg: string; border: string; text: string }> = {
  paper: { bg: "bg-blue-500/10", border: "border-blue-500", text: "text-blue-700" },
  author: { bg: "bg-emerald-500/10", border: "border-emerald-500", text: "text-emerald-700" },
  institution: { bg: "bg-orange-500/10", border: "border-orange-500", text: "text-orange-700" },
  dataset: { bg: "bg-purple-500/10", border: "border-purple-500", text: "text-purple-700" },
  technology: { bg: "bg-cyan-500/10", border: "border-cyan-500", text: "text-cyan-700" },
  methodology: { bg: "bg-pink-500/10", border: "border-pink-500", text: "text-pink-700" },
  research_domain: { bg: "bg-amber-500/10", border: "border-amber-500", text: "text-amber-700" },
};

const NODE_LABELS: Record<NodeType, string> = {
  paper: "Paper",
  author: "Author",
  institution: "Institution",
  dataset: "Dataset",
  technology: "Technology",
  methodology: "Methodology",
  research_domain: "Research Domain",
};

interface GraphNodeData {
  label: string;
  nodeType: NodeType;
  metadata: Record<string, unknown>;
  isHighlighted: boolean;
  isDimmed: boolean;
}

function GraphNode({ data, selected }: NodeProps) {
  const { label, nodeType, isHighlighted, isDimmed } = data as GraphNodeData;
  const colors = NODE_COLORS[nodeType] ?? NODE_COLORS.paper;
  const typeLabel = NODE_LABELS[nodeType] ?? nodeType;

  return (
    <div
      className={cn(
        "rounded-lg border-2 px-4 py-3 shadow-sm transition-all duration-200 min-w-[160px] max-w-[240px]",
        colors.bg,
        colors.border,
        selected && "shadow-md ring-2 ring-accent-default",
        isHighlighted && "ring-2 ring-yellow-400 shadow-lg scale-105",
        isDimmed && "opacity-30",
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />
      <Handle type="source" position={Position.Right} className="!bg-border" />

      <div className="flex flex-col gap-1">
        <span className={cn("text-[10px] font-semibold uppercase tracking-wider", colors.text)}>
          {typeLabel}
        </span>
        <span className="text-xs font-medium text-text-primary leading-snug line-clamp-3">
          {label}
        </span>
      </div>
    </div>
  );
}

export default memo(GraphNode);
