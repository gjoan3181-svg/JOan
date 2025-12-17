#!/usr/bin/env python3
"""
🎯 SEÑALES BINARIAS CON TRADINGVIEW
===================================

Usa datos en TIEMPO REAL de TradingView.
Mucho más preciso que Yahoo Finance.

Uso:
    python3 tv_binarias.py              # Escanear todos
    python3 tv_binarias.py BTCUSD       # Analizar uno
    python3 tv_binarias.py EURUSD GBPUSD # Analizar varios
"""

import sys
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

try:
    from tradingview_ta import TA_Handler, Interval, Exchange
    TV_DISPONIBLE = True
except ImportError:
    TV_DISPONIBLE = False
    print("⚠️ Instala tradingview-ta: pip3 install tradingview-ta")


# ============= MIS ACTIVOS OTC EN TRADINGVIEW =============
MIS_ACTIVOS_TV = {
    # Crypto - Exchange: BINANCE, COINBASE, BITSTAMP
    'BTC': {'symbol': 'BTCUSD', 'exchange': 'BITSTAMP', 'screener': 'crypto', 'nombre': 'BTC/USD (OTC)'},
    'BTCUSD': {'symbol': 'BTCUSD', 'exchange': 'BITSTAMP', 'screener': 'crypto', 'nombre': 'BTC/USD (OTC)'},
    'ETH': {'symbol': 'ETHUSD', 'exchange': 'BITSTAMP', 'screener': 'crypto', 'nombre': 'ETH/USD (OTC)'},
    'ETHUSD': {'symbol': 'ETHUSD', 'exchange': 'BITSTAMP', 'screener': 'crypto', 'nombre': 'ETH/USD (OTC)'},
    'SOL': {'symbol': 'SOLUSD', 'exchange': 'COINBASE', 'screener': 'crypto', 'nombre': 'SOL/USD (OTC)'},
    'SOLUSD': {'symbol': 'SOLUSD', 'exchange': 'COINBASE', 'screener': 'crypto', 'nombre': 'SOL/USD (OTC)'},
    'XRP': {'symbol': 'XRPUSD', 'exchange': 'BITSTAMP', 'screener': 'crypto', 'nombre': 'XRP/USD (OTC)'},
    'DOGE': {'symbol': 'DOGEUSD', 'exchange': 'BINANCE', 'screener': 'crypto', 'nombre': 'DOGE/USD (OTC)'},
    'ADA': {'symbol': 'ADAUSD', 'exchange': 'COINBASE', 'screener': 'crypto', 'nombre': 'ADA/USD (OTC)'},
    'DOT': {'symbol': 'DOTUSD', 'exchange': 'BINANCE', 'screener': 'crypto', 'nombre': 'DOT/USD (OTC)'},
    'TRUMP': {'symbol': 'TRUMPUSD', 'exchange': 'BYBIT', 'screener': 'crypto', 'nombre': 'TRUMP/USD (OTC)'},
    'MELANIA': {'symbol': 'MELANIAUSD', 'exchange': 'BYBIT', 'screener': 'crypto', 'nombre': 'MELANIA/USD (OTC)'},
    
    # Forex - Exchange: FX_IDC, OANDA, FOREXCOM
    'EURUSD': {'symbol': 'EURUSD', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'EUR/USD (OTC)'},
    'GBPUSD': {'symbol': 'GBPUSD', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'GBP/USD (OTC)'},
    'USDCHF': {'symbol': 'USDCHF', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'USD/CHF (OTC)'},
    'AUDCAD': {'symbol': 'AUDCAD', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'AUD/CAD (OTC)'},
    'EURJPY': {'symbol': 'EURJPY', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'EUR/JPY (OTC)'},
    'USDJPY': {'symbol': 'USDJPY', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'USD/JPY (OTC)'},
    'AUDUSD': {'symbol': 'AUDUSD', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'AUD/USD (OTC)'},
    'NZDUSD': {'symbol': 'NZDUSD', 'exchange': 'FX_IDC', 'screener': 'forex', 'nombre': 'NZD/USD (OTC)'},
    
    # Commodities
    'UKO': {'symbol': 'UKOIL', 'exchange': 'FX_IDC', 'screener': 'cfd', 'nombre': 'UK Oil (OTC)'},
    'UKOIL': {'symbol': 'UKOIL', 'exchange': 'FX_IDC', 'screener': 'cfd', 'nombre': 'UK Oil (OTC)'},
    'GOLD': {'symbol': 'XAUUSD', 'exchange': 'FX_IDC', 'screener': 'cfd', 'nombre': 'Gold (OTC)'},
    'XAUUSD': {'symbol': 'XAUUSD', 'exchange': 'FX_IDC', 'screener': 'cfd', 'nombre': 'Gold (OTC)'},
    'SILVER': {'symbol': 'XAGUSD', 'exchange': 'FX_IDC', 'screener': 'cfd', 'nombre': 'Silver (OTC)'},
}


