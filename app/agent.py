# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

from app.trading_tools import search_ticker, get_crossover_signals, get_company_news_sentiment
from app.firestore_backend import add_to_watchlist, get_watchlist, remove_from_watchlist
from app.video_tool import generate_stock_video
from app.a2ui_utils import a2ui_callback

MODEL = "gemini-3.6-flash"

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Quantitative Swing Trading Assistant specializing in Moving Average Crossover Strategies, "
        "managing the user's persistent trade watchlist in Firestore, and generating dynamic 3D financial videos. "
        "When analyzing a company or stock: "
        "1. If given a company name, call search_ticker to resolve the symbol. "
        "2. Call get_crossover_signals to fetch 1-year OHLCV indicators, moving averages, and crossover events. "
        "3. Call get_company_news_sentiment to inspect breaking headlines and catalyst risks. "
        "4. Synthesize disciplined BUY, SELL, or HOLD recommendations with key price levels (Entry, Stop Loss, Target, Support/Resistance). "
        "When asked about the watchlist, call get_watchlist, add_to_watchlist, or remove_from_watchlist. "
        "When asked to generate a video or create visual animation for a stock/company, call generate_stock_video."
    ),
    workflow_description="Analyze the user request, call the necessary financial, Firestore, or video generation tools, and render structured UI cards for trade briefs and watchlists.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image. Never point an Image at a bare filename, an artifact name, or a non-http(s) path. "
        "If you do not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="swing_trader",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        search_ticker,
        get_crossover_signals,
        get_company_news_sentiment,
        add_to_watchlist,
        get_watchlist,
        remove_from_watchlist,
        generate_stock_video,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


