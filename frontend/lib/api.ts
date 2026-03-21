import { CreateNodeRequest, CreateNodeResponse, GraphData } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createNode(text: string): Promise<CreateNodeResponse> {
  const response = await fetch(`${API_BASE_URL}/node`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text } as CreateNodeRequest),
  });

  if (!response.ok) {
    throw new Error(`Failed to create node: ${response.statusText}`);
  }

  return response.json();
}

export async function getGraph(): Promise<GraphData> {
  const response = await fetch(`${API_BASE_URL}/graph`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch graph: ${response.statusText}`);
  }

  return response.json();
}

export async function getNode(id: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/node/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch node: ${response.statusText}`);
  }

  return response.json();
}

export async function getProof(nodeId: string): Promise<{
  node_id: string;
  text_hash: string;
  embedding_hash: string;
  timestamp: number;
  creator: string;
  app_id: number;
} | null> {
  try {
    const response = await fetch(`http://localhost:8001/proof/${nodeId}`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}