class Direccion(Enum):
    CALL = "🟢 CALL ↑"
    PUT = "🔴 PUT ↓"
    ESPERAR = "⚪ ESPERAR"


@dataclass
class SenalTV:
    """Señal basada en TradingView."""
    direccion: Direccion
    probabilidad: float
    fuerza: int
    expiracion: str
    razones: List[str]
    momento: str
    precio: float
    
    # Datos de TradingView
    tv_recomendacion: str  # "BUY", "SELL", "NEUTRAL"
    tv_buy_signals: int
    tv_sell_signals: int
    tv_neutral_signals: int
    
    # Indicadores clave
    rsi: float
    macd_signal: str
    ma_signal: str
    oscillators_signal: str
    
    tendencia: str
    advertencia: str = ""


class AnalizadorTradingView:
    """Analizador usando datos de TradingView en tiempo real."""
    
    def __init__(self):
        if not TV_DISPONIBLE:
            raise ImportError("tradingview-ta no está instalado")
    
    def _get_handler(self, activo: str, intervalo: str = '1m') -> Optional[TA_Handler]:
        """Crea handler de TradingView para el activo."""
        
        config = MIS_ACTIVOS_TV.get(activo.upper())
        if not config:
            # Intentar como símbolo directo forex
            config = {
                'symbol': activo.upper(),
                'exchange': 'FX_IDC',
                'screener': 'forex',
                'nombre': activo.upper()
            }
        
        # Mapear intervalo
        interval_map = {
            '1m': Interval.INTERVAL_1_MINUTE,
            '5m': Interval.INTERVAL_5_MINUTES,
            '15m': Interval.INTERVAL_15_MINUTES,
            '30m': Interval.INTERVAL_30_MINUTES,
            '1h': Interval.INTERVAL_1_HOUR,
            '4h': Interval.INTERVAL_4_HOURS,
            '1d': Interval.INTERVAL_1_DAY,
        }
        
        tv_interval = interval_map.get(intervalo, Interval.INTERVAL_5_MINUTES)
        
        try:
            handler = TA_Handler(
                symbol=config['symbol'],
                exchange=config['exchange'],
                screener=config['screener'],
                interval=tv_interval,
                timeout=10
            )
            return handler
        except Exception as e:
            print(f"  ⚠️ Error creando handler: {e}")
            return None
    
    def analizar(self, activo: str, intervalo: str = '5m') -> Optional[SenalTV]:
        """
        Analiza un activo usando TradingView.
        
        Args:
            activo: Símbolo del activo
            intervalo: '1m', '5m', '15m', '1h'
        """
        config = MIS_ACTIVOS_TV.get(activo.upper(), {})
        nombre = config.get('nombre', activo.upper())
        
        handler = self._get_handler(activo, intervalo)
        if not handler:
            return None
        
        try:
            analysis = handler.get_analysis()
        except Exception as e:
            print(f"  ⚠️ Error obteniendo análisis: {e}")
            return None
        
        # Extraer datos de TradingView
        summary = analysis.summary
        indicators = analysis.indicators
        oscillators = analysis.oscillators
        moving_avgs = analysis.moving_averages
        
        tv_recomendacion = summary['RECOMMENDATION']
        buy_signals = summary['BUY']
        sell_signals = summary['SELL']
        neutral_signals = summary['NEUTRAL']
        
        precio = indicators.get('close', 0)
        rsi = indicators.get('RSI', 50)
        
        # Señales de osciladores y medias móviles
        osc_rec = oscillators['RECOMMENDATION']
        ma_rec = moving_avgs['RECOMMENDATION']
        
        razones = []
        advertencia = ""
        
        # ===== DETERMINAR SEÑAL =====
        call_pts = 0
        put_pts = 0
        
        # 1. Recomendación general de TradingView (peso alto)
        if tv_recomendacion == 'STRONG_BUY':
            call_pts += 35
            razones.append("📊 TradingView: COMPRA FUERTE")
        elif tv_recomendacion == 'BUY':
            call_pts += 25
            razones.append("📊 TradingView: COMPRA")
        elif tv_recomendacion == 'STRONG_SELL':
            put_pts += 35
            razones.append("📊 TradingView: VENTA FUERTE")
        elif tv_recomendacion == 'SELL':
            put_pts += 25
            razones.append("📊 TradingView: VENTA")
        else:
            razones.append("📊 TradingView: NEUTRAL")
        
        # 2. Osciladores
        if osc_rec == 'STRONG_BUY':
            call_pts += 20
            razones.append("📈 Osciladores: COMPRA FUERTE")
        elif osc_rec == 'BUY':
            call_pts += 15
            razones.append("📈 Osciladores: COMPRA")
        elif osc_rec == 'STRONG_SELL':
            put_pts += 20
            razones.append("📉 Osciladores: VENTA FUERTE")
        elif osc_rec == 'SELL':
            put_pts += 15
            razones.append("📉 Osciladores: VENTA")
        
        # 3. Medias Móviles (tendencia)
        if ma_rec == 'STRONG_BUY':
            call_pts += 25
            tendencia = "ALCISTA FUERTE"
            razones.append("📈 MAs: COMPRA FUERTE")
        elif ma_rec == 'BUY':
            call_pts += 18
            tendencia = "ALCISTA"
            razones.append("📈 MAs: COMPRA")
        elif ma_rec == 'STRONG_SELL':
            put_pts += 25
            tendencia = "BAJISTA FUERTE"
            razones.append("📉 MAs: VENTA FUERTE")
        elif ma_rec == 'SELL':
            put_pts += 18
            tendencia = "BAJISTA"
            razones.append("📉 MAs: VENTA")
        else:
            tendencia = "LATERAL"
        
        # 4. RSI
        if rsi < 30:
            call_pts += 10
            razones.append(f"📊 RSI bajo: {rsi:.0f}")
        elif rsi > 70:
            put_pts += 10
            razones.append(f"📊 RSI alto: {rsi:.0f}")
        
        # 5. Proporción de señales
        total_signals = buy_signals + sell_signals + neutral_signals
        if total_signals > 0:
            buy_ratio = buy_signals / total_signals
            sell_ratio = sell_signals / total_signals
            
            if buy_ratio > 0.6:
                call_pts += 10
            elif sell_ratio > 0.6:
                put_pts += 10
        
        # ===== CALCULAR RESULTADO =====
        diferencia = abs(call_pts - put_pts)
        
        if call_pts > put_pts and diferencia >= 15:
            direccion = Direccion.CALL
            prob = min(55 + diferencia * 0.8, 92)
        elif put_pts > call_pts and diferencia >= 15:
            direccion = Direccion.PUT
            prob = min(55 + diferencia * 0.8, 92)
        else:
            direccion = Direccion.ESPERAR
            prob = 50
            advertencia = "⚠️ Señal no clara - esperar"
        
        # Fuerza basada en señales de TV
        if diferencia >= 50:
            fuerza = 5
        elif diferencia >= 40:
            fuerza = 4
        elif diferencia >= 30:
            fuerza = 3
        elif diferencia >= 20:
            fuerza = 2
        else:
            fuerza = 1
        
        # Momento
        if fuerza >= 4:
            momento = "🔥 ENTRAR AHORA"
        elif fuerza >= 3:
            momento = "✅ BUENA ENTRADA"
        elif fuerza >= 2:
            momento = "⏳ ESPERAR"
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
        
        # Macd signal
        macd = indicators.get('MACD.macd', 0)
        macd_sig = indicators.get('MACD.signal', 0)
        if macd > macd_sig:
            macd_signal = "ALCISTA"
        elif macd < macd_sig:
            macd_signal = "BAJISTA"
        else:
            macd_signal = "NEUTRAL"
        
        return SenalTV(
            direccion=direccion,
            probabilidad=prob,
            fuerza=fuerza,
            expiracion=exp,
            razones=razones,
            momento=momento,
            precio=precio,
            tv_recomendacion=tv_recomendacion,
            tv_buy_signals=buy_signals,
            tv_sell_signals=sell_signals,
            tv_neutral_signals=neutral_signals,
            rsi=rsi,
            macd_signal=macd_signal,
            ma_signal=ma_rec,
            oscillators_signal=osc_rec,
            tendencia=tendencia,
            advertencia=advertencia
        )


