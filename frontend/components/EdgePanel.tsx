"use client";

import React, { useMemo } from "react";
import { Link, Node } from "@/lib/types";

interface EdgePanelProps {
  edge: (Link & { source: Node; target: Node }) | null;
  onClose: () => void;
}

export default function EdgePanel({ edge, onClose }: EdgePanelProps) {
  if (!edge) return null;

  const sourceNode = edge.source as Node;
  const targetNode = edge.target as Node;

  // Calculate confidence level based on overall score
  const confidence = useMemo(() => {
    const score = edge.score || edge.semantic || 0;
    if (score >= 0.75)
      return {
        level: "Strong",
        color: "text-green-400",
        bg: "bg-green-900/20",
      };
    if (score >= 0.5)
      return {
        level: "Moderate",
        color: "text-yellow-400",
        bg: "bg-yellow-900/20",
      };
    if (score >= 0.25)
      return {
        level: "Weak",
        color: "text-orange-400",
        bg: "bg-orange-900/20",
      };
    return { level: "Very Weak", color: "text-red-400", bg: "bg-red-900/20" };
  }, [edge.score, edge.semantic]);

  return (
    <div className="absolute top-0 right-0 w-96 h-full bg-gray-900 border-l border-gray-700 overflow-y-auto shadow-2xl">
      {/* Header */}
      <div className="sticky top-0 bg-gray-800 p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 className="text-xl font-bold text-purple-400">
          Connection Details
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Overall Score */}
        <div
          className={`p-3 rounded-lg ${confidence.bg} border border-gray-700`}
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-300">
              Connection Strength
            </h3>
            <span className={`text-2xl font-bold ${confidence.color}`}>
              {((edge.score || edge.semantic || 0) * 100).toFixed(0)}%
            </span>
          </div>
          <p className={`text-sm ${confidence.color}`}>
            {confidence.level} Connection
          </p>
        </div>

        {/* Similarity Breakdown */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            Similarity Breakdown
          </h3>
          <div className="space-y-2">
            {/* Semantic Score */}
            <div className="bg-gray-800 p-3 rounded">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-400">Semantic</span>
                <span className="text-lg font-semibold text-blue-400">
                  {((edge.semantic || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded h-2">
                <div
                  className="bg-blue-500 h-2 rounded transition-all"
                  style={{
                    width: `${Math.min((edge.semantic || 0) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>

            {/* Keyword Score */}
            {edge.keyword !== undefined && edge.keyword !== null && (
              <div className="bg-gray-800 p-3 rounded">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-400">Keyword</span>
                  <span className="text-lg font-semibold text-purple-400">
                    {((edge.keyword || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded h-2">
                  <div
                    className="bg-purple-500 h-2 rounded transition-all"
                    style={{
                      width: `${Math.min((edge.keyword || 0) * 100, 100)}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Processing Time */}
            {edge.time !== undefined && edge.time !== null && (
              <div className="bg-gray-800 p-3 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Processing Time</span>
                  <span className="text-sm font-mono text-gray-300">
                    {(edge.time * 1000).toFixed(0)}ms
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Source Node */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            From (Source)
          </h3>
          <div className="bg-gray-800 p-3 rounded border border-gray-700">
            <p className="text-white leading-relaxed text-sm mb-2">
              {sourceNode.text}
            </p>
            <p className="text-gray-500 font-mono text-xs break-all">
              {sourceNode.id}
            </p>
          </div>
        </div>

        {/* Target Node */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            To (Target)
          </h3>
          <div className="bg-gray-800 p-3 rounded border border-gray-700">
            <p className="text-white leading-relaxed text-sm mb-2">
              {targetNode.text}
            </p>
            <p className="text-gray-500 font-mono text-xs break-all">
              {targetNode.id}
            </p>
          </div>
        </div>

        {/* Connection Info */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            Connection IDs
          </h3>
          <div className="bg-gray-800 p-3 rounded space-y-2 text-xs">
            <div>
              <span className="text-gray-500">Source ID:</span>
              <p className="text-gray-300 font-mono break-all mt-1">
                {typeof edge.source === "string" ? edge.source : sourceNode.id}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Target ID:</span>
              <p className="text-gray-300 font-mono break-all mt-1">
                {typeof edge.target === "string" ? edge.target : targetNode.id}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
