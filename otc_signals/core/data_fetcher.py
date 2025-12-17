"""
Módulo para obtener datos de diferentes mercados
Soporta: Crypto (via CCXT), Acciones/Forex (via yfinance)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Literal
import warnings

warnings.filterwarnings('ignore')


class DataFetcher:
    """Clase para obtener datos de mercado de múltiples fuentes."""
    
    def __init__(self):
        self.supported_markets = ['crypto', 'stock', 'forex']
        self._ccxt_exchange = None
    
    def _get_ccxt_exchange(self, exchange_name: str = 'binance'):
        """Inicializa el exchange de CCXT."""
        try:
            import ccxt
            exchange_class = getattr(ccxt, exchange_name)
            return exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
        except ImportError:
            print("⚠️ CCXT no instalado. Usa: pip install ccxt")
            return None
        except Exception as e:
            print(f"⚠️ Error inicializando exchange: {e}")
            return None
    
    def fetch_crypto(
        self,
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        limit: int = 500,
        exchange: str = 'binance'
    ) -> pd.DataFrame:
        """
        Obtiene datos de criptomonedas.
        
        Args:
            symbol: Par de trading (ej: 'BTC/USDT', 'ETH/USDT')
            timeframe: Intervalo ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Cantidad de velas a obtener
            exchange: Exchange a usar ('binance', 'coinbase', 'kraken')
        
        Returns:
            DataFrame con OHLCV
        """
        exchange_obj = self._get_ccxt_exchange(exchange)
        if exchange_obj is None:
            return self._generate_sample_data(symbol, limit)
        
        try:
            ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['symbol'] = symbol
            df['market_type'] = 'crypto'
            return df
        except Exception as e:
            print(f"⚠️ Error obteniendo datos crypto: {e}")
            return self._generate_sample_data(symbol, limit)
    
    def fetch_stock(
        self,
        symbol: str = 'AAPL',
        period: str = '3mo',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Obtiene datos de acciones (incluyendo OTC).
        
        Args:
            symbol: Ticker (ej: 'AAPL', 'TSLA', o OTC como 'TSNP')
            period: Periodo ('1d', '5d', '1mo', '3mo', '6mo', '1y')
            interval: Intervalo ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            DataFrame con OHLCV
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
            df['market_type'] = 'stock'
            return df
        except ImportError:
            print("⚠️ yfinance no instalado. Usa: pip install yfinance")
            return self._generate_sample_data(symbol, 500)
        except Exception as e:
            print(f"⚠️ Error obteniendo datos de {symbol}: {e}")
            return self._generate_sample_data(symbol, 500)
    
    def fetch_forex(
        self,
        symbol: str = 'EURUSD=X',
        period: str = '3mo',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Obtiene datos de Forex.
        
        Args:
            symbol: Par forex (ej: 'EURUSD=X', 'GBPUSD=X')
            period: Periodo de datos
            interval: Intervalo temporal
        
        Returns:
            DataFrame con OHLCV
        """
        df = self.fetch_stock(symbol, period, interval)
        df['market_type'] = 'forex'
        return df
    
    def _generate_sample_data(self, symbol: str, periods: int = 500) -> pd.DataFrame:
        """Genera datos de ejemplo para demostración."""
        print(f"📊 Generando datos de ejemplo para {symbol}...")
        
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1h')
        
        # Simular precio con tendencia y volatilidad realista
        base_price = 100
        returns = np.random.randn(periods) * 0.02  # 2% volatilidad
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generar OHLCV
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(periods) * 0.005),
            'high': prices * (1 + np.abs(np.random.randn(periods) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(periods) * 0.01)),
            'close': prices,
            'volume': np.random.randint(1000, 100000, periods).astype(float)
        }, index=dates)
        
        # Asegurar que high >= open, close y low <= open, close
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        df['symbol'] = symbol
        df['market_type'] = 'sample'
        
        return df
    
    def get_data(
        self,
        symbol: str,
        market_type: Literal['crypto', 'stock', 'forex'] = 'crypto',
        **kwargs
    ) -> pd.DataFrame:
        """
        Método unificado para obtener datos de cualquier mercado.
        
        Args:
            symbol: Símbolo del activo
            market_type: Tipo de mercado ('crypto', 'stock', 'forex')
            **kwargs: Argumentos adicionales específicos del mercado
        
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
