import { inngest } from "./client";
import { GoogleGenAI } from "@google/genai";

// Initialize Gemini Client with your API key
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// Data structure definitions matching React Flow's graph
type NodeData = { label: string; prompt: string };
type FlowNode = { id: string; data: NodeData };
type FlowEdge = { id: string; source: string; target: string; sourceHandle: string };

type WorkflowPayload = {
  nodes: FlowNode[];
  edges: FlowEdge[];
  startNodeId: string;
};

export const runAIDecisionFlow = inngest.createFunction(
  { id: "run-ai-decision-flow" },
  { event: "flow/execute.requested" },
  async ({ event, step }) => {
    const { nodes, edges, startNodeId } = event.data as WorkflowPayload;

    let currentNodeId: string | null = startNodeId;
    const executionHistory: Array<{ nodeId: string; prompt: string; decision: "YES" | "NO" }> = [];

    // Loop through the graph node-by-node
    while (currentNodeId) {
      const activeNodeId: string = currentNodeId;
      const currentNode = nodes.find((n) => n.id === activeNodeId);

      if (!currentNode) break;

      // STEP 1: Ask Gemini AI to evaluate the prompt inside the node
      const aiDecision = await step.run(`eval-node-${activeNodeId}`, async () => {
        const response = await ai.models.generateContent({
          model: "gemini-3.5-flash",
          contents: `You are an AI decision engine. Analyze the following condition/question and decide whether the answer is YES or NO.
                    
Condition: "${currentNode.data.prompt}"

STRICT RULE: Reply ONLY with the word "YES" or "NO". Do not include punctuation, explanation, or extra characters.`,
        });

        const rawText = response.text?.trim().toUpperCase() || "NO";
        return rawText.includes("YES") ? "YES" : "NO";
      });

      // Track execution step in history array
      executionHistory.push({
        nodeId: activeNodeId,
        prompt: currentNode.data.prompt,
        decision: aiDecision,
      });

      // STEP 2: Find outgoing edge matching the decision ('yes' handle or 'no' handle)
      const targetHandle = aiDecision.toLowerCase(); // 'yes' or 'no'
      const matchingEdge = edges.find(
        (edge) => edge.source === activeNodeId && edge.sourceHandle === targetHandle
      );

      // STEP 3: Move to next node or finish if end of flow reached
      currentNodeId = matchingEdge ? matchingEdge.target : null;
    }

    return {
      status: "COMPLETED",
      history: executionHistory,
    };
  }
);