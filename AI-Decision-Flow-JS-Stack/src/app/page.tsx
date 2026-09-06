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

type LogEntry = {
  id: string;
  timestamp: string;
  message: string;
  type: "info" | "success" | "error";
};

export default function FlowEditorPage() {
  const nodeTypes = useMemo(() => ({ decisionNode: DecisionNode }), []);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (message: string, type: LogEntry["type"] = "info") => {
    const entry: LogEntry = {
      id: Math.random().toString(),
      timestamp: new Date().toLocaleTimeString(),
      message,
      type,
    };
    setLogs((prev) => [entry, ...prev]);
  };

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
      position: { x: 250, y: 80 },
      data: {
        label: "Node 1",
        prompt: "Is 10 greater than 5?",
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
      position: { x: 100 + nodes.length * 30, y: 100 + nodes.length * 30 },
      data: { label: `Node ${nodes.length + 1}`, prompt: "", onChangePrompt: handlePromptChange },
    };
    setNodes((nds) => nds.concat(newNode));
    addLog(`Added Node ${nodes.length + 1}`, "info");
  }, [nodes, setNodes, handlePromptChange]);

  // Export Workflow to JSON file
  const exportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({ nodes, edges }, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "workflow-graph.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    addLog("Exported workflow configuration to JSON", "success");
  };

  // Import Workflow from JSON file
  const importJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileReader = new FileReader();
    if (e.target.files && e.target.files[0]) {
      fileReader.readAsText(e.target.files[0], "UTF-8");
      fileReader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target?.result as string);
          if (parsed.nodes && parsed.edges) {
            const restoredNodes = parsed.nodes.map((n: Node) => ({
              ...n,
              data: { ...n.data, onChangePrompt: handlePromptChange },
            }));
            setNodes(restoredNodes);
            setEdges(parsed.edges);
            addLog("Successfully imported workflow JSON", "success");
          }
        } catch (err) {
          addLog("Failed to parse JSON file", "error");
        }
      };
    }
  };

  // Trigger Execution with Visual Logs & Animated Edges
  const runWorkflow = async () => {
    if (nodes.length === 0) return alert("Add at least one node!");
    setIsRunning(true);
    addLog("Starting workflow execution request...", "info");

    try {
      const res = await fetch("/api/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodes, edges, startNodeId: nodes[0].id }),
      });

      const data = await res.json();
      if (data.success) {
        addLog(`Execution triggered! Inngest Event ID: ${data.eventId}`, "success");
      } else {
        addLog(`Execution Error: ${data.error}`, "error");
      }
    } catch (err) {
      addLog(`Network Error: ${(err as Error).message}`, "error");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-50">
      {/* Top Header */}
      <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between z-10 shadow-sm">
        <h1 className="font-bold text-slate-800 text-sm">AI Decision Flow Canvas</h1>
        
        <div className="flex items-center gap-2">
          <button onClick={addNode} className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded">
            + Node
          </button>
          
          <button onClick={exportJSON} className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded">
            Export JSON
          </button>

          <label className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded cursor-pointer">
            Import JSON
            <input type="file" accept=".json" onChange={importJSON} className="hidden" />
          </label>

          <button
            onClick={runWorkflow}
            disabled={isRunning}
            className="bg-green-600 hover:bg-green-700 text-white text-xs font-semibold px-4 py-1.5 rounded shadow disabled:opacity-50 ml-2"
          >
            {isRunning ? "Running..." : "▶ Run Flow"}
          </button>
        </div>
      </header>

      {/* Main Flow Editor Area */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        <main className="flex-1 h-full">
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

        {/* Execution Logs Sidebar */}
        <aside className="w-full md:w-80 border-t md:border-t-0 md:border-l border-slate-200 bg-white flex flex-col h-48 md:h-full">
          <div className="p-3 border-b border-slate-100 font-bold text-xs text-slate-700 flex justify-between items-center">
            <span>Execution Logs</span>
            <button onClick={() => setLogs([])} className="text-[10px] text-slate-400 hover:text-slate-600">Clear</button>
          </div>
          <div className="flex-1 p-3 overflow-y-auto font-mono text-[11px] space-y-2">
            {logs.length === 0 ? (
              <p className="text-slate-400 italic">No execution logs yet...</p>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="border-b border-slate-50 pb-1">
                  <span className="text-slate-400 mr-2">[{log.timestamp}]</span>
                  <span className={log.type === "error" ? "text-red-600" : log.type === "success" ? "text-green-600" : "text-slate-700"}>
                    {log.message}
                  </span>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}