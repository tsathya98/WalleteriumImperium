# 🤖 Onboarding Agent System

**Agentic AI-Powered Financial Onboarding for Walletarium Imperium**

A sophisticated multi-agent system built with Google ADK Agents and Gemini 2.5 Flash for comprehensive user financial profiling during onboarding.

## 🚀 Features

### Multi-Agent Architecture
- **Orchestrator Agent**: Coordinates the entire onboarding flow
- **Persona Agent**: Identifies user financial personality (Budgetor, Investor, Explorer, etc.)
- **Asset Discovery Agent**: Catalogs user's existing investments and assets
- **Bills Agent**: Maps recurring financial obligations and bank accounts
- **Profile Generator**: Creates structured JSON profiles from conversations

### Comprehensive Profiling
- ✅ **Financial Persona Detection**: Budgetor, Investor, Explorer, Maximizer, Spontaneous
- ✅ **Asset Cataloging**: Real estate, Gold, Stocks, Vehicles, Crypto, Art & Collectibles
- ✅ **Recurring Bills**: Rent, Utilities, Subscriptions, Insurance
- ✅ **Risk Assessment**: Low, Medium, High risk appetite
- ✅ **Goal Setting**: Short-term and long-term financial objectives
- ✅ **Multilingual Support**: Configurable language preference

### Intelligent Data Structure
```json
{
  "user_id": "111",
  "persona": "Investor",
  "financial_goals": ["Europe tour", "Property investment"],
  "spending_habits": "meticulous",
  "risk_appetite": "medium",
  "investment_interests": ["stocks", "real_estate"],
  "has_invested_before": true,
  "real_estate_assets": [
    {
      "size_sqft": 1200,
      "purchase_price": 5000000,
      "purchase_date": "2023-01-15",
      "location": "Mumbai"
    }
  ],
  "gold_assets": [
    {
      "volume_g": 50.0,
      "purchase_price_per_g": 4700,
      "purchase_date": "2023-06-10"
    }
  ],
  "stock_assets": [
    {
      "ticker": "INFY",
      "units_bought": 100,
      "unit_price_purchase": 1500,
      "exchange_date": "2023-08-20"
    }
  ],
  "recurring_bills": [
    {
      "name": "Netflix",
      "amount": 199,
      "due_date": 15
    }
  ],
  "onboarding_complete": true
}
```

## 🛠 Technical Architecture

### Google ADK Agents Integration
```python
from google.adk.agents import Agent

# Orchestrator coordinates all sub-agents
orchestrator = Agent(
    name="onboarding_orchestrator",
    model="gemini-2.5-flash",
    description="Orchestrates complete onboarding flow",
    instruction="Guide users through comprehensive financial profiling...",
    tools=[save_user_profile_data, get_complete_user_profile]
)
```

### Firestore Data Storage
- **Main Profile**: `wallet_user_collection/{user_id}`
- **Assets**: `wallet_user_collection/{user_id}/user_assets/{asset_id}`
- **Conversation History**: Maintained in-memory during session

### Agent System Flow
1. **Welcome & Context Gathering**: Orchestrator initiates friendly conversation
2. **Persona Discovery**: Specialized agent asks engaging questions to identify financial personality
3. **Asset Cataloging**: Dedicated agent helps users identify and structure their investments
4. **Bills & Accounts**: Maps recurring financial obligations and banking relationships
5. **Profile Generation**: Creates comprehensive structured JSON profile
6. **Storage**: Saves complete profile to Firestore with subcollections for assets

## 📡 API Endpoints

### 1. Chat Interface
```http
POST /api/v1/onboarding/chat
```

**Request:**
```json
{
  "user_id": "111",
  "session_id": "session_123",
  "query": "I want to start my financial onboarding",
  "language": "en"
}
```

**Response:**
```json
{
  "response": "Welcome! Let's discover your financial personality...",
  "session_id": "session_123", 
  "onboarding_complete": false
}
```

### 2. Get Complete Profile
```http
GET /api/v1/onboarding/profile/{user_id}
```

**Response:**
```json
{
  "status": "success",
  "profile": {
    "user_id": "111",
    "persona": "Investor",
    "financial_goals": ["..."],
    "real_estate_assets": ["..."],
    "gold_assets": ["..."],
    "stock_assets": ["..."]
  }
}
```

### 3. Regenerate Profile
```http
POST /api/v1/onboarding/profile/{user_id}/regenerate
```

## 🎯 Persona Classification

