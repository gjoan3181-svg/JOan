#!/usr/bin/env python3
"""
🎯 BULLEX BOT - SEÑALES EN TIEMPO REAL v2.0
==========================================

Bot que genera señales de trading basadas en
el sentimiento de traders en Bullex.

Uso:
    python3 bot_final.py

Controles:
    Ctrl+C para detener
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
import os
import sys

# ============= CREDENCIALES =============
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# ============= ACTIVOS =============
ACTIVOS = {
    # Forex principales
    1: "EUR/USD", 2: "EUR/GBP", 3: "GBP/USD", 4: "EUR/JPY", 5: "USD/JPY",
    6: "AUD/USD", 7: "USD/CAD", 31: "AUD/JPY", 32: "EUR/AUD", 33: "EUR/CAD",
    34: "GBP/JPY", 35: "GBP/CAD", 36: "GBP/AUD", 37: "CAD/JPY", 38: "NZD/USD",
    45: "NZD/JPY", 46: "CHF/JPY", 51: "EUR/CHF", 52: "GBP/CHF", 53: "AUD/CHF",
    72: "USD/MXN", 74: "USD/NOK", 76: "USD/PLN", 77: "USD/RUB", 78: "EUR/NZD",
    79: "USD/CNH", 80: "NZD/CAD", 81: "EUR/TRY", 82: "USD/TRY", 84: "USD/CHF",
    85: "AUD/CAD", 86: "AUD/CAD (OTC)",
    
    # Crypto TOP
    212: "BTC/USD", 220: "ETH/USD", 756: "LTC/USD", 867: "GOLD", 892: "SILVER",
    1470: "XRP/USD", 1857: "BNB/USD", 1861: "LINK/USD", 1863: "DOT/USD",
    1866: "ADA/USD", 1867: "UNI/USD", 1873: "DOGE/USD", 1874: "SHIB/USD",
    1876: "SOL/USD", 1881: "AVAX/USD", 1884: "ATOM/USD", 1885: "MATIC/USD",
    
    # Memecoins y Nuevas
    1912: "SAND/USD", 1921: "MANA/USD", 1935: "KAVA/USD", 1936: "NEAR/USD",
    1937: "FTM/USD", 1941: "XTZ/USD", 1973: "PEPE/USD", 2044: "ARB/USD",
    2048: "SUI/USD", 2049: "RNDR/USD", 2050: "WLD/USD", 2063: "BONK/USD",
    2073: "JUP/USD", 2076: "WIF/USD", 2099: "FLOKI/USD", 2100: "NOT/USD",
    2108: "DOGS/USD", 2114: "HMSTR/USD", 2117: "SAFE/USD", 2122: "PNUT/USD",
    2132: "HYPE/USD", 2137: "PENGU/USD", 2140: "USUAL/USD", 2141: "AI16Z/USD",
    2142: "VIRTUAL/USD", 2143: "FARTCOIN/USD", 2144: "GRIFFAIN/USD",
    2145: "AIXBT/USD", 2148: "ZEREBRO/USD", 2150: "ELIZA/USD", 2151: "TRUMP/USD",
    2152: "MELANIA/USD", 2155: "SOLV/USD", 2156: "SONIC/USD", 2166: "KAITO/USD",
    2182: "NIL/USD", 2183: "PARTI/USD", 2276: "ALPACA/USD", 2289: "DARK/USD",
    2291: "KEKIUS/USD", 2299: "KTA/USD", 2300: "WCT/USD", 2313: "PUMP/USD",
    2320: "FUEL/USD",
    
    # Acciones
    1280: "Amazon", 1346: "Google", 1347: "Facebook", 1348: "Tesla",
    1379: "Microsoft", 1383: "NVIDIA", 1543: "S&P 500",
}


def banner():
    """Muestra banner inicial."""
    print("\n" + "═" * 65)
    print("  🤖 BULLEX BOT - SEÑALES EN TIEMPO REAL v2.0")
    print("  📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═" * 65)


def mostrar_senal(nombre: str, inst: str, call_pct: float):
    """Muestra una señal."""
    hora = datetime.now().strftime("%H:%M:%S")
    put_pct = 100 - call_pct
    
    # Tipo de instrumento
    tipo = ""
    if "blitz" in inst:
        tipo = " ⚡"
    elif "turbo" in inst:
        tipo = " 🚀"
    
    # Dirección y nivel
    if call_pct >= 95:
        print(f"🟢🟢🟢🟢🟢 {hora} | {nombre}{tipo} | CALL {call_pct:.0f}% !!!EXTREMO!!!")
    elif call_pct >= 85:
        print(f"🟢🟢🟢🟢 {hora} | {nombre}{tipo} | CALL {call_pct:.0f}% !!FUERTE!!")
    elif call_pct >= 75:
        print(f"🟢🟢🟢 {hora} | {nombre}{tipo} | CALL {call_pct:.0f}% !BUENA!")
    elif call_pct >= 65:
        print(f"🟢🟢 {hora} | {nombre}{tipo} | CALL {call_pct:.0f}%")
    elif put_pct >= 95:
        print(f"🔴🔴🔴🔴🔴 {hora} | {nombre}{tipo} | PUT {put_pct:.0f}% !!!EXTREMO!!!")
    elif put_pct >= 85:
        print(f"🔴🔴🔴🔴 {hora} | {nombre}{tipo} | PUT {put_pct:.0f}% !!FUERTE!!")
    elif put_pct >= 75:
        print(f"🔴🔴🔴 {hora} | {nombre}{tipo} | PUT {put_pct:.0f}% !BUENA!")
    elif put_pct >= 65:
        print(f"🔴🔴 {hora} | {nombre}{tipo} | PUT {put_pct:.0f}%")


async def main():
    banner()
    
    # ===== LOGIN =====
    print("\n🔐 Conectando a Bullex...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URL,
                json={'identifier': EMAIL, 'password': PASSWORD},
                headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
                
                if resp.status != 200:
                    print(f"   ❌ Error de login: {resp.status}")
                    return
                    
                data = await resp.json()
                ssid = data.get('ssid', '')
                cookies = {c.key: c.value for c in resp.cookies.values()}
        
        print("   ✅ Login exitoso")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # ===== WEBSOCKET =====
    print("🔌 Conectando WebSocket...")
    try:
        cookie_str = '; '.join([f'{k}={v}' for k,v in cookies.items()])
        ws = await websockets.connect(
            WS_URL,
            origin='https://trade.bull-ex.com',
            extra_headers={'Cookie': cookie_str}
        )
        print("   ✅ Conectado")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # ===== AUTH Y SUSCRIPCIÓN =====
    await ws.send(json.dumps({'name': 'ssid', 'msg': ssid}))
    await asyncio.sleep(1)  # Esperar auth
    await ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
    
    # ===== ESCUCHAR SEÑALES =====
    print("\n📡 SEÑALES EN TIEMPO REAL")
    print("─" * 65)
    print("  Mostrando activos con sentimiento > 65%")
    print("  🟢 = CALL (Subida)    🔴 = PUT (Bajada)")
    print("  ⚡ = Blitz (5s)       🚀 = Turbo (1min)")
    print("─" * 65)
    
    vistas = {}  # Para evitar spam
    stats = {"total": 0, "call": 0, "put": 0, "extremos": 0}
    balance = 0
    
    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                name = data.get('name', '')
                
                if name == 'traders-mood-changed':
                    m = data.get('msg', {})
                    aid = m.get('asset_id', 0)
                    inst = m.get('instrument', '')
                    value = m.get('value', 0.5)
                    
                    call_pct = value * 100
                    put_pct = 100 - call_pct
                    
                    # Solo señales significativas (>65%)
                    if call_pct >= 65 or put_pct >= 65:
                        nombre = ACTIVOS.get(aid, f"#{aid}")
                        clave = f"{aid}_{inst}"
                        ahora = asyncio.get_event_loop().time()
                        
                        # Evitar spam - misma señal cada 30s
                        if clave not in vistas or ahora - vistas[clave] > 30:
                            vistas[clave] = ahora
                            mostrar_senal(nombre, inst, call_pct)
                            
                            stats["total"] += 1
                            if call_pct > 50:
                                stats["call"] += 1
                            else:
                                stats["put"] += 1
                            if call_pct >= 95 or put_pct >= 95:
                                stats["extremos"] += 1
                
                elif name == 'profile':
                    balance = data.get('msg', {}).get('balance', 0)
                    print(f"\n💰 Balance: ${balance:.2f}\n")
                    
                elif name == 'balance':
                    m = data.get('msg', {})
                    balance = m.get('amount', m.get('current_balance', {}).get('amount', 0))
                    print(f"\n💰 Balance actualizado: ${balance:.2f}\n")
                    
            except asyncio.TimeoutError:
                # Heartbeat cada 5s sin datos
                print(".", end="", flush=True)
                
            except websockets.exceptions.ConnectionClosed:
                print("\n⚠️ Conexión perdida. Reconectando...")
                break
                
    except KeyboardInterrupt:
        pass
    
    # ===== RESUMEN =====
    print("\n\n" + "═" * 65)
    print("📊 RESUMEN DE SESIÓN")
    print("═" * 65)
    print(f"   Total señales: {stats['total']}")
    print(f"   🟢 CALL: {stats['call']}")
    print(f"   🔴 PUT: {stats['put']}")
    print(f"   ⚡ Extremos (>95%): {stats['extremos']}")
    if balance:
        print(f"   💰 Balance: ${balance:.2f}")
    print("═" * 65)
    
    await ws.close()
    print("\n👋 Bot cerrado")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
