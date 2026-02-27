# 📊 Stock Dashboard

A full-stack stock tracking application with real-time prices, interactive charts, and AI-powered chat assistant.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│────▶│  MySQL Database │
│  (Port 3000)    │     │  (Port 8000)    │     │  (Port 3307)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌──────────────┐         ┌──────────────┐
            │ Yahoo Finance│         │    Ollama    │
            │   (Stocks)   │         │  (AI Chat)   │
            └──────────────┘         └──────────────┘
```

## ✨ Features

- **Real-time Stock Data** - Live prices from Yahoo Finance with fallback support
- **Market Indices** - S&P 500, Dow Jones, NASDAQ, VIX tracking
- **Trending Stocks** - Top 5 most active stocks
- **Interactive Charts** - Multiple timeframes (1D, 5D, 1M, 3M, 1Y, 5Y)
- **Watchlist** - Save and track favorite stocks
- **AI Chat Assistant** - Local AI powered by Ollama (no API key needed)
- **Dark/Light Theme** - Toggle between themes
- **Stock Search** - Search any ticker symbol

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Ollama (for AI chat) - Install: `brew install ollama`

### Start the Application

```bash
# 1. Start Ollama (required for AI chat)
brew services start ollama
ollama pull qwen2.5:0.5b

# 2. Start the application
cd stock_dashboard
docker-compose up --build
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## 📁 Project Structure

```
stock_dashboard/
├── docker-compose.yml          # Docker orchestration
├── init.sql                    # Database schema
├── backend/
│   ├── main.py                 # FastAPI endpoints
│   ├── database.py             # SQLAlchemy models
│   ├── stock_service.py        # Yahoo Finance integration
│   ├── ai_service.py           # Ollama AI integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   └── App.css             # Styles
│   └── package.json
└── documentation/
    ├── README.md
    └── CHEATSHEET.md
```

## 🔌 API Endpoints

### Stock Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks/{symbol}` | Get stock details |
| GET | `/api/stocks/{symbol}/history` | Get price history |
| GET | `/api/stocks/search/{query}` | Search stocks |
| GET | `/api/market/indices` | Get market indices |
| GET | `/api/market/trending` | Get trending stocks |

### Watchlist

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/watchlist` | Get watchlist |
| POST | `/api/watchlist` | Add stock to watchlist |
| DELETE | `/api/watchlist/{symbol}` | Remove from watchlist |

### AI Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI |
| GET | `/api/chat/history/{session_id}` | Get chat history |

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+pymysql://...` | Database connection |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `qwen2.5:0.5b` | AI model to use |

### Ports

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend | 8000 |
| MySQL | 3307 |
| Ollama | 11434 |

## 🛠️ Development

### Restart Services

```bash
# Restart backend only
docker-compose restart backend

# Rebuild and restart
docker-compose up --build

# Stop all services
docker-compose down
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Access Database

```bash
docker exec -it stock_db mysql -u stockuser -pstockpass stockdb
```

## 🔧 Troubleshooting

### AI Chat Not Working

```bash
# Ensure Ollama is running
brew services start ollama

# Check if model is installed
ollama list

# Pull model if missing
ollama pull qwen2.5:0.5b
```

### Port Conflicts

```bash
# Check what's using port 3000
lsof -i :3000

# Check what's using port 8000
lsof -i :8000
```

### Database Issues

```bash
# Reset database completely
docker-compose down -v
docker-compose up --build
```
