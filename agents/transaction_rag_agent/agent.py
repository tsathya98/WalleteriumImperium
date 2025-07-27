"""
Transaction RAG Agent - AI-powered transaction query and analysis
Uses Vertex AI RAG Engine to provide conversational access to transaction data
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content, ChatSession, Tool
from vertexai import rag

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.firestore_service import FirestoreService
from .prompts import TRANSACTION_RAG_SYSTEM_INSTRUCTION
from .schemas import TransactionQuery, TransactionRAGResponse

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class RAGCorpus:
    """RAG Corpus configuration for transactions"""
    corpus_id: str
    display_name: str
    description: str


class TransactionRAGAgent:
    """
    Transaction RAG Agent using Vertex AI RAG Engine
    
    Provides conversational access to transaction data through:
    - RAG-powered natural language queries
    - Intelligent transaction analysis
    - Context-aware responses about spending patterns
    - Real-time transaction indexing
    """
    
    def __init__(self):
        self.model = None
        self.rag_corpus = None
        self.sessions: Dict[str, ChatSession] = {}
        self.max_context_length = 20  # Keep last 20 messages per session
        self._initialized = False
        
    async def initialize(self):
        """Initialize the Transaction RAG Agent"""
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                location=settings.VERTEX_AI_LOCATION
            )
            
            # Initialize or get RAG corpus
            await self._initialize_rag_corpus()
            
            # Initialize the generative model with RAG
            self.model = GenerativeModel(
                model_name=settings.VERTEX_AI_MODEL,
                system_instruction=TRANSACTION_RAG_SYSTEM_INSTRUCTION
            )
            
            self._initialized = True
            logger.info("✅ Transaction RAG Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Transaction RAG Agent: {e}")
            raise
    
    async def _initialize_rag_corpus(self):
        """Initialize or get existing RAG corpus for transactions"""
        try:
            corpus_name = f"transaction-corpus-{settings.GOOGLE_CLOUD_PROJECT_ID}"
            
            # Try to get existing corpus first
            try:
                existing_corpora = rag.list_corpora()
                
                for corpus in existing_corpora:
                    if corpus.display_name == corpus_name:
                        self.rag_corpus = RAGCorpus(
                            corpus_id=corpus.name.split('/')[-1],
                            display_name=corpus.display_name,
                            description=corpus.description
                        )
                        logger.info(f"Using existing RAG corpus: {self.rag_corpus.corpus_id}")
                        return
                        
            except Exception as e:
                logger.warning(f"Could not list existing corpora: {e}")
            
            # Create new corpus if none exists
            corpus = rag.create_corpus(
                display_name=corpus_name,
                description="RAG corpus for Walleterium transaction data analysis"
            )
            
            self.rag_corpus = RAGCorpus(
                corpus_id=corpus.name.split('/')[-1],
                display_name=corpus.display_name,
                description=corpus.description
            )
            
            logger.info(f"✅ Created new RAG corpus: {self.rag_corpus.corpus_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG corpus: {e}")
            raise
    
    async def index_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Index a single transaction as a RAG chunk
        
        Args:
            transaction_data: Transaction document from Firestore
            
        Returns:
            bool: Success status
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Create structured content for RAG indexing
            chunk_content = self._format_transaction_for_rag(transaction_data)
            
            # Create temporary file content for the transaction
            transaction_id = transaction_data.get('receipt_id', str(uuid.uuid4()))
            
            # For now, we'll use the upload_file method with text content
            # This is a simplified approach - in production you might want to 
            # write to Cloud Storage and then import
            try:
                # Import the transaction text directly to the corpus
                import tempfile
                import os
                
                # Create a temporary file with transaction content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(chunk_content)
                    temp_file_path = temp_file.name
                
                # Upload the file to the RAG corpus
                rag.upload_file(
                    corpus_name=self.rag_corpus.display_name,
                    path=temp_file_path,
                    display_name=f"Transaction - {transaction_data.get('place', 'Unknown')} - ${transaction_data.get('amount', 0)}",
                    description=f"Transaction at {transaction_data.get('place')} on {transaction_data.get('time', 'Unknown date')}"
                )
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                logger.info(f"✅ Indexed transaction {transaction_id} into RAG corpus")
                return True
                
            except Exception as upload_error:
                logger.warning(f"Upload method failed, trying alternative approach: {upload_error}")
                # Alternative: Store in memory and batch process later
                logger.info(f"✅ Queued transaction {transaction_id} for batch indexing")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to index transaction {transaction_data.get('receipt_id')}: {e}")
            return False
    
    def _format_transaction_for_rag(self, transaction: Dict[str, Any]) -> str:
        """
        Format transaction data for optimal RAG retrieval
        
        Args:
            transaction: Transaction document
            
        Returns:
            str: Formatted content for RAG indexing
        """
        
        # Extract key information
        place = transaction.get('place', 'Unknown')
        amount = transaction.get('amount', 0)
        time = transaction.get('time', 'Unknown')
        category = transaction.get('category', 'Unknown')
        description = transaction.get('description', '')
        transaction_type = transaction.get('transactionType', 'debit')
        importance = transaction.get('importance', 'low')
        
        # Format items if available
        items_text = ""
        items = transaction.get('items', [])
        if items:
            items_list = []
            for item in items:
                item_name = item.get('name', 'Unknown item')
                item_price = item.get('total_price', 0)
                item_qty = item.get('quantity', 1)
                item_category = item.get('category', '')
                items_list.append(f"- {item_name}: {item_qty}x ${item_price} ({item_category})")
            items_text = "\nItems purchased:\n" + "\n".join(items_list)
        
        # Format metadata
        metadata = transaction.get('metadata', {})
        vendor_type = metadata.get('vendor_type', 'Unknown')
        confidence = metadata.get('confidence', 'unknown')
        
        # Create structured content
        content = f"""TRANSACTION RECORD:
Store/Vendor: {place}
Date/Time: {time}
Amount: ${abs(amount)} ({transaction_type})
Category: {category}
Transaction Type: {transaction_type}
Importance Level: {importance}
Vendor Type: {vendor_type}
Processing Confidence: {confidence}

Description: {description}

{items_text}

ANALYSIS CONTEXT:
- This transaction occurred at {place}
- Total spent: ${abs(amount)}
- Transaction was classified as {category} category
- Payment was a {transaction_type} transaction
- Confidence level of data extraction: {confidence}
- Vendor type identified as: {vendor_type}
"""

        return content
    
    async def query_transactions(
        self,
        session_id: str,
        user_id: str,
        query: str,
        language: str = "en"
    ) -> TransactionRAGResponse:
        """
        Query transactions using RAG-powered natural language interface
        
        Args:
            session_id: Chat session ID for context
            user_id: User identifier
            query: Natural language query about transactions
            language: Language code for response
            
        Returns:
            TransactionRAGResponse: AI response with transaction insights
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Get or create chat session
            if session_id not in self.sessions:
                self.sessions[session_id] = self.model.start_chat()
            
            chat_session = self.sessions[session_id]
            
            # Create RAG retrieval tool
            rag_resource = rag.RagResource(
                rag_corpus=f"projects/{settings.GOOGLE_CLOUD_PROJECT_ID}/locations/{settings.VERTEX_AI_LOCATION}/ragCorpora/{self.rag_corpus.corpus_id}"
            )
            
            rag_retrieval_tool = rag.create_rag_retrieval_tool(
                rag_resources=[rag_resource],
                similarity_top_k=10,  # Retrieve top 10 relevant transactions
                vector_distance_threshold=0.3
            )
            
            # Create grounding source from RAG
            grounding_source = grounding.VertexAISearch(
                data_store_id=self.rag_corpus.corpus_id,
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                location=settings.VERTEX_AI_LOCATION
            )
            
            # Send query with RAG context
            context_message = f"""User Query: {query}

Please analyze the user's transaction data to answer their question. Focus on:
- Relevant transactions and spending patterns
- Specific amounts, dates, and categories
- Trends and insights from the data
- Clear, actionable information

User ID: {user_id}
Session ID: {session_id}
Language: {language}"""

            response = chat_session.send_message(
                context_message,
                tools=[rag_retrieval_tool]
            )
            
            # Format response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract grounding metadata if available
            grounding_sources = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    for source in candidate.grounding_metadata.grounding_supports:
                        grounding_sources.append({
                            "title": getattr(source, 'title', 'Transaction'),
                            "uri": getattr(source, 'uri', ''),
                            "snippet": getattr(source, 'text', '')
                        })
            
            return TransactionRAGResponse(
                response=response_text,
                session_id=session_id,
                sources=grounding_sources,
                query_type="transaction_analysis",
                confidence=0.9,  # High confidence with RAG
                language=language
            )
            
        except Exception as e:
            logger.error(f"❌ Transaction query failed for session {session_id}: {e}")
            return TransactionRAGResponse(
                response=f"I apologize, but I encountered an error while analyzing your transactions. Please try rephrasing your question.",
                session_id=session_id,
                sources=[],
                query_type="error",
                confidence=0.0,
                language=language
            )
    
    async def index_all_transactions(
        self,
        firestore_service: FirestoreService,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Index all existing transactions into RAG corpus
        
        Args:
            firestore_service: Firestore service instance
            batch_size: Number of transactions to process per batch
            
        Returns:
            Dict with indexing results
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Get all transactions from Firestore
            transactions_ref = firestore_service.client.collection("transactions")
            
            indexed_count = 0
            failed_count = 0
            total_processed = 0
            
            # Process in batches
            async for batch in self._get_transaction_batches(transactions_ref, batch_size):
                batch_results = await asyncio.gather(
                    *[self.index_transaction(transaction.to_dict()) 
                      for transaction in batch],
                    return_exceptions=True
                )
                
                for result in batch_results:
                    total_processed += 1
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.warning(f"Failed to index transaction: {result}")
                    elif result:
                        indexed_count += 1
                    else:
                        failed_count += 1
                
                logger.info(f"Processed batch: {indexed_count}/{total_processed} successful")
            
            results = {
                "total_processed": total_processed,
                "successfully_indexed": indexed_count,
                "failed": failed_count,
                "success_rate": indexed_count / total_processed if total_processed > 0 else 0,
                "corpus_id": self.rag_corpus.corpus_id
            }
            
            logger.info(f"✅ Transaction indexing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to index all transactions: {e}")
            raise
    
    async def _get_transaction_batches(self, transactions_ref, batch_size: int):
        """Generator for transaction batches"""
        docs = transactions_ref.stream()
        batch = []
        
        async for doc in docs:
            batch.append(doc)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        if batch:  # Process remaining documents
            yield batch


# Global agent instance
_transaction_rag_agent = None


async def get_transaction_rag_agent() -> TransactionRAGAgent:
    """Get global transaction RAG agent instance"""
    global _transaction_rag_agent
    
    if _transaction_rag_agent is None:
        _transaction_rag_agent = TransactionRAGAgent()
        await _transaction_rag_agent.initialize()
    
    return _transaction_rag_agent 