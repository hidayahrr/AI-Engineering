import { serve } from "inngest/next";
import { inngest } from "@/lib/inngest/client";
import { runAIDecisionFlow } from "@/lib/inngest/functions";

// Serves the Inngest API endpoint at /api/inngest
export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [runAIDecisionFlow],
});