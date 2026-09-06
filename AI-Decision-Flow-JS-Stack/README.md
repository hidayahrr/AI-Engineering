# ⚡ Visual AI Workflow System (Pure Docker Setup)

Node-based AI decision engine built with Next.js, React Flow, Inngest, and OpenAI—configured to run entirely inside Docker.

---

## 🛠️ Launching with Docker

### 1. Environment Setup

Populate `.env`:

```env
OPENAI_API_KEY=your_actual_openai_api_key
```

### 2. Build and Start Services

PowerShell:

```powershell
docker compose up --build
```

### 3. Application Endpoints

- **Visual Canvas UI**: `http://localhost:3000`
- **Inngest Engine Dashboard**: `http://localhost:8288`