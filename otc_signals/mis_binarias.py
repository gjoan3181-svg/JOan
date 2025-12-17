#!/usr/bin/env python3
"""
🎯 MIS SEÑALES BINARIAS OTC
===========================

Configurado para los activos de tu plataforma:
- Crypto: ETH, BTC, SOL, TRUMP, MELANIA
- Forex: EUR/USD, GBP/USD, USD/CHF, AUD/CAD, EUR/JPY
- Commodities: UKO (Petróleo)

Uso:
    python3 mis_binarias.py           # Escanear todos mis activos
    python3 mis_binarias.py ETH       # Analizar ETH
    python3 mis_binarias.py EURUSD    # Analizar EUR/USD
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


class AnalizadorOTC:
    """Analizador para mis activos OTC específicos."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def _obtener_datos(self, activo: str) -> pd.DataFrame:
        """Obtiene datos del activo."""
        config = MIS_ACTIVOS.get(activo.upper())
        
        if not config:
            # Intentar como símbolo directo
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
        
        # Fallback para crypto
        if config.get('tipo') == 'crypto':
            return self.fetcher.fetch_crypto(activo, timeframe='1h', limit=200)
        
        return pd.DataFrame()
    
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
        
        # Patrones CALL
        if lower_wick > size3 * 2 and upper_wick < size3 * 0.5 and body3 > 0:
            return "🔨 Martillo", "CALL"
        
        if body2 < 0 and body3 > 0 and c3['close'] > c2['open'] and c3['open'] < c2['close']:
            return "📈 Envolvente Alcista", "CALL"
        
        if body1 > 0 and body2 > 0 and body3 > 0 and c3['close'] > c2['close'] > c1['close']:
            return "💪 3 Soldados Blancos", "CALL"
        
        # Patrones PUT
        if upper_wick > size3 * 2 and lower_wick < size3 * 0.5 and body3 < 0:
            return "💫 Estrella Fugaz", "PUT"
        
        if body2 > 0 and body3 < 0 and c3['close'] < c2['open'] and c3['open'] > c2['close']:
            return "📉 Envolvente Bajista", "PUT"
        
        if body1 < 0 and body2 < 0 and body3 < 0 and c3['close'] < c2['close'] < c1['close']:
            return "🐦 3 Cuervos Negros", "PUT"
        
        # Doji
        if size3 < avg_size * 0.1:
            return "✚ Doji", "ESPERAR"
        
        return None, None
    
    def analizar(self, activo: str) -> SenalBinaria:
        """Analiza un activo y genera señal."""
        
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
                tendencia="?"
            )
        
        # Calcular indicadores
        df = TechnicalIndicators.calculate_all(df)
        
        call_pts = 0
        put_pts = 0
        razones = []
        
        close = df['close'].iloc[-1]
        
        # 1. Patrones de velas (peso alto)
        patron, patron_dir = self._detectar_patrones(df)
        if patron:
            if patron_dir == "CALL":
                call_pts += 20
                razones.append(patron)
            elif patron_dir == "PUT":
                put_pts += 20
                razones.append(patron)
        
        # 2. RSI
        rsi = df['rsi'].iloc[-1]
        if not pd.isna(rsi):
            if rsi < 25:
                call_pts += 15
                razones.append(f"📊 RSI muy bajo ({rsi:.0f})")
            elif rsi < 35:
                call_pts += 10
                razones.append(f"📊 RSI bajo ({rsi:.0f})")
            elif rsi > 75:
                put_pts += 15
                razones.append(f"📊 RSI muy alto ({rsi:.0f})")
            elif rsi > 65:
                put_pts += 10
                razones.append(f"📊 RSI alto ({rsi:.0f})")
        
        # 3. Stochastic
        k = df['stoch_k'].iloc[-1]
        d = df['stoch_d'].iloc[-1]
        k_prev = df['stoch_k'].iloc[-2]
        d_prev = df['stoch_d'].iloc[-2]
        
        if not pd.isna(k):
            # Cruce alcista en sobreventa
            if k < 25 and k_prev < d_prev and k > d:
                call_pts += 15
                razones.append("📈 Stoch cruce alcista")
            # Cruce bajista en sobrecompra
            elif k > 75 and k_prev > d_prev and k < d:
                put_pts += 15
                razones.append("📉 Stoch cruce bajista")
            elif k < 20:
                call_pts += 8
            elif k > 80:
                put_pts += 8
        
        # 4. Bollinger Bands
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        
        if not pd.isna(bb_upper):
            if close <= bb_lower * 1.005:
                call_pts += 12
                razones.append("📉 En banda inferior BB")
            elif close >= bb_upper * 0.995:
                put_pts += 12
                razones.append("📈 En banda superior BB")
        
        # 5. MACD
        hist = df['macd_hist'].iloc[-1]
        hist_prev = df['macd_hist'].iloc[-2]
        
        if not pd.isna(hist):
            if hist > 0 and hist_prev <= 0:
                call_pts += 12
                razones.append("📊 MACD cruce alcista")
            elif hist < 0 and hist_prev >= 0:
                put_pts += 12
                razones.append("📊 MACD cruce bajista")
            elif hist > 0 and hist > hist_prev:
                call_pts += 5
            elif hist < 0 and hist < hist_prev:
                put_pts += 5
        
        # 6. Momentum (últimas 3 velas)
        mom = (close - df['close'].iloc[-4]) / df['close'].iloc[-4] * 100
        if mom > 0.3:
            call_pts += 8
            razones.append(f"📈 Momentum +{mom:.2f}%")
        elif mom < -0.3:
            put_pts += 8
            razones.append(f"📉 Momentum {mom:.2f}%")
        
        # 7. EMAs
        ema12 = df['ema_12'].iloc[-1]
        ema26 = df['ema_26'].iloc[-1]
        
        if close > ema12 > ema26:
            call_pts += 5
            tendencia = "ALCISTA"
        elif close < ema12 < ema26:
            put_pts += 5
            tendencia = "BAJISTA"
        else:
            tendencia = "LATERAL"
        
        # Calcular resultado
        diferencia = abs(call_pts - put_pts)
        total = call_pts + put_pts
        
        if call_pts > put_pts and diferencia >= 10:
            direccion = Direccion.CALL
            prob = min(60 + diferencia * 1.5, 95)
        elif put_pts > call_pts and diferencia >= 10:
            direccion = Direccion.PUT
            prob = min(60 + diferencia * 1.5, 95)
        else:
            direccion = Direccion.ESPERAR
            prob = 50
            razones.append("⚠️ Señal muy débil")
        
        # Fuerza
        if diferencia >= 35:
            fuerza = 5
        elif diferencia >= 25:
            fuerza = 4
        elif diferencia >= 18:
            fuerza = 3
        elif diferencia >= 12:
            fuerza = 2
        else:
            fuerza = 1
        
        # Momento
        if fuerza >= 4 and len(razones) >= 2:
            momento = "🔥 ENTRAR AHORA"
        elif fuerza >= 3:
            momento = "✅ BUENA ENTRADA"
        elif fuerza >= 2:
            momento = "⏳ ESPERAR"
        else:
            momento = "❌ NO OPERAR"
        
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
            tendencia=tendencia
        )


