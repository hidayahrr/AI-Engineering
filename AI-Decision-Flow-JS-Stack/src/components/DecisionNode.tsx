"use client";

import React, { ChangeEvent } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";

export type DecisionNodeData = {
  label: string;
  prompt: string;
  status?: "idle" | "running" | "completed";
  lastDecision?: "YES" | "NO";
  onChangePrompt?: (id: string, newPrompt: string) => void;
};

export default function DecisionNode({ id, data }: NodeProps) {
  const nodeData = data as unknown as DecisionNodeData;

  // Dynamic border styling based on status
  let borderStyle = "border-slate-300";
  if (nodeData.status === "running") borderStyle = "border-yellow-500 animate-pulse ring-2 ring-yellow-400";
  if (nodeData.status === "completed") borderStyle = "border-green-500 ring-1 ring-green-400";

  return (
    <div className={`bg-white border-2 ${borderStyle} rounded-xl p-3 shadow-md min-w-[240px] transition-all`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500 w-3 h-3" />

      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          {nodeData.label || "Decision Node"}
        </span>
        {nodeData.lastDecision && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
            nodeData.lastDecision === "YES" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}>
            {nodeData.lastDecision}
          </span>
        )}
      </div>

      <textarea
        className="w-full text-xs p-2 border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-800 resize-none bg-slate-50"
        rows={2}
        placeholder="Type AI question..."
        value={nodeData.prompt || ""}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
          if (nodeData.onChangePrompt) nodeData.onChangePrompt(id, e.target.value);
        }}
      />

      <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100 text-[10px] font-bold">
        <div className="relative flex items-center text-green-600">
          <Handle type="source" position={Position.Bottom} id="yes" className="!bg-green-500 w-3 h-3 !left-2" />
          <span className="ml-5">YES</span>
        </div>
        <div className="relative flex items-center text-red-600">
          <span className="mr-5">NO</span>
          <Handle type="source" position={Position.Bottom} id="no" className="!bg-red-500 w-3 h-3 !left-auto !right-2" />
        </div>
      </div>
    </div>
  );
}