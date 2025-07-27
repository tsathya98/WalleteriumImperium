"""
Direct Vertex AI RAG Engine Agent
"""
import json
import tempfile
import os
import uuid
import vertexai
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.firestore_service import FirestoreService

settings = get_settings()
logger = get_logger(__name__)

CHAT_PROMPT = """
You are a helpful assistant that answers questions about a user's transactions.
Use the provided transaction data to answer the user's query.
The data is a list of transactions, each a full JSON object.
"""

class TransactionRAG:
    def __init__(self):
        vertexai.init(project=settings.GOOGLE_CLOUD_PROJECT_ID, location=settings.VERTEX_AI_LOCATION)
        self.corpus = self._get_or_create_corpus()
        self.model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=CHAT_PROMPT
        )

    def _get_or_create_corpus(self):
        """Gets or creates the RAG corpus."""
        try:
            corpora = rag.list_corpora()
            for corpus in corpora:
                if corpus.display_name == "transactions":
                    logger.info(f"Using existing corpus: {corpus.name}")
                    return corpus
            
            logger.info("Creating new corpus: transactions")
            return rag.create_corpus(display_name="transactions", description="All user transactions")
        except Exception as e:
            logger.error(f"Failed to get or create corpus: {e}")
            raise

    def index_transaction(self, transaction: dict):
        """Indexes a single transaction object."""
        try:
            transaction_id = transaction.get("receipt_id", str(uuid.uuid4()))
            transaction_string = json.dumps(transaction, indent=2, default=str)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_file.write(transaction_string)
                temp_file_path = temp_file.name
            
            rag.upload_file(
                corpus_name=self.corpus.name,
                path=temp_file_path,
                display_name=f"Transaction {transaction_id}",
                description="A single transaction document."
            )
            os.unlink(temp_file_path)
            
            logger.info(f"Successfully indexed transaction {transaction_id}")
            return {"status": "success", "transaction_id": transaction_id}
        except Exception as e:
            logger.error(f"Failed to index transaction: {e}")
            return {"status": "error", "message": str(e)}

    def chat(self, query: str):
        """Chats with the RAG engine about transactions."""
        try:
            rag_retrieval_tool = Tool.from_retrieval(
                retrieval=rag.Retrieval(
                    source=rag.VertexRagStore(
                        rag_resources=[rag.RagResource(rag_corpus=self.corpus.name)]
                    )
                )
            )
            
            chat_model = GenerativeModel(
                model_name=settings.VERTEX_AI_MODEL,
                tools=[rag_retrieval_tool]
            )
            
            response = chat_model.generate_content(query)
            return {"response": response.text}
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"response": f"Error during chat: {e}"}

# Singleton instance
_rag_agent = None

def get_rag_agent():
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = TransactionRAG()
    return _rag_agent 