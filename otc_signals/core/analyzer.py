"""
Módulo de análisis de mercado y generación de reportes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketAnalysis:
    """Resultado del análisis de mercado."""
    symbol: str
    timestamp: datetime
    trend: str
    trend_strength: float
    volatility: str
    volatility_value: float
    support_levels: List[float]
    resistance_levels: List[float]
    key_insights: List[str]
    risk_score: float  # 1-10


class MarketAnalyzer:
    """Analiza condiciones de mercado y genera insights."""
    
    def __init__(self):
        pass
    
    def identify_trend(self, df: pd.DataFrame) -> tuple:
        """
        Identifica la tendencia actual del mercado.
        
        Returns:
            (trend_direction, trend_strength)
        """
        close = df['close']
        
        # Usar múltiples EMAs para determinar tendencia
        if 'ema_12' not in df.columns:
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            sma_50 = close.rolling(50).mean()
            sma_200 = close.rolling(200).mean()
        else:
            ema_12 = df['ema_12']
            ema_26 = df['ema_26']
            sma_50 = df['sma_50']
            sma_200 = df['sma_200']
        
        current_price = close.iloc[-1]
        
        # Contar señales alcistas/bajistas
        bullish_signals = 0
        bearish_signals = 0
        
        if current_price > ema_12.iloc[-1]:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if ema_12.iloc[-1] > ema_26.iloc[-1]:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if not pd.isna(sma_50.iloc[-1]) and not pd.isna(sma_200.iloc[-1]):
            if sma_50.iloc[-1] > sma_200.iloc[-1]:
                bullish_signals += 2  # Más peso
            else:
                bearish_signals += 2
        
        # Calcular pendiente de la tendencia
        if len(close) >= 20:
            slope = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20] * 100
        else:
            slope = 0
        
        total_signals = bullish_signals + bearish_signals
        if bullish_signals > bearish_signals:
            strength = bullish_signals / total_signals * 100
            if strength > 75:
                trend = "🟢 ALCISTA FUERTE"
            else:
                trend = "🔵 ALCISTA"
        elif bearish_signals > bullish_signals:
            strength = bearish_signals / total_signals * 100
            if strength > 75:
                trend = "🔴 BAJISTA FUERTE"
            else:
                trend = "🟠 BAJISTA"
        else:
            trend = "⚪ LATERAL"
            strength = 50
        
        return trend, strength
    
    def calculate_volatility(self, df: pd.DataFrame) -> tuple:
        """
        Calcula y clasifica la volatilidad del mercado.
        
        Returns:
            (volatility_class, volatility_value)
        """
        if 'atr' in df.columns:
            atr = df['atr'].iloc[-1]
        else:
            high, low, close = df['high'], df['low'], df['close']
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
        
        # ATR como porcentaje del precio
        atr_pct = (atr / df['close'].iloc[-1]) * 100
        
        # Comparar con volatilidad histórica
        returns = df['close'].pct_change().dropna()
        historical_vol = returns.std() * np.sqrt(252) * 100  # Anualizada
        
        if atr_pct < 1:
            vol_class = "🟢 BAJA"
        elif atr_pct < 3:
            vol_class = "🟡 MODERADA"
        elif atr_pct < 5:
            vol_class = "🟠 ALTA"
        else:
            vol_class = "🔴 MUY ALTA"
        
        return vol_class, atr_pct
    
    def find_support_resistance(self, df: pd.DataFrame, num_levels: int = 3) -> tuple:
        """
        Identifica niveles de soporte y resistencia.
        
        Returns:
            (support_levels, resistance_levels)
        """
        close = df['close']
        high = df['high']
        low = df['low']
        current_price = close.iloc[-1]
        
        # Método: Usar pivotes locales
        window = 10
        
        # Encontrar máximos locales (resistencias)
        local_max = high.rolling(window, center=True).max()
        potential_resistance = high[high == local_max].unique()
        resistance = sorted([r for r in potential_resistance if r > current_price])[:num_levels]
        
        # Encontrar mínimos locales (soportes)
        local_min = low.rolling(window, center=True).min()
        potential_support = low[low == local_min].unique()
        support = sorted([s for s in potential_support if s < current_price], reverse=True)[:num_levels]
        
        # Añadir niveles de Bollinger si están disponibles
        if 'bb_lower' in df.columns and 'bb_upper' in df.columns:
            bb_lower = df['bb_lower'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            
            if bb_lower < current_price and bb_lower not in support:
                support.append(bb_lower)
            if bb_upper > current_price and bb_upper not in resistance:
                resistance.append(bb_upper)
        
        return sorted(support, reverse=True)[:num_levels], sorted(resistance)[:num_levels]
    
    def generate_insights(self, df: pd.DataFrame) -> List[str]:
        """Genera insights basados en el análisis técnico."""
        insights = []
        
        close = df['close'].iloc[-1]
        
        # RSI insights
        if 'rsi' in df.columns:
            rsi = df['rsi'].iloc[-1]
            if rsi < 30:
                insights.append(f"📉 RSI en sobreventa ({rsi:.1f}) - Posible rebote")
            elif rsi > 70:
                insights.append(f"📈 RSI en sobrecompra ({rsi:.1f}) - Posible corrección")
            elif 45 <= rsi <= 55:
                insights.append(f"⚖️ RSI neutral ({rsi:.1f}) - Sin señal clara")
        
        # Bollinger Bands insights
        if 'bb_width' in df.columns:
            bb_width = df['bb_width'].iloc[-1]
            bb_width_mean = df['bb_width'].mean()
            
            if bb_width < bb_width_mean * 0.5:
                insights.append("🔄 Bandas de Bollinger muy estrechas - Posible ruptura inminente")
        
        # Volume insights
        if 'volume_ratio' in df.columns:
            vol_ratio = df['volume_ratio'].iloc[-1]
            if vol_ratio > 2:
                insights.append(f"📊 Volumen inusualmente alto ({vol_ratio:.1f}x promedio)")
            elif vol_ratio < 0.5:
                insights.append(f"📊 Volumen muy bajo ({vol_ratio:.1f}x promedio) - Poca convicción")
        
        # MACD insights
        if 'macd_hist' in df.columns:
            hist = df['macd_hist'].iloc[-1]
            hist_prev = df['macd_hist'].iloc[-2]
            
            if hist > 0 and hist > hist_prev:
                insights.append("📈 MACD: Momentum alcista creciendo")
            elif hist < 0 and hist < hist_prev:
                insights.append("📉 MACD: Momentum bajista creciendo")
        
        # ADX insights
        if 'adx' in df.columns:
            adx = df['adx'].iloc[-1]
            if adx > 40:
                insights.append(f"💪 Tendencia muy fuerte (ADX: {adx:.1f})")
            elif adx < 20:
                insights.append(f"😴 Mercado sin tendencia clara (ADX: {adx:.1f}) - Mejor para range trading")
        
        # Price vs VWAP
        if 'vwap' in df.columns:
            vwap = df['vwap'].iloc[-1]
            if close > vwap * 1.02:
                insights.append("💹 Precio significativamente sobre VWAP - Posible sobreextensión")
            elif close < vwap * 0.98:
                insights.append("💹 Precio significativamente bajo VWAP - Posible oportunidad")
        
        return insights
    
    def calculate_risk_score(self, df: pd.DataFrame) -> float:
        """
        Calcula un score de riesgo del 1 al 10.
        Mayor = más riesgoso.
        """
        risk_factors = []
        
        # Factor: Volatilidad
        _, vol_pct = self.calculate_volatility(df)
        risk_factors.append(min(vol_pct / 0.5, 10))  # Normalizar
        
        # Factor: ADX bajo (mercado errático)
        if 'adx' in df.columns:
            adx = df['adx'].iloc[-1]
            if adx < 20:
                risk_factors.append(7)  # Alto riesgo en mercado sin tendencia
            elif adx > 40:
                risk_factors.append(3)  # Menor riesgo con tendencia clara
            else:
                risk_factors.append(5)
        
        # Factor: Posición en Bollinger
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            close = df['close'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            bb_position = (close - bb_lower) / (bb_upper - bb_lower)
            
            # Riesgo alto en extremos
            if bb_position > 0.9 or bb_position < 0.1:
                risk_factors.append(8)
            else:
                risk_factors.append(4)
        
        # Factor: Volumen
        if 'volume_ratio' in df.columns:
            vol_ratio = df['volume_ratio'].iloc[-1]
            if vol_ratio < 0.5:
                risk_factors.append(7)  # Bajo volumen = mayor riesgo
            else:
                risk_factors.append(3)
        
        return np.mean(risk_factors) if risk_factors else 5.0
    
    def analyze(self, df: pd.DataFrame, symbol: str = "ASSET") -> MarketAnalysis:
        """
        Realiza un análisis completo del mercado.
        
        Args:
            df: DataFrame con datos e indicadores
            symbol: Símbolo del activo
        
        Returns:
            MarketAnalysis con el análisis completo
        """
        trend, trend_strength = self.identify_trend(df)
        vol_class, vol_value = self.calculate_volatility(df)
        support, resistance = self.find_support_resistance(df)
        insights = self.generate_insights(df)
        risk = self.calculate_risk_score(df)
        
        return MarketAnalysis(
            symbol=symbol,
            timestamp=datetime.now(),
            trend=trend,
            trend_strength=trend_strength,
            volatility=vol_class,
            volatility_value=vol_value,
            support_levels=support,
            resistance_levels=resistance,
            key_insights=insights,
            risk_score=risk
        )
