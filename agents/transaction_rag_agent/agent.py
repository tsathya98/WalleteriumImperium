"""
Minimal Viable Transaction RAG Agent using google-genai
"""
from google import genai
from google.genai import types
from app.core.logging import get_logger

logger = get_logger(__name__)

class TransactionRAG:
    """
    A minimal RAG agent that uses a pre-existing Vertex AI RAG corpus
    to answer questions about transactions. This implementation is based on
    the user-provided script for a quick, non-streaming MVP.
    """
    def __init__(self):
        """Initializes the Google GenAI client."""
        try:
            self.client = genai.Client(
                vertexai=True,
                project="walleterium",
                location="global",
            )
            self.model = "gemini-2.5-flash"
        except Exception as e:
            logger.error(f"Failed to initialize TransactionRAG agent: {e}")
            raise

    def chat(self, query: str):
        """
        Chats with the RAG engine and returns a static, non-streaming response.
        """
        if not query:
            return {"response": "Please provide a query."}
            
        try:
            # This configuration is based directly on the user-provided script.
            tools = [
                types.Tool(
                    retrieval=types.Retrieval(
                        vertex_rag_store=types.VertexRagStore(
                            rag_resources=[
                                types.VertexRagStoreRagResource(
                                    rag_corpus="projects/walleterium/locations/us-central1/ragCorpora/2305843009213693952"
                                )
                            ],
                        )
                    )
                )
            ]

            generation_config = types.GenerationConfig(
                temperature=1,
                top_p=1,
                max_output_tokens=8192,  # Using a more reasonable limit than 65535
            )
            
            # Safety thresholds are set to be non-restrictive as in the script.
            # Using the correct enum values for the google-genai library.
            safety_settings = {
                types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: types.HarmBlockThreshold.BLOCK_NONE,
                types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: types.HarmBlockThreshold.BLOCK_NONE,
                types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: types.HarmBlockThreshold.BLOCK_NONE,
                types.HarmCategory.HARM_CATEGORY_HARASSMENT: types.HarmBlockThreshold.BLOCK_NONE,
            }

            contents = [types.Content(role="user", parts=[types.Part.from_text(query)])]
            
            response = self.client.generate_content(
                model=self.model,
                contents=contents,
                tools=tools,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            return {"response": response.text}
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"response": f"Error during chat: {e}"}

# Singleton instance
_rag_agent = None

def get_rag_agent():
    """Provides a singleton instance of the TransactionRAG agent."""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = TransactionRAG()
    return _rag_agent 