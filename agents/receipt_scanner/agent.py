"""
A simplified AI agent for receipt analysis.
"""

import datetime
import json
import io
import re
from typing import Dict, Any
from PIL import Image

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig

from app.core.config import get_settings
from .prompts import create_simplified_prompt

settings = get_settings()


class SimplifiedReceiptAgent:
    """A simplified, prompt-driven agent for receipt analysis."""

    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"

        print("🤖 Initializing Simplified Receipt Agent")
        self._initialize_model()

    def _initialize_model(self):
        """Initializes the Vertex AI model."""
        try:
            vertexai.init(project=self.project_id, location=self.location)

            generation_config = GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
            )

            self.model = GenerativeModel(
                model_name=self.model_name, generation_config=generation_config
            )
            print("✅ Agent ready!")

        except Exception as e:
            print(f"❌ Failed to initialize model: {e}")
            raise

    def analyze_receipt(
        self, media_bytes: bytes, media_type: str, user_id: str
    ) -> Dict[str, Any]:
        """Analyzes a receipt and returns simple JSON response."""
        start_time = datetime.datetime.utcnow()

        print(f"🧠 Analyzing {media_type} for user: {user_id}")

        try:
            media_data, mime_type = self._prepare_media(media_bytes, media_type)
            prompt = create_simplified_prompt(media_type)

            print("🤖 Calling Gemini...")
            response = self.model.generate_content(
                [prompt, Part.from_data(data=media_data, mime_type=mime_type)]
            )

            # Extract JSON from response
            ai_json = self._extract_json_from_response(response.text)
            if not ai_json:
                raise ValueError("Could not extract valid JSON from AI response")

            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()

            # Add processing metadata
            if "metadata" not in ai_json:
                ai_json["metadata"] = {}
            ai_json["metadata"]["processing_time_seconds"] = processing_time
            ai_json["metadata"]["model_version"] = self.model_name

            print(f"✅ Analysis successful! Time: {processing_time:.2f}s")

            return {
                "status": "success",
                "data": ai_json,
                "processing_time": processing_time,
            }

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time": (datetime.datetime.utcnow() - start_time).total_seconds(),
            }

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Finds and parses the first valid JSON object from a string."""
        # Look for JSON in markdown code blocks
        match = re.search(r"```(json)?\s*({.*?})\s*```", text, re.DOTALL)
        if match:
            json_str = match.group(2)
        else:
            # Fallback for plain JSON
            match = re.search(r"({.*?})", text, re.DOTALL)
            if not match:
                return None
            json_str = match.group(1)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("⚠️ Warning: Failed to decode JSON")
            return None

    def _prepare_media(self, media_bytes: bytes, media_type: str) -> tuple[bytes, str]:
        """Prepares media, including resizing large images."""
        if media_type == "image":
            image = Image.open(io.BytesIO(media_bytes))

            # Resize if too large
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=90)
                media_bytes = output_buffer.getvalue()

            return media_bytes, "image/jpeg"

        return media_bytes, "video/mp4"


# Singleton instance
_agent = None


def get_receipt_scanner_agent() -> "SimplifiedReceiptAgent":
    """Provides a singleton instance of the agent."""
    global _agent
    if _agent is None:
        _agent = SimplifiedReceiptAgent()
    return _agent
