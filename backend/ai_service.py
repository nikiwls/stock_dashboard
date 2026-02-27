"""
AI Chatbot Service using Ollama (Local LLM)
Handles stock-related questions with context from the database
No API key required - runs completely free!
"""

import os
import httpx
from typing import Optional, List, Dict
from datetime import datetime


# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")


class AIService:
    """
    AI-powered chatbot for stock inquiries
    Uses Ollama for local, free AI responses
    """
    
    def __init__(self):
        """Initialize Ollama client"""
        self.ollama_host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if Ollama is running and model is available"""
        try:
            response = httpx.get(f"{self.ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                model_base = self.model.split(":")[0]
                if any(model_base in name for name in model_names) or models:
                    self.available = True
                    print(f"✅ Ollama AI client initialized with model: {self.model}")
                else:
                    print(f"⚠️  Model {self.model} not found. Available models: {model_names}")
                    self.available = True
            else:
                print(f"⚠️  Warning: Ollama not responding properly")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to Ollama at {self.ollama_host}: {e}")
            print("   Make sure Ollama is running: brew services start ollama")
    
    
    def get_stock_context(self, stock_data: Optional[Dict] = None) -> str:
        """Build context string from stock data"""
        if not stock_data:
            return ""
        
        context = f"""
Current Stock Information:
- Symbol: {stock_data.get('symbol', 'N/A')}
- Company: {stock_data.get('company_name', 'N/A')}
- Current Price: ${stock_data.get('price', 'N/A')}
- Change: {stock_data.get('change_percent', 'N/A')}%
- Volume: {stock_data.get('volume', 'N/A'):,}
- Market Cap: ${stock_data.get('market_cap', 'N/A'):,}
- Day High: ${stock_data.get('day_high', 'N/A')}
- Day Low: ${stock_data.get('day_low', 'N/A')}
- P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
- Beta: {stock_data.get('beta', 'N/A')}
"""
        return context
    
    
    async def chat(
        self,
        user_message: str,
        stock_data: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate AI response to user's stock inquiry"""
        system_prompt = """You are a helpful stock market assistant. You provide:
1. Clear, accurate information about stocks
2. Analysis of stock performance and trends
3. Explanations of stock market concepts
4. Investment insights (but NOT financial advice)

Always remind users that you're providing information, not financial advice, and they should do their own research or consult a financial advisor.

Be concise but informative. Use the stock data provided to give context-aware answers."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            for msg in chat_history[-5:]:
                messages.append({"role": "user", "content": msg.get("user_message", "")})
                messages.append({"role": "assistant", "content": msg.get("ai_response", "")})
        
        current_content = user_message
        if stock_data:
            context = self.get_stock_context(stock_data)
            current_content = f"{context}\n\nUser Question: {user_message}"
        
        messages.append({"role": "user", "content": current_content})
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 500}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("message", {}).get("content", "")
                    return ai_response if ai_response else "I couldn't generate a response. Please try again."
                else:
                    print(f"❌ Ollama API error: {response.status_code} - {response.text}")
                    return f"I encountered an error. Please make sure Ollama is running with the model '{self.model}'."
                    
        except httpx.TimeoutException:
            return "The AI is taking too long to respond. Please try again with a shorter question."
        except httpx.ConnectError:
            return "Cannot connect to the AI service. Please ensure Ollama is running (brew services start ollama)."
        except Exception as e:
            print(f"❌ AI Service Error: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    
    def extract_stock_symbol(self, user_message: str) -> Optional[str]:
        """Extract stock symbol from user message"""
        common_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT']
        message_upper = user_message.upper()
        for symbol in common_symbols:
            if symbol in message_upper:
                return symbol
        return None
    
    
    def generate_summary(self, stock_data: Dict) -> str:
        """Generate a quick summary of stock performance"""
        symbol = stock_data.get('symbol', '')
        company = stock_data.get('company_name', '')
        price = stock_data.get('price', 0)
        change = stock_data.get('change_percent', 0)
        
        if change > 2:
            sentiment = "📈 Strong upward momentum"
        elif change > 0:
            sentiment = "📊 Slight positive movement"
        elif change > -2:
            sentiment = "📉 Slight decline"
        else:
            sentiment = "⚠️ Significant drop"
        
        summary = f"""
{company} ({symbol})
Current Price: ${price}
Change: {change}%
{sentiment}

Market Status: {'Open' if datetime.utcnow().hour < 21 else 'Closed'}
"""
        return summary.strip()


if __name__ == "__main__":
    import asyncio
    
    async def test_ai_service():
        ai = AIService()
        stock_data = {
            'symbol': 'AAPL', 'company_name': 'Apple Inc.',
            'price': 175.50, 'change_percent': 1.25,
            'volume': 50000000, 'market_cap': 2700000000000
        }
        response = await ai.chat("What do you think about this stock?", stock_data=stock_data)
        print("\n🤖 AI Response:")
        print(response)
    
    asyncio.run(test_ai_service())
