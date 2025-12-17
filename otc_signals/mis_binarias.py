#!/usr/bin/env python3
"""
🎯 MIS SEÑALES BINARIAS OTC v2.0
================================

MEJORADO: Ahora respeta la tendencia y evita señales contra-tendencia.

Regla #1: NO operar contra la tendencia fuerte
Regla #2: En tendencia bajista, solo PUT
Regla #3: En tendencia alcista, solo CALL
Regla #4: En lateral, buscar rebotes en extremos
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from core import DataFetcher, TechnicalIndicators


# ============= MIS ACTIVOS OTC =============
MIS_ACTIVOS = {
    # Crypto
    'ETH': {'yahoo': 'ETH-USD', 'nombre': 'ETH/USD (OTC)', 'tipo': 'crypto'},
    'BTC': {'yahoo': 'BTC-USD', 'nombre': 'BTC/USD (OTC)', 'tipo': 'crypto'},
    'SOL': {'yahoo': 'SOL-USD', 'nombre': 'SOL/USD (OTC)', 'tipo': 'crypto'},
    'TRUMP': {'yahoo': 'TRUMP-USD', 'coingecko': 'official-trump', 'nombre': 'TRUMP Coin (OTC)', 'tipo': 'crypto'},
    'MELANIA': {'yahoo': 'MELANIA-USD', 'coingecko': 'melania-meme', 'nombre': 'MELANIA Coin (OTC)', 'tipo': 'crypto'},
    
    # Forex
    'EURUSD': {'yahoo': 'EURUSD=X', 'nombre': 'EUR/USD (OTC)', 'tipo': 'forex'},
    'GBPUSD': {'yahoo': 'GBPUSD=X', 'nombre': 'GBP/USD (OTC)', 'tipo': 'forex'},
    'USDCHF': {'yahoo': 'CHF=X', 'nombre': 'USD/CHF (OTC)', 'tipo': 'forex'},
    'AUDCAD': {'yahoo': 'AUDCAD=X', 'nombre': 'AUD/CAD (OTC)', 'tipo': 'forex'},
    'EURJPY': {'yahoo': 'EURJPY=X', 'nombre': 'EUR/JPY (OTC)', 'tipo': 'forex'},
    
    # Commodities
    'UKO': {'yahoo': 'BZ=F', 'nombre': 'UK Oil (OTC)', 'tipo': 'commodity'},
    'GOLD': {'yahoo': 'GC=F', 'nombre': 'Gold (OTC)', 'tipo': 'commodity'},
}


class Direccion(Enum):
    CALL = "🟢 CALL ↑"
    PUT = "🔴 PUT ↓"
    ESPERAR = "⚪ ESPERAR"


@dataclass
class SenalBinaria:
    direccion: Direccion
    probabilidad: float
    fuerza: int
    expiracion: str
    razones: List[str]
    momento: str
    precio: float
    tendencia: str
    advertencia: str = ""


class AnalizadorOTC:
    """Analizador mejorado - RESPETA LA TENDENCIA."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def _obtener_datos(self, activo: str) -> pd.DataFrame:
        """Obtiene datos del activo."""
        config = MIS_ACTIVOS.get(activo.upper())
        
        if not config:
            return self.fetcher.fetch_crypto(activo, timeframe='1h', limit=200)
        
        yahoo_symbol = config.get('yahoo')
        
        try:
            import yfinance as yf
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period='5d', interval='1h')
            
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
                df = df[['open', 'high', 'low', 'close', 'volume']]
                return df
        except:
            pass
        
        if config.get('tipo') == 'crypto':
            return self.fetcher.fetch_crypto(activo, timeframe='1h', limit=200)
        
        return pd.DataFrame()
    
    def _analizar_tendencia(self, df: pd.DataFrame) -> Tuple[str, int]:
        """
        Analiza la tendencia de forma más precisa.
        
        Returns:
            (tendencia, fuerza_tendencia)
            tendencia: "ALCISTA", "BAJISTA", "LATERAL"
            fuerza: 0-100 (qué tan fuerte es la tendencia)
        """
        close = df['close']
        
        # 1. Pendiente de las últimas 10 velas
        ultimas_10 = close.tail(10).values
        pendiente_corta = (ultimas_10[-1] - ultimas_10[0]) / ultimas_10[0] * 100
        
        # 2. Pendiente de las últimas 20 velas
        ultimas_20 = close.tail(20).values
        pendiente_media = (ultimas_20[-1] - ultimas_20[0]) / ultimas_20[0] * 100
        
        # 3. Contar velas rojas vs verdes en últimas 10
        velas_verdes = 0
        velas_rojas = 0
        for i in range(-10, 0):
            if df['close'].iloc[i] > df['open'].iloc[i]:
                velas_verdes += 1
            else:
                velas_rojas += 1
        
        # 4. EMAs
        ema12 = df['ema_12'].iloc[-1] if 'ema_12' in df.columns else close.ewm(span=12).mean().iloc[-1]
        ema26 = df['ema_26'].iloc[-1] if 'ema_26' in df.columns else close.ewm(span=26).mean().iloc[-1]
        precio = close.iloc[-1]
        
        # 5. Calcular score de tendencia
        score_alcista = 0
        score_bajista = 0
        
        # Pendiente corta
        if pendiente_corta > 0.5:
            score_alcista += 30
        elif pendiente_corta < -0.5:
            score_bajista += 30
        
        # Pendiente media
        if pendiente_media > 0.3:
            score_alcista += 20
        elif pendiente_media < -0.3:
            score_bajista += 20
        
        # Velas
        if velas_verdes >= 7:
            score_alcista += 25
        elif velas_rojas >= 7:
            score_bajista += 25
        elif velas_verdes >= 6:
            score_alcista += 15
        elif velas_rojas >= 6:
            score_bajista += 15
        
        # Posición respecto a EMAs
        if precio > ema12 > ema26:
            score_alcista += 25
        elif precio < ema12 < ema26:
            score_bajista += 25
        elif precio > ema12:
            score_alcista += 10
        elif precio < ema12:
            score_bajista += 10
        
        # Determinar tendencia
        if score_alcista >= 50 and score_alcista > score_bajista + 20:
            return "ALCISTA FUERTE", score_alcista
        elif score_bajista >= 50 and score_bajista > score_alcista + 20:
            return "BAJISTA FUERTE", score_bajista
        elif score_alcista > score_bajista + 10:
            return "ALCISTA", score_alcista
        elif score_bajista > score_alcista + 10:
            return "BAJISTA", score_bajista
        else:
            return "LATERAL", max(score_alcista, score_bajista)
    
    def _detectar_patrones(self, df: pd.DataFrame) -> Tuple[str, str]:
        """Detecta patrones de velas."""
        if len(df) < 3:
            return None, None
        
        c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        
        body1 = c1['close'] - c1['open']
        body2 = c2['close'] - c2['open']
        body3 = c3['close'] - c3['open']
        
        size3 = abs(body3)
        avg_size = (abs(body1) + abs(body2) + size3) / 3
        
        lower_wick = min(c3['open'], c3['close']) - c3['low']
        upper_wick = c3['high'] - max(c3['open'], c3['close'])
        
        # Patrones CALL (reversión alcista)
        if lower_wick > size3 * 2.5 and upper_wick < size3 * 0.3 and body3 > 0:
            return "🔨 Martillo fuerte", "CALL"
        
        if body2 < 0 and body3 > 0 and abs(body3) > abs(body2) * 1.5:
            if c3['close'] > c2['open'] and c3['open'] < c2['close']:
                return "📈 Envolvente Alcista", "CALL"
        
        # Patrones PUT (reversión bajista)
        if upper_wick > size3 * 2.5 and lower_wick < size3 * 0.3 and body3 < 0:
            return "💫 Estrella Fugaz fuerte", "PUT"
        
        if body2 > 0 and body3 < 0 and abs(body3) > abs(body2) * 1.5:
            if c3['close'] < c2['open'] and c3['open'] > c2['close']:
                return "📉 Envolvente Bajista", "PUT"
        
        # Continuación de tendencia
        if body1 > 0 and body2 > 0 and body3 > 0:
            if c3['close'] > c2['close'] > c1['close']:
                return "💪 Continuación Alcista", "CALL"
        
        if body1 < 0 and body2 < 0 and body3 < 0:
            if c3['close'] < c2['close'] < c1['close']:
                return "📉 Continuación Bajista", "PUT"
        
        # Doji = indecisión
        if size3 < avg_size * 0.15:
            return "✚ Doji - Indecisión", "ESPERAR"
        
        return None, None
    
    def analizar(self, activo: str) -> SenalBinaria:
        """Analiza un activo respetando la tendencia."""
        
        config = MIS_ACTIVOS.get(activo.upper(), {})
        nombre = config.get('nombre', activo.upper())
        
        df = self._obtener_datos(activo)
        
        if df.empty or len(df) < 30:
            return SenalBinaria(
                direccion=Direccion.ESPERAR,
                probabilidad=0,
                fuerza=0,
                expiracion="N/A",
                razones=["Sin datos disponibles"],
                momento="❌ NO OPERAR",
                precio=0,
                tendencia="?",
                advertencia="No hay datos"
            )
        
        # Calcular indicadores
        df = TechnicalIndicators.calculate_all(df)
        
        close = df['close'].iloc[-1]
        
        # ===== PASO 1: ANALIZAR TENDENCIA (MÁS IMPORTANTE) =====
        tendencia, fuerza_tendencia = self._analizar_tendencia(df)
        
        razones = []
        advertencia = ""
        
        # ===== PASO 2: DETERMINAR DIRECCIÓN PERMITIDA =====
        if "BAJISTA FUERTE" in tendencia:
            # Solo permitir PUT
            direccion_permitida = "PUT"
            razones.append(f"📉 TENDENCIA {tendencia}")
            advertencia = "⚠️ Solo PUT - Tendencia bajista fuerte"
        elif "ALCISTA FUERTE" in tendencia:
            # Solo permitir CALL
            direccion_permitida = "CALL"
            razones.append(f"📈 TENDENCIA {tendencia}")
            advertencia = "⚠️ Solo CALL - Tendencia alcista fuerte"
        elif "BAJISTA" in tendencia:
            direccion_permitida = "PUT_PREFERIDO"
            razones.append(f"📉 Tendencia {tendencia}")
        elif "ALCISTA" in tendencia:
            direccion_permitida = "CALL_PREFERIDO"
            razones.append(f"📈 Tendencia {tendencia}")
        else:
            direccion_permitida = "AMBOS"
            razones.append("↔️ Mercado lateral")
        
        # ===== PASO 3: BUSCAR SEÑALES DE ENTRADA =====
        call_pts = 0
        put_pts = 0
        
        # Patrones de velas
        patron, patron_dir = self._detectar_patrones(df)
        if patron and patron_dir != "ESPERAR":
            if patron_dir == "CALL":
                call_pts += 20
            else:
                put_pts += 20
            razones.append(patron)
        
        # RSI - SOLO si va con la tendencia o en lateral
        rsi = df['rsi'].iloc[-1]
        if not pd.isna(rsi):
            if rsi < 30 and direccion_permitida in ["CALL", "CALL_PREFERIDO", "AMBOS"]:
                call_pts += 15
                razones.append(f"📊 RSI bajo ({rsi:.0f})")
            elif rsi > 70 and direccion_permitida in ["PUT", "PUT_PREFERIDO", "AMBOS"]:
                put_pts += 15
                razones.append(f"📊 RSI alto ({rsi:.0f})")
        
        # Stochastic
        k = df['stoch_k'].iloc[-1]
        d = df['stoch_d'].iloc[-1]
        k_prev = df['stoch_k'].iloc[-2]
        d_prev = df['stoch_d'].iloc[-2]
        
        if not pd.isna(k):
            if k < 20 and k_prev < d_prev and k > d:
                if direccion_permitida in ["CALL", "CALL_PREFERIDO", "AMBOS"]:
                    call_pts += 15
                    razones.append("📈 Stoch cruce alcista")
            elif k > 80 and k_prev > d_prev and k < d:
                if direccion_permitida in ["PUT", "PUT_PREFERIDO", "AMBOS"]:
                    put_pts += 15
                    razones.append("📉 Stoch cruce bajista")
        
        # Bollinger - Solo en mercado lateral o con la tendencia
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        
        if not pd.isna(bb_upper):
            if close <= bb_lower * 1.002 and direccion_permitida in ["CALL", "CALL_PREFERIDO", "AMBOS"]:
                call_pts += 12
                razones.append("📉 Tocando Bollinger inferior")
            elif close >= bb_upper * 0.998 and direccion_permitida in ["PUT", "PUT_PREFERIDO", "AMBOS"]:
                put_pts += 12
                razones.append("📈 Tocando Bollinger superior")
        
        # MACD
        hist = df['macd_hist'].iloc[-1]
        hist_prev = df['macd_hist'].iloc[-2]
        
        if not pd.isna(hist):
            if hist > 0 and hist_prev <= 0:
                call_pts += 10
                razones.append("📊 MACD cruce alcista")
            elif hist < 0 and hist_prev >= 0:
                put_pts += 10
                razones.append("📊 MACD cruce bajista")
        
        # Momentum últimas 3 velas
        mom = (close - df['close'].iloc[-4]) / df['close'].iloc[-4] * 100
        if mom > 0.2:
            call_pts += 10
        elif mom < -0.2:
            put_pts += 10
        
        # ===== PASO 4: APLICAR FILTRO DE TENDENCIA =====
        if direccion_permitida == "PUT":
            # Anular señales CALL en tendencia bajista fuerte
            call_pts = 0
            if put_pts < 10:
                # Dar puntos base por seguir tendencia
                put_pts += 15
                razones.append("↘️ A favor de tendencia")
        elif direccion_permitida == "CALL":
            # Anular señales PUT en tendencia alcista fuerte
            put_pts = 0
            if call_pts < 10:
                call_pts += 15
                razones.append("↗️ A favor de tendencia")
        elif direccion_permitida == "PUT_PREFERIDO":
            # Penalizar CALL ligeramente
            call_pts = int(call_pts * 0.6)
        elif direccion_permitida == "CALL_PREFERIDO":
            put_pts = int(put_pts * 0.6)
        
        # ===== PASO 5: CALCULAR RESULTADO =====
        diferencia = abs(call_pts - put_pts)
        
        if call_pts > put_pts and diferencia >= 12:
            direccion = Direccion.CALL
            prob = min(55 + diferencia * 1.2, 90)
        elif put_pts > call_pts and diferencia >= 12:
            direccion = Direccion.PUT
            prob = min(55 + diferencia * 1.2, 90)
        else:
            direccion = Direccion.ESPERAR
            prob = 50
            if not advertencia:
                advertencia = "⚠️ Señal débil - esperar"
        
        # Fuerza
        if diferencia >= 40:
            fuerza = 5
        elif diferencia >= 30:
            fuerza = 4
        elif diferencia >= 22:
            fuerza = 3
        elif diferencia >= 15:
            fuerza = 2
        else:
            fuerza = 1
        
        # Momento
        if fuerza >= 4 and len(razones) >= 3:
            momento = "🔥 ENTRAR AHORA"
        elif fuerza >= 3 and len(razones) >= 2:
            momento = "✅ BUENA ENTRADA"
        elif fuerza >= 2:
            momento = "⏳ ESPERAR CONFIRM."
        else:
            momento = "❌ NO OPERAR"
            direccion = Direccion.ESPERAR
        
        # Expiración
        if fuerza >= 4:
            exp = "1-3 min"
        elif fuerza >= 3:
            exp = "3-5 min"
        else:
            exp = "5+ min"
        
        return SenalBinaria(
            direccion=direccion,
            probabilidad=prob,
            fuerza=fuerza,
            expiracion=exp,
            razones=razones if razones else ["Sin señales claras"],
            momento=momento,
            precio=close,
            tendencia=tendencia,
            advertencia=advertencia
        )


