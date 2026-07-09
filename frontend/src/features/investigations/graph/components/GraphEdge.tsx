import { memo } from "react";
import type { EdgeProps } from "@xyflow/react";
import { BaseEdge, getBezierPath, EdgeLabelRenderer } from "@xyflow/react";

const EDGE_COLORS: Record<string, string> = {
  AUTHORED_BY: "#10b981",
  BELONGS_TO: "#f97316",
  INTRODUCES: "#ec4899",
  EVALUATED_ON: "#a855f7",
  USES: "#06b6d4",
  RELATED_TO: "#f59e0b",
  AFFILIATED_WITH: "#6366f1",
};

function GraphEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const label = (data as { label?: string })?.label ?? "";
  const color = EDGE_COLORS[label] ?? "#6b7280";

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={{ stroke: color, strokeWidth: 1.5 }} />
      <EdgeLabelRenderer>
        <div
          className="absolute z-10"
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: "all",
          }}
        >
          <span className="rounded bg-background px-1.5 py-0.5 text-[9px] font-medium tracking-wider text-text-muted border border-border shadow-xs">
            {label}
          </span>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

export default memo(GraphEdge);
