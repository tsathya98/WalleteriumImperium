# Onboarding Agent

The Onboarding Agent is a conversational AI designed to create a comprehensive user profile by understanding their financial habits, goals, and risk appetite. It uses a friendly, multi-lingual, and adaptive conversational approach to gather necessary details for personalizing the user's experience in Walleterium Imperium.

## Features

- **Conversational Onboarding**: Engages users in a natural conversation to gather information, replacing traditional static forms.
- **User Persona Profiling**: Dynamically identifies user personas (e.g., `Budgetor`, `Investor`, `Explorer`) based on their responses.
- **Multi-lingual Support**: Can conduct conversations in multiple languages, specified via an API parameter.
- **Adaptive Questioning**: The agent can ask follow-up questions based on the context of the conversation.
- **Structured Data Output**: The gathered information is structured into a clear JSON format, which can be easily used by other services.

## Architecture

The Onboarding Agent is built using the `google.adk` library and powered by Gemini. It operates as a sub-agent within the Walleterium Imperium ecosystem. The conversation flow is managed by the agent, which uses a set of tools to create and update the user's profile in real-time.

The agent's logic is primarily defined in `agent.py`, with prompts and data schemas in `prompts.py` and `schemas.py` respectively.

## API Endpoint

The agent is exposed via a RESTful API endpoint for easy integration with the frontend.

### Chat with the Onboarding Agent

- **URL**: `/api/v1/onboarding/chat`
- **Method**: `POST`
- **Request Body**:

```json
{
  "user_id": "user-123",
  "query": "I'd like to set up my profile.",
  "language": "en",
  "session_id": "session-abc-456"
}
```

- **Response Body**:

```json
{
    "response": "Hello! I'm here to help you set up your financial profile. To start, could you tell me what your biggest financial goal is this year?",
    "session_id": "session-abc-456"
}
```

## How It Works

1.  The frontend initiates a conversation with the Onboarding Agent by sending a request to the chat endpoint.
2.  The agent receives the user's query and, based on the conversation history (or lack thereof), it decides on the next question to ask.
3.  The agent uses its predefined prompts to generate a response that is both engaging and informative.
4.  As the user provides information, the agent can use its internal tools to start building a user profile.
5.  The conversation continues until the agent has gathered enough information to create a baseline user profile, including a suggested persona.

## Future Enhancements

- **Integration with Firestore**: Store and retrieve user profiles from a Firestore database.
- **RAG for Deeper Insights**: Utilize Retrieval-Augmented Generation (RAG) to pull in external data or previous conversation snippets to provide a more contextual experience.
- **More Sophisticated Personas**: Expand the range of personas and the logic used to assign them. 