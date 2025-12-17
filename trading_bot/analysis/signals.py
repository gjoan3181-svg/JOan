"""
Generador de Señales
=====================
Genera señales de trading basadas en indicadores técnicos.
"""

import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from loguru import logger


class SignalType(Enum):
    """Tipo de señal de trading."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """Representa una señal de trading."""
    signal_type: SignalType
    strength: float  # 0.0 a 1.0
    price: float
    reason: str
    timestamp: pd.Timestamp
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def __str__(self):
        return f"{self.signal_type.value} @ {self.price:.2f} (strength: {self.strength:.2%}) - {self.reason}"


class SignalGenerator:
    """
    Genera señales de trading basadas en múltiples indicadores.
    
    Combina varios indicadores técnicos para generar señales más robustas.
    """
    
    def __init__(
        self,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        macd_threshold: float = 0,
        bb_threshold: float = 0.1,
        min_signal_strength: float = 0.5
    ):
        """
        Inicializa el generador de señales.
        
        Args:
            rsi_oversold: Nivel de sobreventa RSI
            rsi_overbought: Nivel de sobrecompra RSI
            macd_threshold: Umbral para señales MACD
            bb_threshold: Umbral para Bollinger Bands
            min_signal_strength: Fuerza mínima para emitir señal
        """
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_threshold = macd_threshold
        self.bb_threshold = bb_threshold
        self.min_signal_strength = min_signal_strength
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Genera una señal basada en el DataFrame con indicadores.
        
        Args:
            df: DataFrame con indicadores técnicos calculados
            
        Returns:
            Signal con la recomendación
        """
        if len(df) < 2:
            return Signal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                price=0.0,
                reason="Datos insuficientes",
                timestamp=pd.Timestamp.now()
            )
        
        # Obtener última fila
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        buy_signals = []
        sell_signals = []
        
        # 1. RSI Signal
        if 'rsi' in df.columns:
            if current['rsi'] < self.rsi_oversold:
                buy_signals.append(("RSI sobreventa", 0.3))
            elif current['rsi'] > self.rsi_overbought:
                sell_signals.append(("RSI sobrecompra", 0.3))
        
        # 2. MACD Signal (cruce)
        if all(col in df.columns for col in ['macd', 'macd_signal']):
            # Cruce alcista
            if previous['macd'] < previous['macd_signal'] and current['macd'] > current['macd_signal']:
                buy_signals.append(("MACD cruce alcista", 0.25))
            # Cruce bajista
            elif previous['macd'] > previous['macd_signal'] and current['macd'] < current['macd_signal']:
                sell_signals.append(("MACD cruce bajista", 0.25))
        
        # 3. Bollinger Bands
        if all(col in df.columns for col in ['bb_lower', 'bb_upper', 'close']):
            if current['close'] < current['bb_lower']:
                buy_signals.append(("Precio bajo BB inferior", 0.2))
            elif current['close'] > current['bb_upper']:
                sell_signals.append(("Precio sobre BB superior", 0.2))
        
        # 4. Media móvil crossover
        if all(col in df.columns for col in ['sma_10', 'sma_20']):
            if previous['sma_10'] < previous['sma_20'] and current['sma_10'] > current['sma_20']:
                buy_signals.append(("SMA 10/20 cruce alcista", 0.15))
            elif previous['sma_10'] > previous['sma_20'] and current['sma_10'] < current['sma_20']:
                sell_signals.append(("SMA 10/20 cruce bajista", 0.15))
        
        # 5. Stochastic
        if all(col in df.columns for col in ['stoch_k', 'stoch_d']):
            if current['stoch_k'] < 20 and current['stoch_k'] > current['stoch_d']:
                buy_signals.append(("Stochastic sobreventa + cruce", 0.1))
            elif current['stoch_k'] > 80 and current['stoch_k'] < current['stoch_d']:
                sell_signals.append(("Stochastic sobrecompra + cruce", 0.1))
        
        # Calcular fuerza total
        buy_strength = sum(s[1] for s in buy_signals)
        sell_strength = sum(s[1] for s in sell_signals)
        
        # Determinar señal final
        price = current['close']
        timestamp = current.get('timestamp', pd.Timestamp.now())
        
        # Calcular stop loss y take profit basados en ATR
        atr = current.get('atr', price * 0.02)  # Default 2% si no hay ATR
        
        if buy_strength > sell_strength and buy_strength >= self.min_signal_strength:
            reasons = ", ".join([s[0] for s in buy_signals])
            return Signal(
                signal_type=SignalType.BUY,
                strength=min(buy_strength, 1.0),
                price=price,
                reason=reasons,
                timestamp=timestamp,
                stop_loss=price - (atr * 2),
                take_profit=price + (atr * 3)
            )
        elif sell_strength > buy_strength and sell_strength >= self.min_signal_strength:
            reasons = ", ".join([s[0] for s in sell_signals])
            return Signal(
                signal_type=SignalType.SELL,
                strength=min(sell_strength, 1.0),
                price=price,
                reason=reasons,
                timestamp=timestamp,
                stop_loss=price + (atr * 2),
                take_profit=price - (atr * 3)
            )
        else:
            return Signal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                price=price,
                reason="Sin señal clara",
                timestamp=timestamp
            )
    
    def backtest_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera señales para todo el histórico (backtesting).
        
        Args:
            df: DataFrame con datos históricos e indicadores
            
        Returns:
            DataFrame con columna de señales añadida
        """
        df = df.copy()
        signals = []
        
        for i in range(1, len(df)):
            subset = df.iloc[:i+1]
            signal = self.generate_signal(subset)
            signals.append({
                'signal_type': signal.signal_type.value,
                'signal_strength': signal.strength,
                'signal_reason': signal.reason
            })
        
        # Primera fila sin señal
        signals.insert(0, {
            'signal_type': 'HOLD',
            'signal_strength': 0.0,
            'signal_reason': 'Primera vela'
        })
        
        signal_df = pd.DataFrame(signals)
        return pd.concat([df.reset_index(drop=True), signal_df], axis=1)
