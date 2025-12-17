"""
Sistema de generación de señales de trading.
Combina múltiples indicadores para generar señales de compra/venta.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    STRONG_BUY = "🟢 COMPRA FUERTE"
    BUY = "🔵 COMPRA"
    NEUTRAL = "⚪ NEUTRAL"
    SELL = "🟠 VENTA"
    STRONG_SELL = "🔴 VENTA FUERTE"


@dataclass
class Signal:
    """Representa una señal de trading."""
    type: SignalType
    strength: float  # 0-100
    price: float
    timestamp: pd.Timestamp
    reasons: List[str]
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class SignalGenerator:
    """Generador de señales de trading basado en múltiples indicadores."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el generador de señales.
        
        Args:
            config: Configuración personalizada de umbrales
        """
        self.config = config or self._default_config()
    
    def _default_config(self) -> Dict:
        """Configuración por defecto de los indicadores."""
        return {
            'rsi': {
                'oversold': 30,
                'overbought': 70,
                'weight': 15
            },
            'macd': {
                'weight': 20
            },
            'bollinger': {
                'weight': 15
            },
            'stochastic': {
                'oversold': 20,
                'overbought': 80,
                'weight': 10
            },
            'ma_cross': {
                'weight': 20
            },
            'adx': {
                'trend_threshold': 25,
                'weight': 10
            },
            'volume': {
                'surge_threshold': 1.5,
                'weight': 10
            }
        }
    
    def _check_rsi(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa señal basada en RSI."""
        rsi = df['rsi'].iloc[-1]
        config = self.config['rsi']
        
        if pd.isna(rsi):
            return 0, ""
        
        if rsi < config['oversold']:
            score = config['weight'] * (1 - rsi / config['oversold'])
            return score, f"RSI en sobreventa ({rsi:.1f})"
        elif rsi > config['overbought']:
            score = -config['weight'] * ((rsi - config['overbought']) / (100 - config['overbought']))
            return score, f"RSI en sobrecompra ({rsi:.1f})"
        
        return 0, ""
    
    def _check_macd(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa señal basada en MACD."""
        macd = df['macd'].iloc[-1]
        signal = df['macd_signal'].iloc[-1]
        macd_prev = df['macd'].iloc[-2]
        signal_prev = df['macd_signal'].iloc[-2]
        hist = df['macd_hist'].iloc[-1]
        
        config = self.config['macd']
        
        if pd.isna(macd) or pd.isna(signal):
            return 0, ""
        
        # Cruce alcista
        if macd_prev < signal_prev and macd > signal:
            return config['weight'], "MACD cruce alcista ↗"
        # Cruce bajista
        elif macd_prev > signal_prev and macd < signal:
            return -config['weight'], "MACD cruce bajista ↘"
        # Histograma creciente
        elif hist > 0 and hist > df['macd_hist'].iloc[-2]:
            return config['weight'] * 0.5, "MACD histograma creciente"
        elif hist < 0 and hist < df['macd_hist'].iloc[-2]:
            return -config['weight'] * 0.5, "MACD histograma decreciente"
        
        return 0, ""
    
    def _check_bollinger(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa señal basada en Bollinger Bands."""
        close = df['close'].iloc[-1]
        upper = df['bb_upper'].iloc[-1]
        lower = df['bb_lower'].iloc[-1]
        middle = df['bb_middle'].iloc[-1]
        
        config = self.config['bollinger']
        
        if pd.isna(upper) or pd.isna(lower):
            return 0, ""
        
        bb_position = (close - lower) / (upper - lower)
        
        if close <= lower:
            return config['weight'], f"Precio en banda inferior de Bollinger"
        elif close >= upper:
            return -config['weight'], f"Precio en banda superior de Bollinger"
        elif bb_position < 0.2:
            return config['weight'] * 0.6, "Precio cerca de banda inferior"
        elif bb_position > 0.8:
            return -config['weight'] * 0.6, "Precio cerca de banda superior"
        
        return 0, ""
    
    def _check_stochastic(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa señal basada en Stochastic."""
        k = df['stoch_k'].iloc[-1]
        d = df['stoch_d'].iloc[-1]
        k_prev = df['stoch_k'].iloc[-2]
        d_prev = df['stoch_d'].iloc[-2]
        
        config = self.config['stochastic']
        
        if pd.isna(k) or pd.isna(d):
            return 0, ""
        
        # Cruce en zona de sobreventa
        if k < config['oversold'] and k_prev < d_prev and k > d:
            return config['weight'], f"Stochastic cruce alcista en sobreventa"
        # Cruce en zona de sobrecompra
        elif k > config['overbought'] and k_prev > d_prev and k < d:
            return -config['weight'], f"Stochastic cruce bajista en sobrecompra"
        elif k < config['oversold']:
            return config['weight'] * 0.5, f"Stochastic en sobreventa ({k:.1f})"
        elif k > config['overbought']:
            return -config['weight'] * 0.5, f"Stochastic en sobrecompra ({k:.1f})"
        
        return 0, ""
    
    def _check_ma_cross(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa señales de cruce de medias móviles."""
        ema12 = df['ema_12'].iloc[-1]
        ema26 = df['ema_26'].iloc[-1]
        sma50 = df['sma_50'].iloc[-1]
        sma200 = df['sma_200'].iloc[-1]
        close = df['close'].iloc[-1]
        
        config = self.config['ma_cross']
        score = 0
        reasons = []
        
        if pd.isna(ema12) or pd.isna(ema26):
            return 0, ""
        
        # Golden Cross / Death Cross (SMA 50 vs 200)
        if not pd.isna(sma50) and not pd.isna(sma200):
            sma50_prev = df['sma_50'].iloc[-2]
            sma200_prev = df['sma_200'].iloc[-2]
            
            if sma50_prev < sma200_prev and sma50 > sma200:
                score += config['weight']
                reasons.append("⭐ Golden Cross (SMA50 > SMA200)")
            elif sma50_prev > sma200_prev and sma50 < sma200:
                score -= config['weight']
                reasons.append("💀 Death Cross (SMA50 < SMA200)")
        
        # Precio sobre/bajo EMAs
        if close > ema12 > ema26:
            score += config['weight'] * 0.3
            reasons.append("Precio sobre EMAs alineadas")
        elif close < ema12 < ema26:
            score -= config['weight'] * 0.3
            reasons.append("Precio bajo EMAs alineadas")
        
        return score, " | ".join(reasons)
    
    def _check_adx(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa fuerza de tendencia con ADX."""
        adx = df['adx'].iloc[-1]
        plus_di = df['plus_di'].iloc[-1]
        minus_di = df['minus_di'].iloc[-1]
        
        config = self.config['adx']
        
        if pd.isna(adx):
            return 0, ""
        
        # ADX indica tendencia fuerte
        if adx > config['trend_threshold']:
            if plus_di > minus_di:
                return config['weight'], f"Tendencia alcista fuerte (ADX: {adx:.1f})"
            else:
                return -config['weight'], f"Tendencia bajista fuerte (ADX: {adx:.1f})"
        
        return 0, f"Mercado sin tendencia clara (ADX: {adx:.1f})"
    
    def _check_volume(self, df: pd.DataFrame) -> Tuple[float, str]:
        """Evalúa confirmación por volumen."""
        volume_ratio = df['volume_ratio'].iloc[-1]
        close = df['close'].iloc[-1]
        close_prev = df['close'].iloc[-2]
        
        config = self.config['volume']
        
        if pd.isna(volume_ratio):
            return 0, ""
        
        if volume_ratio > config['surge_threshold']:
            if close > close_prev:
                return config['weight'], f"Volumen alto con precio subiendo ({volume_ratio:.1f}x)"
            else:
                return -config['weight'], f"Volumen alto con precio bajando ({volume_ratio:.1f}x)"
        
        return 0, ""
    
    def _calculate_levels(self, df: pd.DataFrame, signal_type: SignalType) -> Tuple[float, float]:
        """Calcula niveles de Stop Loss y Take Profit basados en ATR."""
        close = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        if pd.isna(atr):
            atr = close * 0.02  # 2% por defecto
        
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            stop_loss = close - (atr * 2)
            take_profit = close + (atr * 3)
        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            stop_loss = close + (atr * 2)
            take_profit = close - (atr * 3)
        else:
            stop_loss = None
            take_profit = None
        
        return stop_loss, take_profit
    
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """
        Genera una señal de trading basada en el análisis de múltiples indicadores.
        
        Args:
            df: DataFrame con indicadores calculados
        
        Returns:
            Signal con la recomendación
        """
        if len(df) < 200:
            # Necesitamos suficientes datos para indicadores
            pass
        
        total_score = 0
        reasons = []
        
        # Evaluar cada indicador
        checks = [
            self._check_rsi,
            self._check_macd,
            self._check_bollinger,
            self._check_stochastic,
            self._check_ma_cross,
            self._check_adx,
            self._check_volume
        ]
        
        for check in checks:
            score, reason = check(df)
            total_score += score
            if reason:
                reasons.append(reason)
        
        # Normalizar score a -100 a 100
        max_possible = sum([c['weight'] for c in self.config.values()])
        normalized_score = (total_score / max_possible) * 100
        
        # Determinar tipo de señal
        if normalized_score >= 50:
            signal_type = SignalType.STRONG_BUY
        elif normalized_score >= 20:
            signal_type = SignalType.BUY
        elif normalized_score <= -50:
            signal_type = SignalType.STRONG_SELL
        elif normalized_score <= -20:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.NEUTRAL
        
        # Calcular niveles de SL/TP
        stop_loss, take_profit = self._calculate_levels(df, signal_type)
        
        return Signal(
            type=signal_type,
            strength=abs(normalized_score),
            price=df['close'].iloc[-1],
            timestamp=df.index[-1],
            reasons=reasons,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def scan_multiple(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Signal]:
        """
        Escanea múltiples activos y genera señales.
        
        Args:
            data_dict: Diccionario {symbol: DataFrame}
        
        Returns:
            Diccionario {symbol: Signal}
        """
        signals = {}
        for symbol, df in data_dict.items():
            try:
                signals[symbol] = self.generate_signal(df)
            except Exception as e:
                print(f"Error analizando {symbol}: {e}")
        
        return signals
