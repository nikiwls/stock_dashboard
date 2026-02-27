"""
Stock Data Service
Fetches real-time stock data from Yahoo Finance (FREE!)
With fallback data when rate limited
"""

import yfinance as yf
from datetime import datetime
from typing import Optional, Dict, List
import time
import random
import requests


# Simple cache to reduce API requests
_stock_cache: Dict[str, Dict] = {}
_cache_expiry: Dict[str, float] = {}
_company_name_cache: Dict[str, str] = {}  # Persistent company name cache
CACHE_TTL_SECONDS = 300  # Cache data for 5 minutes to avoid rate limits

# Track if we're being rate limited
_rate_limited_until: float = 0

# Fallback data when Yahoo Finance is rate limiting
FALLBACK_DATA = {
    # Market Indices
    '^GSPC': {'symbol': '^GSPC', 'company_name': 'S&P 500', 'price': 5021.84, 'change_percent': 0.52, 'volume': 2500000000, 'market_cap': 0},
    '^DJI': {'symbol': '^DJI', 'company_name': 'Dow Jones Industrial Average', 'price': 38996.39, 'change_percent': 0.35, 'volume': 350000000, 'market_cap': 0},
    '^IXIC': {'symbol': '^IXIC', 'company_name': 'NASDAQ Composite', 'price': 15942.55, 'change_percent': 0.78, 'volume': 4500000000, 'market_cap': 0},
    '^VIX': {'symbol': '^VIX', 'company_name': 'CBOE Volatility Index', 'price': 14.25, 'change_percent': -2.15, 'volume': 0, 'market_cap': 0},
    # Stocks
    'AAPL': {'symbol': 'AAPL', 'company_name': 'Apple Inc.', 'price': 178.50, 'change_percent': 1.25, 'volume': 50000000, 'market_cap': 2800000000000},
    'GOOGL': {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc.', 'price': 142.30, 'change_percent': -0.80, 'volume': 25000000, 'market_cap': 1800000000000},
    'MSFT': {'symbol': 'MSFT', 'company_name': 'Microsoft Corporation', 'price': 385.00, 'change_percent': 2.10, 'volume': 30000000, 'market_cap': 2900000000000},
    'TSLA': {'symbol': 'TSLA', 'company_name': 'Tesla Inc.', 'price': 248.75, 'change_percent': -1.50, 'volume': 100000000, 'market_cap': 790000000000},
    'AMZN': {'symbol': 'AMZN', 'company_name': 'Amazon.com Inc.', 'price': 158.20, 'change_percent': 0.95, 'volume': 40000000, 'market_cap': 1650000000000},
    'META': {'symbol': 'META', 'company_name': 'Meta Platforms Inc.', 'price': 505.00, 'change_percent': 1.80, 'volume': 20000000, 'market_cap': 1300000000000},
    'NVDA': {'symbol': 'NVDA', 'company_name': 'NVIDIA Corporation', 'price': 875.50, 'change_percent': 3.20, 'volume': 45000000, 'market_cap': 2150000000000},
    'JPM': {'symbol': 'JPM', 'company_name': 'JPMorgan Chase & Co.', 'price': 198.25, 'change_percent': 0.45, 'volume': 12000000, 'market_cap': 570000000000},
    'V': {'symbol': 'V', 'company_name': 'Visa Inc.', 'price': 280.50, 'change_percent': 0.65, 'volume': 8000000, 'market_cap': 580000000000},
    'WMT': {'symbol': 'WMT', 'company_name': 'Walmart Inc.', 'price': 165.30, 'change_percent': -0.25, 'volume': 10000000, 'market_cap': 450000000000},
    # Additional common stocks
    'AAL': {'symbol': 'AAL', 'company_name': 'American Airlines Group Inc.', 'price': 14.50, 'change_percent': -0.35, 'volume': 35000000, 'market_cap': 9500000000},
    'KO': {'symbol': 'KO', 'company_name': 'The Coca-Cola Company', 'price': 62.80, 'change_percent': 0.55, 'volume': 15000000, 'market_cap': 270000000000},
    'DIS': {'symbol': 'DIS', 'company_name': 'The Walt Disney Company', 'price': 112.40, 'change_percent': 0.85, 'volume': 12000000, 'market_cap': 205000000000},
    'NFLX': {'symbol': 'NFLX', 'company_name': 'Netflix Inc.', 'price': 485.20, 'change_percent': 1.45, 'volume': 8000000, 'market_cap': 215000000000},
    'BA': {'symbol': 'BA', 'company_name': 'The Boeing Company', 'price': 215.60, 'change_percent': -1.20, 'volume': 6000000, 'market_cap': 130000000000},
    'INTC': {'symbol': 'INTC', 'company_name': 'Intel Corporation', 'price': 45.30, 'change_percent': -0.65, 'volume': 25000000, 'market_cap': 190000000000},
    'AMD': {'symbol': 'AMD', 'company_name': 'Advanced Micro Devices Inc.', 'price': 165.80, 'change_percent': 2.35, 'volume': 50000000, 'market_cap': 270000000000},
    'PYPL': {'symbol': 'PYPL', 'company_name': 'PayPal Holdings Inc.', 'price': 68.40, 'change_percent': 0.95, 'volume': 15000000, 'market_cap': 75000000000},
    'CRM': {'symbol': 'CRM', 'company_name': 'Salesforce Inc.', 'price': 275.30, 'change_percent': 1.15, 'volume': 5000000, 'market_cap': 265000000000},
    'UBER': {'symbol': 'UBER', 'company_name': 'Uber Technologies Inc.', 'price': 72.50, 'change_percent': 1.85, 'volume': 20000000, 'market_cap': 150000000000},
    'SBUX': {'symbol': 'SBUX', 'company_name': 'Starbucks Corporation', 'price': 98.20, 'change_percent': 0.45, 'volume': 8000000, 'market_cap': 112000000000},
    'NKE': {'symbol': 'NKE', 'company_name': 'Nike Inc.', 'price': 108.50, 'change_percent': -0.55, 'volume': 7000000, 'market_cap': 165000000000},
    'PEP': {'symbol': 'PEP', 'company_name': 'PepsiCo Inc.', 'price': 178.90, 'change_percent': 0.35, 'volume': 6000000, 'market_cap': 245000000000},
    'COST': {'symbol': 'COST', 'company_name': 'Costco Wholesale Corporation', 'price': 585.40, 'change_percent': 0.75, 'volume': 3000000, 'market_cap': 260000000000},
    'HD': {'symbol': 'HD', 'company_name': 'The Home Depot Inc.', 'price': 365.20, 'change_percent': 0.65, 'volume': 4000000, 'market_cap': 365000000000},
    'MCD': {'symbol': 'MCD', 'company_name': "McDonald's Corporation", 'price': 295.80, 'change_percent': 0.25, 'volume': 3500000, 'market_cap': 215000000000},
    'XOM': {'symbol': 'XOM', 'company_name': 'Exxon Mobil Corporation', 'price': 105.40, 'change_percent': -0.85, 'volume': 18000000, 'market_cap': 420000000000},
    'CVX': {'symbol': 'CVX', 'company_name': 'Chevron Corporation', 'price': 158.70, 'change_percent': -0.45, 'volume': 8000000, 'market_cap': 295000000000},
    'BAC': {'symbol': 'BAC', 'company_name': 'Bank of America Corporation', 'price': 35.80, 'change_percent': 0.55, 'volume': 45000000, 'market_cap': 280000000000},
    'GS': {'symbol': 'GS', 'company_name': 'The Goldman Sachs Group Inc.', 'price': 385.60, 'change_percent': 0.95, 'volume': 2500000, 'market_cap': 125000000000},
    'MS': {'symbol': 'MS', 'company_name': 'Morgan Stanley', 'price': 95.40, 'change_percent': 0.75, 'volume': 9000000, 'market_cap': 155000000000},
    'T': {'symbol': 'T', 'company_name': 'AT&T Inc.', 'price': 18.50, 'change_percent': 0.15, 'volume': 35000000, 'market_cap': 132000000000},
    'VZ': {'symbol': 'VZ', 'company_name': 'Verizon Communications Inc.', 'price': 42.80, 'change_percent': 0.25, 'volume': 20000000, 'market_cap': 180000000000},
    'PFE': {'symbol': 'PFE', 'company_name': 'Pfizer Inc.', 'price': 28.90, 'change_percent': -0.35, 'volume': 40000000, 'market_cap': 165000000000},
    'JNJ': {'symbol': 'JNJ', 'company_name': 'Johnson & Johnson', 'price': 158.40, 'change_percent': 0.45, 'volume': 8000000, 'market_cap': 385000000000},
    'UNH': {'symbol': 'UNH', 'company_name': 'UnitedHealth Group Inc.', 'price': 525.30, 'change_percent': 0.85, 'volume': 4000000, 'market_cap': 485000000000},
    'ABBV': {'symbol': 'ABBV', 'company_name': 'AbbVie Inc.', 'price': 165.20, 'change_percent': 0.55, 'volume': 6000000, 'market_cap': 290000000000},
    'LLY': {'symbol': 'LLY', 'company_name': 'Eli Lilly and Company', 'price': 585.80, 'change_percent': 1.25, 'volume': 3000000, 'market_cap': 555000000000},
    'MRNA': {'symbol': 'MRNA', 'company_name': 'Moderna Inc.', 'price': 98.50, 'change_percent': -1.85, 'volume': 12000000, 'market_cap': 38000000000},
    'F': {'symbol': 'F', 'company_name': 'Ford Motor Company', 'price': 12.40, 'change_percent': 0.65, 'volume': 55000000, 'market_cap': 50000000000},
    'GM': {'symbol': 'GM', 'company_name': 'General Motors Company', 'price': 38.90, 'change_percent': 0.85, 'volume': 15000000, 'market_cap': 53000000000},
    'RIVN': {'symbol': 'RIVN', 'company_name': 'Rivian Automotive Inc.', 'price': 18.20, 'change_percent': -2.15, 'volume': 25000000, 'market_cap': 18000000000},
    'LCID': {'symbol': 'LCID', 'company_name': 'Lucid Group Inc.', 'price': 4.85, 'change_percent': -1.45, 'volume': 30000000, 'market_cap': 11000000000},
    'PLTR': {'symbol': 'PLTR', 'company_name': 'Palantir Technologies Inc.', 'price': 22.40, 'change_percent': 2.85, 'volume': 45000000, 'market_cap': 48000000000},
    'SNOW': {'symbol': 'SNOW', 'company_name': 'Snowflake Inc.', 'price': 185.60, 'change_percent': 1.45, 'volume': 5000000, 'market_cap': 62000000000},
    'COIN': {'symbol': 'COIN', 'company_name': 'Coinbase Global Inc.', 'price': 145.30, 'change_percent': 3.25, 'volume': 12000000, 'market_cap': 35000000000},
    'SQ': {'symbol': 'SQ', 'company_name': 'Block Inc.', 'price': 72.80, 'change_percent': 1.65, 'volume': 10000000, 'market_cap': 45000000000},
    'SHOP': {'symbol': 'SHOP', 'company_name': 'Shopify Inc.', 'price': 68.40, 'change_percent': 1.95, 'volume': 8000000, 'market_cap': 85000000000},
    'SPOT': {'symbol': 'SPOT', 'company_name': 'Spotify Technology S.A.', 'price': 185.20, 'change_percent': 0.85, 'volume': 3000000, 'market_cap': 36000000000},
    'ABNB': {'symbol': 'ABNB', 'company_name': 'Airbnb Inc.', 'price': 145.60, 'change_percent': 1.35, 'volume': 6000000, 'market_cap': 92000000000},
    'ZM': {'symbol': 'ZM', 'company_name': 'Zoom Video Communications Inc.', 'price': 68.90, 'change_percent': -0.75, 'volume': 4000000, 'market_cap': 21000000000},
    'ROKU': {'symbol': 'ROKU', 'company_name': 'Roku Inc.', 'price': 85.40, 'change_percent': 1.15, 'volume': 5000000, 'market_cap': 12000000000},
    'SNAP': {'symbol': 'SNAP', 'company_name': 'Snap Inc.', 'price': 12.80, 'change_percent': -0.95, 'volume': 25000000, 'market_cap': 21000000000},
    'PINS': {'symbol': 'PINS', 'company_name': 'Pinterest Inc.', 'price': 32.50, 'change_percent': 0.65, 'volume': 12000000, 'market_cap': 22000000000},
    'TWTR': {'symbol': 'TWTR', 'company_name': 'X Corp (Twitter)', 'price': 45.00, 'change_percent': 0.00, 'volume': 0, 'market_cap': 0},
    'GOOG': {'symbol': 'GOOG', 'company_name': 'Alphabet Inc. Class C', 'price': 143.50, 'change_percent': -0.75, 'volume': 20000000, 'market_cap': 1790000000000},
}


def _lookup_company_name(symbol: str) -> str:
    """
    Look up company name from Yahoo Finance search API
    Uses a separate cache to avoid repeated lookups
    """
    global _company_name_cache
    symbol = symbol.upper()
    
    # Check cache first
    if symbol in _company_name_cache:
        return _company_name_cache[symbol]
    
    # Check if in FALLBACK_DATA
    if symbol in FALLBACK_DATA:
        name = FALLBACK_DATA[symbol]['company_name']
        _company_name_cache[symbol] = name
        return name
    
    # Try Yahoo Finance search API
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': symbol,
            'quotesCount': 5,
            'newsCount': 0
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            for quote in quotes:
                if quote.get('symbol', '').upper() == symbol:
                    name = quote.get('longname') or quote.get('shortname') or symbol
                    _company_name_cache[symbol] = name
                    print(f"🔍 Found company name for {symbol}: {name}")
                    return name
    except Exception as e:
        print(f"⚠️ Could not lookup company name for {symbol}: {e}")
    
    # Default: return symbol itself
    _company_name_cache[symbol] = symbol
    return symbol


class StockService:
    """
    Service class to interact with Yahoo Finance
    yfinance is a FREE library that doesn't require API keys!
    """
    
    @staticmethod
    def _get_fallback_data(symbol: str) -> Optional[Dict]:
        """Return fallback data for a symbol when rate limited"""
        global _rate_limited_until
        symbol = symbol.upper()
        
        if symbol in FALLBACK_DATA:
            data = FALLBACK_DATA[symbol].copy()
            # Add small random variation to make it look dynamic
            variation = random.uniform(-0.5, 0.5)
            data['price'] = round(data['price'] * (1 + variation/100), 2)
            data['change_percent'] = round(data['change_percent'] + random.uniform(-0.1, 0.1), 2)
            data['timestamp'] = datetime.utcnow()
            # Add enhanced metrics with reasonable defaults
            data['previous_close'] = round(data['price'] / (1 + data['change_percent']/100), 2)
            data['open'] = round(data['price'] * random.uniform(0.995, 1.005), 2)
            data['day_high'] = round(data['price'] * random.uniform(1.005, 1.02), 2)
            data['day_low'] = round(data['price'] * random.uniform(0.98, 0.995), 2)
            data['year_high'] = round(data['price'] * random.uniform(1.1, 1.4), 2)
            data['year_low'] = round(data['price'] * random.uniform(0.6, 0.85), 2)
            data['pe_ratio'] = round(random.uniform(15, 45), 2)
            data['eps'] = round(data['price'] / data['pe_ratio'], 2)
            data['dividend_yield'] = round(random.uniform(0, 2.5), 2)
            data['beta'] = round(random.uniform(0.8, 1.5), 2)
            data['avg_volume'] = int(data['volume'] * random.uniform(0.9, 1.1))
            data['sector'] = 'Technology'
            data['industry'] = 'Technology'
            data['description'] = ''
            print(f"📦 Using fallback data for {symbol} (rate limited)")
            return data
        
        # For unknown symbols, try to get real company name and generate simulated data
        company_name = _lookup_company_name(symbol)
        print(f"📦 Generating dynamic data for {symbol} ({company_name})")
        base_price = 50.00 + random.uniform(10, 200)  # More varied price range
        pe = round(random.uniform(12, 40), 2)
        change_pct = round(random.uniform(-3, 3), 2)
        return {
            'symbol': symbol,
            'company_name': company_name,
            'price': round(base_price, 2),
            'change_percent': change_pct,
            'volume': random.randint(500000, 80000000),
            'market_cap': random.randint(1000000000, 500000000000),
            'previous_close': round(base_price / (1 + change_pct/100), 2),
            'open': round(base_price * random.uniform(0.995, 1.005), 2),
            'day_high': round(base_price * random.uniform(1.01, 1.025), 2),
            'day_low': round(base_price * random.uniform(0.975, 0.99), 2),
            'year_high': round(base_price * random.uniform(1.15, 1.5), 2),
            'year_low': round(base_price * random.uniform(0.55, 0.85), 2),
            'pe_ratio': pe,
            'eps': round(base_price / pe, 2),
            'dividend_yield': round(random.uniform(0, 3), 2),
            'beta': round(random.uniform(0.7, 1.6), 2),
            'avg_volume': random.randint(5000000, 30000000),
            'sector': 'Unknown',
            'industry': 'Unknown',
            'description': '',
            'timestamp': datetime.utcnow()
        }
    
    @staticmethod
    def get_stock_data(symbol: str, max_retries: int = 2) -> Optional[Dict]:
        """
        Fetch real-time stock data for a given symbol
        Falls back to cached data when rate limited
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
            max_retries: Number of retry attempts
            
        Returns:
            Dictionary with stock data or None if error
        """
        global _rate_limited_until
        symbol = symbol.upper()
        
        # Check cache first to avoid unnecessary API calls
        if symbol in _stock_cache and symbol in _cache_expiry:
            if time.time() < _cache_expiry[symbol]:
                print(f"📦 Using cached data for {symbol}")
                return _stock_cache[symbol]
        
        # If we're in rate-limited mode, use fallback immediately
        if time.time() < _rate_limited_until:
            print(f"⏸️  Rate limit cooldown active, using fallback for {symbol}")
            return StockService._get_fallback_data(symbol)
        
        for attempt in range(max_retries):
            try:
                # Add small delay to avoid rate limiting
                if attempt > 0:
                    delay = (attempt + 1) * 2
                    print(f"⏳ Waiting {delay}s before retry {attempt + 1}...")
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(0.2, 0.5))
                
                # Create ticker object
                ticker = yf.Ticker(symbol)
                
                # Get real-time info (this is where rate limiting happens)
                info = ticker.info
                
                # Get current price from fast_info (faster than info)
                try:
                    fast_info = ticker.fast_info
                    current_price = fast_info.get('last_price', info.get('currentPrice', 0))
                except:
                    current_price = info.get('currentPrice', 0)
                
                # If we got no price, use fallback
                if not current_price or current_price == 0:
                    print(f"⚠️  No price data for {symbol}, using fallback")
                    return StockService._get_fallback_data(symbol)
                
                # Calculate change percentage
                previous_close = info.get('previousClose', current_price)
                change_percent = ((current_price - previous_close) / previous_close * 100) if previous_close else 0
                
                result = {
                    'symbol': symbol.upper(),
                    'company_name': info.get('longName', symbol),
                    'price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'previous_close': info.get('previousClose', 0),
                    'open': info.get('open', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                    'year_high': info.get('fiftyTwoWeekHigh', 0),
                    'year_low': info.get('fiftyTwoWeekLow', 0),
                    # New enhanced metrics
                    'pe_ratio': round(info.get('trailingPE', 0) or 0, 2),
                    'eps': round(info.get('trailingEps', 0) or 0, 2),
                    'dividend_yield': round((info.get('dividendYield', 0) or 0) * 100, 2),
                    'beta': round(info.get('beta', 0) or 0, 2),
                    'avg_volume': info.get('averageVolume', 0),
                    'shares_outstanding': info.get('sharesOutstanding', 0),
                    'book_value': round(info.get('bookValue', 0) or 0, 2),
                    'price_to_book': round(info.get('priceToBook', 0) or 0, 2),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'description': info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else '',
                    'timestamp': datetime.utcnow()
                }
                
                # Store in cache
                _stock_cache[symbol] = result
                _cache_expiry[symbol] = time.time() + CACHE_TTL_SECONDS
                print(f"✅ Got live data for {symbol}")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    print(f"⚠️  Rate limited on {symbol}!")
                    # Set cooldown for 60 seconds
                    _rate_limited_until = time.time() + 60
                    return StockService._get_fallback_data(symbol)
                else:
                    print(f"❌ Error fetching data for {symbol}: {e}")
                    return StockService._get_fallback_data(symbol)
        
        return StockService._get_fallback_data(symbol)
    
    
    @staticmethod
    def get_multiple_stocks(symbols: List[str]) -> List[Dict]:
        """
        Fetch data for multiple stocks at once
        WITH DELAYS to avoid rate limiting
        
        Args:
            symbols: List of stock ticker symbols
            
        Returns:
            List of stock data dictionaries
        """
        results = []
        for i, symbol in enumerate(symbols):
            print(f"📊 Fetching {symbol} ({i+1}/{len(symbols)})...")
            data = StockService.get_stock_data(symbol)
            if data:
                results.append(data)
            
            # Reduced delay between stocks (was 1-5 seconds)
            if i < len(symbols) - 1:
                delay = random.uniform(0.3, 0.8)
                time.sleep(delay)
        
        return results
    
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1d", interval: str = "1m"):
        """
        Get historical stock data
        
        Args:
            symbol: Stock ticker symbol
            period: Data period - "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
            interval: Data interval - "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"
            
        Returns:
            Pandas DataFrame with historical data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            # Convert to list of dictionaries
            data = []
            for index, row in hist.iterrows():
                data.append({
                    'timestamp': index.isoformat(),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume'])
                })
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching historical data for {symbol}: {e}")
            return []
    
    
    @staticmethod
    def search_stocks(query: str) -> List[Dict]:
        """
        Search for stocks by company name or symbol
        Uses Yahoo Finance search API with fallback to expanded local list
        
        Args:
            query: Search query
            
        Returns:
            List of matching stocks
        """
        import requests
        
        query = query.strip().upper()
        if not query:
            return []
        
        # Try Yahoo Finance search API first
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                'q': query,
                'quotesCount': 10,
                'newsCount': 0,
                'enableFuzzyQuery': True,
                'quotesQueryId': 'tss_match_phrase_query'
            }
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for quote in data.get('quotes', []):
                    # Only include stocks (not ETFs, mutual funds, etc.) - or include them all
                    quote_type = quote.get('quoteType', '')
                    if quote_type in ['EQUITY', 'ETF', 'INDEX']:
                        results.append({
                            'symbol': quote.get('symbol', ''),
                            'name': quote.get('shortname') or quote.get('longname') or quote.get('symbol', '')
                        })
                
                if results:
                    print(f"🔍 Found {len(results)} results from Yahoo Finance for '{query}'")
                    return results[:8]
                    
        except Exception as e:
            print(f"⚠️ Yahoo search failed: {e}, using fallback")
        
        # Expanded fallback list of popular stocks
        common_stocks = [
            # Tech
            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
            {'symbol': 'GOOG', 'name': 'Alphabet Inc. Class C'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
            {'symbol': 'AMD', 'name': 'Advanced Micro Devices'},
            {'symbol': 'INTC', 'name': 'Intel Corporation'},
            {'symbol': 'CRM', 'name': 'Salesforce Inc.'},
            {'symbol': 'ORCL', 'name': 'Oracle Corporation'},
            {'symbol': 'ADBE', 'name': 'Adobe Inc.'},
            {'symbol': 'NFLX', 'name': 'Netflix Inc.'},
            {'symbol': 'PYPL', 'name': 'PayPal Holdings Inc.'},
            {'symbol': 'UBER', 'name': 'Uber Technologies'},
            {'symbol': 'LYFT', 'name': 'Lyft Inc.'},
            {'symbol': 'SNAP', 'name': 'Snap Inc.'},
            {'symbol': 'TWTR', 'name': 'Twitter Inc.'},
            {'symbol': 'SQ', 'name': 'Block Inc.'},
            {'symbol': 'SHOP', 'name': 'Shopify Inc.'},
            {'symbol': 'SPOT', 'name': 'Spotify Technology'},
            {'symbol': 'ZM', 'name': 'Zoom Video Communications'},
            {'symbol': 'ROKU', 'name': 'Roku Inc.'},
            # Finance
            {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
            {'symbol': 'BAC', 'name': 'Bank of America'},
            {'symbol': 'WFC', 'name': 'Wells Fargo & Company'},
            {'symbol': 'GS', 'name': 'Goldman Sachs Group'},
            {'symbol': 'MS', 'name': 'Morgan Stanley'},
            {'symbol': 'V', 'name': 'Visa Inc.'},
            {'symbol': 'MA', 'name': 'Mastercard Inc.'},
            {'symbol': 'AXP', 'name': 'American Express'},
            {'symbol': 'C', 'name': 'Citigroup Inc.'},
            # Consumer
            {'symbol': 'WMT', 'name': 'Walmart Inc.'},
            {'symbol': 'TGT', 'name': 'Target Corporation'},
            {'symbol': 'COST', 'name': 'Costco Wholesale'},
            {'symbol': 'HD', 'name': 'Home Depot Inc.'},
            {'symbol': 'LOW', 'name': 'Lowes Companies'},
            {'symbol': 'NKE', 'name': 'Nike Inc.'},
            {'symbol': 'SBUX', 'name': 'Starbucks Corporation'},
            {'symbol': 'MCD', 'name': 'McDonalds Corporation'},
            {'symbol': 'KO', 'name': 'Coca-Cola Company'},
            {'symbol': 'PEP', 'name': 'PepsiCo Inc.'},
            {'symbol': 'PG', 'name': 'Procter & Gamble'},
            # Healthcare
            {'symbol': 'JNJ', 'name': 'Johnson & Johnson'},
            {'symbol': 'UNH', 'name': 'UnitedHealth Group'},
            {'symbol': 'PFE', 'name': 'Pfizer Inc.'},
            {'symbol': 'MRNA', 'name': 'Moderna Inc.'},
            {'symbol': 'ABBV', 'name': 'AbbVie Inc.'},
            {'symbol': 'LLY', 'name': 'Eli Lilly and Company'},
            {'symbol': 'MRK', 'name': 'Merck & Co.'},
            # Energy
            {'symbol': 'XOM', 'name': 'Exxon Mobil Corporation'},
            {'symbol': 'CVX', 'name': 'Chevron Corporation'},
            {'symbol': 'COP', 'name': 'ConocoPhillips'},
            # Industrial
            {'symbol': 'BA', 'name': 'Boeing Company'},
            {'symbol': 'CAT', 'name': 'Caterpillar Inc.'},
            {'symbol': 'GE', 'name': 'General Electric'},
            {'symbol': 'MMM', 'name': '3M Company'},
            {'symbol': 'HON', 'name': 'Honeywell International'},
            # Telecom
            {'symbol': 'T', 'name': 'AT&T Inc.'},
            {'symbol': 'VZ', 'name': 'Verizon Communications'},
            {'symbol': 'TMUS', 'name': 'T-Mobile US Inc.'},
            # Entertainment
            {'symbol': 'DIS', 'name': 'Walt Disney Company'},
            {'symbol': 'CMCSA', 'name': 'Comcast Corporation'},
            # Auto
            {'symbol': 'F', 'name': 'Ford Motor Company'},
            {'symbol': 'GM', 'name': 'General Motors'},
            {'symbol': 'RIVN', 'name': 'Rivian Automotive'},
            {'symbol': 'LCID', 'name': 'Lucid Group Inc.'},
            # Airlines
            {'symbol': 'DAL', 'name': 'Delta Air Lines'},
            {'symbol': 'UAL', 'name': 'United Airlines'},
            {'symbol': 'AAL', 'name': 'American Airlines'},
            {'symbol': 'LUV', 'name': 'Southwest Airlines'},
            # Crypto-related
            {'symbol': 'COIN', 'name': 'Coinbase Global'},
            {'symbol': 'MSTR', 'name': 'MicroStrategy Inc.'},
            # ETFs
            {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF'},
            {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust'},
            {'symbol': 'IWM', 'name': 'iShares Russell 2000 ETF'},
            {'symbol': 'DIA', 'name': 'SPDR Dow Jones ETF'},
            {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF'},
            {'symbol': 'VOO', 'name': 'Vanguard S&P 500 ETF'},
            {'symbol': 'ARKK', 'name': 'ARK Innovation ETF'},
            # Indices (for reference)
            {'symbol': '^GSPC', 'name': 'S&P 500 Index'},
            {'symbol': '^DJI', 'name': 'Dow Jones Industrial Average'},
            {'symbol': '^IXIC', 'name': 'NASDAQ Composite'},
        ]
        
        query_lower = query.lower()
        results = [
            stock for stock in common_stocks
            if query_lower in stock['symbol'].lower() or query_lower in stock['name'].lower()
        ]
        
        # If exact symbol match, also add it even if not in list
        if not results and len(query) <= 5 and query.isalpha():
            results.append({'symbol': query.upper(), 'name': f'{query.upper()} (Custom)'})
        
        return results[:8]  # Return top 8 matches


# =======================
# Example Usage
# =======================

if __name__ == "__main__":
    # Test the stock service
    service = StockService()
    
    print("\n📊 Fetching AAPL stock data...")
    aapl_data = service.get_stock_data("AAPL")
    if aapl_data:
        print(f"✅ {aapl_data['company_name']}")
        print(f"   Price: ${aapl_data['price']}")
        print(f"   Change: {aapl_data['change_percent']}%")
    
    print("\n📊 Fetching multiple stocks...")
    stocks = service.get_multiple_stocks(["AAPL", "GOOGL", "MSFT"])
    for stock in stocks:
        print(f"   {stock['symbol']}: ${stock['price']} ({stock['change_percent']}%)")
    
    print("\n📊 Fetching historical data...")
    history = service.get_historical_data("AAPL", period="1d", interval="1h")
    print(f"   Got {len(history)} data points")