def format_price(p):
    if p == 0: return "N/A"
    if p < 0.001: return f"${p:.8f}"
    if p < 1: return f"${p:.6f}"
    if p < 100: return f"${p:.4f}"
    return f"${p:,.2f}"


def mostrar_senal(activo: str, senal: SenalBinaria):
    """Muestra señal de forma clara."""
    
    config = MIS_ACTIVOS.get(activo.upper(), {})
    nombre = config.get('nombre', activo.upper())
    
    estrellas = "⭐" * senal.fuerza + "☆" * (5 - senal.fuerza)
    
    print(f"\n{'═'*55}")
    print(f"  🎯 {nombre}")
    print(f"  💰 Precio: {format_price(senal.precio)}")
    print(f"  📈 Tendencia: {senal.tendencia}")
    print(f"{'═'*55}")
    
    # Advertencia si hay
    if senal.advertencia:
        print(f"\n  {senal.advertencia}")
    
    # Señal principal
    if senal.direccion == Direccion.CALL:
        print(f"\n  ╔{'═'*51}╗")
        print(f"  ║{'🟢 CALL ↑ (SUBE)':^51}║")
        print(f"  ╚{'═'*51}╝")
    elif senal.direccion == Direccion.PUT:
        print(f"\n  ╔{'═'*51}╗")
        print(f"  ║{'🔴 PUT ↓ (BAJA)':^51}║")
        print(f"  ╚{'═'*51}╝")
    else:
        print(f"\n  ╔{'═'*51}╗")
        print(f"  ║{'⚪ ESPERAR - NO OPERAR':^51}║")
        print(f"  ╚{'═'*51}╝")
    
    print(f"\n  📊 Probabilidad: {senal.probabilidad:.0f}%")
    print(f"  💪 Fuerza:       {estrellas}")
    print(f"  ⏱️  Expiración:   {senal.expiracion}")
    print(f"  🚦 Momento:      {senal.momento}")
    
    print(f"\n  {'─'*50}")
    print(f"  📋 RAZONES:")
    for r in senal.razones[:6]:
        print(f"     • {r}")
    
    print(f"{'═'*55}")


