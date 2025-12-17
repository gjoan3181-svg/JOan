"""
Indicadores Técnicos
=====================
Calcula indicadores técnicos para análisis de mercado.
"""

import pandas as pd
import numpy as np
from typing import Tuple


class TechnicalIndicators:
    """
    Clase para calcular indicadores técnicos.
    
    Todos los métodos son estáticos y trabajan con DataFrames de pandas.
    """
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average (Media Móvil Simple).
        
        Args:
            series: Serie de precios
            period: Período de la media
        """
        return series.rolling(window=period).mean()
    
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average (Media Móvil Exponencial).
        
        Args:
            series: Serie de precios
            period: Período de la media
        """
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (Índice de Fuerza Relativa).
        
        Args:
            series: Serie de precios de cierre
            period: Período del RSI (default: 14)
            
        Returns:
            Serie con valores RSI (0-100)
        """
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(
        series: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence.
        
        Args:
            series: Serie de precios de cierre
            fast: Período EMA rápida (default: 12)
            slow: Período EMA lenta (default: 26)
            signal: Período de la línea de señal (default: 9)
            
        Returns:
            Tuple de (macd_line, signal_line, histogram)
        """
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        series: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bandas de Bollinger.
        
        Args:
            series: Serie de precios de cierre
            period: Período de la media móvil (default: 20)
            std_dev: Número de desviaciones estándar (default: 2)
            
        Returns:
            Tuple de (upper_band, middle_band, lower_band)
        """
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def atr(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Average True Range (Rango Verdadero Promedio).
        
        Args:
            high: Precios máximos
            low: Precios mínimos
            close: Precios de cierre
            period: Período del ATR (default: 14)
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def stochastic(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        k_period: int = 14, 
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator (Oscilador Estocástico).
        
        Args:
            high: Precios máximos
            low: Precios mínimos
            close: Precios de cierre
            k_period: Período %K (default: 14)
            d_period: Período %D (default: 3)
            
        Returns:
            Tuple de (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        return stoch_k, stoch_d
    
    @staticmethod
    def adx(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Average Directional Index.
        
        Args:
            high: Precios máximos
            low: Precios mínimos
            close: Precios de cierre
            period: Período del ADX (default: 14)
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr = TechnicalIndicators.atr(high, low, close, period)
        
        plus_di = 100 * (plus_dm.ewm(span=period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(span=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period).mean()
        
        return adx
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume.
        
        Args:
            close: Precios de cierre
            volume: Volumen
        """
        direction = np.sign(close.diff())
        return (volume * direction).cumsum()
    
    @staticmethod
    def vwap(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        volume: pd.Series
    ) -> pd.Series:
        """
        Volume Weighted Average Price.
        
        Args:
            high: Precios máximos
            low: Precios mínimos
            close: Precios de cierre
            volume: Volumen
        """
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Añade todos los indicadores técnicos al DataFrame.
        
        Args:
            df: DataFrame con columnas 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            DataFrame con todos los indicadores añadidos
        """
        df = df.copy()
        
        # Medias móviles
        df['sma_10'] = TechnicalIndicators.sma(df['close'], 10)
        df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        df['ema_10'] = TechnicalIndicators.ema(df['close'], 10)
        df['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
        
        # RSI
        df['rsi'] = TechnicalIndicators.rsi(df['close'])
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = TechnicalIndicators.macd(df['close'])
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = TechnicalIndicators.bollinger_bands(df['close'])
        
        # ATR
        df['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        
        # ADX
        df['adx'] = TechnicalIndicators.adx(df['high'], df['low'], df['close'])
        
        # OBV
        df['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
        
        # Características adicionales para ML
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Tendencia de precio
        df['price_momentum'] = df['close'] - df['close'].shift(10)
        df['price_acceleration'] = df['price_momentum'] - df['price_momentum'].shift(5)
        
        # Posición relativa
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
