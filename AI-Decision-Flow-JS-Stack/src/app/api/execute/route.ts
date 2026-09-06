import { NextResponse } from "next/server";
import { inngest } from "@/lib/inngest/client";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { nodes, edges, startNodeId } = body;

    // Send execution request event to Inngest engine
    const event = await inngest.send({
      name: "flow/execute.requested",
      data: {
        nodes,
        edges,
        startNodeId: startNodeId || nodes[0]?.id,
      },
    });

    return NextResponse.json({ success: true, eventId: event.ids[0] });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: (error as Error).message },
      { status: 500 }
    );
  }
}