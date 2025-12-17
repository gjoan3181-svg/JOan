"""
Módulo para obtener datos de diferentes mercados SIN necesidad de API keys.
Fuentes gratuitas: Yahoo Finance, CoinGecko, APIs públicas de exchanges.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Literal, List, Dict
import warnings
import time

warnings.filterwarnings('ignore')


class DataFetcher:
    """
    Clase para obtener datos de mercado de múltiples fuentes GRATUITAS.
    No requiere API keys.
    """
    
    def __init__(self):
        self.supported_markets = ['crypto', 'stock', 'forex']
        self._session = None
    
    def _get_session(self):
        """Crea una sesión de requests con retry."""
        if self._session is None:
            try:
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                
                self._session = requests.Session()
                retry = Retry(total=3, backoff_factor=0.5)
                adapter = HTTPAdapter(max_retries=retry)
                self._session.mount('http://', adapter)
                self._session.mount('https://', adapter)
            except ImportError:
                import requests
                self._session = requests.Session()
        return self._session
    
    # ==================== CRYPTO ====================
    
    def fetch_crypto_yahoo(
        self,
        symbol: str = 'BTC',
        period: str = '3mo',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Obtiene datos de crypto via Yahoo Finance (SIN API KEY).
        
        Args:
            symbol: Símbolo base (BTC, ETH, SOL, etc.)
            period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y'
            interval: '1m', '5m', '15m', '1h', '1d'
        
        Returns:
            DataFrame con OHLCV
        """
        try:
            import yfinance as yf
            
            # Convertir símbolo al formato de Yahoo
            if '/' in symbol:
                symbol = symbol.split('/')[0]
            
            yahoo_symbol = f"{symbol}-USD"
            
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"⚠️ Yahoo Finance: No hay datos para {yahoo_symbol}")
                return pd.DataFrame()
            
            df.columns = [c.lower() for c in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df['symbol'] = symbol
            df['source'] = 'yahoo'
            
            print(f"✅ Yahoo Finance: {len(df)} velas de {yahoo_symbol}")
            return df
            
        except Exception as e:
            print(f"⚠️ Yahoo Finance error: {e}")
            return pd.DataFrame()
    
    def fetch_crypto_coingecko(
        self,
        symbol: str = 'bitcoin',
        vs_currency: str = 'usd',
        days: int = 90
    ) -> pd.DataFrame:
        """
        Obtiene datos de crypto via CoinGecko (API PÚBLICA GRATUITA).
        
        Args:
            symbol: ID de CoinGecko (bitcoin, ethereum, solana, etc.)
            vs_currency: Moneda de cotización (usd, eur, etc.)
            days: Días de historia (max 365 para datos horarios)
        
        Returns:
            DataFrame con OHLCV
        """
        try:
            session = self._get_session()
            
            # Mapeo de símbolos comunes a IDs de CoinGecko
            symbol_map = {
                'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano',
                'DOGE': 'dogecoin', 'DOT': 'polkadot', 'MATIC': 'matic-network',
                'SHIB': 'shiba-inu', 'LTC': 'litecoin', 'AVAX': 'avalanche-2',
                'LINK': 'chainlink', 'UNI': 'uniswap', 'ATOM': 'cosmos',
                'XLM': 'stellar', 'ALGO': 'algorand', 'VET': 'vechain',
                'FTM': 'fantom', 'SAND': 'the-sandbox', 'MANA': 'decentraland',
                'AAVE': 'aave', 'AXS': 'axie-infinity', 'THETA': 'theta-token',
                'EOS': 'eos', 'XTZ': 'tezos', 'CAKE': 'pancakeswap-token',
                'NEO': 'neo', 'KCS': 'kucoin-shares', 'EGLD': 'elrond-erd-2',
                'PEPE': 'pepe', 'ARB': 'arbitrum', 'OP': 'optimism',
                'SUI': 'sui', 'APT': 'aptos', 'INJ': 'injective-protocol',
            }
            
            # Normalizar símbolo
            if '/' in symbol:
                symbol = symbol.split('/')[0]
            symbol = symbol.upper()
            
            coin_id = symbol_map.get(symbol, symbol.lower())
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': vs_currency,
                'days': days
            }
            
            response = session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                print("⚠️ CoinGecko: Rate limit alcanzado, esperando...")
                time.sleep(60)
                response = session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ CoinGecko error: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # CoinGecko OHLC no incluye volumen, lo simulamos
            df['volume'] = 0.0
            df['symbol'] = symbol
            df['source'] = 'coingecko'
            
            print(f"✅ CoinGecko: {len(df)} velas de {coin_id}")
            return df
            
        except Exception as e:
            print(f"⚠️ CoinGecko error: {e}")
            return pd.DataFrame()
    
    def fetch_crypto_binance_public(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1h',
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Obtiene datos de Binance API pública (SIN API KEY).
        Nota: Puede no funcionar en algunas regiones.
        
        Args:
            symbol: Par de trading (BTCUSDT, ETHUSDT, etc.)
            interval: '1m', '5m', '15m', '1h', '4h', '1d'
            limit: Cantidad de velas (max 1000)
        """
        try:
            session = self._get_session()
            
            # Normalizar símbolo
            if '/' in symbol:
                symbol = symbol.replace('/', '')
            symbol = symbol.upper()
            
            # Intentar Binance.US primero (más accesible)
            urls = [
                f"https://api.binance.us/api/v3/klines",
                f"https://api.binance.com/api/v3/klines",
            ]
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            for url in urls:
                try:
                    response = session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        break
                except:
                    continue
            else:
                return pd.DataFrame()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['symbol'] = symbol
            df['source'] = 'binance'
            
            print(f"✅ Binance: {len(df)} velas de {symbol}")
            return df
            
        except Exception as e:
            print(f"⚠️ Binance error: {e}")
            return pd.DataFrame()
    
    def fetch_crypto_kraken_public(
        self,
        symbol: str = 'XBTUSD',
        interval: int = 60,
        limit: int = 720
    ) -> pd.DataFrame:
        """
        Obtiene datos de Kraken API pública (SIN API KEY).
        
        Args:
            symbol: Par de trading (XBTUSD=BTC, ETHUSD, etc.)
            interval: Minutos (1, 5, 15, 30, 60, 240, 1440, 10080)
        """
        try:
            session = self._get_session()
            
            # Mapeo de símbolos
            symbol_map = {
                'BTC': 'XBTUSD', 'ETH': 'ETHUSD', 'SOL': 'SOLUSD',
                'XRP': 'XRPUSD', 'ADA': 'ADAUSD', 'DOT': 'DOTUSD',
                'DOGE': 'DOGEUSD', 'LTC': 'LTCUSD', 'LINK': 'LINKUSD',
                'AVAX': 'AVAXUSD', 'MATIC': 'MATICUSD', 'UNI': 'UNIUSD',
            }
            
            if '/' in symbol:
                symbol = symbol.split('/')[0]
            symbol = symbol.upper()
            
            kraken_symbol = symbol_map.get(symbol, f"{symbol}USD")
            
            url = "https://api.kraken.com/0/public/OHLC"
            params = {
                'pair': kraken_symbol,
                'interval': interval
            }
            
            response = session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('error'):
                print(f"⚠️ Kraken error: {data['error']}")
                return pd.DataFrame()
            
            # Obtener el nombre real del par de los resultados
            result_key = list(data['result'].keys())[0]
            if result_key == 'last':
                result_key = list(data['result'].keys())[1]
            
            ohlc_data = data['result'][result_key]
            
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['symbol'] = symbol
            df['source'] = 'kraken'
            
            # Limitar resultados
            df = df.tail(limit)
            
            print(f"✅ Kraken: {len(df)} velas de {kraken_symbol}")
            return df
            
        except Exception as e:
            print(f"⚠️ Kraken error: {e}")
            return pd.DataFrame()
    
    def fetch_crypto(
        self,
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Obtiene datos de crypto intentando múltiples fuentes.
        PRIORIDAD: Yahoo -> CoinGecko -> Kraken -> Binance -> Datos de ejemplo
        
        Args:
            symbol: Par de trading (BTC/USDT, ETH/USDT, etc.)
            timeframe: Intervalo ('1h', '4h', '1d')
            limit: Cantidad de velas deseadas
        """
        print(f"\n🔍 Buscando datos para {symbol}...")
        
        # Mapeo de timeframes a días para CoinGecko
        days_map = {'1h': 90, '4h': 180, '1d': 365, '1m': 1, '5m': 7, '15m': 30}
        days = days_map.get(timeframe, 90)
        
        # Mapeo de timeframes para Yahoo
        interval_map = {'1h': '1h', '4h': '1h', '1d': '1d', '1m': '1m', '5m': '5m', '15m': '15m'}
        yahoo_interval = interval_map.get(timeframe, '1h')
        
        # 1. Intentar Yahoo Finance primero (más confiable)
        df = self.fetch_crypto_yahoo(symbol, period='3mo', interval=yahoo_interval)
        if not df.empty and len(df) >= 100:
            return df.tail(limit)
        
        # 2. Intentar CoinGecko
        df = self.fetch_crypto_coingecko(symbol, days=days)
        if not df.empty and len(df) >= 50:
            return df.tail(limit)
        
        # 3. Intentar Kraken
        interval_minutes = {'1h': 60, '4h': 240, '1d': 1440}.get(timeframe, 60)
        df = self.fetch_crypto_kraken_public(symbol, interval=interval_minutes)
        if not df.empty and len(df) >= 100:
            return df.tail(limit)
        
        # 4. Intentar Binance (puede fallar por región)
        df = self.fetch_crypto_binance_public(symbol, interval=timeframe, limit=limit)
        if not df.empty:
            return df
        
        # 5. Si todo falla, generar datos de ejemplo
        print(f"⚠️ No se pudieron obtener datos reales para {symbol}")
        return self._generate_sample_data(symbol, limit)
    
    # ==================== STOCKS ====================
    
    def fetch_stock(
        self,
        symbol: str = 'AAPL',
        period: str = '3mo',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Obtiene datos de acciones via Yahoo Finance (SIN API KEY).
        Funciona con acciones regulares y OTC.
        
        Args:
            symbol: Ticker (AAPL, TSLA, MSFT, o OTC como TSNP)
            period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
            interval: '1m', '5m', '15m', '1h', '1d', '1wk', '1mo'
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"⚠️ No hay datos para {symbol}")
                return self._generate_sample_data(symbol, 500)
            
            df.columns = [c.lower() for c in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df['symbol'] = symbol
            df['source'] = 'yahoo'
            df['market_type'] = 'stock'
            
            print(f"✅ Yahoo Finance: {len(df)} velas de {symbol}")
            return df
            
        except ImportError:
            print("⚠️ yfinance no instalado. Usa: pip install yfinance")
            return self._generate_sample_data(symbol, 500)
        except Exception as e:
            print(f"⚠️ Error obteniendo {symbol}: {e}")
            return self._generate_sample_data(symbol, 500)
    
    # ==================== FOREX ====================
    
    def fetch_forex(
        self,
        symbol: str = 'EURUSD=X',
        period: str = '3mo',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Obtiene datos de Forex via Yahoo Finance (SIN API KEY).
        
        Args:
            symbol: Par forex (EURUSD=X, GBPUSD=X, USDJPY=X)
        """
        # Asegurar formato correcto
        if not symbol.endswith('=X') and not symbol.endswith('.FX'):
            symbol = f"{symbol}=X"
        
        df = self.fetch_stock(symbol, period, interval)
        df['market_type'] = 'forex'
        return df
    
    # ==================== MÉTODO UNIFICADO ====================
    
    def get_data(
        self,
        symbol: str,
        market_type: Literal['crypto', 'stock', 'forex'] = 'crypto',
        **kwargs
    ) -> pd.DataFrame:
        """
        Método unificado para obtener datos de cualquier mercado.
        NO REQUIERE API KEYS.
        
        Args:
            symbol: Símbolo del activo
            market_type: 'crypto', 'stock', 'forex'
            **kwargs: Argumentos adicionales
        
        Returns:
            DataFrame con datos OHLCV
        """
        if market_type == 'crypto':
            return self.fetch_crypto(symbol, **kwargs)
        elif market_type == 'stock':
            return self.fetch_stock(symbol, **kwargs)
        elif market_type == 'forex':
            return self.fetch_forex(symbol, **kwargs)
        else:
            raise ValueError(f"Tipo de mercado no soportado: {market_type}")
    
    # ==================== UTILIDADES ====================
    
    def _generate_sample_data(self, symbol: str, periods: int = 500) -> pd.DataFrame:
        """Genera datos de ejemplo realistas para demostración."""
        print(f"📊 Generando datos de ejemplo para {symbol}...")
        
        np.random.seed(hash(symbol) % 2**32)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
        
        # Simular precio con tendencia y volatilidad realista
        base_price = 100 if 'BTC' not in symbol.upper() else 45000
        returns = np.random.randn(periods) * 0.015
        trend = np.linspace(0, np.random.randn() * 0.3, periods)
        prices = base_price * np.exp(np.cumsum(returns) + trend)
        
        # Generar OHLCV
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(periods) * 0.003),
            'high': prices * (1 + np.abs(np.random.randn(periods) * 0.008)),
            'low': prices * (1 - np.abs(np.random.randn(periods) * 0.008)),
            'close': prices,
            'volume': np.random.randint(10000, 1000000, periods).astype(float)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        df['symbol'] = symbol
        df['source'] = 'sample'
        
        return df
    
    def get_available_cryptos(self) -> List[str]:
        """Retorna lista de criptomonedas disponibles."""
        return [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT',
            'MATIC', 'SHIB', 'LTC', 'AVAX', 'LINK', 'UNI', 'ATOM',
            'XLM', 'ALGO', 'VET', 'FTM', 'SAND', 'MANA', 'AAVE',
            'AXS', 'THETA', 'EOS', 'XTZ', 'CAKE', 'NEO', 'PEPE',
            'ARB', 'OP', 'SUI', 'APT', 'INJ'
        ]
    
    def search_crypto(self, query: str) -> List[Dict]:
        """
        Busca criptomonedas por nombre o símbolo.
        
        Args:
            query: Término de búsqueda
        
        Returns:
            Lista de coincidencias
        """
        try:
            session = self._get_session()
            url = f"https://api.coingecko.com/api/v3/search"
            params = {'query': query}
            
            response = session.get(url, params=params, timeout=10)
            data = response.json()
            
            coins = data.get('coins', [])[:10]
            return [{'id': c['id'], 'symbol': c['symbol'], 'name': c['name']} for c in coins]
            
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
