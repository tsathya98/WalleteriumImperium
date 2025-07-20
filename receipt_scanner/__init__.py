"""
Receipt Scanner Agent

A comprehensive AI-powered receipt processing agent that supports text, Excel, PDF, 
image, and video inputs using Google's Agent Development Kit (ADK), Gemini 2.5 Flash 
for vision AI, and LLM enrichment for structured data extraction.

Key Features:
- Multimodal input processing (text, Excel, PDF, image, video)
- Gemini 2.5 Flash Vision AI for image/video analysis
- LLM enrichment for text-based content
- Local storage with search and analytics
- MCP-compatible output format
"""

from .agent import receipt_processing_agent, root_agent
from .models import (
    ProcessedReceipt,
    ProcessingResult,
    InputType,
    ProcessorModel,
    MCPFormat,
    ReceiptPayload,
)
from .sub_agents import (
    multimodal_processor_agent,
    gemini_processor_agent,
    llm_enricher_agent,
    storage_agent,
)

__version__ = "0.1.0"
__all__ = [
    # Main agent
    "receipt_processing_agent",
    "root_agent",
    # Models
    "ProcessedReceipt",
    "ProcessingResult", 
    "InputType",
    "ProcessorModel",
    "MCPFormat",
    "ReceiptPayload",
    # Sub-agents
    "multimodal_processor_agent",
    "gemini_processor_agent",
    "llm_enricher_agent", 
    "storage_agent",
]
