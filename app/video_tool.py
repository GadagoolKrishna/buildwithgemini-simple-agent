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

import base64
import uuid
from typing import Any, Dict
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# Hardcoded project and bucket name strings
PROJECT_ID = "qwiklabs-gcp-03-6fca0bafb4e6"
BUCKET_NAME = "bwg3-qwiklabs-gcp-03-6fca0bafb4e6"
MODEL_NAME = "gemini-omni-flash-preview"
LOCATION = "global"

_genai_client = None
_storage_client = None


def get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
    return _genai_client


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


async def generate_stock_video(
    company_or_ticker: str,
    trend_description: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates a dynamic 3D financial animation video for a stock or trading setup using gemini-omni-flash-preview.

    Saves the generated video artifact to the playground session and uploads the bytes
    directly to public Cloud Storage, returning the public HTTPS URL.

    Args:
        company_or_ticker: The stock ticker or company name (e.g. 'NVDA', 'AAPL', 'Tesla').
        trend_description: Short visual theme or trend description (e.g. 'bullish breakout with green glowing candlesticks', 'golden crossover surge').
        tool_context: ADK ToolContext injected by the framework to save artifacts.

    Returns:
        A dictionary with the public video URL, artifact name, and video metadata.
    """
    clean_target = company_or_ticker.strip().upper()
    prompt = (
        f"Cinematic 3D financial visualization representing {clean_target} stock. "
        f"{trend_description}. High tech stock market line chart and glowing neon candlesticks, "
        f"dynamic camera sweep, photorealistic volumetric lighting, 8k resolution motion graphics."
    )

    client = get_genai_client()
    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        response_format={
            "type": "video",
            "aspect_ratio": "16:9",
        },
    )

    if not hasattr(interaction, "output_video") or not interaction.output_video:
        return {
            "status": "error",
            "message": "Failed to generate video: no video output returned by gemini-omni-flash-preview.",
        }

    # Extract raw video bytes from base64
    video_bytes = base64.b64decode(interaction.output_video.data)

    # 1. Save artifact with tool_context so it appears in Playground's Artifacts panel
    artifact_filename = f"{clean_target.lower()}_trade_brief_{uuid.uuid4().hex[:6]}.mp4"
    artifact_part = types.Part(
        inline_data=types.Blob(
            mime_type="video/mp4",
            data=video_bytes,
        )
    )
    if tool_context:
        try:
            await tool_context.save_artifact(artifact_filename, artifact_part)
        except Exception as e:
            print(f"[Warning] save_artifact error: {e}")

    # 2. Upload bytes directly to public Cloud Storage bucket
    gcs_client = get_storage_client()
    bucket = gcs_client.bucket(BUCKET_NAME)
    object_name = f"videos/{artifact_filename}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

    return {
        "status": "success",
        "symbol": clean_target,
        "artifact_filename": artifact_filename,
        "public_url": public_url,
        "content_type": "video/mp4",
        "size_bytes": len(video_bytes),
        "message": f"Generated short video for {clean_target}. Stored as artifact '{artifact_filename}' and public URL: {public_url}",
    }
