"""
Intelligent Receipt Scanner Agent with Google SDK
Implements sophisticated, schema-driven receipt analysis.
"""

import datetime
import json
import io
from typing import Dict, Any
from PIL import Image

import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, Tool

from app.core.config import get_settings
from .models import ProcessedReceipt
from .prompts import create_structured_receipt_prompt
from .schemas import get_enhanced_receipt_schema

settings = get_settings()


class IntelligentReceiptScannerAgent:
    """A schema-driven agent for extracting detailed receipt information."""

    def __init__(self):
        """Initializes the agent with the Gemini model and a dynamic schema."""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        self.model_name = "gemini-2.5-flash"
        
        print("🤖 Initializing Intelligent Receipt Scanner Agent")
        self._initialize_model()

    def _initialize_model(self):
        """Initializes the Vertex AI model with a dynamically generated schema."""
        try:
            vertexai.init(project=self.project_id, location=self.location)
            
            # Generate the schema from our Pydantic models
            receipt_schema_dict = get_enhanced_receipt_schema()

            # Fix for Pydantic v2 schema compatibility with Vertex AI
            if '$defs' in receipt_schema_dict:
                receipt_schema_dict['definitions'] = receipt_schema_dict.pop('$defs')

            # Wrap the schema in a Tool object for the Vertex AI SDK
            receipt_tool = Tool.from_dict({
                "function_declarations": [{
                    "name": "extract_receipt_data",
                    "description": "Extracts and structures all visible information from a receipt image.",
                    "parameters": receipt_schema_dict
                }]
            })

            generation_config = GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )

            # Pass the correctly formatted Tool object to the model
            self.model = GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                tools=[receipt_tool]
            )
            print("✅ Agent ready with dynamic schema!")

        except Exception as e:
            print(f"❌ Failed to initialize model: {e}")
            raise

    def analyze_receipt(self, media_bytes: bytes, media_type: str, user_id: str) -> Dict[str, Any]:
        """
        Analyzes a receipt and returns a structured, validated ProcessedReceipt object.
        """
        start_time = datetime.datetime.utcnow()
        
        print(f"🧠 Analyzing {media_type} for user: {user_id}")

        try:
            media_data, mime_type = self._prepare_media(media_bytes, media_type)
            prompt = create_structured_receipt_prompt(media_type)
            
            print("🤖 Calling Gemini with structured prompt and tool enforcement...")
            
            # Force the model to use our schema-defined tool
            response = self.model.generate_content(
                [prompt, Part.from_data(data=media_data, mime_type=mime_type)],
                tool_config={
                    "function_calling_config": {
                        "mode": "any",
                        "allowed_function_names": ["extract_receipt_data"]
                    }
                }
            )

            # Extract the arguments from the function call in the response
            function_call = response.parts[0].function_call
            if not function_call.name == "extract_receipt_data":
                raise ValueError("Model did not call the expected function to format the data.")

            # The arguments are a dict-like object that we can convert to a dictionary
            ai_result = {key: value for key, value in function_call.args.items()}
            
            # Use Pydantic to parse and validate the complex structure
            processed_receipt = ProcessedReceipt.model_validate(ai_result)

            # Manual fixups and enhancements after validation
            self._enhance_receipt_data(processed_receipt, user_id, start_time, media_type)
            
            processing_time = (datetime.datetime.utcnow() - start_time).total_seconds()
            
            print(f"✅ Analysis successful! Time: {processing_time:.2f}s")

            return {
                "status": "success",
                "data": processed_receipt.dict(),
                "processing_time": processing_time
            }

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            raise

    def _prepare_media(self, media_bytes: bytes, media_type: str) -> tuple[bytes, str]:
        """Prepares media, including resizing large images."""
        if media_type == "image":
            image = Image.open(io.BytesIO(media_bytes))
            
            max_size = (2048, 2048)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output_buffer = io.BytesIO()
                image.save(output_buffer, format="JPEG", quality=90)
                media_bytes = output_buffer.getvalue()

            return media_bytes, "image/jpeg"
        
        return media_bytes, "video/mp4" # Basic handling for video

    def _enhance_receipt_data(self, receipt: ProcessedReceipt, user_id: str, start_time: datetime.datetime, media_type: str):
        """Applies final touches and calculations to the processed receipt."""
        
        payload = receipt.receipt_payload
        
        # Ensure processing metadata is set correctly
        if not payload.processing_metadata.receipt_id:
            payload.processing_metadata.receipt_id = f"{user_id}_{int(start_time.timestamp())}"
        payload.processing_metadata.source_type = media_type.upper()


        # Recalculate total amount as a final validation check
        if payload.payment_summary and payload.line_items:
            calculated_total = sum(item.total_price for item in payload.line_items)
            if abs(calculated_total - payload.payment_summary.total_amount) > 0.05: # Allow 5-cent tolerance
                 print(f"⚠️ Warning: Calculated total ({calculated_total:.2f}) differs from LLM total ({payload.payment_summary.total_amount:.2f})")
                 # We trust the sum of items more
                 payload.payment_summary.total_amount = calculated_total


# Singleton instance of the agent
_agent = None

def get_receipt_scanner_agent() -> "IntelligentReceiptScannerAgent":
    """Provides a singleton instance of the agent."""
    global _agent
    if _agent is None:
        _agent = IntelligentReceiptScannerAgent()
    return _agent
