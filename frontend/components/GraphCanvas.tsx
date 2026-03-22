"use client";

import React, { useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { GraphData, Node } from "@/lib/types";

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface GraphCanvasProps {
  data: GraphData;
  onNodeClick?: (node: Node) => void;
  onLinkClick?: (link: any) => void;
  selectedNodeId?: string | null;
  newNodeId?: string | null;
  onEdgeClick?: (edge: any) => void;
}

export default function GraphCanvas({
  data,
  onNodeClick,
  onLinkClick,
  onEdgeClick,
  selectedNodeId,
  newNodeId,
}: GraphCanvasProps) {
  const graphRef = useRef<any>(null);

  const handleNodeClick = useCallback(
    (node: any) => {
      if (onNodeClick) {
        onNodeClick(node as Node);
      }
    },
    [onNodeClick],
  );

  const handleLinkClick = useCallback(
    (link: any) => {
      // Log to console
      const edgeData = {
        source: typeof link.source === "object" ? link.source.id : link.source,
        target: typeof link.target === "object" ? link.target.id : link.target,
        score: link.score,
        semantic: link.semantic,
        keyword: link.keyword,
        time: link.time,
      };
      console.log("Link clicked:", edgeData);

      // Call edge click handler with full data
      if (onEdgeClick) {
        onEdgeClick(link);
      }

      // Also call legacy onLinkClick if provided
      if (onLinkClick) {
        onLinkClick(link);
      }
    },
    [onLinkClick, onEdgeClick],
  );

  const paintNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      // Safety check: ensure node has valid coordinates
      if (!isFinite(node.x) || !isFinite(node.y)) {
        return; // Skip rendering if coordinates are invalid
      }

      const label = node.text;
      const fontSize = 12 / globalScale;
      const isSelected = node.id === selectedNodeId;
      const isNew = node.id === newNodeId;

      // Draw glow for new nodes
      if (isNew) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 12, 0, 2 * Math.PI);
        const gradient = ctx.createRadialGradient(
          node.x,
          node.y,
          0,
          node.x,
          node.y,
          12,
        );
        gradient.addColorStop(0, "rgba(139, 92, 246, 0.8)");
        gradient.addColorStop(1, "rgba(139, 92, 246, 0)");
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // Draw node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = isNew ? "#a78bfa" : isSelected ? "#3b82f6" : "#8b5cf6";
      ctx.fill();

      // Draw outline if selected or new
      if (isSelected || isNew) {
        ctx.strokeStyle = isNew ? "#a78bfa" : "#60a5fa";
        ctx.lineWidth = isNew ? 3 / globalScale : 2 / globalScale;
        ctx.stroke();
      }

      // Draw label
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#e5e7eb";
      ctx.fillText(
        label.substring(0, 30) + (label.length > 30 ? "..." : ""),
        node.x,
        node.y + 8,
      );
    },
    [selectedNodeId, newNodeId],
  );

  const paintLink = useCallback(
    (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const start = link.source;
      const end = link.target;

      // Safety check: ensure start and end have valid coordinates
      if (
        !start ||
        !end ||
        !isFinite(start.x) ||
        !isFinite(start.y) ||
        !isFinite(end.x) ||
        !isFinite(end.y)
      ) {
        return; // Skip rendering if coordinates are invalid
      }

      // Draw link
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);

      // Color based on score (use semantic score for primary color)
      const semanticScore = link.semantic || link.score || 0;
      const alpha = Math.min(semanticScore, 1);
      ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`;
      ctx.lineWidth = 1 / globalScale;
      ctx.stroke();

      // Draw score label showing overall score
      const textPos = Object.assign(
        {},
        ...["x", "y"].map((c) => ({
          [c]: start[c] + (end[c] - start[c]) / 2,
        })),
      );

      ctx.font = `${10 / globalScale}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#9ca3af";

      // Show overall score (or semantic if that's the primary)
      const displayScore = link.score || semanticScore;
      ctx.fillText((displayScore * 100).toFixed(0) + "%", textPos.x, textPos.y);
    },
    [],
  );

  return (
    <div className="w-full h-full bg-gray-950">
      <ForceGraph2D
        ref={graphRef}
        graphData={data}
        nodeLabel="text"
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          // Define clickable area for nodes
          // Safety check for valid coordinates
          if (!isFinite(node.x!) || !isFinite(node.y!)) return;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, 5, 0, 2 * Math.PI);
          ctx.fill();
        }}
        linkCanvasObject={paintLink}
        linkPointerAreaPaint={(link, color, ctx) => {
          // Define clickable area for links
          const start = link.source as any;
          const end = link.target as any;
          if (
            !start ||
            !end ||
            !isFinite(start.x) ||
            !isFinite(start.y) ||
            !isFinite(end.x) ||
            !isFinite(end.y)
          )
            return;

          ctx.strokeStyle = color;
          ctx.lineWidth = 3; // Wider for easier clicking
          ctx.beginPath();
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
        }}
        onNodeClick={handleNodeClick}
        onLinkClick={handleLinkClick}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        backgroundColor="#030712"
        warmupTicks={100}
        cooldownTicks={0}
      />
    </div>
  );
}
