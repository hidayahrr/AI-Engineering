"use client";

import React, { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import DecisionNode from "@/components/DecisionNode";

export default function FlowEditorPage() {
  const nodeTypes = useMemo(() => ({ decisionNode: DecisionNode }), []);
  const [isRunning, setIsRunning] = useState(false);

  const handlePromptChange = useCallback((nodeId: string, newPrompt: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, prompt: newPrompt } };
        }
        return node;
      })
    );
  }, []);

  const initialNodes: Node[] = [
    {
      id: "node-1",
      type: "decisionNode",
      position: { x: 250, y: 100 },
      data: {
        label: "Start Node",
        prompt: "Is the user asking for customer support?",
        onChangePrompt: handlePromptChange,
      },
    },
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const onConnect = useCallback(
    (params: Connection) => {
      const isYes = params.sourceHandle === "yes";
      const newEdge: Edge = {
        ...params,
        id: `e-${params.source}-${params.target}-${params.sourceHandle}`,
        animated: true,
        label: isYes ? "YES" : "NO",
        style: { stroke: isYes ? "#22c55e" : "#ef4444", strokeWidth: 2 },
        labelStyle: { fill: isYes ? "#15803d" : "#b91c1c", fontWeight: 700 },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const addNode = useCallback(() => {
    const newNodeId = `node-${nodes.length + 1}`;
    const newNode: Node = {
      id: newNodeId,
      type: "decisionNode",
      position: { x: 100 + nodes.length * 40, y: 100 + nodes.length * 40 },
      data: { label: `Node ${nodes.length + 1}`, prompt: "", onChangePrompt: handlePromptChange },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [nodes, setNodes, handlePromptChange]);

  // Triggers workflow execution via Next.js API
  const runWorkflow = async () => {
    if (nodes.length === 0) return alert("Add at least one node to run!");
    setIsRunning(true);

    try {
      const res = await fetch("/api/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nodes,
          edges,
          startNodeId: nodes[0].id,
        }),
      });

      const data = await res.json();
      if (data.success) {
        alert(`Workflow execution triggered successfully! Event ID: ${data.eventId}`);
      } else {
        alert(`Failed to start workflow: ${data.error}`);
      }
    } catch (err) {
      alert(`Execution Error: ${(err as Error).message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-50">
      <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-10 shadow-sm">
        <h1 className="font-bold text-slate-800 text-base">AI Decision Flow Canvas</h1>
        <div className="flex gap-3">
          <button
            onClick={addNode}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold px-4 py-2 rounded transition-colors"
          >
            + Add Decision Node
          </button>
          <button
            onClick={runWorkflow}
            disabled={isRunning}
            className="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold px-4 py-2 rounded shadow transition-colors disabled:opacity-50"
          >
            {isRunning ? "Starting..." : "▶ Run AI Flow"}
          </button>
        </div>
      </header>

      <main className="flex-1 w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#cbd5e1" gap={16} />
          <Controls />
        </ReactFlow>
      </main>
    </div>
  );
}