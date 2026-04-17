"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { motion } from "framer-motion";

/**
 * Custom React Flow edge for the workflow graph.
 *
 * Slice-29a: idle stroke only.
 * Slice-29b: state-driven shimmer + packet dot.
 *   - idle / armed / firing / packet / completed
 *   - shimmer (stroke-dashoffset) driven by CSS keyframes (see globals.css).
 *   - packet dot animates a small SVG circle along the bezier path using
 *     framer-motion's offsetPath support. Gated by prefers-reduced-motion.
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

const STROKE: Record<EdgeAnimatedState, string> = {
  idle: "#cbd5e1",
  armed: "#a5b4fc",
  firing: "#6366f1",
  packet: "#6366f1",
  completed: "#6366f1",
};

const WIDTH: Record<EdgeAnimatedState, number> = {
  idle: 1.25,
  armed: 1.5,
  firing: 2,
  packet: 2,
  completed: 1.5,
};

const OPACITY: Record<EdgeAnimatedState, number> = {
  idle: 0.55,
  armed: 0.8,
  firing: 0.95,
  packet: 0.95,
  completed: 0.9,
};

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
  const shimmering = state === "firing" || state === "packet";
  const showPacket = state === "packet";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        className={shimmering ? "graph-edge-shimmer" : undefined}
        style={{
          stroke: STROKE[state],
          strokeWidth: WIDTH[state],
          opacity: OPACITY[state],
        }}
        data-edge-state={state}
      />
      {showPacket ? (
        <EdgeLabelRenderer>
          <PacketDot path={edgePath} />
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}

/**
 * Small indigo circle that slides from source → target along the bezier.
 * Uses CSS `offset-path` via framer-motion's style transforms so we stay
 * on the compositor (no layout thrash). Renders inside EdgeLabelRenderer
 * so React Flow doesn't re-layout it.
 */
function PacketDot({ path }: { path: string }) {
  // prefers-reduced-motion is handled via CSS variable + animation fallback.
  return (
    <motion.span
      aria-hidden
      className="graph-edge-packet"
      initial={{ offsetDistance: "0%", opacity: 0 }}
      animate={{ offsetDistance: "100%", opacity: [0, 1, 1, 0] }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      style={{
        position: "absolute",
        width: 8,
        height: 8,
        borderRadius: "9999px",
        background: "#6366f1",
        boxShadow: "0 0 6px rgba(99,102,241,0.7)",
        offsetPath: `path('${path}')`,
        offsetRotate: "0deg",
      }}
    />
  );
}
