import { serve } from "inngest/next";
import { inngest } from "@/lib/inngest/client";
import { evaluateDecisionNode } from "@/lib/inngest/functions";

export const { GET, POST, PUT } = serve({
  client: inngest,
  baseUrl: process.env.INNGEST_BASE_URL ?? "http://inngest:8288",
  serveHost: process.env.INNGEST_SERVE_HOST ?? "http://app:3000",
  functions: [
    evaluateDecisionNode,
  ],
});