#!/usr/bin/env python3
"""
🎯 SEÑALES PARA OPCIONES BINARIAS OTC
=====================================

Sistema de señales específico para trading de opciones binarias.
- Solo CALL (↑) o PUT (↓)
- Tiempo de expiración recomendado
- Probabilidad de éxito estimada
- Sin Stop Loss ni Take Profit (no aplica en binarias)

Uso:
    python3 binarias.py              # Menú interactivo
    python3 binarias.py BTC          # Analizar Bitcoin
    python3 binarias.py ETH 5        # ETH con expiración de 5 min
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from core import DataFetcher, TechnicalIndicators


class Direccion(Enum):
    CALL = "🟢 CALL ↑"
    PUT = "🔴 PUT ↓"
    ESPERAR = "⚪ ESPERAR"


@dataclass
class SenalBinaria:
    """Señal para opciones binarias."""
    direccion: Direccion
    probabilidad: float  # 0-100%
    fuerza: int  # 1-5 estrellas
    expiracion_recomendada: str  # "1m", "5m", "15m"
    razones: List[str]
    momento: str  # "AHORA", "ESPERAR VELA", "NO OPERAR"
    precio_entrada: float
    tendencia_general: str


class AnalizadorBinarias:
    """Analizador especializado para opciones binarias OTC."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def _detectar_patron_velas(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        Detecta patrones de velas japonesas.
        
        Returns:
            (patron_nombre, direccion_sugerida)
        """
        if len(df) < 3:
            return None, None
        
        # Últimas 3 velas
        c1 = df.iloc[-3]  # Antepenúltima
        c2 = df.iloc[-2]  # Penúltima
        c3 = df.iloc[-1]  # Actual
        
        # Calcular cuerpos de velas
        body1 = c1['close'] - c1['open']
        body2 = c2['close'] - c2['open']
        body3 = c3['close'] - c3['open']
        
        # Tamaño de cuerpos
        size1 = abs(body1)
        size2 = abs(body2)
        size3 = abs(body3)
        
        avg_size = (size1 + size2 + size3) / 3
        
        patrones = []
        
        # ===== PATRONES ALCISTAS (CALL) =====
        
        # Martillo (Hammer) - Cuerpo pequeño arriba, mecha larga abajo
        lower_wick = c3['open'] - c3['low'] if body3 > 0 else c3['close'] - c3['low']
        upper_wick = c3['high'] - c3['close'] if body3 > 0 else c3['high'] - c3['open']
        if lower_wick > size3 * 2 and upper_wick < size3 * 0.5 and body3 > 0:
            patrones.append(("🔨 Martillo", "CALL"))
        
        # Envolvente Alcista
        if body2 < 0 and body3 > 0 and c3['close'] > c2['open'] and c3['open'] < c2['close']:
            patrones.append(("📈 Envolvente Alcista", "CALL"))
        
        # Estrella de la Mañana
        if body1 < 0 and abs(body2) < avg_size * 0.3 and body3 > 0:
            if c3['close'] > (c1['open'] + c1['close']) / 2:
                patrones.append(("⭐ Estrella de la Mañana", "CALL"))
        
        # Tres Soldados Blancos
        if body1 > 0 and body2 > 0 and body3 > 0:
            if c2['close'] > c1['close'] and c3['close'] > c2['close']:
                patrones.append(("💪 Tres Soldados Blancos", "CALL"))
        
        # ===== PATRONES BAJISTAS (PUT) =====
        
        # Estrella Fugaz (Shooting Star)
        if upper_wick > size3 * 2 and lower_wick < size3 * 0.5 and body3 < 0:
            patrones.append(("💫 Estrella Fugaz", "PUT"))
        
        # Envolvente Bajista
        if body2 > 0 and body3 < 0 and c3['close'] < c2['open'] and c3['open'] > c2['close']:
            patrones.append(("📉 Envolvente Bajista", "PUT"))
        
        # Estrella de la Tarde
        if body1 > 0 and abs(body2) < avg_size * 0.3 and body3 < 0:
            if c3['close'] < (c1['open'] + c1['close']) / 2:
                patrones.append(("🌙 Estrella de la Tarde", "PUT"))
        
        # Tres Cuervos Negros
        if body1 < 0 and body2 < 0 and body3 < 0:
            if c2['close'] < c1['close'] and c3['close'] < c2['close']:
                patrones.append(("🐦 Tres Cuervos Negros", "PUT"))
        
        # Doji (indecisión)
        if size3 < avg_size * 0.1:
            patrones.append(("✚ Doji (Indecisión)", "ESPERAR"))
        
        if patrones:
            return patrones[0]  # Retornar el primer patrón encontrado
        
        return None, None
    
    def _analizar_momentum(self, df: pd.DataFrame) -> Tuple[str, float]:
        """
        Analiza el momentum de corto plazo.
        
        Returns:
            (direccion, fuerza)
        """
        close = df['close']
        
        # Momentum de las últimas 5 velas
        momentum_5 = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
        
        # Momentum de las últimas 3 velas
        momentum_3 = (close.iloc[-1] - close.iloc[-3]) / close.iloc[-3] * 100
        
        # Momentum de la última vela
        momentum_1 = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        
        # Promediar con más peso a las recientes
        momentum_total = momentum_1 * 0.5 + momentum_3 * 0.3 + momentum_5 * 0.2
        
        if momentum_total > 0.1:
            return "CALL", abs(momentum_total)
        elif momentum_total < -0.1:
            return "PUT", abs(momentum_total)
        else:
            return "NEUTRAL", 0
    
    def _evaluar_rsi_binarias(self, rsi: float) -> Tuple[str, int]:
        """
        Evalúa RSI para binarias (más sensible).
        
        Returns:
            (direccion, puntos)
        """
        if rsi < 20:
            return "CALL", 3  # Muy sobrevendido - fuerte señal de compra
        elif rsi < 30:
            return "CALL", 2
        elif rsi < 40:
            return "CALL", 1
        elif rsi > 80:
            return "PUT", 3  # Muy sobrecomprado - fuerte señal de venta
        elif rsi > 70:
            return "PUT", 2
        elif rsi > 60:
            return "PUT", 1
        else:
            return "NEUTRAL", 0
    
    def _evaluar_stochastic_binarias(self, k: float, d: float, k_prev: float, d_prev: float) -> Tuple[str, int]:
        """Evalúa Stochastic para binarias."""
        # Cruce en zona extrema
        if k < 20 and k_prev < d_prev and k > d:
            return "CALL", 3  # Cruce alcista en sobreventa
        elif k > 80 and k_prev > d_prev and k < d:
            return "PUT", 3  # Cruce bajista en sobrecompra
        elif k < 30:
            return "CALL", 1
        elif k > 70:
            return "PUT", 1
        else:
            return "NEUTRAL", 0
    
    def _evaluar_bollinger_binarias(self, close: float, bb_upper: float, bb_lower: float, bb_middle: float) -> Tuple[str, int]:
        """Evalúa Bollinger Bands para binarias."""
        if close <= bb_lower:
            return "CALL", 3  # Tocó banda inferior
        elif close >= bb_upper:
            return "PUT", 3  # Tocó banda superior
        elif close < bb_lower * 1.01:
            return "CALL", 2
        elif close > bb_upper * 0.99:
            return "PUT", 2
        elif close < bb_middle:
            return "CALL", 1
        else:
            return "PUT", 1
    
    def _evaluar_macd_binarias(self, macd: float, signal: float, hist: float, hist_prev: float) -> Tuple[str, int]:
        """Evalúa MACD para binarias."""
        # Cruce reciente
        if hist > 0 and hist_prev <= 0:
            return "CALL", 3  # Cruce alcista
        elif hist < 0 and hist_prev >= 0:
            return "PUT", 3  # Cruce bajista
        # Histograma creciendo/decreciendo
        elif hist > 0 and hist > hist_prev:
            return "CALL", 1
        elif hist < 0 and hist < hist_prev:
            return "PUT", 1
        else:
            return "NEUTRAL", 0
    
    def _determinar_expiracion(self, fuerza: int, volatilidad: float) -> str:
        """Determina tiempo de expiración recomendado."""
        if fuerza >= 4:
            if volatilidad > 2:
                return "1-2 min"
            else:
                return "3-5 min"
        elif fuerza >= 3:
            return "5 min"
        else:
            return "5-15 min"
    
    def analizar(self, symbol: str, timeframe: str = '1m') -> SenalBinaria:
        """
        Analiza un activo y genera señal para binarias.
        
        Args:
            symbol: Símbolo del activo
            timeframe: Timeframe ('1m', '5m', '15m')
        
        Returns:
            SenalBinaria con la recomendación
        """
        # Obtener datos
        df = self.fetcher.get_data(symbol, 'crypto', timeframe=timeframe, limit=200)
        
        if df.empty or len(df) < 50:
            return SenalBinaria(
                direccion=Direccion.ESPERAR,
                probabilidad=0,
                fuerza=0,
                expiracion_recomendada="N/A",
                razones=["No hay suficientes datos"],
                momento="NO OPERAR",
                precio_entrada=0,
                tendencia_general="Desconocida"
            )
        
        # Calcular indicadores
        df = TechnicalIndicators.calculate_all(df)
        
        # Scores
        call_score = 0
        put_score = 0
        razones = []
        
        # 1. Patrones de velas
        patron, patron_dir = self._detectar_patron_velas(df)
        if patron:
            if patron_dir == "CALL":
                call_score += 15
                razones.append(f"{patron}")
            elif patron_dir == "PUT":
                put_score += 15
                razones.append(f"{patron}")
            else:
                razones.append(f"{patron}")
        
        # 2. Momentum
        mom_dir, mom_fuerza = self._analizar_momentum(df)
        if mom_dir == "CALL":
            call_score += min(mom_fuerza * 5, 10)
            if mom_fuerza > 0.3:
                razones.append(f"📈 Momentum alcista ({mom_fuerza:.2f}%)")
        elif mom_dir == "PUT":
            put_score += min(mom_fuerza * 5, 10)
            if mom_fuerza > 0.3:
                razones.append(f"📉 Momentum bajista ({mom_fuerza:.2f}%)")
        
        # 3. RSI
        rsi = df['rsi'].iloc[-1]
        if not pd.isna(rsi):
            rsi_dir, rsi_pts = self._evaluar_rsi_binarias(rsi)
            if rsi_dir == "CALL":
                call_score += rsi_pts * 5
                if rsi_pts >= 2:
                    razones.append(f"📊 RSI sobrevendido ({rsi:.1f})")
            elif rsi_dir == "PUT":
                put_score += rsi_pts * 5
                if rsi_pts >= 2:
                    razones.append(f"📊 RSI sobrecomprado ({rsi:.1f})")
        
        # 4. Stochastic
        k = df['stoch_k'].iloc[-1]
        d = df['stoch_d'].iloc[-1]
        k_prev = df['stoch_k'].iloc[-2]
        d_prev = df['stoch_d'].iloc[-2]
        if not pd.isna(k):
            stoch_dir, stoch_pts = self._evaluar_stochastic_binarias(k, d, k_prev, d_prev)
            if stoch_dir == "CALL":
                call_score += stoch_pts * 5
                if stoch_pts >= 2:
                    razones.append(f"📈 Stochastic señal CALL ({k:.1f})")
            elif stoch_dir == "PUT":
                put_score += stoch_pts * 5
                if stoch_pts >= 2:
                    razones.append(f"📉 Stochastic señal PUT ({k:.1f})")
        
        # 5. Bollinger Bands
        close = df['close'].iloc[-1]
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        bb_middle = df['bb_middle'].iloc[-1]
        if not pd.isna(bb_upper):
            bb_dir, bb_pts = self._evaluar_bollinger_binarias(close, bb_upper, bb_lower, bb_middle)
            if bb_dir == "CALL":
                call_score += bb_pts * 4
                if bb_pts >= 2:
                    razones.append("📉 Precio en zona inferior de Bollinger")
            elif bb_dir == "PUT":
                put_score += bb_pts * 4
                if bb_pts >= 2:
                    razones.append("📈 Precio en zona superior de Bollinger")
        
        # 6. MACD
        macd = df['macd'].iloc[-1]
        signal = df['macd_signal'].iloc[-1]
        hist = df['macd_hist'].iloc[-1]
        hist_prev = df['macd_hist'].iloc[-2]
        if not pd.isna(macd):
            macd_dir, macd_pts = self._evaluar_macd_binarias(macd, signal, hist, hist_prev)
            if macd_dir == "CALL":
                call_score += macd_pts * 5
                if macd_pts >= 2:
                    razones.append("📊 MACD cruce alcista")
            elif macd_dir == "PUT":
                put_score += macd_pts * 5
                if macd_pts >= 2:
                    razones.append("📊 MACD cruce bajista")
        
        # 7. EMAs (tendencia)
        ema12 = df['ema_12'].iloc[-1]
        ema26 = df['ema_26'].iloc[-1]
        if close > ema12 > ema26:
            call_score += 5
            tendencia = "ALCISTA"
        elif close < ema12 < ema26:
            put_score += 5
            tendencia = "BAJISTA"
        else:
            tendencia = "LATERAL"
        
        # Calcular probabilidad y dirección
        total_score = call_score + put_score
        if total_score == 0:
            total_score = 1
        
        if call_score > put_score:
            direccion = Direccion.CALL
            probabilidad = (call_score / (call_score + put_score * 0.5)) * 100
            diferencia = call_score - put_score
        elif put_score > call_score:
            direccion = Direccion.PUT
            probabilidad = (put_score / (put_score + call_score * 0.5)) * 100
            diferencia = put_score - call_score
        else:
            direccion = Direccion.ESPERAR
            probabilidad = 50
            diferencia = 0
        
        # Limitar probabilidad entre 50-95%
        probabilidad = min(max(probabilidad, 50), 95)
        
        # Calcular fuerza (1-5 estrellas)
        if diferencia >= 30:
            fuerza = 5
        elif diferencia >= 20:
            fuerza = 4
        elif diferencia >= 15:
            fuerza = 3
        elif diferencia >= 10:
            fuerza = 2
        else:
            fuerza = 1
        
        # Determinar momento
        if fuerza >= 3 and len(razones) >= 2:
            momento = "🔥 AHORA"
        elif fuerza >= 2:
            momento = "⏳ ESPERAR CONFIRMACIÓN"
        else:
            momento = "❌ NO OPERAR"
        
        # Si la señal es muy débil, recomendar esperar
        if diferencia < 8:
            direccion = Direccion.ESPERAR
            momento = "❌ NO OPERAR"
            razones.append("⚠️ Señal muy débil - esperar mejor entrada")
        
        # Calcular volatilidad para expiración
        atr = df['atr'].iloc[-1]
        volatilidad = (atr / close) * 100 if close > 0 else 1
        
        expiracion = self._determinar_expiracion(fuerza, volatilidad)
        
        return SenalBinaria(
            direccion=direccion,
            probabilidad=probabilidad,
            fuerza=fuerza,
            expiracion_recomendada=expiracion,
            razones=razones if razones else ["Sin señales claras"],
            momento=momento,
            precio_entrada=close,
            tendencia_general=tendencia
        )


def format_price(precio):
    """Formatea el precio según su magnitud."""
    if precio is None or precio == 0:
        return "N/A"
    if precio < 0.0001:
        return f"${precio:.10f}"
    elif precio < 1:
        return f"${precio:.6f}"
    elif precio < 100:
        return f"${precio:.4f}"
    else:
        return f"${precio:,.2f}"


def mostrar_senal(symbol: str, senal: SenalBinaria):
    """Muestra la señal de forma visual."""
    
    estrellas = "⭐" * senal.fuerza + "☆" * (5 - senal.fuerza)
    
    print(f"\n{'='*60}")
    print(f"  🎯 SEÑAL BINARIAS OTC: {symbol.upper()}")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    print(f"\n  💰 Precio: {format_price(senal.precio_entrada)}")
    print(f"  📈 Tendencia: {senal.tendencia_general}")
    
    print(f"\n  {'─'*50}")
    
    # Señal principal
    if senal.direccion == Direccion.CALL:
        print(f"\n  ╔{'═'*48}╗")
        print(f"  ║  {senal.direccion.value:^44}  ║")
        print(f"  ╚{'═'*48}╝")
    elif senal.direccion == Direccion.PUT:
        print(f"\n  ╔{'═'*48}╗")
        print(f"  ║  {senal.direccion.value:^44}  ║")
        print(f"  ╚{'═'*48}╝")
    else:
        print(f"\n  ╔{'═'*48}╗")
        print(f"  ║  {senal.direccion.value:^44}  ║")
        print(f"  ╚{'═'*48}╝")
    
    print(f"\n  📊 Probabilidad: {senal.probabilidad:.0f}%")
    print(f"  💪 Fuerza: {estrellas}")
    print(f"  ⏱️  Expiración: {senal.expiracion_recomendada}")
    print(f"  🚦 Momento: {senal.momento}")
    
    print(f"\n  {'─'*50}")
    print(f"  📋 RAZONES:")
    for razon in senal.razones:
        print(f"     • {razon}")
    
    # Recomendación final
    print(f"\n  {'─'*50}")
    if senal.direccion != Direccion.ESPERAR and senal.fuerza >= 3:
        accion = "CALL (COMPRAR)" if senal.direccion == Direccion.CALL else "PUT (VENDER)"
        print(f"  ✅ RECOMENDACIÓN: {accion}")
        print(f"     Expiración: {senal.expiracion_recomendada}")
    elif senal.fuerza >= 2:
        print(f"  ⚠️  RECOMENDACIÓN: Esperar confirmación")
    else:
        print(f"  ❌ RECOMENDACIÓN: No operar - señal débil")
    
    print(f"\n{'='*60}\n")


def menu_interactivo():
    """Menú interactivo para opciones binarias."""
    
    print("\n" + "🎯"*25)
    print("  SEÑALES PARA OPCIONES BINARIAS OTC")
    print("  Sin API Keys - 100% Gratis")
    print("🎯"*25)
    
    print("\n📊 ACTIVOS POPULARES PARA BINARIAS:")
    print("   BTC, ETH, EUR/USD, GBP/USD, USD/JPY")
    print("   GOLD, SILVER, OIL, AAPL, GOOGL")
    
    print("\n⏱️  TIMEFRAMES: 1m, 5m, 15m")
    
    analizador = AnalizadorBinarias()
    
    while True:
        try:
            print("\n" + "-"*50)
            entrada = input("🔍 Símbolo a analizar (o 'salir'): ").strip().upper()
            
            if entrada.lower() in ['salir', 'exit', 'q', 'quit', 'SALIR']:
                print("\n👋 ¡Éxito en tus operaciones!")
                break
            
            if not entrada:
                continue
            
            # Analizar
            print(f"\n⏳ Analizando {entrada}...")
            senal = analizador.analizar(entrada, timeframe='1h')
            mostrar_senal(entrada, senal)
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def escanear_activos():
    """Escanea múltiples activos buscando señales fuertes."""
    
    print("\n🔍 ESCANEANDO ACTIVOS PARA BINARIAS...")
    print("="*60)
    
    activos = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'DOT', 'AVAX']
    
    analizador = AnalizadorBinarias()
    senales_fuertes = []
    
    for activo in activos:
        try:
            print(f"  Analizando {activo}...", end=" ")
            senal = analizador.analizar(activo, timeframe='1h')
            
            emoji = "🟢" if senal.direccion == Direccion.CALL else "🔴" if senal.direccion == Direccion.PUT else "⚪"
            print(f"{emoji} {senal.direccion.value} | Fuerza: {'⭐'*senal.fuerza}")
            
            if senal.fuerza >= 3 and senal.direccion != Direccion.ESPERAR:
                senales_fuertes.append((activo, senal))
                
        except Exception as e:
            print(f"❌ Error")
    
    if senales_fuertes:
        print("\n" + "🔥"*20)
        print("  SEÑALES FUERTES ENCONTRADAS")
        print("🔥"*20)
        
        for activo, senal in sorted(senales_fuertes, key=lambda x: x[1].fuerza, reverse=True):
            mostrar_senal(activo, senal)
    else:
        print("\n⚪ No hay señales fuertes en este momento")
        print("   Espera o analiza activos específicos")


def main():
    """Punto de entrada principal."""
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == '--scan':
            escanear_activos()
        else:
            analizador = AnalizadorBinarias()
            for simbolo in sys.argv[1:]:
                if simbolo.startswith('--'):
                    continue
                print(f"\n⏳ Analizando {simbolo.upper()}...")
                senal = analizador.analizar(simbolo.upper(), timeframe='1h')
                mostrar_senal(simbolo.upper(), senal)
    else:
        menu_interactivo()


if __name__ == '__main__':
    main()
