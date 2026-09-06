# Visual AI Workflow System (Pure Docker Setup)

An interactive, node-based visual AI decision engine built with **Next.js (App Router)**, **React Flow**, **Inngest**, and **Google Gemini AI**—configured to run entirely inside a containerized Docker environment.

---

## 🚀 Features

* **Visual Canvas Editor**: Drag, connect, and configure decision nodes using React Flow (`@xyflow/react`).
* **AI Decision Branching**: Evaluate prompts dynamically using Google Gemini (`gemini-2.5-flash`), enforcing strict `YES` or `NO` path routing.
* **Orchestration with Inngest**: Step-by-step workflow execution, tracking node history and maintaining fault-tolerant execution.
* **JSON Export / Import**: Save custom flow diagrams to a local `.json` file and reload them at any time.
* **Real-time Execution Logs**: Monitor active node evaluations and status directly from the side panel.

---

## 🛠️ Launching with Docker

### 1. Environment Setup

Create a `.env` file inside the `AI-Decision-Flow-JS-Stack` folder and populate it with your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Build and Start Services

Run the following command in PowerShell inside `AI-Decision-Flow-JS-Stack`:

```powershell
docker compose up --build
```

### 3. Application Endpoints

- **Visual Canvas UI**: [http://localhost:3000](http://localhost:3000)
- **Inngest Engine Dashboard**: [http://localhost:8288](http://localhost:8288)

## 📂 Project Structure

```plaintext
AI-Decision-Flow-JS-Stack/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── execute/route.ts      # Trigger workflow execution
│   │   │   └── inngest/route.ts      # Inngest API endpoint
│   │   └── page.tsx                  # React Flow Canvas & Sidebar Logs
│   ├── components/
│   │   └── DecisionNode.tsx          # Custom Decision Node Component
│   └── lib/
│       └── inngest/
│           ├── client.ts             # Inngest Client Initialization
│           └── functions.ts          # AI Graph Traversal & Gemini Logic
├── docker-compose.yml
├── Dockerfile
└── package.json
```