def format_price(p):
    if p == 0: return "N/A"
    if p < 0.001: return f"${p:.8f}"
    if p < 1: return f"${p:.6f}"
    if p < 100: return f"${p:.4f}"
    return f"${p:,.2f}"


def mostrar_senal(activo: str, senal: SenalBinaria):
    """Muestra señal de forma compacta y clara."""
    
    config = MIS_ACTIVOS.get(activo.upper(), {})
    nombre = config.get('nombre', activo.upper())
    
    estrellas = "⭐" * senal.fuerza + "☆" * (5 - senal.fuerza)
    
    print(f"\n{'═'*55}")
    print(f"  🎯 {nombre}")
    print(f"  💰 Precio: {format_price(senal.precio)}")
    print(f"{'═'*55}")
    
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
        print(f"  ║{'⚪ ESPERAR':^51}║")
        print(f"  ╚{'═'*51}╝")
    
    print(f"\n  📊 Probabilidad: {senal.probabilidad:.0f}%")
    print(f"  💪 Fuerza:       {estrellas}")
    print(f"  ⏱️  Expiración:   {senal.expiracion}")
    print(f"  🚦 Momento:      {senal.momento}")
    print(f"  📈 Tendencia:    {senal.tendencia}")
    
    print(f"\n  {'─'*50}")
    print(f"  📋 RAZONES:")
    for r in senal.razones[:5]:
        print(f"     • {r}")
    
    print(f"{'═'*55}")


def escanear_todos():
    """Escanea todos mis activos."""
    
    print("\n" + "🎯"*20)
    print("  ESCANEANDO MIS ACTIVOS OTC")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🎯"*20)
    
    analizador = AnalizadorOTC()
    resultados = []
    
    activos_ordenados = [
        # Crypto primero
        'BTC', 'ETH', 'SOL', 'TRUMP', 'MELANIA',
        # Luego Forex
        'EURUSD', 'GBPUSD', 'USDCHF', 'AUDCAD', 'EURJPY',
        # Commodities
        'UKO'
    ]
    
    for activo in activos_ordenados:
        config = MIS_ACTIVOS.get(activo, {})
        nombre = config.get('nombre', activo)
        
        print(f"\n  ⏳ {nombre}...", end=" ", flush=True)
        
        try:
            senal = analizador.analizar(activo)
            
            emoji = "🟢" if senal.direccion == Direccion.CALL else "🔴" if senal.direccion == Direccion.PUT else "⚪"
            print(f"{emoji} {'⭐'*senal.fuerza}")
            
            resultados.append((activo, senal))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Filtrar señales fuertes
    fuertes = [(a, s) for a, s in resultados if s.fuerza >= 3 and s.direccion != Direccion.ESPERAR]
    
    if fuertes:
        print("\n" + "🔥"*20)
        print("  MEJORES SEÑALES AHORA")
        print("🔥"*20)
        
        # Ordenar por fuerza
        fuertes.sort(key=lambda x: x[1].fuerza, reverse=True)
        
        for activo, senal in fuertes:
            mostrar_senal(activo, senal)
    else:
        print("\n" + "⚪"*20)
        print("  No hay señales fuertes ahora")
        print("  Espera unos minutos y vuelve a escanear")
        print("⚪"*20)
    
    return resultados


def menu():
    """Menú interactivo."""
    
    print("\n" + "🎯"*20)
    print("  MIS BINARIAS OTC")
    print("🎯"*20)
    
    print("\n📊 MIS ACTIVOS:")
    print("  CRYPTO: BTC, ETH, SOL, TRUMP, MELANIA")
    print("  FOREX:  EURUSD, GBPUSD, USDCHF, AUDCAD, EURJPY")
    print("  OTROS:  UKO (Petróleo)")
    
    print("\n💡 COMANDOS:")
    print("  • Escribe un activo: BTC, EURUSD, etc.")
    print("  • 'todos' = escanear todos")
    print("  • 'salir' = salir")
    
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
            
            # Normalizar entrada
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
