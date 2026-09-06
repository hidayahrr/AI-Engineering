"use client";

import React, { useCallback, useMemo } from "react";
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

import DecisionNode, { DecisionNodeData } from "@/components/DecisionNode";

export default function FlowEditorPage() {
  // Register custom node types
  const nodeTypes = useMemo(() => ({ decisionNode: DecisionNode }), []);

  // Handler to update a node's prompt inside local state
  const handlePromptChange = useCallback((nodeId: string, newPrompt: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              prompt: newPrompt,
            },
          };
        }
        return node;
      })
    );
  }, []);

  // Initial starter nodes on the canvas
  const initialNodes: Node[] = [
    {
      id: "node-1",
      type: "decisionNode",
      position: { x: 250, y: 100 },
      data: {
        label: "Start Node",
        prompt: "Is 5 greater than 3?",
        onChangePrompt: handlePromptChange,
      },
    },
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Connects two nodes with labeled YES/NO lines
  const onConnect = useCallback(
    (params: Connection) => {
      const isYes = params.sourceHandle === "yes";
      const newEdge: Edge = {
        ...params,
        id: `e-${params.source}-${params.target}-${params.sourceHandle}`,
        animated: true,
        label: isYes ? "YES" : "NO",
        style: {
          stroke: isYes ? "#22c55e" : "#ef4444",
          strokeWidth: 2,
        },
        labelStyle: {
          fill: isYes ? "#15803d" : "#b91c1c",
          fontWeight: 700,
        },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // Button function to spawn a new decision node on the canvas
  const addNode = useCallback(() => {
    const newNodeId = `node-${nodes.length + 1}`;
    const newNode: Node = {
      id: newNodeId,
      type: "decisionNode",
      position: { x: 100 + nodes.length * 40, y: 100 + nodes.length * 40 },
      data: {
        label: `Node ${nodes.length + 1}`,
        prompt: "",
        onChangePrompt: handlePromptChange,
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [nodes, setNodes, handlePromptChange]);

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-50">
      {/* Top Action Bar */}
      <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-10 shadow-sm">
        <h1 className="font-bold text-slate-800 text-base">AI Decision Flow Canvas</h1>
        <button
          onClick={addNode}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded shadow transition-colors"
        >
          + Add Decision Node
        </button>
      </header>

      {/* Main Flow Canvas Area */}
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