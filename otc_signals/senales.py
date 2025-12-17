#!/usr/bin/env python3
"""
🎯 BULLEX - SEÑALES EN TIEMPO REAL
==================================

Bot que genera señales de trading basadas en
el sentimiento de traders en Bullex.

Uso:
    python3 senales.py

Autor: Bot de Trading
Fecha: 2025
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
from collections import defaultdict
import os

# ============= CREDENCIALES =============
# Usa variables de entorno para seguridad
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# ============= MAPEO DE ACTIVOS =============
ACTIVOS = {
    # Forex
    1: "EUR/USD", 2: "EUR/GBP", 3: "GBP/USD", 4: "EUR/JPY", 5: "USD/JPY",
    6: "AUD/USD", 7: "USD/CAD", 31: "AUD/JPY", 32: "EUR/AUD", 33: "EUR/CAD",
    34: "GBP/JPY", 35: "GBP/CAD", 36: "GBP/AUD", 37: "CAD/JPY", 38: "NZD/USD",
    45: "NZD/JPY", 46: "CHF/JPY", 51: "EUR/CHF", 52: "GBP/CHF", 53: "AUD/CHF",
    72: "USD/MXN", 74: "USD/NOK", 76: "USD/PLN", 77: "USD/RUB", 78: "EUR/NZD",
    79: "USD/CNH", 80: "NZD/CAD", 81: "EUR/TRY", 82: "USD/TRY", 84: "USD/CHF",
    85: "AUD/CAD", 86: "AUD/CAD (OTC)", 99: "USD/SGD", 100: "USD/ZAR",
    102: "GBP/NZD", 103: "AUD/NZD", 104: "USD/SEK", 105: "EUR/NOK",
    106: "EUR/SEK", 107: "USD/HKD", 108: "USD/PLN", 168: "EUR/PLN",
    816: "CAD/CHF", 817: "EUR/HKD", 818: "EUR/SGD", 893: "NZD/CHF",
    
    # Crypto principales
    212: "BTC/USD", 220: "ETH/USD", 756: "LTC/USD", 867: "XAU/USD (Gold)",
    892: "XAG/USD (Silver)", 971: "DASH/USD", 1062: "EOS/USD", 1470: "XRP/USD",
    1857: "BNB/USD", 1858: "BCH/USD", 1861: "LINK/USD", 1862: "VET/USD",
    1863: "DOT/USD", 1865: "FTT/USD", 1866: "ADA/USD", 1867: "UNI/USD",
    1868: "AAVE/USD", 1872: "SUSHI/USD", 1873: "DOGE/USD", 1874: "SHIB/USD",
    1876: "SOL/USD", 1877: "LUNA/USD", 1881: "AVAX/USD", 1884: "ATOM/USD",
    1885: "MATIC/USD", 1886: "ALGO/USD", 1896: "ONE/USD", 1898: "XLM/USD",
    1901: "TRX/USD", 1910: "FIL/USD", 1912: "SAND/USD", 1916: "GALA/USD",
    1917: "ENS/USD", 1921: "MANA/USD", 1922: "AXS/USD", 1925: "SUSHI/USD",
    1926: "CRV/USD", 1928: "ENJ/USD", 1930: "COMP/USD", 1931: "YFI/USD",
    1933: "1INCH/USD", 1935: "KAVA/USD", 1936: "NEAR/USD", 1937: "FTM/USD",
    1938: "THETA/USD", 1941: "XTZ/USD", 1972: "APE/USD", 1973: "PEPE/USD",
    1974: "FLOKI/USD", 1975: "OP/USD", 1976: "ARB/USD",
    
    # Memecoins y nuevas
    2044: "ARB/USD", 2045: "INJ/USD", 2046: "LDO/USD", 2047: "BLUR/USD",
    2048: "SUI/USD", 2049: "RNDR/USD", 2050: "WLD/USD", 2051: "SEI/USD",
    2062: "RUNE/USD", 2063: "BONK/USD", 2064: "JTO/USD", 2065: "TIA/USD",
    2067: "ORDI/USD", 2069: "MEME/USD", 2070: "PYTH/USD", 2073: "JUP/USD",
    2074: "DYM/USD", 2076: "WIF/USD", 2078: "MYRO/USD", 2079: "STRK/USD",
    2080: "PIXEL/USD", 2082: "DYM/USD", 2083: "PIXEL/USD", 2084: "PORTAL/USD",
    2085: "AEVO/USD", 2086: "ALT/USD", 2087: "MEME/USD", 2088: "PANDORA/USD",
    2089: "AEVO/USD", 2090: "ENA/USD", 2091: "ETHFI/USD", 2092: "W/USD",
    2093: "TNSR/USD", 2096: "REZ/USD", 2097: "BOME/USD", 2098: "TAO/USD",
    2099: "FLOKI/USD", 2100: "NOT/USD", 2101: "IO/USD", 2102: "ZK/USD",
    2104: "LISTA/USD", 2105: "ZRO/USD", 2106: "BLAST/USD", 2107: "BRETT/USD",
    2108: "DOGS/USD", 2109: "POPCAT/USD", 2110: "SUN/USD", 2111: "WEN/USD",
    2112: "NEIRO/USD", 2113: "CATI/USD", 2114: "HMSTR/USD", 2115: "EIGEN/USD",
    2116: "SCR/USD", 2117: "SAFE/USD", 2120: "GOAT/USD", 2121: "ACT/USD",
    2122: "PNUT/USD", 2123: "COW/USD", 2124: "MOODENG/USD", 2125: "CHILLGUY/USD",
    2126: "GRASS/USD", 2127: "BAN/USD", 2129: "ME/USD", 2130: "MOVE/USD",
    2131: "VANA/USD", 2132: "HYPE/USD", 2137: "PENGU/USD", 2138: "ORCA/USD",
    2139: "BIO/USD", 2140: "USUAL/USD", 2141: "AI16Z/USD", 2142: "VIRTUAL/USD",
    2143: "FARTCOIN/USD", 2144: "GRIFFAIN/USD", 2145: "AIXBT/USD",
    2146: "ARC/USD", 2147: "SWARMS/USD", 2148: "ZEREBRO/USD", 2149: "COOKIE/USD",
    2150: "ELIZA/USD", 2151: "TRUMP/USD", 2152: "MELANIA/USD", 2153: "VINE/USD",
    2154: "ANON/USD", 2155: "SOLV/USD", 2156: "SONIC/USD", 2157: "ONDO/USD",
    2158: "PLUME/USD", 2159: "IP/USD", 2160: "LAYER/USD", 2161: "TST/USD",
    2164: "BERA/USD", 2165: "LAYER/USD", 2166: "KAITO/USD", 2167: "SHELL/USD",
    2168: "ANIME/USD", 2181: "STO/USD", 2182: "NIL/USD", 2183: "PARTI/USD",
    2186: "BMT/USD", 2187: "GPS/USD", 2188: "SHELL/USD", 2201: "PI/USD",
    2202: "RED/USD", 2265: "FORM/USD", 2267: "OM/USD", 2270: "BABY/USD",
    2276: "ALPACA/USD", 2277: "HAEDAL/USD", 2278: "SIGN/USD", 2279: "MILK/USD",
    2286: "RFC/USD", 2287: "OBOL/USD", 2288: "GORK/USD", 2289: "DARK/USD",
    2290: "LAUNCHCOIN/USD", 2291: "KEKIUS/USD", 2293: "KILO/USD",
    2294: "SKYAI/USD", 2298: "SCF/USD", 2299: "KTA/USD", 2300: "WCT/USD",
    2301: "JELLYJELLY/USD", 2303: "INIT/USD", 2304: "ONDO/USD",
    2311: "VIRTUAL/USD", 2312: "ZORA/USD", 2313: "PUMP/USD", 2320: "FUEL/USD",
    2323: "B2/USD",
    
    # Acciones
    1280: "Amazon", 1281: "Microsoft", 1285: "Apple", 1287: "Apple",
    1345: "Netflix", 1346: "Google", 1347: "Facebook", 1348: "Tesla",
    1379: "Microsoft", 1380: "Intel", 1381: "Intel", 1382: "Cisco",
    1383: "NVIDIA", 1473: "Alibaba", 1474: "Baidu", 1475: "IBM",
    1476: "Nike", 1477: "McDonald's", 1478: "Visa", 1481: "Mastercard",
    1487: "Boeing", 1520: "Disney", 1536: "Twitter", 1543: "S&P 500",
}


def banner():
    """Muestra el banner del bot."""
    print("\n" + "═" * 70)
    print("  🤖 BULLEX - SISTEMA DE SEÑALES EN TIEMPO REAL")
    print("  📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═" * 70)


async def login():
    """Inicia sesión y devuelve ssid y cookies."""
    print("\n🔐 Iniciando sesión...")
    
    async with aiohttp.ClientSession() as session:
        payload = {"identifier": EMAIL, "password": PASSWORD}
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://trade.bull-ex.com"
        }
        
        async with session.post(LOGIN_URL, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                ssid = data.get("ssid", "")
                cookies = {c.key: c.value for c in resp.cookies.values()}
                balance = data.get("balance", 0)
                print(f"   ✅ Login exitoso")
                return ssid, cookies
            else:
                print(f"   ❌ Error: {resp.status}")
                return None, None


async def conectar_ws(ssid, cookies):
    """Conecta al WebSocket."""
    print("🔌 Conectando al servidor...")
    
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    try:
        ws = await websockets.connect(
            WS_URL,
            extra_headers={
                "Cookie": cookie_str,
                "Origin": "https://trade.bull-ex.com"
            }
        )
    except TypeError:
        ws = await websockets.connect(WS_URL, origin="https://trade.bull-ex.com")
    
    # Autenticar
    await ws.send(json.dumps({"name": "ssid", "msg": ssid}))
    
    # Suscribir a sentimiento
    await ws.send(json.dumps({
        "name": "subscribeMessage",
        "msg": {"name": "traders-mood-changed"}
    }))
    
    print("   ✅ Conectado y suscrito")
    return ws


def mostrar_senal(nombre: str, instrumento: str, call_pct: float, fuerza: int):
    """Muestra una señal de trading."""
    hora = datetime.now().strftime("%H:%M:%S")
    put_pct = 100 - call_pct
    
    # Determinar dirección y emoji
    if call_pct > 50:
        direccion = "CALL"
        pct = call_pct
        emoji = "🟢" * min(fuerza, 5)
    else:
        direccion = "PUT"
        pct = put_pct
        emoji = "🔴" * min(fuerza, 5)
    
    # Tipo de instrumento
    tipo = ""
    if "blitz" in instrumento:
        tipo = " [⚡BLITZ]"
    elif "turbo" in instrumento:
        tipo = " [🚀TURBO]"
    elif "binary" in instrumento:
        tipo = " [📊BINARY]"
    
    # Barra visual
    lleno = int(pct / 10)
    barra = "█" * lleno + "░" * (10 - lleno)
    
    # Intensidad del mensaje
    if fuerza >= 5:
        intensidad = "¡¡¡SEÑAL EXTREMA!!!"
    elif fuerza >= 4:
        intensidad = "¡¡SEÑAL FUERTE!!"
    elif fuerza >= 3:
        intensidad = "¡BUENA SEÑAL!"
    else:
        intensidad = ""
    
    print(f"\n{emoji} {hora} | {nombre}{tipo}")
    print(f"   → {direccion} [{barra}] {pct:.1f}%  {intensidad}")


async def escuchar_senales(ws, duracion_minutos: int = 10):
    """Escucha y procesa señales."""
    print(f"\n📡 ESCUCHANDO SEÑALES ({duracion_minutos} min)...")
    print("─" * 70)
    print("  Mostrando activos con sentimiento > 65%")
    print("  🟢 = CALL (Comprar)    🔴 = PUT (Vender)")
    print("  ⚡ = Blitz    🚀 = Turbo    📊 = Binary")
    print("─" * 70)
    
    señales_vistas = {}
    estadisticas = {"total": 0, "call": 0, "put": 0}
    
    start = asyncio.get_event_loop().time()
    timeout = duracion_minutos * 60
    balance = 0
    
    try:
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                name = data.get("name", "")
                
                if name == "traders-mood-changed":
                    m = data.get("msg", {})
                    aid = m.get("asset_id", 0)
                    inst = m.get("instrument", "")
                    value = m.get("value", 0.5)
                    
                    call_pct = value * 100
                    put_pct = 100 - call_pct
                    
                    # Calcular fuerza de la señal
                    desviacion = abs(call_pct - 50)
                    if desviacion >= 45:  # >95% o <5%
                        fuerza = 5
                    elif desviacion >= 35:  # >85% o <15%
                        fuerza = 4
                    elif desviacion >= 25:  # >75% o <25%
                        fuerza = 3
                    elif desviacion >= 15:  # >65% o <35%
                        fuerza = 2
                    else:
                        fuerza = 1
                    
                    # Solo mostrar señales significativas (>65% o <35%)
                    if fuerza >= 2:
                        nombre = ACTIVOS.get(aid, f"Activo #{aid}")
                        
                        # Evitar spam - cada señal por activo cada 60s
                        clave = f"{aid}_{inst}"
                        ahora = asyncio.get_event_loop().time()
                        
                        if clave not in señales_vistas or \
                           ahora - señales_vistas[clave] > 60:
                            señales_vistas[clave] = ahora
                            mostrar_senal(nombre, inst, call_pct, fuerza)
                            
                            estadisticas["total"] += 1
                            if call_pct > 50:
                                estadisticas["call"] += 1
                            else:
                                estadisticas["put"] += 1
                
                elif name == "profile":
                    m = data.get("msg", {})
                    balance = m.get("balance", 0)
                    print(f"\n💰 Balance: ${balance:.2f}")
                    
                elif name == "balance":
                    m = data.get("msg", {})
                    balance = m.get("amount", m.get("current_balance", {}).get("amount", 0))
                    print(f"\n💰 Balance actualizado: ${balance:.2f}")
                    
            except asyncio.TimeoutError:
                # Heartbeat visual cada 30 segundos sin señales
                elapsed = int(asyncio.get_event_loop().time() - start)
                if elapsed % 30 < 3:
                    print(".", end="", flush=True)
                    
            except websockets.exceptions.ConnectionClosed:
                print("\n⚠️ Conexión perdida")
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 Detenido por el usuario")
    
    # Resumen final
    print("\n" + "═" * 70)
    print("📊 RESUMEN DE SESIÓN")
    print("═" * 70)
    print(f"   Total señales: {estadisticas['total']}")
    print(f"   🟢 CALL: {estadisticas['call']}")
    print(f"   🔴 PUT: {estadisticas['put']}")
    if balance:
        print(f"   💰 Balance final: ${balance:.2f}")
    print("═" * 70)


async def main():
    """Función principal."""
    banner()
    
    # Login
    ssid, cookies = await login()
    if not ssid:
        print("❌ No se pudo conectar")
        return
    
    # Conectar WebSocket
    ws = await conectar_ws(ssid, cookies)
    
    # Escuchar señales
    await escuchar_senales(ws, duracion_minutos=15)
    
    # Cerrar
    await ws.close()
    print("\n👋 Bot cerrado")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
