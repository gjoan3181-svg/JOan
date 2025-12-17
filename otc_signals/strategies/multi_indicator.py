"""
Estrategia de trading basada en múltiples indicadores.
Diseñada para mercados OTC con mayor volatilidad.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class TradeSetup:
    """Configuración de una operación potencial."""
    position: PositionType
    entry_price: float
    stop_loss: float
    take_profit_1: float  # TP parcial
    take_profit_2: float  # TP final
    risk_reward: float
    confidence: float  # 0-100
    reasons: List[str]
    size_recommendation: str  # "pequeño", "medio", "grande"


class MultiIndicatorStrategy:
    """
    Estrategia que combina múltiples indicadores para generar
    setups de trading de alta probabilidad.
    
    Ideal para:
    - Mercados OTC con volatilidad
    - Criptomonedas
    - Forex
    """
    
    def __init__(self, risk_per_trade: float = 2.0):
        """
        Args:
            risk_per_trade: Porcentaje del capital a arriesgar por operación
        """
        self.risk_per_trade = risk_per_trade
        self.min_rr_ratio = 2.0  # Mínimo Risk/Reward
    
    def _check_trend_alignment(self, df: pd.DataFrame) -> Tuple[bool, str, int]:
        """
        Verifica alineación de tendencia en múltiples timeframes.
        
        Returns:
            (is_aligned, direction, score)
        """
        close = df['close'].iloc[-1]
        score = 0
        
        # EMA 12 vs 26
        if 'ema_12' in df.columns and 'ema_26' in df.columns:
            if df['ema_12'].iloc[-1] > df['ema_26'].iloc[-1]:
                score += 1
            else:
                score -= 1
        
        # SMA 50 vs 200
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            sma50 = df['sma_50'].iloc[-1]
            sma200 = df['sma_200'].iloc[-1]
            if not pd.isna(sma50) and not pd.isna(sma200):
                if sma50 > sma200:
                    score += 2
                else:
                    score -= 2
        
        # Precio vs EMAs
        if 'ema_12' in df.columns:
            if close > df['ema_12'].iloc[-1]:
                score += 1
            else:
                score -= 1
        
        # ADX para confirmar tendencia
        if 'adx' in df.columns:
            adx = df['adx'].iloc[-1]
            if adx > 25:
                if df['plus_di'].iloc[-1] > df['minus_di'].iloc[-1]:
                    score += 2
                else:
                    score -= 2
        
        direction = "ALCISTA" if score > 0 else "BAJISTA" if score < 0 else "LATERAL"
        is_aligned = abs(score) >= 3
        
        return is_aligned, direction, score
    
    def _find_entry_trigger(self, df: pd.DataFrame, direction: str) -> Tuple[bool, List[str]]:
        """
        Busca gatillos de entrada basados en la dirección.
        
        Returns:
            (trigger_found, reasons)
        """
        triggers = []
        
        # RSI en zonas extremas
        if 'rsi' in df.columns:
            rsi = df['rsi'].iloc[-1]
            if direction == "ALCISTA" and rsi < 40:
                triggers.append(f"RSI en zona de compra ({rsi:.1f})")
            elif direction == "BAJISTA" and rsi > 60:
                triggers.append(f"RSI en zona de venta ({rsi:.1f})")
        
        # Stochastic cruce
        if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
            k = df['stoch_k'].iloc[-1]
            d = df['stoch_d'].iloc[-1]
            k_prev = df['stoch_k'].iloc[-2]
            d_prev = df['stoch_d'].iloc[-2]
            
            if direction == "ALCISTA" and k_prev < d_prev and k > d and k < 50:
                triggers.append("Stochastic cruce alcista")
            elif direction == "BAJISTA" and k_prev > d_prev and k < d and k > 50:
                triggers.append("Stochastic cruce bajista")
        
        # MACD cruce
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            macd = df['macd'].iloc[-1]
            signal = df['macd_signal'].iloc[-1]
            macd_prev = df['macd'].iloc[-2]
            signal_prev = df['macd_signal'].iloc[-2]
            
            if direction == "ALCISTA" and macd_prev < signal_prev and macd > signal:
                triggers.append("MACD cruce alcista")
            elif direction == "BAJISTA" and macd_prev > signal_prev and macd < signal:
                triggers.append("MACD cruce bajista")
        
        # Precio tocando Bollinger
        if 'bb_lower' in df.columns and 'bb_upper' in df.columns:
            close = df['close'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            
            if direction == "ALCISTA" and close <= bb_lower * 1.01:
                triggers.append("Precio en banda inferior de Bollinger")
            elif direction == "BAJISTA" and close >= bb_upper * 0.99:
                triggers.append("Precio en banda superior de Bollinger")
        
        # Volumen confirmando
        if 'volume_ratio' in df.columns:
            vol_ratio = df['volume_ratio'].iloc[-1]
            if vol_ratio > 1.3:
                triggers.append(f"Volumen elevado ({vol_ratio:.1f}x)")
        
        return len(triggers) >= 2, triggers
    
    def _calculate_levels(self, df: pd.DataFrame, direction: str) -> Tuple[float, float, float, float]:
        """
        Calcula niveles de entrada, SL y TP.
        
        Returns:
            (entry, stop_loss, tp1, tp2)
        """
        close = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else close * 0.02
        
        if direction == "ALCISTA":
            entry = close
            stop_loss = close - (atr * 1.5)
            tp1 = close + (atr * 2)
            tp2 = close + (atr * 3.5)
        else:  # BAJISTA
            entry = close
            stop_loss = close + (atr * 1.5)
            tp1 = close - (atr * 2)
            tp2 = close - (atr * 3.5)
        
        return entry, stop_loss, tp1, tp2
    
    def _calculate_confidence(self, trend_score: int, triggers: List[str], df: pd.DataFrame) -> float:
        """Calcula nivel de confianza del setup."""
        confidence = 50  # Base
        
        # Bonus por alineación de tendencia
        confidence += abs(trend_score) * 5
        
        # Bonus por cantidad de triggers
        confidence += len(triggers) * 10
        
        # Bonus por volumen
        if 'volume_ratio' in df.columns:
            vol_ratio = df['volume_ratio'].iloc[-1]
            if vol_ratio > 1.5:
                confidence += 10
        
        # Bonus por ADX fuerte
        if 'adx' in df.columns:
            adx = df['adx'].iloc[-1]
            if adx > 30:
                confidence += 10
        
        return min(confidence, 100)
    
    def find_setup(self, df: pd.DataFrame) -> Optional[TradeSetup]:
        """
        Busca un setup de trading válido.
        
        Args:
            df: DataFrame con indicadores calculados
        
        Returns:
            TradeSetup si encuentra una oportunidad, None si no
        """
        # 1. Verificar alineación de tendencia
        is_aligned, direction, trend_score = self._check_trend_alignment(df)
        
        if direction == "LATERAL":
            return None
        
        # 2. Buscar gatillos de entrada
        has_trigger, triggers = self._find_entry_trigger(df, direction)
        
        if not has_trigger:
            return None
        
        # 3. Calcular niveles
        entry, sl, tp1, tp2 = self._calculate_levels(df, direction)
        
        # 4. Calcular Risk/Reward
        risk = abs(entry - sl)
        reward = abs(tp2 - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        if rr_ratio < self.min_rr_ratio:
            return None
        
        # 5. Calcular confianza
        confidence = self._calculate_confidence(trend_score, triggers, df)
        
        # 6. Determinar tamaño de posición
        if confidence >= 80:
            size = "grande"
        elif confidence >= 60:
            size = "medio"
        else:
            size = "pequeño"
        
        position_type = PositionType.LONG if direction == "ALCISTA" else PositionType.SHORT
        
        return TradeSetup(
            position=position_type,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward=rr_ratio,
            confidence=confidence,
            reasons=triggers + [f"Tendencia {direction} (score: {trend_score})"],
            size_recommendation=size
        )
    
    def backtest_simple(self, df: pd.DataFrame, initial_capital: float = 10000) -> Dict:
        """
        Realiza un backtest simple de la estrategia.
        
        Args:
            df: DataFrame con datos históricos e indicadores
            initial_capital: Capital inicial
        
        Returns:
            Diccionario con métricas del backtest
        """
        capital = initial_capital
        trades = []
        position = None
        
        for i in range(200, len(df)):
            window = df.iloc[:i+1]
            
            if position is None:
                setup = self.find_setup(window)
                if setup:
                    position = {
                        'type': setup.position,
                        'entry': setup.entry_price,
                        'sl': setup.stop_loss,
                        'tp': setup.take_profit_2,
                        'entry_idx': i
                    }
            else:
                current_price = df['close'].iloc[i]
                
                # Check stop loss
                if position['type'] == PositionType.LONG:
                    if current_price <= position['sl']:
                        pnl = (position['sl'] - position['entry']) / position['entry']
                        capital *= (1 + pnl * 0.1)  # 10% del capital en cada trade
                        trades.append({'pnl': pnl, 'result': 'loss'})
                        position = None
                    elif current_price >= position['tp']:
                        pnl = (position['tp'] - position['entry']) / position['entry']
                        capital *= (1 + pnl * 0.1)
                        trades.append({'pnl': pnl, 'result': 'win'})
                        position = None
                else:  # SHORT
                    if current_price >= position['sl']:
                        pnl = (position['entry'] - position['sl']) / position['entry']
                        capital *= (1 + pnl * 0.1)
                        trades.append({'pnl': pnl, 'result': 'loss'})
                        position = None
                    elif current_price <= position['tp']:
                        pnl = (position['entry'] - position['tp']) / position['entry']
                        capital *= (1 + pnl * 0.1)
                        trades.append({'pnl': pnl, 'result': 'win'})
                        position = None
        
        wins = len([t for t in trades if t['result'] == 'win'])
        losses = len([t for t in trades if t['result'] == 'loss'])
        
        return {
            'total_trades': len(trades),
            'wins': wins,
            'losses': losses,
            'win_rate': wins / len(trades) * 100 if trades else 0,
            'final_capital': capital,
            'return_pct': (capital - initial_capital) / initial_capital * 100,
            'trades': trades
        }
