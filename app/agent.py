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
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from app.trading_tools import search_ticker, get_crossover_signals, get_company_news_sentiment
from app.firestore_backend import add_to_watchlist, get_watchlist, remove_from_watchlist
from app.video_tool import generate_stock_video
from app.a2ui_utils import a2ui_callback
from app.a2ui_prompt import INSTRUCTION

MODEL = "gemini-2.5-flash"

instruction = INSTRUCTION


# WRITE: After each turn, persist salient user facts and preferences to Memory Bank.
async def generate_memories_callback(callback_context: CallbackContext) -> None:
    session = callback_context._invocation_context.session
    if session and session.events:
        await callback_context.add_events_to_memory(
            events=session.events,
            custom_metadata={"wait_for_completion": True},
        )
    return None


root_agent = Agent(
    name="swing_trader",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_ticker,
        get_crossover_signals,
        get_company_news_sentiment,
        add_to_watchlist,
        get_watchlist,
        remove_from_watchlist,
        generate_stock_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


