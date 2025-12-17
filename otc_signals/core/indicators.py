"""
Módulo de indicadores técnicos para análisis de mercado.
Incluye indicadores de tendencia, momentum, volatilidad y volumen.
"""

import pandas as pd
import numpy as np
from typing import Tuple


class TechnicalIndicators:
    """Clase para calcular indicadores técnicos."""
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index.
        
        Interpretación:
        - RSI > 70: Sobrecompra (posible venta)
        - RSI < 30: Sobreventa (posible compra)
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
        
        Returns:
            macd_line, signal_line, histogram
        
        Interpretación:
        - MACD cruza hacia arriba la señal: Compra
        - MACD cruza hacia abajo la señal: Venta
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
        Bollinger Bands.
        
        Returns:
            upper_band, middle_band, lower_band
        
        Interpretación:
        - Precio cerca de banda superior: Sobrecompra
        - Precio cerca de banda inferior: Sobreventa
        - Bandas estrechas: Baja volatilidad, posible ruptura
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
        Average True Range - Mide volatilidad.
        
        Útil para:
        - Determinar stop-loss dinámico
        - Evaluar volatilidad del mercado
        """
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
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
        Stochastic Oscillator.
        
        Returns:
            %K, %D
        
        Interpretación:
        - %K > 80: Sobrecompra
        - %K < 20: Sobreventa
        - %K cruza %D hacia arriba: Compra
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        
        return k, d
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume.
        
        Interpretación:
        - OBV subiendo con precio: Confirma tendencia alcista
        - OBV bajando con precio subiendo: Divergencia bajista
        """
        direction = np.where(close > close.shift(1), 1, 
                            np.where(close < close.shift(1), -1, 0))
        obv = (volume * direction).cumsum()
        return pd.Series(obv, index=close.index)
    
    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Volume Weighted Average Price.
        
        Interpretación:
        - Precio > VWAP: Tendencia alcista
        - Precio < VWAP: Tendencia bajista
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Average Directional Index - Mide fuerza de tendencia.
        
        Returns:
            ADX, +DI, -DI
        
        Interpretación:
        - ADX > 25: Tendencia fuerte
        - ADX < 20: Mercado sin tendencia (rango)
        - +DI > -DI: Tendencia alcista
        """
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def ichimoku(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> dict:
        """
        Ichimoku Cloud - Sistema completo de análisis.
        
        Returns:
            Dict con: tenkan, kijun, senkou_a, senkou_b, chikou
        
        Interpretación:
        - Precio sobre la nube: Alcista
        - Precio bajo la nube: Bajista
        - Tenkan cruza Kijun hacia arriba: Compra
        """
        # Tenkan-sen (Conversion Line): 9 periodos
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        
        # Kijun-sen (Base Line): 26 periodos
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        
        # Senkou Span A: Promedio de Tenkan y Kijun, desplazado 26 periodos
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        
        # Senkou Span B: 52 periodos, desplazado 26
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        
        # Chikou Span: Close desplazado 26 periodos hacia atrás
        chikou = close.shift(-26)
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }
    
    @classmethod
    def calculate_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula todos los indicadores y los añade al DataFrame.
        
        Args:
            df: DataFrame con columnas OHLCV
        
        Returns:
            DataFrame con indicadores añadidos
        """
        df = df.copy()
        
        # Moving Averages
        df['sma_20'] = cls.sma(df['close'], 20)
        df['sma_50'] = cls.sma(df['close'], 50)
        df['sma_200'] = cls.sma(df['close'], 200)
        df['ema_12'] = cls.ema(df['close'], 12)
        df['ema_26'] = cls.ema(df['close'], 26)
        
        # RSI
        df['rsi'] = cls.rsi(df['close'], 14)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = cls.macd(df['close'])
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = cls.bollinger_bands(df['close'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR
        df['atr'] = cls.atr(df['high'], df['low'], df['close'])
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = cls.stochastic(df['high'], df['low'], df['close'])
        
        # Volume indicators
        df['obv'] = cls.obv(df['close'], df['volume'])
        df['vwap'] = cls.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        # ADX
        df['adx'], df['plus_di'], df['minus_di'] = cls.adx(df['high'], df['low'], df['close'])
        
        # Volume MA
        df['volume_sma'] = cls.sma(df['volume'], 20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