def escanear_todos():
    """Escanea todos mis activos."""
    
    print("\n" + "🎯"*20)
    print("  ESCANEANDO MIS ACTIVOS OTC v2.0")
    print("  RESPETA TENDENCIA - Más conservador")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🎯"*20)
    
    analizador = AnalizadorOTC()
    resultados = []
    
    activos = ['BTC', 'ETH', 'SOL', 'TRUMP', 'MELANIA',
               'EURUSD', 'GBPUSD', 'USDCHF', 'AUDCAD', 'EURJPY', 'UKO']
    
    for activo in activos:
        config = MIS_ACTIVOS.get(activo, {})
        nombre = config.get('nombre', activo)
        
        print(f"\n  ⏳ {nombre}...", end=" ", flush=True)
        
        try:
            senal = analizador.analizar(activo)
            
            emoji = "🟢" if senal.direccion == Direccion.CALL else "🔴" if senal.direccion == Direccion.PUT else "⚪"
            trend_emoji = "📈" if "ALCISTA" in senal.tendencia else "📉" if "BAJISTA" in senal.tendencia else "↔️"
            print(f"{emoji} {'⭐'*senal.fuerza} {trend_emoji} {senal.tendencia}")
            
            resultados.append((activo, senal))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Filtrar señales fuertes
    fuertes = [(a, s) for a, s in resultados if s.fuerza >= 3 and s.direccion != Direccion.ESPERAR]
    
    if fuertes:
        print("\n" + "🔥"*20)
        print("  MEJORES SEÑALES AHORA")
        print("🔥"*20)
        
        fuertes.sort(key=lambda x: x[1].fuerza, reverse=True)
        
        for activo, senal in fuertes:
            mostrar_senal(activo, senal)
    else:
        print("\n" + "⚪"*20)
        print("  No hay señales fuertes ahora")
        print("  El mercado no tiene entradas claras")
        print("  Espera mejores condiciones")
        print("⚪"*20)
    
    return resultados


