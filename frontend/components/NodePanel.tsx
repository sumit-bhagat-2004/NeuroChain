"use client";

import React, { useEffect, useState } from "react";
import { Node } from "@/lib/types";
import { getProof } from "@/lib/api";

interface NodePanelProps {
  node: Node | null;
  onClose: () => void;
}

interface ProofData {
  node_id: string;
  text_hash: string;
  embedding_hash: string;
  timestamp: number;
  creator: string;
  app_id: number;
}

export default function NodePanel({ node, onClose }: NodePanelProps) {
  const [proof, setProof] = useState<ProofData | null>(null);
  const [loadingProof, setLoadingProof] = useState(false);

  useEffect(() => {
    if (!node) return;
    setProof(null);
    setLoadingProof(true);
    getProof(node.id)
      .then(setProof)
      .finally(() => setLoadingProof(false));
  }, [node?.id]);

  if (!node) return null;

  return (
    <div className="absolute top-0 right-0 w-96 h-full bg-gray-900 border-l border-gray-700 overflow-y-auto shadow-2xl">
      <div className="sticky top-0 bg-gray-800 p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 className="text-xl font-bold text-purple-400">Node Details</h2>
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
        {/* Node ID */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-1">Node ID</h3>
          <p className="text-white font-mono text-xs break-all bg-gray-800 p-2 rounded">
            {node.id}
          </p>
        </div>

        {/* Content */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-1">Content</h3>
          <p className="text-white bg-gray-800 p-3 rounded leading-relaxed">
            {node.text}
          </p>
        </div>

        {/* Timestamp */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-1">Created</h3>
          <p className="text-white bg-gray-800 p-2 rounded">
            {new Date(node.timestamp).toLocaleString()}
          </p>
        </div>

        {/* Embedding Preview */}
        {node.embedding && node.embedding.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-400 mb-1">
              Embedding Vector
            </h3>
            <div className="bg-gray-800 p-2 rounded">
              <p className="text-white font-mono text-xs">
                [{node.embedding.slice(0, 5).map((v) => v.toFixed(4)).join(", ")}...]
              </p>
              <p className="text-gray-500 text-xs mt-1">
                Dimension: {node.embedding.length}
              </p>
            </div>
          </div>
        )}

        {/* ── Algorand Proof Section ── */}
        <div className="border border-purple-800 rounded-lg overflow-hidden">
          <div className="bg-purple-900/40 px-3 py-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></div>
            <span className="text-purple-300 text-sm font-semibold">
              Algorand Proof
            </span>
          </div>

          {loadingProof && (
            <div className="p-4 text-center text-gray-400 text-sm">
              Fetching on-chain proof...
            </div>
          )}

          {!loadingProof && !proof && (
            <div className="p-4 text-center text-gray-500 text-sm">
              Not yet anchored on-chain
            </div>
          )}

          {!loadingProof && proof && (
            <div className="p-3 space-y-3">
              {/* Verified badge */}
              <div className="flex items-center gap-2 text-green-400 text-sm font-medium">
                <svg
                  className="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                Verified on Algorand
              </div>

              <div>
                <p className="text-xs text-gray-400 mb-1">App ID</p>
                <p className="text-purple-400 font-mono text-xs">
                  {proof.app_id}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-400 mb-1">
                  Text Hash (SHA-256)
                </p>
                <p className="text-white font-mono text-xs break-all bg-gray-800 p-2 rounded">
                  {proof.text_hash}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-400 mb-1">
                  Embedding Hash (AI fingerprint)
                </p>
                <p className="text-white font-mono text-xs break-all bg-gray-800 p-2 rounded">
                  {proof.embedding_hash}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-400 mb-1">Anchored at</p>
                <p className="text-white text-xs">
                  {new Date(proof.timestamp * 1000).toLocaleString()}
                </p>
              </div>

              <div className="pt-1 border-t border-gray-700">
                <p className="text-xs text-gray-500 italic">
                  "We store not just what was said, but how the AI understood
                  it."
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
