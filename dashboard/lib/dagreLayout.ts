/**
 * Pure positional layout for React Flow nodes using dagre (slice-29a).
 * Separate from buildGraph() so each can be tested in isolation.
 */

import * as dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";

export type LayoutDirection = "LR" | "TB";

const NODE_WIDTH = 220;
const NODE_HEIGHT = 96;

/**
 * Run dagre over the given React Flow nodes + edges and return the nodes
 * with `position` set. Direction defaults to `LR` (left-to-right).
 */
export function layoutNodes<N extends Node>(
  nodes: N[],
  edges: Edge[],
  direction: LayoutDirection = "LR",
): N[] {
  if (nodes.length === 0) return nodes;

  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({
    rankdir: direction,
    marginx: 24,
    marginy: 24,
    nodesep: 40,
    ranksep: 80,
  });

  for (const node of nodes) {
    graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of edges) {
    graph.setEdge(edge.source, edge.target);
  }
  dagre.layout(graph);

  return nodes.map((node) => {
    const pos = graph.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}
