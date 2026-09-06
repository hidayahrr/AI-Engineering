"use client";

import React, { ChangeEvent } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";

// Defines the data structure expected by each node
export type DecisionNodeData = {
  label: string;
  prompt: string;
  onChangePrompt?: (id: string, newPrompt: string) => void;
};

export default function DecisionNode({ id, data }: NodeProps) {
  const nodeData = data as unknown as DecisionNodeData;

  return (
    <div className="bg-white border-2 border-slate-700 rounded-lg p-3 shadow-md min-w-[220px]">
      {/* Top Handle: Receives incoming connection lines */}
      <Handle type="target" position={Position.Top} className="!bg-slate-600 w-3 h-3" />

      {/* Node Header */}
      <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
        {nodeData.label || "Decision Node"}
      </div>

      {/* Editable Prompt Input Field */}
      <textarea
        className="w-full text-sm p-1.5 border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-800 resize-none"
        rows={2}
        placeholder="Enter AI prompt..."
        value={nodeData.prompt || ""}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
          if (nodeData.onChangePrompt) {
            nodeData.onChangePrompt(id, e.target.value);
          }
        }}
      />

      {/* Output Handles for YES and NO routes */}
      <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-100 text-[10px] font-bold">
        {/* Left Output Handle: YES Path */}
        <div className="relative flex items-center text-green-600">
          <Handle
            type="source"
            position={Position.Bottom}
            id="yes"
            className="!bg-green-500 w-3 h-3 !left-2"
          />
          <span className="ml-5">YES</span>
        </div>

        {/* Right Output Handle: NO Path */}
        <div className="relative flex items-center text-red-600">
          <span className="mr-5">NO</span>
          <Handle
            type="source"
            position={Position.Bottom}
            id="no"
            className="!bg-red-500 w-3 h-3 !left-auto !right-2"
          />
        </div>
      </div>
    </div>
  );
}