def menu():
    """Menú interactivo."""
    
    print("\n" + "🎯"*20)
    print("  MIS BINARIAS OTC v2.0")
    print("  RESPETA TENDENCIA")
    print("🎯"*20)
    
    print("\n📊 MIS ACTIVOS:")
    print("  CRYPTO: BTC, ETH, SOL, TRUMP, MELANIA")
    print("  FOREX:  EURUSD, GBPUSD, USDCHF, AUDCAD, EURJPY")
    print("  OTROS:  UKO (Petróleo)")
    
    print("\n⚠️  REGLAS v2.0:")
    print("  • Tendencia BAJISTA fuerte → Solo PUT")
    print("  • Tendencia ALCISTA fuerte → Solo CALL")
    print("  • No operar contra la tendencia")
    
    print("\n💡 COMANDOS: 'todos', 'salir', o un activo")
    
    analizador = AnalizadorOTC()
    
    while True:
        try:
            entrada = input("\n🔍 Activo: ").strip().upper()
            
            if entrada in ['SALIR', 'EXIT', 'Q']:
                print("\n👋 ¡Éxito en tus trades!")
                break
            
            if entrada in ['TODOS', 'ALL', 'SCAN', '']:
                escanear_todos()
                continue
            
            entrada = entrada.replace('/', '').replace('-', '').replace(' ', '')
            
            print(f"\n⏳ Analizando {entrada}...")
            senal = analizador.analizar(entrada)
            mostrar_senal(entrada, senal)
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ['--SCAN', 'TODOS', 'ALL']:
            escanear_todos()
        else:
            analizador = AnalizadorOTC()
            for a in sys.argv[1:]:
                if not a.startswith('--'):
                    a = a.upper().replace('/', '').replace('-', '')
                    print(f"\n⏳ Analizando {a}...")
                    senal = analizador.analizar(a)
                    mostrar_senal(a, senal)
    else:
        menu()


if __name__ == '__main__':
    main()
