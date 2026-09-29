# Integration & Usage Guide

This guide details how to integrate, communicate with, and invoke the **Quantitative Swing Trading Agent** across its supported runtime protocols and interfaces. It includes a curated collection of verified user prompts derived from integration tests, evaluation configurations, and core tool workflows.

---

## 1. Architecture & Protocol Endpoints

The agent runs as an ADK application on FastAPI (`app.fast_api_app:app`) and exposes three primary interaction protocols:

| Interface / Protocol | Endpoint / Command | Format | Use Case |
|---|---|---|---|
| **ADK Web UI** | `uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<ID>` | Web Browser UI | Local development, interactive chat, inspecting artifacts & A2UI cards |
| **Native ADK SSE Stream** | `POST /run_sse` | Server-Sent Events (SSE) / JSON | Real-time streaming into custom web apps & backend clients |
| **A2A Protocol (JSON-RPC)**| `POST /a2a/app/` | JSON-RPC 2.0 streaming | Agent-to-Agent federation, cross-agent coordination |
| **Agent Card Discovery** | `GET /a2a/app/.well-known/agent-card.json` | JSON | Discovery metadata: agent skills, capabilities, and version |
| **Reasoning Engine Adapter** | `POST /api/stream_reasoning_engine` | Line-delimited JSON stream | Vertex AI Console Playground and Vertex AI Agent Engine client |

---

## 2. Integration Patterns & Examples

### Pattern A: Native ADK Stream (`/run_sse`)

To integrate the agent into backend microservices or custom client applications:

1. **Create or resume a user session**:
   ```bash
   curl -X POST "http://127.0.0.1:8080/apps/app/users/trader_42/sessions" \
     -H "Content-Type: application/json" \
     -d '{"state": {"risk_tolerance": "moderate"}}'
   ```
   *Response*: `{"id": "session_abc123", ...}`

2. **Stream agent thoughts, tool calls, and replies**:
   ```bash
   curl -N -X POST "http://127.0.0.1:8080/run_sse" \
     -H "Content-Type: application/json" \
     -d '{
       "app_name": "app",
       "user_id": "trader_42",
       "session_id": "session_abc123",
       "new_message": {
         "role": "user",
         "parts": [{"text": "Analyze NVDA using moving average crossovers."}]
       },
       "streaming": true
     }'
   ```

---

### Pattern B: Agent-to-Agent (A2A) Client

The service implements the open Agent-to-Agent (A2A) specification. You can communicate with it programmatically using the `a2a` Python SDK:

```python
import asyncio
import uuid
import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest, TaskState

async def query_trading_agent(user_query: str):
    config = ClientConfig(
        streaming=True,
        httpx_client=httpx.AsyncClient(timeout=60.0),
    )
    client = await create_client("http://127.0.0.1:8080/a2a/app", config)
    
    request = SendMessageRequest(
        message=Message(
            message_id=f"msg-{uuid.uuid4()}",
            role=Role.ROLE_USER,
            parts=[Part(text=user_query)],
        )
    )
    
    async for chunk in client.send_message(request):
        if chunk.HasField("status_update"):
            print(f"Status: {chunk.status_update.status.state}")
        elif chunk.HasField("task"):
            print(f"Result: {chunk.task.output}")

asyncio.run(query_trading_agent("Show my current Firestore watchlist"))
```

---

### Pattern C: Reasoning Engine Protocol (`/api/stream_reasoning_engine`)

To forward calls via the Vertex AI Reasoning Engine adapter:

```bash
curl -N -X POST "http://127.0.0.1:8080/api/stream_reasoning_engine" \
  -H "Content-Type: application/json" \
  -d '{
    "class_method": "async_stream_query",
    "input": {
      "user_id": "trader_42",
      "message": "Generate a 3D financial animation video for Tesla stock."
    }
  }'
```

---

## 3. Verified Prompt Library (Categorized by Tool Capability)

### 📈 1. Quantitative Technical Analysis & Crossover Engine
*Triggers: `search_ticker`, `get_crossover_signals`*
- `"Analyze Apple stock for moving average crossovers."`
- `"What is the current 20, 50, and 200 SMA alignment for NVDA? Is there a Golden Cross?"`
- `"Check technical indicators and RSI momentum for Tesla."`
- `"Calculate swing entry, stop loss, and take-profit targets for Microsoft."`
- `"Evaluate NVIDE stock setup."` *(Tests typo tolerance and fuzzy ticker resolution)*

### 📰 2. News Sentiment & Market Catalysts
*Triggers: `get_company_news_sentiment`*
- `"Check the latest breaking headlines and market sentiment for Google."`
- `"Are there any upcoming earnings or regulatory risks impacting Meta stock right now?"`
- `"Summarize recent news catalyst risks for Amazon before I take a swing position."`

### 📋 3. Persistent Firestore Watchlist Management
*Triggers: `add_to_watchlist`, `get_watchlist`, `remove_from_watchlist`*
- `"Show my current watchlist."`
- `"Add AAPL to my watchlist with an entry at $320, target price $365, stop loss $309, and note 'Bullish SMA continuation'."`
- `"Update TSLA in my watchlist with target $386 and stop loss $340."`
- `"Remove NVDA from my watchlist."`

### 🎥 4. Omni 3D Financial Video Generation
*Triggers: `generate_stock_video` (Google Cloud Storage + ADK Artifact)*
- `"Generate a 3D financial video for NVDA showing a bullish breakout with glowing green candlesticks."`
- `"Create a short 3D stock chart video illustrating a Golden Cross surge for Tesla."`
- `"Visualize a market momentum animation for Apple stock."`

### 🧠 5. Cross-Session Long-Term Memory (Memory Bank)
*Triggers: `PreloadMemoryTool` (recall) & `generate_memories_callback` (write)*
- Session 1: `"Remember that I have a conservative risk tolerance and never trade without a strict 4% stop loss."`
- Session 2 (New Session): `"What trading parameters and risk limits do you have on file for me?"`
- Session 2 (New Session): `"Recommend a swing trade setup for Microsoft that fits my risk profile."`

---

## 4. Automated Testing & Verification

Run the test suite locally to verify runtime integrity and protocol routes:

```bash
# Run all unit and integration tests with Vertex AI enabled
GOOGLE_GENAI_USE_VERTEXAI=true uv run pytest tests/

# Run specific server integration test:
GOOGLE_GENAI_USE_VERTEXAI=true uv run pytest tests/integration/test_server_e2e.py -k test_agent_card
```
