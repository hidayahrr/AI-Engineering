import { OpenAI } from "openai";
import { inngest } from "./client";

type EvaluateDecisionEvent = {
  prompt?: string;
  nodeId?: string;
};

type DecisionResponse = {
  decision?: "YES" | "NO";
};

const geminiClient = new OpenAI({
  apiKey: process.env.GEMINI_API_KEY ?? "",
  baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/",
});

export const evaluateDecisionNode = inngest.createFunction(
  { 
    id: "evaluate-decision-node",
    event: "workflow/node.evaluate", // Combined trigger into the 1st argument
  },
  async ({ event, step }) => { // Handler is now the 2nd argument
    const data = event.data as EvaluateDecisionEvent;

    const result = await step.run("evaluate-prompt", async () => {
      const response = await geminiClient.chat.completions.create({
        model: "gemini-3.5-flash",
        messages: [
          {
            role: "system",
            content:
              'Evaluate the user prompt and respond strictly in JSON: {"decision": "YES"} or {"decision": "NO"}.',
          },
          {
            role: "user",
            content: data.prompt ?? "Is 5 greater than 3?",
          },
        ],
        response_format: { type: "json_object" },
      });

      const content = response.choices[0]?.message?.content;

      if (!content) {
        throw new Error("Gemini returned an empty response.");
      }

      let parsed: DecisionResponse;

      try {
        parsed = JSON.parse(content) as DecisionResponse;
      } catch {
        throw new Error(`Invalid JSON returned by Gemini: ${content}`);
      }

      const decision: "YES" | "NO" =
        parsed.decision === "YES" || parsed.decision === "NO"
          ? parsed.decision
          : "NO";

      return {
        nodeId: data.nodeId ?? "test-node",
        decision,
        reason: "Evaluated using Gemini API.",
      };
    });

    return {
      status: "completed",
      result,
    };
  }
);