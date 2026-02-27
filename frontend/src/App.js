import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Search, MessageCircle, X, Send, Plus, Trash2, BarChart3, Activity, DollarSign, Percent, Clock, Sun, Moon, RefreshCw, Info, Building2, PieChart } from 'lucide-react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Chart period options
const CHART_PERIODS = [
  { label: '1D', period: '1d', interval: '5m' },
  { label: '5D', period: '5d', interval: '15m' },
  { label: '1M', period: '1mo', interval: '1h' },
  { label: '3M', period: '3mo', interval: '1d' },
  { label: '1Y', period: '1y', interval: '1d' },
  { label: '5Y', period: '5y', interval: '1wk' },
];

function App() {
  // State management
  const [watchlist, setWatchlist] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockHistory, setStockHistory] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [marketIndices, setMarketIndices] = useState([]);
  const [trendingStocks, setTrendingStocks] = useState([]);
  
  // Chart state
  const [selectedPeriod, setSelectedPeriod] = useState(CHART_PERIODS[0]);
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  
  // Theme state
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // Chat state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [addingStock, setAddingStock] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const chatEndRef = useRef(null);
  
  // Session ID for chat
  const [sessionId] = useState(`session_${Date.now()}`);

  // Polling interval ref for real-time updates
  const pollingIntervalRef = useRef(null);

  // Load initial data on mount
  useEffect(() => {
    loadWatchlist();
    loadMarketIndices();
    loadTrendingStocks();
    startPolling();
    
    return () => {
      // Clear polling interval on unmount
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Theme effect
  useEffect(() => {
    document.body.classList.toggle('light-mode', !isDarkMode);
  }, [isDarkMode]);

  // Ref to store current watchlist for polling (avoids closure issues)
  const watchlistRef = useRef(watchlist);
  
  // Keep ref in sync with state
  useEffect(() => {
    watchlistRef.current = watchlist;
  }, [watchlist]);

  // Load market indices
  const loadMarketIndices = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/market/indices`);
      setMarketIndices(response.data.indices || []);
    } catch (error) {
      console.error('Error loading market indices:', error);
    }
  };

  // Load trending stocks
  const loadTrendingStocks = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/market/trending`);
      setTrendingStocks(response.data.trending || []);
    } catch (error) {
      console.error('Error loading trending stocks:', error);
    }
  };

  // Fetch stock updates via HTTP polling (more reliable than WebSocket)
  const fetchStockUpdates = async () => {
    try {
      const currentWatchlist = watchlistRef.current;
      const symbols = currentWatchlist.map(s => s.symbol).join(',');
      if (!symbols) return; // No stocks to fetch
      
      const response = await axios.get(`${API_URL}/api/stocks/batch?symbols=${symbols}`);
      if (response.data.type === 'stock_update') {
        updateWatchlistPrices(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching stock updates:', error.message);
      // Polling will automatically retry on next interval
    }
  };

  // Start polling for real-time updates
  const startPolling = () => {
    // Clear any existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    // Initial fetch
    fetchStockUpdates();
    
    // Poll every 30 seconds
    pollingIntervalRef.current = setInterval(fetchStockUpdates, 30000);
    console.log('Stock polling started (30s interval)');
  };

  // Update watchlist with real-time prices
  const updateWatchlistPrices = (newData) => {
    setWatchlist(prevWatchlist => {
      const updatedList = [...prevWatchlist];
      newData.forEach(newStock => {
        const index = updatedList.findIndex(s => s.symbol === newStock.symbol);
        if (index !== -1) {
          updatedList[index] = { ...updatedList[index], ...newStock };
        }
      });
      return updatedList;
    });
  };

  // Load watchlist from API
  const loadWatchlist = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/watchlist`);
      setWatchlist(response.data.stocks);
    } catch (error) {
      console.error('Error loading watchlist:', error);
    }
  };

  // Restart polling when watchlist changes (to fetch correct symbols)
  useEffect(() => {
    if (watchlist.length > 0) {
      startPolling();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchlist.length]); // Only restart when watchlist size changes

  // Select a stock to view details
  const selectStock = async (symbol) => {
    try {
      setIsLoadingChart(true);
      const response = await axios.get(`${API_URL}/api/stocks/${symbol}`);
      setSelectedStock(response.data);
      
      // Load historical data with selected period
      await loadStockHistory(symbol, selectedPeriod);
    } catch (error) {
      console.error('Error selecting stock:', error);
    } finally {
      setIsLoadingChart(false);
    }
  };

  // Load stock history with period
  const loadStockHistory = async (symbol, periodObj) => {
    try {
      setIsLoadingChart(true);
      const historyResponse = await axios.get(
        `${API_URL}/api/stocks/${symbol}/history?period=${periodObj.period}&interval=${periodObj.interval}`
      );
      setStockHistory(historyResponse.data.data);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setIsLoadingChart(false);
    }
  };

  // Handle period change
  const handlePeriodChange = (periodObj) => {
    setSelectedPeriod(periodObj);
    if (selectedStock) {
      loadStockHistory(selectedStock.symbol, periodObj);
    }
  };

  // Refresh all data
  const refreshAllData = async () => {
    setIsRefreshing(true);
    await Promise.all([
      loadWatchlist(),
      loadMarketIndices(),
      loadTrendingStocks(),
    ]);
    if (selectedStock) {
      await selectStock(selectedStock.symbol);
    }
    setIsRefreshing(false);
  };

  // Format large numbers
  const formatNumber = (num) => {
    if (!num) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString();
  };

  // Format volume
  const formatVolume = (num) => {
    if (!num) return 'N/A';
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toLocaleString();
  };

  // Debounced search ref
  const searchTimeoutRef = useRef(null);

  // Search stocks with debouncing
  const handleSearch = (query) => {
    setSearchQuery(query);
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (query.length >= 2) {  // Only search if 2+ characters
      // Debounce: wait 300ms before searching
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const response = await axios.get(`${API_URL}/api/stocks/search/${query}`);
          setSearchResults(response.data.results);
        } catch (error) {
          console.error('Error searching stocks:', error);
        }
      }, 300);
    } else {
      setSearchResults([]);
    }
  };

  // Add stock to watchlist with optimistic UI update
  const addToWatchlist = async (symbol) => {
    // Check if already in local watchlist state first (faster)
    if (watchlist.some(s => s.symbol.toUpperCase() === symbol.toUpperCase())) {
      alert(`${symbol} is already in your watchlist!`);
      setSearchQuery('');
      setSearchResults([]);
      return;
    }
    
    // Set loading state
    setAddingStock(symbol);
    
    // Optimistic UI: Clear search immediately for faster feel
    setSearchQuery('');
    setSearchResults([]);
    
    try {
      await axios.post(`${API_URL}/api/watchlist`, { symbol });
      // Reload to get full stock data
      await loadWatchlist();
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      
      // Handle "already exists" error from server
      if (error.response && error.response.status === 400) {
        alert(`${symbol} is already in your watchlist!`);
      } else {
        alert(`Failed to add ${symbol}. Please try again.`);
      }
    } finally {
      setAddingStock(null);
    }
  };

  // Remove stock from watchlist
  const removeFromWatchlist = async (symbol) => {
    try {
      await axios.delete(`${API_URL}/api/watchlist/${symbol}`);
      loadWatchlist();
      if (selectedStock?.symbol === symbol) {
        setSelectedStock(null);
      }
    } catch (error) {
      console.error('Error removing from watchlist:', error);
    }
  };

  // Send chat message
  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatInput('');
    setIsLoading(true);

    // Add user message to chat
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: userMessage,
        session_id: sessionId,
        stock_symbol: selectedStock?.symbol
      });

      // Add AI response to chat
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response 
      }]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <BarChart3 size={32} />
            <h1>AI StockPulse</h1>
          </div>
          
          <div className="search-container">
            <div className="search-bar">
              <Search size={20} />
              <input
                type="text"
                placeholder="Search stocks (e.g., AAPL, GOOGL)..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>
            
            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map(stock => (
                  <div 
                    key={stock.symbol} 
                    className={`search-result-item ${addingStock === stock.symbol ? 'adding' : ''}`}
                  >
                    <div className="stock-info-text">
                      <strong>{stock.symbol}</strong>
                      <span>{stock.name}</span>
                    </div>
                    <button 
                      className="add-stock-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        addToWatchlist(stock.symbol);
                      }}
                      disabled={addingStock === stock.symbol}
                    >
                      {addingStock === stock.symbol ? (
                        <span className="loading-spinner"></span>
                      ) : (
                        <>
                          <Plus size={16} />
                          <span>Add</span>
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="header-actions">
            <button 
              className={`icon-btn ${isRefreshing ? 'spinning' : ''}`}
              onClick={refreshAllData}
              title="Refresh Data"
            >
              <RefreshCw size={20} />
            </button>
            <button 
              className="icon-btn"
              onClick={() => setIsDarkMode(!isDarkMode)}
              title="Toggle Theme"
            >
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
        </div>
        
        {/* Market Indices Ticker */}
        {marketIndices.length > 0 && (
          <div className="market-ticker">
            {marketIndices.map(index => (
              <div key={index.symbol} className="ticker-item">
                <span className="ticker-name">{index.display_name || index.symbol}</span>
                <span className="ticker-price">{index.price?.toFixed(2)}</span>
                <span className={`ticker-change ${index.change_percent >= 0 ? 'positive' : 'negative'}`}>
                  {index.change_percent >= 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Watchlist Sidebar */}
        <aside className="sidebar">
          <div className="watchlist">
            <h2>
              <Activity size={20} />
              Your Watchlist
            </h2>
            <div className="watchlist-items">
              {watchlist.length === 0 ? (
                <div className="empty-watchlist">
                  <p>No stocks in watchlist</p>
                  <span>Search to add stocks</span>
                </div>
              ) : (
                watchlist.map(stock => (
                  <div 
                    key={stock.symbol}
                    className={`watchlist-item ${selectedStock?.symbol === stock.symbol ? 'active' : ''}`}
                    onClick={() => selectStock(stock.symbol)}
                  >
                    <div className="stock-info">
                      <div className="stock-header">
                        <strong>{stock.symbol}</strong>
                        <button 
                          className="remove-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeFromWatchlist(stock.symbol);
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                      <span className="company-name">{stock.company_name}</span>
                    </div>
                    <div className="stock-price">
                      <strong>${stock.price?.toFixed(2)}</strong>
                      <span className={stock.change_percent >= 0 ? 'positive' : 'negative'}>
                        {stock.change_percent >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {stock.change_percent?.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Trending Section */}
          {trendingStocks.length > 0 && (
            <div className="trending-section">
              <h3>
                <TrendingUp size={18} />
                Trending Today
              </h3>
              <div className="trending-items">
                {trendingStocks.slice(0, 5).map(stock => (
                  <div 
                    key={stock.symbol}
                    className="trending-item"
                    onClick={() => selectStock(stock.symbol)}
                  >
                    <div className="trending-info">
                      <strong>{stock.symbol}</strong>
                      <span>${stock.price?.toFixed(2)}</span>
                    </div>
                    <span className={`trending-change ${stock.change_percent >= 0 ? 'positive' : 'negative'}`}>
                      {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Stock Details */}
        <main className="stock-details">
          {selectedStock ? (
            <>
              <div className="stock-header-section">
                <div className="stock-title">
                  <h1>{selectedStock.company_name}</h1>
                  <div className="stock-meta">
                    <span className="symbol">{selectedStock.symbol}</span>
                    {selectedStock.sector && (
                      <span className="sector">
                        <Building2 size={14} />
                        {selectedStock.sector}
                      </span>
                    )}
                  </div>
                </div>
                <div className="price-section">
                  <h2>${selectedStock.price?.toFixed(2)}</h2>
                  <span className={selectedStock.change_percent >= 0 ? 'change positive' : 'change negative'}>
                    {selectedStock.change_percent >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                    {selectedStock.change_percent >= 0 ? '+' : ''}
                    {selectedStock.change_percent?.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Chart with Period Selection */}
              <div className="chart-container">
                <div className="chart-header">
                  <h3>Price Chart</h3>
                  <div className="period-selector">
                    {CHART_PERIODS.map(period => (
                      <button
                        key={period.label}
                        className={`period-btn ${selectedPeriod.label === period.label ? 'active' : ''}`}
                        onClick={() => handlePeriodChange(period)}
                      >
                        {period.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                {isLoadingChart ? (
                  <div className="chart-loading">
                    <div className="loading-spinner large"></div>
                    <p>Loading chart data...</p>
                  </div>
                ) : stockHistory.length > 0 ? (
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={stockHistory}>
                      <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDarkMode ? '#333' : '#eee'} />
                      <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(time) => {
                          const date = new Date(time);
                          if (selectedPeriod.period === '1d') {
                            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                          }
                          return date.toLocaleDateString([], {month: 'short', day: 'numeric'});
                        }}
                        stroke={isDarkMode ? '#888' : '#666'}
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis 
                        stroke={isDarkMode ? '#888' : '#666'}
                        domain={['auto', 'auto']}
                        tickFormatter={(val) => `$${val.toFixed(0)}`}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: isDarkMode ? '#1a1a2e' : '#fff', 
                          border: `1px solid ${isDarkMode ? '#333' : '#ddd'}`,
                          borderRadius: '8px'
                        }}
                        labelFormatter={(time) => new Date(time).toLocaleString()}
                        formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="close" 
                        stroke="#00d4ff" 
                        strokeWidth={2}
                        fill="url(#colorPrice)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="no-chart-data">
                    <p>No chart data available</p>
                  </div>
                )}
              </div>

              {/* Stock Stats Grid */}
              <div className="stock-stats-grid">
                <div className="stat-card">
                  <div className="stat-icon"><DollarSign size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">Market Cap</span>
                    <span className="stat-value">{formatNumber(selectedStock.market_cap)}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><Activity size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">Volume</span>
                    <span className="stat-value">{formatVolume(selectedStock.volume)}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><PieChart size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">P/E Ratio</span>
                    <span className="stat-value">{selectedStock.pe_ratio || 'N/A'}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><Percent size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">Dividend Yield</span>
                    <span className="stat-value">{selectedStock.dividend_yield ? `${selectedStock.dividend_yield}%` : 'N/A'}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><TrendingUp size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">52W High</span>
                    <span className="stat-value">${selectedStock.year_high?.toFixed(2) || 'N/A'}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><TrendingDown size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">52W Low</span>
                    <span className="stat-value">${selectedStock.year_low?.toFixed(2) || 'N/A'}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><Clock size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">Day Range</span>
                    <span className="stat-value">${selectedStock.day_low?.toFixed(2)} - ${selectedStock.day_high?.toFixed(2)}</span>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon"><Info size={20} /></div>
                  <div className="stat-content">
                    <span className="stat-label">Beta</span>
                    <span className="stat-value">{selectedStock.beta || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Company Description */}
              {selectedStock.description && (
                <div className="company-description">
                  <h3>About {selectedStock.company_name}</h3>
                  <p>{selectedStock.description}</p>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <BarChart3 size={80} />
              <h2>Welcome to AI StockPulse</h2>
              <p>Select a stock from your watchlist or search for a new one</p>
              <div className="quick-actions">
                <button onClick={() => addToWatchlist('AAPL')}>
                  <Plus size={16} /> Add AAPL
                </button>
                <button onClick={() => addToWatchlist('GOOGL')}>
                  <Plus size={16} /> Add GOOGL
                </button>
                <button onClick={() => addToWatchlist('TSLA')}>
                  <Plus size={16} /> Add TSLA
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* AI Chat Button */}
      <button 
        className="chat-button"
        onClick={() => setIsChatOpen(!isChatOpen)}
      >
        {isChatOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* AI Chat Panel */}
      {isChatOpen && (
        <div className="chat-panel">
          <div className="chat-header">
            <h3>AI Stock Assistant</h3>
            <button onClick={() => setIsChatOpen(false)}>
              <X size={20} />
            </button>
          </div>
          
          <div className="chat-messages">
            {chatMessages.length === 0 && (
              <div className="chat-welcome">
                <MessageCircle size={48} />
                <p>Ask me anything about stocks!</p>
                <div className="example-questions">
                  <button onClick={() => setChatInput("What's a good P/E ratio?")}>
                    What's a good P/E ratio?
                  </button>
                  <button onClick={() => setChatInput("Should I invest in tech stocks?")}>
                    Should I invest in tech?
                  </button>
                </div>
              </div>
            )}
            
            {chatMessages.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="chat-message assistant">
                <div className="message-content loading">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>
          
          <div className="chat-input">
            <input
              type="text"
              placeholder="Ask about stocks..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
              disabled={isLoading}
            />
            <button onClick={sendChatMessage} disabled={isLoading}>
              <Send size={20} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;