### Budgetor
- **Characteristics**: Careful with money, likes tracking expenses, prefers safe investments
- **Triggers**: Keywords like "save", "budget", "careful", "track", "plan"

### Investor  
- **Characteristics**: Interested in growing wealth, comfortable with calculated risks
- **Triggers**: Keywords like "invest", "stock", "portfolio", "grow", "return"

### Explorer
- **Characteristics**: Curious about new financial opportunities, likes learning
- **Triggers**: Keywords like "learn", "explore", "new", "curious", "try"

### Maximizer
- **Characteristics**: Wants to optimize every financial decision, detail-oriented  
- **Triggers**: Keywords like "optimize", "best", "compare", "research"

### Spontaneous
- **Characteristics**: Makes quick decisions, values convenience over optimization
- **Default**: When other patterns don't match

## 🔥 Key Questions for Asset Discovery

### Persona Assessment
- "If you received ₹50,000 unexpectedly, what would you do with it?"
- "How do you currently track your expenses?"
- "What's your biggest financial goal this year?"

### Asset Discovery
- "Do you own any property or land?"
- "Have you invested in gold jewelry, coins, or bars?"
- "Do you have any stocks, mutual funds, or investment accounts?"
- "What about vehicles - cars, bikes, or other valuable items?"
- "Any crypto holdings or digital assets?"

### Bills & Accounts
- "What are your major monthly expenses?"
- "Which subscriptions do you pay for regularly?"
- "How many bank accounts do you actively use?"
- "Would you prefer to upload bank statements or add details manually?"

## 🚀 Quick Start

### 1. Test the Chat API
```bash
curl -X POST "http://localhost:8000/api/v1/onboarding/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session", 
    "query": "",
    "language": "en"
  }'
```

### 2. Get User Profile
```bash
curl "http://localhost:8000/api/v1/onboarding/profile/test_user"
```

### 3. Integration Example
```python
import requests

# Start onboarding
response = requests.post("http://localhost:8000/api/v1/onboarding/chat", json={
    "user_id": "111",
    "session_id": "session_123",
    "query": "",
    "language": "en"
})

# Continue conversation
response = requests.post("http://localhost:8000/api/v1/onboarding/chat", json={
    "user_id": "111", 
    "session_id": "session_123",
    "query": "I have a house and some gold jewelry",
    "language": "en"
})

# Get final profile
profile = requests.get("http://localhost:8000/api/v1/onboarding/profile/111")
```

## 🎮 Demo Conversation Flow

```
User: Hello
Agent: Welcome! I'm excited to help you create your financial profile. 
       Let's start with a fun question - if you unexpectedly received 
       ₹50,000 today, what would you do with it?

User: I'd probably invest half in stocks and save the rest
Agent: Great! You sound like someone who thinks strategically about money. 
       Have you invested in stocks before? What draws you to them?

User: Yes, I have some Infosys shares and a small mutual fund
Agent: Excellent! Let's catalog those. How many Infosys shares do you own 
       and when did you buy them?

User: 100 shares bought at ₹1500 each in August 2023
Agent: Perfect! Now, do you own any property, gold, or other investments?

User: I have a 1200 sq ft apartment in Mumbai worth about ₹50 lakhs
Agent: Wonderful! When did you purchase it? 
       [Continues until complete profile is built...]
```

## 🔧 Configuration

### Environment Variables
```env
GOOGLE_CLOUD_PROJECT_ID=your-project
VERTEX_AI_LOCATION=us-central1
FIRESTORE_DATABASE=(default)
```

### Customization
- **Languages**: Add language support in agent instructions
- **Personas**: Extend persona classification logic
- **Asset Types**: Add new asset categories to schemas
- **Questions**: Customize conversation prompts in agent instructions

## 🏆 Hackathon Optimizations

- **Fast Response**: Gemini 2.5 Flash for sub-second responses
- **Simple Storage**: Direct Firestore integration without complex ORM
- **Modular Design**: Each agent handles specific domain expertise  
- **Conversation Memory**: In-memory session storage for quick iteration
- **RESTful APIs**: Clean endpoints for easy frontend integration

## 🔮 Future Enhancements

- **Advanced NLP**: Better entity extraction from conversations
- **Voice Support**: Audio input/output for hands-free onboarding  
- **Document Upload**: Bank statement and investment document parsing
- **Real-time Validation**: API integrations for asset verification
- **Advanced Analytics**: Spending pattern analysis and recommendations

---

**Built with ❤️ for Walletarium Imperium Hackathon**
