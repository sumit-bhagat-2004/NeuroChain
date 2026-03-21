"use client";

import { useState, useEffect } from "react";
import GraphCanvas from "@/components/GraphCanvas";
import NodePanel from "@/components/NodePanel";
import InputBar from "@/components/InputBar";
import { GraphData, Node } from "@/lib/types";
import { createNode, getGraph } from "@/lib/api";
import ConnectButton from "@/components/ConnectButton";

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    links: [],
  });
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReplayMode, setIsReplayMode] = useState(false);

  // Load initial graph data
  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    try {
      const data = await getGraph();
      setGraphData(data);
    } catch (err) {
      console.error("Failed to load graph:", err);
      // Initialize with empty graph if backend is not available
      setGraphData({ nodes: [], links: [] });
    }
  };

  const handleAddNode = async (text: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await createNode(text);

      // Update graph data with new node and connections
      setGraphData((prev) => ({
        nodes: [...prev.nodes, response.node],
        links: [...prev.links, ...response.connections],
      }));

      // Show success message (could be replaced with a toast notification)
      console.log("Node added successfully:", response.node.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create node");
      console.error("Error creating node:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
  };

  const handleClosePanel = () => {
    setSelectedNode(null);
  };

  const handleReplay = async () => {
    if (graphData.nodes.length === 0) return;

    setIsReplayMode(true);
    setGraphData({ nodes: [], links: [] });

    // Sort nodes by timestamp
    const sortedNodes = [...graphData.nodes].sort(
      (a, b) => a.timestamp - b.timestamp,
    );
    const allLinks = [...graphData.links];

    // Replay nodes one by one
    for (let i = 0; i < sortedNodes.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 400));

      const currentNode = sortedNodes[i];
      const relevantLinks = allLinks.filter(
        (link) =>
          (typeof link.source === "string" ? link.source : link.source.id) ===
            currentNode.id ||
          (typeof link.target === "string" ? link.target : link.target.id) ===
            currentNode.id,
      );

      setGraphData((prev) => ({
        nodes: [...prev.nodes, currentNode],
        links: [...prev.links, ...relevantLinks],
      }));
    }

    setIsReplayMode(false);
  };

  const handleReset = () => {
    setGraphData({ nodes: [], links: [] });
    setSelectedNode(null);
    setError(null);
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-gray-950">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-10 bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-purple-400">NeuroChain</h1>
            <p className="text-sm text-gray-400">Knowledge Graph Visualizer</p>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats */}
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-gray-300">
                  {graphData.nodes.length} Nodes
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
                <span className="text-gray-300">
                  {graphData.links.length} Connections
                </span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex gap-2">
              <button
                onClick={handleReplay}
                disabled={isReplayMode || graphData.nodes.length === 0}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
              >
                {isReplayMode ? "Replaying..." : "Replay"}
              </button>
              <button
                onClick={handleReset}
                disabled={graphData.nodes.length === 0}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        <ConnectButton />

        {/* Error Message */}
        {error && (
          <div className="mt-3 bg-red-900/50 border border-red-700 text-red-200 px-4 py-2 rounded-lg text-sm">
            {error}
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="absolute top-[73px] bottom-[100px] left-0 right-0">
        <GraphCanvas
          data={graphData}
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedNode?.id}
        />
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <NodePanel node={selectedNode} onClose={handleClosePanel} />
      )}

      {/* Input Bar */}
      <InputBar onSubmit={handleAddNode} isLoading={isLoading} />
    </div>
  );
}
