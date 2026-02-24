# 📊 Stock Dashboard - Full-Stack Tutorial Project

A complete full-stack web application featuring real-time stock prices and an AI-powered chatbot.

## 🏗️ Architecture

```
Frontend (React)
    ↕ HTTP/WebSocket
Backend (FastAPI)
    ↕
MySQL Database
    ↕
Yahoo Finance API (yfinance)
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API Key (for AI chatbot - get free at https://console.anthropic.com)

### Step 1: Clone or Create Project

```bash
cd stock-dashboard
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
```

**Note:** The chatbot will work with limited functionality without an API key, but for full AI features, you need to:
1. Go to https://console.anthropic.com
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to the .env file

### Step 3: Start All Services

```bash
docker-compose up --build
```

This single command will:
- 🐘 Start MySQL database
- 🐍 Start FastAPI backend (port 8000)
- ⚛️  Start React frontend (port 3000)

### Step 4: Access the Application

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs (Interactive Swagger UI)
- **API:** http://localhost:8000

---

## 📖 Tutorial Sections

### Part 1: Understanding Docker

**What is Docker?**
Docker packages your application and all its dependencies into containers. Think of it like a shipping container - it contains everything needed to run your app.

**Key Concepts:**
- **Container:** A lightweight, standalone package with your app
- **Image:** A blueprint for creating containers
- **Docker Compose:** Runs multiple containers together

**Our Docker Setup:**
```yaml
# docker-compose.yml defines 3 services:
- db (MySQL database)
- backend (Python FastAPI)
- frontend (React)
```

**Commands:**
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild containers
docker-compose up --build
```

---

### Part 2: SQL & MySQL

**Database Schema:**

```sql
-- Table 1: stock_prices
-- Stores real-time and historical stock data
CREATE TABLE stock_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(10),
    price DECIMAL(10, 2),
    timestamp DATETIME
);

-- Table 2: chat_history
-- Stores AI chatbot conversations
CREATE TABLE chat_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(50),
    user_message TEXT,
    ai_response TEXT
);

-- Table 3: watchlist
-- Stores user's favorite stocks
CREATE TABLE watchlist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(50),
    symbol VARCHAR(10)
);
```

**SQL Operations Explained:**

```sql
-- INSERT: Add new data
INSERT INTO stock_prices (symbol, price) VALUES ('AAPL', 175.50);

-- SELECT: Retrieve data
SELECT * FROM stock_prices WHERE symbol = 'AAPL';

-- UPDATE: Modify existing data
UPDATE stock_prices SET price = 176.00 WHERE symbol = 'AAPL';

-- DELETE: Remove data
DELETE FROM stock_prices WHERE timestamp < '2024-01-01';

-- JOIN: Combine tables
SELECT w.symbol, sp.price 
FROM watchlist w
JOIN stock_prices sp ON w.symbol = sp.symbol;
```

**Accessing MySQL:**

```bash
# Connect to MySQL container
docker exec -it stock_db mysql -u stockuser -pstockpass stockdb

# Run queries
mysql> SELECT * FROM stock_prices LIMIT 5;
mysql> SHOW TABLES;
mysql> DESCRIBE stock_prices;
```

---

### Part 3: Python Backend with FastAPI

**SQLAlchemy ORM (Object-Relational Mapping):**

Instead of writing raw SQL, you work with Python objects:

```python
# Without ORM (raw SQL)
cursor.execute("INSERT INTO stock_prices (symbol, price) VALUES (?, ?)", 
               ('AAPL', 175.50))

# With ORM (SQLAlchemy)
new_stock = StockPrice(symbol='AAPL', price=175.50)
db.add(new_stock)
db.commit()
```

**FastAPI Endpoints:**

```python
# GET endpoint
@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str):
    # Fetch stock data
    return stock_data

# POST endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Process chat message
    return response

# WebSocket endpoint
@app.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket):
    # Real-time updates
```

