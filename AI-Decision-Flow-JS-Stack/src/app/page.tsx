"use client";

import React from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const initialNodes: Node[] = [
  {
    id: "node-1",
    position: { x: 100, y: 150 },
    data: { label: "AI Node 1: Is user logged in?" },
    style: { padding: 12, borderRadius: 8, background: "#ffffff", border: "2px solid #000" },
  },
  {
    id: "node-2",
    position: { x: 450, y: 100 },
    data: { label: "AI Node 2: Show Dashboard (YES)" },
    style: { padding: 12, borderRadius: 8, background: "#e6ffe6", border: "1px solid #00aa00" },
  },
  {
    id: "node-3",
    position: { x: 450, y: 220 },
    data: { label: "AI Node 3: Redirect to Login (NO)" },
    style: { padding: 12, borderRadius: 8, background: "#ffe6e6", border: "1px solid #aa0000" },
  },
];

const initialEdges: Edge[] = [
  { id: "e1-2", source: "node-1", target: "node-2", label: "YES", animated: true },
  { id: "e1-3", source: "node-1", target: "node-3", label: "NO", animated: true },
];

export default function WorkflowPage() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-100">
      <header className="p-4 border-b bg-white flex justify-between items-center shadow-sm">
        <div>
          <h1 className="text-xl font-bold">Visual AI Decision Workflow</h1>
          <p className="text-xs text-slate-500">
            Phase 1: Pure Docker Stack (Next.js + React Flow + Inngest)
          </p>
        </div>
      </header>

      <div className="flex-1 w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}