def format_price(p):
    if p == 0: return "N/A"
    if p < 0.001: return f"${p:.8f}"
    if p < 1: return f"${p:.6f}"
    if p < 100: return f"${p:.4f}"
    return f"${p:,.2f}"


def mostrar_senal(activo: str, senal: SenalTV):
    """Muestra la señal de forma visual."""
    
    config = MIS_ACTIVOS_TV.get(activo.upper(), {})
    nombre = config.get('nombre', activo.upper())
    
    estrellas = "⭐" * senal.fuerza + "☆" * (5 - senal.fuerza)
    
    print(f"\n{'═'*60}")
    print(f"  🎯 {nombre}")
    print(f"  💰 Precio: {format_price(senal.precio)} (TIEMPO REAL)")
    print(f"  📈 Tendencia: {senal.tendencia}")
    print(f"{'═'*60}")
    
    if senal.advertencia:
        print(f"\n  {senal.advertencia}")
    
    # Señal principal
    if senal.direccion == Direccion.CALL:
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'🟢 CALL ↑ (SUBE)':^56}║")
        print(f"  ╚{'═'*56}╝")
    elif senal.direccion == Direccion.PUT:
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'🔴 PUT ↓ (BAJA)':^56}║")
        print(f"  ╚{'═'*56}╝")
    else:
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'⚪ ESPERAR - NO OPERAR':^56}║")
        print(f"  ╚{'═'*56}╝")
    
    print(f"\n  📊 Probabilidad: {senal.probabilidad:.0f}%")
    print(f"  💪 Fuerza:       {estrellas}")
    print(f"  ⏱️  Expiración:   {senal.expiracion}")
    print(f"  🚦 Momento:      {senal.momento}")
    
    # Datos de TradingView
    print(f"\n  {'─'*55}")
    print(f"  📺 DATOS TRADINGVIEW:")
    print(f"     Recomendación: {senal.tv_recomendacion}")
    print(f"     Señales COMPRA: {senal.tv_buy_signals} | VENTA: {senal.tv_sell_signals} | NEUTRAL: {senal.tv_neutral_signals}")
    print(f"     RSI: {senal.rsi:.1f} | MACD: {senal.macd_signal}")
    print(f"     Medias Móviles: {senal.ma_signal}")
    print(f"     Osciladores: {senal.oscillators_signal}")
    
    print(f"\n  {'─'*55}")
    print(f"  📋 RAZONES:")
    for r in senal.razones[:6]:
        print(f"     • {r}")
    
    print(f"{'═'*60}")


