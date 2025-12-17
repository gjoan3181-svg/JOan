#!/usr/bin/env python3
"""
🎯 BULLEX SEÑALES EN TIEMPO REAL
================================

Bot que conecta directamente a Bullex y genera señales
basadas en el sentimiento de traders.

Uso:
    python3 bullex_senales.py
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
from collections import defaultdict
import os

# Credenciales (usa variables de entorno en producción)
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# Mapeo de activos conocidos (se actualiza dinámicamente)
ACTIVOS = {
    1: "EUR/USD",
    2: "EUR/GBP", 
    3: "GBP/USD",
    4: "EUR/JPY",
    5: "USD/JPY",
    6: "AUD/USD",
    7: "USD/CAD",
    31: "AUD/JPY",
    32: "EUR/AUD",
    33: "EUR/CAD",
    34: "GBP/JPY",
    35: "GBP/CAD",
    36: "GBP/AUD",
    37: "CAD/JPY",
    38: "NZD/USD",
    45: "NZD/JPY",
    46: "CHF/JPY",
    51: "EUR/CHF",
    52: "GBP/CHF",
    53: "AUD/CHF",
    72: "USD/MXN",
    74: "USD/NOK",
    77: "USD/RUB",
    78: "EUR/NZD",
    80: "NZD/CAD",
    81: "EUR/TRY",
    82: "USD/TRY",
    84: "USD/CHF",
    85: "AUD/CAD",
    86: "AUD/CAD (OTC)",
    99: "USD/SGD",
    100: "USD/ZAR",
    102: "GBP/NZD",
    103: "AUD/NZD",
    104: "USD/SEK",
    105: "EUR/NOK",
    106: "EUR/SEK",
    107: "USD/HKD",
    108: "USD/PLN",
    168: "EUR/PLN",
    212: "BTC/USD",
    220: "ETH/USD",
    756: "LTC/USD",
    816: "CAD/CHF",
    817: "EUR/HKD",
    818: "EUR/SGD",
    867: "XAU/USD (Gold)",
    892: "XAG/USD (Silver)",
    893: "NZD/CHF",
    971: "DASH/USD",
    1062: "EOS/USD",
    1280: "Amazon",
    1287: "Apple",
    1345: "Netflix",
    1346: "Google",
    1347: "Facebook",
    1348: "Tesla",
    1379: "Microsoft",
    1381: "Intel",
    1382: "Cisco",
    1383: "NVIDIA",
    1470: "XRP/USD",
    1473: "Alibaba",
    1474: "Baidu",
    1475: "IBM",
    1476: "Nike",
    1477: "McDonald's",
    1478: "Visa",
    1481: "Mastercard",
    1487: "Boeing",
    1520: "Disney",
    1536: "Twitter",
    1543: "S&P 500",
    1857: "BNB/USD",
    1858: "BCH/USD",
    1861: "LINK/USD",
    1863: "DOT/USD",
    1866: "ADA/USD",
    1867: "UNI/USD",
    1868: "AAVE/USD",
    1873: "DOGE/USD",
    1874: "SHIB/USD",
    1876: "SOL/USD",
    1881: "AVAX/USD",
    1884: "ATOM/USD",
    1885: "MATIC/USD",
    1886: "ALGO/USD",
    1898: "XLM/USD",
    1901: "TRX/USD",
    1910: "FIL/USD",
    1912: "SAND/USD",
    1921: "MANA/USD",
    1922: "AXS/USD",
    1925: "SUSHI/USD",
    1926: "CRV/USD",
    1928: "ENJ/USD",
    1930: "COMP/USD",
    1931: "YFI/USD",
    1933: "1INCH/USD",
    1936: "NEAR/USD",
    1937: "FTM/USD",
    1938: "THETA/USD",
    1941: "XTZ/USD",
    1972: "APE/USD",
    1973: "PEPE/USD",
    1975: "OP/USD",
    2044: "ARB/USD",
    2045: "INJ/USD",
    2046: "LDO/USD",
    2047: "BLUR/USD",
    2048: "SUI/USD",
    2050: "WLD/USD",
    2051: "SEI/USD",
    2063: "BONK/USD",
    2064: "JTO/USD",
    2065: "TIA/USD",
    2067: "ORDI/USD",
    2070: "PYTH/USD",
    2073: "JUP/USD",
    2076: "WIF/USD",
    2079: "STRK/USD",
    2082: "DYM/USD",
    2083: "PIXEL/USD",
    2084: "PORTAL/USD",
    2086: "ALT/USD",
    2087: "MEME/USD",
    2089: "AEVO/USD",
    2090: "ENA/USD",
    2092: "W/USD",
    2093: "TNSR/USD",
    2096: "REZ/USD",
    2097: "BOME/USD",
    2098: "TAO/USD",
    2099: "FLOKI/USD",
    2100: "NOT/USD",
    2101: "IO/USD",
    2102: "ZK/USD",
    2104: "LISTA/USD",
    2105: "ZRO/USD",
    2106: "BLAST/USD",
    2108: "DOGS/USD",
    2109: "POPCAT/USD",
    2110: "SUN/USD",
    2112: "NEIRO/USD",
    2113: "CATI/USD",
    2114: "HMSTR/USD",
    2115: "EIGEN/USD",
    2116: "SCR/USD",
    2120: "GOAT/USD",
    2121: "ACT/USD",
    2122: "PNUT/USD",
    2123: "COW/USD",
    2124: "MOODENG/USD",
    2126: "GRASS/USD",
    2129: "ME/USD",
    2130: "MOVE/USD",
    2131: "VANA/USD",
    2137: "PENGU/USD",
    2139: "BIO/USD",
    2140: "USUAL/USD",
    2141: "AI16Z/USD",
    2143: "FARTCOIN/USD",
    2144: "GRIFFAIN/USD",
    2145: "AIXBT/USD",
    2147: "SWARMS/USD",
    2148: "ZEREBRO/USD",
    2149: "COOKIE/USD",
    2151: "TRUMP/USD",
    2152: "MELANIA/USD",
    2153: "VINE/USD",
    2155: "SOLV/USD",
    2156: "SONIC/USD",
    2158: "PLUME/USD",
    2159: "IP/USD",
    2161: "TST/USD",
    2164: "BERA/USD",
    2165: "LAYER/USD",
    2166: "KAITO/USD",
    2168: "ANIME/USD",
    2181: "STO/USD",
    2182: "NIL/USD",
    2183: "PARTI/USD",
    2186: "BMT/USD",
    2187: "GPS/USD",
    2188: "SHELL/USD",
    2201: "PI/USD",
    2265: "FORM/USD",
    2270: "BABY/USD",
    2277: "HAEDAL/USD",
    2278: "SIGN/USD",
    2287: "OBOL/USD",
    2288: "GORK/USD",
    2290: "LAUNCHCOIN/USD",
    2293: "KILO/USD",
    2294: "SKYAI/USD",
    2298: "SCF/USD",
    2299: "KTA/USD",
    2300: "WCT/USD",
    2303: "INIT/USD",
    2304: "ONDO/USD",
    2311: "VIRTUAL/USD",
    2313: "PUMP/USD",
    2323: "B2/USD",
}


class BullexSeñales:
    def __init__(self):
        self.ssid = ""
        self.ws = None
        self.sentimiento = {}
        self.señales = []
        self.velas = defaultdict(list)
        
    async def login(self) -> bool:
        """Inicia sesión en Bullex."""
        print("\n🔐 INICIANDO SESIÓN...")
        
        async with aiohttp.ClientSession() as session:
            payload = {"identifier": EMAIL, "password": PASSWORD}
            headers = {
                "Content-Type": "application/json",
                "Origin": "https://trade.bull-ex.com"
            }
            
            async with session.post(LOGIN_URL, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.ssid = data.get("ssid", "")
                    self.cookies = {c.key: c.value for c in resp.cookies.values()}
                    print(f"   ✅ Login exitoso!")
                    return True
                else:
                    print(f"   ❌ Error: {resp.status}")
                    return False
    
    async def conectar(self) -> bool:
        """Conecta al WebSocket."""
        print("🔌 CONECTANDO...")
        
        headers = {
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookies.items()]),
            "Origin": "https://trade.bull-ex.com"
        }
        
        try:
            self.ws = await websockets.connect(WS_URL, extra_headers=headers)
        except TypeError:
            self.ws = await websockets.connect(WS_URL, origin="https://trade.bull-ex.com")
        
        # Autenticar
        await self.ws.send(json.dumps({"name": "ssid", "msg": self.ssid}))
        
        # Suscribir a canales
        await self.ws.send(json.dumps({
            "name": "subscribeMessage", 
            "msg": {"name": "traders-mood-changed"}
        }))
        await self.ws.send(json.dumps({
            "name": "subscribeMessage", 
            "msg": {"name": "candle-generated"}
        }))
        
        print("   ✅ Conectado y suscrito!")
        return True
    
    def _procesar_sentimiento(self, msg: dict):
        """Procesa datos de sentimiento y genera señales."""
        aid = msg.get("asset_id", 0)
        instrument = msg.get("instrument", "")
        value = msg.get("value", 0.5)
        
        call_pct = value * 100
        put_pct = 100 - call_pct
        
        nombre = ACTIVOS.get(aid, f"Activo #{aid}")
        
        # Solo mostrar activos con sentimiento significativo
        if call_pct >= 70 or put_pct >= 70:
            # Agregar tipo de instrumento si no es standard
            tipo = ""
            if "blitz" in instrument:
                tipo = " [BLITZ]"
            elif "otc" in instrument.lower() or "OTC" in nombre:
                tipo = " [OTC]"
                
            # Generar señal
            if call_pct >= 90:
                self._señal(nombre + tipo, "CALL", 5, call_pct)
            elif call_pct >= 80:
                self._señal(nombre + tipo, "CALL", 4, call_pct)
            elif call_pct >= 70:
                self._señal(nombre + tipo, "CALL", 3, call_pct)
            elif put_pct >= 90:
                self._señal(nombre + tipo, "PUT", 5, put_pct)
            elif put_pct >= 80:
                self._señal(nombre + tipo, "PUT", 4, put_pct)
            elif put_pct >= 70:
                self._señal(nombre + tipo, "PUT", 3, put_pct)
    
    def _señal(self, activo: str, direccion: str, fuerza: int, porcentaje: float):
        """Registra y muestra una señal."""
        ahora = datetime.now().strftime("%H:%M:%S")
        
        # Evitar señales repetidas en los últimos 30 segundos
        clave = f"{activo}_{direccion}"
        for s in self.señales[-20:]:
            if s.get("clave") == clave:
                return
        
        self.señales.append({
            "clave": clave,
            "activo": activo,
            "direccion": direccion,
            "fuerza": fuerza,
            "porcentaje": porcentaje,
            "hora": ahora
        })
        
        # Mostrar señal
        emoji = "🟢" * fuerza if direccion == "CALL" else "🔴" * fuerza
        barra = "█" * int(porcentaje / 10) + "░" * (10 - int(porcentaje / 10))
        
        print(f"\n{emoji} {ahora} | {activo}")
        print(f"   → {direccion} [{barra}] {porcentaje:.1f}%")
        
        if fuerza >= 4:
            print(f"   ⚡ ¡SEÑAL FUERTE! Considera entrar")
    
    async def escuchar(self, minutos: int = 5):
        """Escucha datos en tiempo real."""
        print(f"\n📡 ESCUCHANDO SEÑALES ({minutos} minutos)...")
        print("═" * 60)
        print("  Mostrando solo activos con sentimiento > 70%")
        print("  🟢 = CALL    🔴 = PUT")
        print("═" * 60)
        
        start = asyncio.get_event_loop().time()
        timeout = minutos * 60
        
        try:
            while asyncio.get_event_loop().time() - start < timeout:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    data = json.loads(msg)
                    name = data.get("name", "")
                    
                    if name == "traders-mood-changed":
                        self._procesar_sentimiento(data.get("msg", {}))
                    
                    elif name == "candle-generated":
                        m = data.get("msg", {})
                        aid = m.get("active_id", 0)
                        self.velas[aid].append({
                            "o": m.get("open"),
                            "h": m.get("high"),
                            "l": m.get("low"),
                            "c": m.get("close"),
                            "t": m.get("at")
                        })
                        # Mantener solo últimas 100 velas
                        if len(self.velas[aid]) > 100:
                            self.velas[aid] = self.velas[aid][-100:]
                    
                    elif name == "balance":
                        bal = data.get("msg", {}).get("amount", 0)
                        print(f"\n💰 Balance actualizado: ${bal:.2f}")
                        
                except asyncio.TimeoutError:
                    # Mostrar que sigue activo
                    print(".", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print("\n⚠️ Conexión perdida. Reconectando...")
                    if await self.login() and await self.conectar():
                        continue
                    break
                    
        except KeyboardInterrupt:
            print("\n\n👋 Detenido por el usuario")
        
        # Resumen final
        self._mostrar_resumen()
    
    def _mostrar_resumen(self):
        """Muestra resumen de señales."""
        print("\n" + "═" * 60)
        print("📊 RESUMEN DE SEÑALES")
        print("═" * 60)
        
        if not self.señales:
            print("  No se generaron señales significativas")
            return
        
        # Agrupar por activo
        por_activo = defaultdict(list)
        for s in self.señales:
            por_activo[s["activo"]].append(s)
        
        print(f"\n  Total: {len(self.señales)} señales")
        print(f"  Activos: {len(por_activo)}")
        
        # Mostrar top señales
        print("\n  🔥 TOP SEÑALES:")
        for s in sorted(self.señales, key=lambda x: -x["fuerza"])[:10]:
            emoji = "🟢" if s["direccion"] == "CALL" else "🔴"
            estrellas = "⭐" * s["fuerza"]
            print(f"     {emoji} {s['activo']}: {s['direccion']} {s['porcentaje']:.0f}% {estrellas}")
    
    async def cerrar(self):
        """Cierra conexiones."""
        if self.ws:
            await self.ws.close()


async def main():
    print("\n" + "🤖" * 25)
    print("  BULLEX SEÑALES EN TIEMPO REAL")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🤖" * 25)
    
    bot = BullexSeñales()
    
    if not await bot.login():
        return
    
    if not await bot.conectar():
        return
    
    # Escuchar por 10 minutos (ajustable)
    await bot.escuchar(minutos=10)
    
    await bot.cerrar()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
