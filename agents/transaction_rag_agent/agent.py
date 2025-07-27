"""
Minimal Viable Transaction RAG Agent using google-genai
"""
from google import genai
from google.genai import types
from app.core.logging import get_logger

logger = get_logger(__name__)

class TransactionRAG:
    """
    A minimal RAG chatbot that uses the exact template configuration
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
        Basic chatbot that takes a query and returns a response using RAG
        """
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=query)]
                )
            ]
            
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

            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                top_p=1,
                seed=0,
                max_output_tokens=65535,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    )
                ],
                tools=tools,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
            )

            # Use generate_content instead of generate_content_stream for static response
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
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