def escanear_todos(intervalo: str = '5m'):
    """Escanea todos mis activos OTC."""
    
    if not TV_DISPONIBLE:
        print("❌ Instala tradingview-ta: pip3 install tradingview-ta")
        return
    
    print("\n" + "🎯"*20)
    print("  SEÑALES BINARIAS - TRADINGVIEW")
    print("  📺 Datos en TIEMPO REAL")
    print(f"  ⏱️  Intervalo: {intervalo}")
    print("  " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🎯"*20)
    
    analizador = AnalizadorTradingView()
    resultados = []
    
    # Lista de activos a escanear
    activos = [
        'BTC', 'ETH', 'SOL', 'XRP', 'DOGE',
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDCAD', 'EURJPY',
        'GOLD', 'UKOIL'
    ]
    
    for activo in activos:
        config = MIS_ACTIVOS_TV.get(activo, {})
        nombre = config.get('nombre', activo)
        
        print(f"\n  ⏳ {nombre}...", end=" ", flush=True)
        
        try:
            senal = analizador.analizar(activo, intervalo)
            
            if senal:
                emoji = "🟢" if senal.direccion == Direccion.CALL else "🔴" if senal.direccion == Direccion.PUT else "⚪"
                print(f"{emoji} {'⭐'*senal.fuerza} | TV: {senal.tv_recomendacion}")
                resultados.append((activo, senal))
            else:
                print("⚠️ Sin datos")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
    
    # Filtrar señales fuertes
    fuertes = [(a, s) for a, s in resultados if s.fuerza >= 3 and s.direccion != Direccion.ESPERAR]
    
    if fuertes:
        print("\n" + "🔥"*20)
        print("  MEJORES SEÑALES AHORA")
        print("🔥"*20)
        
        fuertes.sort(key=lambda x: x[1].fuerza, reverse=True)
        
        for activo, senal in fuertes[:5]:
            mostrar_senal(activo, senal)
    else:
        print("\n" + "⚪"*20)
        print("  No hay señales fuertes ahora")
        print("  Espera mejores condiciones")
        print("⚪"*20)
    
    return resultados


def menu():
    """Menú interactivo."""
    
    if not TV_DISPONIBLE:
        print("❌ Instala tradingview-ta: pip3 install tradingview-ta")
        return
    
    print("\n" + "🎯"*20)
    print("  SEÑALES BINARIAS - TRADINGVIEW")
    print("  📺 Datos en TIEMPO REAL")
    print("🎯"*20)
    
    print("\n📊 ACTIVOS DISPONIBLES:")
    print("  CRYPTO: BTC, ETH, SOL, XRP, DOGE, ADA, DOT")
    print("  FOREX:  EURUSD, GBPUSD, USDJPY, AUDCAD, EURJPY")
    print("  OTROS:  GOLD, UKOIL, SILVER")
    
    print("\n💡 COMANDOS:")
    print("  • Activo: EURUSD, BTC, etc.")
    print("  • 'todos' o Enter = escanear todos")
    print("  • 'salir' = salir")
    
    analizador = AnalizadorTradingView()
    
    while True:
        try:
            entrada = input("\n🔍 Activo: ").strip().upper()
            
            if entrada in ['SALIR', 'EXIT', 'Q']:
                print("\n👋 ¡Éxito en tus trades!")
                break
            
            if entrada in ['TODOS', 'ALL', 'SCAN', '']:
                escanear_todos('5m')
                continue
            
            entrada = entrada.replace('/', '').replace('-', '').replace(' ', '')
            
            print(f"\n⏳ Analizando {entrada} con TradingView...")
            senal = analizador.analizar(entrada, '5m')
            
            if senal:
                mostrar_senal(entrada, senal)
            else:
                print(f"⚠️ No se pudo obtener datos para {entrada}")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ['--SCAN', 'TODOS', 'ALL']:
            intervalo = sys.argv[2] if len(sys.argv) > 2 else '5m'
            escanear_todos(intervalo)
        else:
            if not TV_DISPONIBLE:
                print("❌ Instala: pip3 install tradingview-ta")
                return
            analizador = AnalizadorTradingView()
            for a in sys.argv[1:]:
                if not a.startswith('--'):
                    a = a.upper().replace('/', '').replace('-', '')
                    print(f"\n⏳ Analizando {a}...")
                    senal = analizador.analizar(a, '5m')
                    if senal:
                        mostrar_senal(a, senal)
                    else:
                        print(f"⚠️ No hay datos para {a}")
    else:
        menu()


if __name__ == '__main__':
    main()
