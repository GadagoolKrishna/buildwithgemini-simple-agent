# Quantitative Swing Trading Agent

An autonomous swing trading intelligence agent built with the **Google Agent Development Kit (ADK)** and `agents-cli`. The agent automates technical moving average crossover strategies, analyzes real-time market sentiment catalysts, manages persistent watchlists in **Google Cloud Firestore**, generates dynamic 3D financial market visualizations using Google's Omni model (**`gemini-omni-flash-preview`**), and emits structured **A2UI** interactive display cards.

![Swing Trading Agent Demo](demo.gif)

---

## What the Agent Does

The agent evaluates swing trade setups using disciplined technical and fundamental data, remembers trader profiles and risk constraints across sessions, and generates visual video briefs:

1. **Company & Ticker Resolution (`search_ticker`)**:
   - Resolves everyday company names (e.g., "Apple", "NVIDIA", "Tesla", "Microsoft") and aliases/typos to official stock tickers and primary exchange identifiers.

2. **1-Year Crossover & Momentum Engine (`get_crossover_signals`)**:
   - Retrieves 1-year daily OHLCV historical candlestick data.
   - Computes **20-day**, **50-day**, and **200-day Simple Moving Averages (SMA)**.
   - Calculates **14-day Relative Strength Index (RSI)** for momentum confirmation.
   - Scans for **Golden Cross** (bullish) and **Death Cross** (bearish) trigger signals.
   - Derives risk-managed swing trade parameters: Entry Price, 20-day Support, Resistance, Suggested Stop-Loss, and Take-Profit Targets with conviction scores.

3. **News Sentiment & Catalyst Risk Analysis (`get_company_news_sentiment`)**:
   - Ingests real-time financial headlines directly from RSS market feeds.
   - Flags market catalyst events (earnings reports, guidance revisions, regulatory actions) before trade entry.

4. **Persistent Portfolio Watchlist (`add_to_watchlist`, `get_watchlist`, `remove_from_watchlist`)**:
   - Backed by **Google Cloud Firestore** (Native mode).
   - Persists user symbols, target prices, entry levels, and custom trade notes across sessions in the `watchlist` collection.

5. **3D Financial Video Generation (`generate_stock_video`)**:
   - Generates motion graphics and dynamic 3D candlestick chart videos using **`gemini-omni-flash-preview`** in Vertex AI (`global` region).
   - Automatically registers the video as an ADK session artifact (`tool_context.save_artifact`) for the development playground.
   - Uploads MP4 video bytes directly to a public **Google Cloud Storage** bucket, returning a shareable HTTPS URL.

6. **Interactive A2UI Card Generation**:
   - Formats outputs as **A2UI v0.8** interactive cards using `Card`, `Column`, `Row`, `Text`, and `Image` primitives.
   - Wired via an ADK `after_model_callback` (`a2ui_callback` in `app/a2ui_utils.py`) to render UI surfaces natively in the ADK Web interface.

7. **Cross-Session Long-Term Memory (Vertex AI Memory Bank)**:
   - Uses `PreloadMemoryTool` to inject durable user preferences (risk tolerance, preferred sectors, strict stop-loss percentages) into the system prompt at the start of each turn.
   - Persists salient interaction events to **Vertex AI Memory Bank** (`generate_memories_callback` in `after_agent_callback`) so the agent remembers trader preferences across independent sessions.

---

## Status of Other Features

- **Dynamic Image Generation (e.g. Imagen)**: *Planned, not yet implemented.* The codebase currently implements dynamic video generation via `gemini-omni-flash-preview` and Cloud Storage uploads (`app/video_tool.py`), but does not have a dedicated image generation tool.

---

## Google Cloud Services Used

- **Vertex AI Agent Platform / Agent Runtime**: Hosts and deploys the reasoning engine runtime with A2A protocol support.
- **Vertex AI Gemini Models**:
  - `gemini-2.5-flash`: Reasoning engine driving trade planning, technical calculations, tool dispatch, and A2UI card generation.
  - `gemini-omni-flash-preview`: Generates high-definition 3D motion videos representing trading themes.
- **Vertex AI Memory Bank**: Managed long-term cross-session memory service (`VertexAiMemoryBankService`) retaining user preferences across conversations.
- **Google Cloud Firestore (Native Mode)**: Persists watchlist items and trade plans.
- **Google Cloud Storage (GCS)**: Stores and hosts generated MP4 financial video assets.

---

## Project Structure

```
simple-agent/
├── app/
│   ├── agent.py               # Root ADK agent configuration, tools, memory callback
│   ├── a2ui_prompt.py         # A2UI v0.8 schema system instruction
│   ├── a2ui_utils.py          # A2UI callback transformer for rich cards
│   ├── trading_tools.py       # Technical indicators (SMA/RSI) and news sentiment
│   ├── firestore_backend.py   # Firestore watchlist CRUD tools
│   ├── video_tool.py          # Omni 3D video generator & GCS uploader
│   ├── fast_api_app.py        # FastAPI A2A backend runner
│   └── app_utils/
│       ├── a2a.py             # Agent-to-Agent protocol routes
│       ├── reasoning_engine_adapter.py # Console playground adapter
│       └── services.py        # Shared Session, Artifact, and Memory Bank services
├── agents-cli-manifest.yaml   # Agent deployment metadata
├── docs/
│   └── INTEGRATION_GUIDE.md   # Usage & integration guide + verified prompt library
├── pyproject.toml             # Python project dependencies
├── demo.gif                   # Looping recording of the agent in action
└── demo.webm                  # Source screen recording
```

For detailed protocol documentation, API call examples, and a verified prompt library, see the [Usage & Integration Guide](docs/INTEGRATION_GUIDE.md).

---

## Local Setup & Run Instructions

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) authenticated with Application Default Credentials:
  ```bash
  gcloud auth application-default login
  ```

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment Variables
Set your Google Cloud project:
```bash
export GOOGLE_CLOUD_PROJECT="<YOUR_PROJECT_ID>"
export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_CLOUD_LOCATION="us-east1"
```

### 3. Start the Local Playground
Launch the ADK Web development server with your configured Memory Bank:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<MEMORY_BANK_ID>
```
Once started, open your web browser to the local development UI at port 8080.