**Testing the API:**

```bash
# Using curl
curl http://localhost:8000/api/stocks/AAPL

# Or visit http://localhost:8000/docs for interactive testing
```

---

### Part 4: React Frontend

**Component Structure:**

```
App.js
├── Header (Search bar)
├── Watchlist (Stock list)
├── StockDetails (Main view)
└── ChatPanel (AI chatbot)
```

**Key React Concepts:**

1. **State Management:**
```javascript
const [watchlist, setWatchlist] = useState([]);
const [selectedStock, setSelectedStock] = useState(null);
```

2. **API Calls:**
```javascript
const response = await axios.get(`${API_URL}/api/stocks/${symbol}`);
setSelectedStock(response.data);
```

3. **WebSocket Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stocks');
ws.onmessage = (event) => {
    // Update UI with real-time data
};
```

---

## 🧪 Testing & Development

### Test the Backend API

```bash
# Get stock data
curl http://localhost:8000/api/stocks/AAPL

# Get watchlist
curl http://localhost:8000/api/watchlist

# Send chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is AAPL?", "session_id": "test123"}'
```

### Access Database Directly

```bash
# Enter MySQL container
docker exec -it stock_db mysql -u stockuser -pstockpass stockdb

# Run queries
SELECT * FROM stock_prices ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM watchlist;
SELECT * FROM chat_history;
```

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# Frontend logs
docker-compose logs -f frontend
```

---

## 📚 Learning Resources

### SQL
- [SQLZoo Interactive Tutorial](https://sqlzoo.net/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

### Python & FastAPI
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)

### React
- [React Official Tutorial](https://react.dev/learn)
- [React Hooks Guide](https://react.dev/reference/react)

### Docker
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

---

## 🎯 Practice Exercises

### Beginner
1. Add a new stock to your watchlist
2. Modify the SQL schema to add a "notes" field
3. Change the frontend color scheme

### Intermediate
4. Add a new API endpoint for stock comparison
5. Implement user authentication
6. Add more chart types (candlestick, volume)

### Advanced
7. Implement stock alerts (price thresholds)
8. Add technical indicators (RSI, MACD)
9. Build a portfolio tracker with P&L

---

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Check if MySQL is running
docker ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Backend Not Starting
```bash
# Check Python dependencies
docker-compose exec backend pip list

# Rebuild backend
docker-compose up --build backend
```

### Frontend Issues
```bash
# Clear npm cache
docker-compose exec frontend npm cache clean --force

# Reinstall dependencies
docker-compose exec frontend npm install
```

---

## 🌟 Features

✅ Real-time stock price updates
✅ Interactive price charts
✅ Stock watchlist management
✅ AI-powered chatbot for stock queries
✅ WebSocket for live data
✅ Responsive design
✅ Dark theme UI

---

## 📝 Project Structure

```
stock-dashboard/
├── docker-compose.yml       # Docker orchestration
├── init.sql                 # Database schema
├── backend/                 # Python FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # FastAPI app
│   ├── database.py         # SQLAlchemy models
│   ├── stock_service.py    # Yahoo Finance integration
│   └── ai_service.py       # Claude AI integration
├── frontend/                # React frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js          # Main React component
│       ├── App.css         # Styling
│       └── index.js        # Entry point
└── README.md               # This file
```

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Add new features
- Improve documentation
- Fix bugs
- Share with others learning full-stack development

---

## 📄 License

This project is for educational purposes. Free to use and modify.

---

## 🙏 Acknowledgments

- **Yahoo Finance** for free stock data (via yfinance)
- **Anthropic** for Claude AI API
- **FastAPI** for excellent Python web framework
- **React** for powerful frontend library

---

## 📧 Questions?

This project demonstrates:
- Full-stack web development
- Database design and SQL
- API development
- Real-time data handling
- AI integration
- Docker containerization

Perfect for beginners learning full-stack development! 🚀

---

**Happy Coding! 💻**