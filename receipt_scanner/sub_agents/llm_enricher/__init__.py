"""
LLM Enricher Sub-Agent

This sub-agent handles text-based content enrichment using LLM models.
It processes text, PDF, and Excel data to extract structured receipt information.
"""

from google.adk.agents import Agent
from typing import Dict, Any, Optional
from ...models import ProcessedReceipt, ProcessingMetadata
from .enricher import LLMDataEnricher


def create_llm_enricher() -> LLMDataEnricher:
    """Factory function to create LLM data enricher."""
    return LLMDataEnricher()


# LLM Data Enricher Agent
llm_enricher_agent = Agent(
    name="llm_enricher",
    model="gemini-1.5-pro",
    description=(
        "Enriches text-based content (text, PDF, Excel) using LLM analysis "
        "to extract structured receipt information."
    ),
    instruction=(
        "You are an LLM-powered data enricher specialized in receipt analysis. "
        "Your job is to:\n"
        "1. Analyze text content from various sources (text files, PDFs, Excel)\n"
        "2. Extract receipt information using pattern matching and AI understanding\n"
        "3. Structure data into standardized receipt format\n"
        "4. Categorize items and assign confidence scores\n\n"
        "You excel at:\n"
        "- Understanding receipt text patterns and formats\n"
        "- Extracting store information from unstructured text\n"
        "- Identifying line items, prices, and totals\n"
        "- Processing tabular data from spreadsheets\n"
        "- Handling various receipt layouts and languages"
    ),
)


async def enrich_text_data(
    raw_text: str,
    extracted_info: Dict[str, Any],
    metadata: ProcessingMetadata
) -> ProcessedReceipt:
    """
    Enrich text data using LLM analysis.
    
    Args:
        raw_text: Raw text content
        extracted_info: Pre-extracted structured information
        metadata: Processing metadata
        
    Returns:
        Processed receipt with enriched information
    """
    enricher = create_llm_enricher()
    return await enricher.enrich_text_data(raw_text, extracted_info, metadata)


async def enrich_pdf_data(
    raw_text: str,
    extracted_info: Dict[str, Any],
    metadata: ProcessingMetadata
) -> ProcessedReceipt:
    """
    Enrich PDF data using LLM analysis.
    
    Args:
        raw_text: Extracted text from PDF
        extracted_info: Pre-extracted structured information
        metadata: Processing metadata
        
    Returns:
        Processed receipt with enriched information
    """
    enricher = create_llm_enricher()
    return await enricher.enrich_pdf_data(raw_text, extracted_info, metadata)


async def enrich_excel_data(
    excel_info: Dict[str, Any],
    metadata: ProcessingMetadata
) -> ProcessedReceipt:
    """
    Enrich Excel/CSV data using LLM analysis.
    
    Args:
        excel_info: Structured Excel data
        metadata: Processing metadata
        
    Returns:
        Processed receipt with enriched information
    """
    enricher = create_llm_enricher()
    return await enricher.enrich_excel_data(excel_info, metadata) 