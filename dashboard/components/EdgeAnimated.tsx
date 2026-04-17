"use client";

import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

/**
 * Custom React Flow edge for the workflow graph (slice-29a).
 *
 * Slice 29a ships only the `idle` variant (static stroke). Slice 29b
 * adds `armed / firing / packet / completed` states driven by the
 * graph-state reducer.
 */

export type EdgeAnimatedState =
  | "idle"
  | "armed"
  | "firing"
  | "packet"
  | "completed";

interface EdgeAnimatedData extends Record<string, unknown> {
  kind: "sequential" | "delegation" | "fan-in";
  state?: EdgeAnimatedState;
}

export function EdgeAnimated(
  props: EdgeProps & { data?: EdgeAnimatedData },
) {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
  } = props;
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const state: EdgeAnimatedState = data?.state ?? "idle";
  const stroke =
    state === "completed"
      ? "#6366f1" // indigo-500
      : state === "firing" || state === "packet"
        ? "#6366f1"
        : "#cbd5e1"; // slate-300
  const strokeWidth = state === "idle" ? 1.25 : 1.75;

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        stroke,
        strokeWidth,
        opacity: state === "idle" ? 0.55 : 0.9,
      }}
      data-edge-state={state}
    />
  );
}
