#!/usr/bin/env python3
"""
🎯 BOT SIMPLE DE SEÑALES - BULLEX
==================================
Muestra señales claras y fáciles de entender.
NO hace login automático - usa tu SSID.
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
import time

# ══════════════════════════════════════════════════════════════
#  👇 PEGA TU SSID AQUÍ (entre las comillas)
# ══════════════════════════════════════════════════════════════
MI_SSID = ""
# ══════════════════════════════════════════════════════════════

# Hora República Dominicana
RD = timezone(timedelta(hours=-4))
def hora(): return datetime.now(RD).strftime("%H:%M:%S")

# Activos conocidos
ACTIVOS = {
    1: "EUR/USD", 2: "EUR/GBP", 3: "GBP/USD", 4: "EUR/JPY", 5: "USD/JPY",
    6: "AUD/USD", 7: "USD/CAD", 31: "AUD/JPY", 32: "EUR/AUD", 33: "EUR/CAD",
    34: "GBP/JPY", 35: "GBP/CAD", 36: "GBP/AUD", 37: "CAD/JPY", 38: "NZD/USD",
    51: "EUR/CHF", 78: "EUR/NZD", 84: "USD/CHF", 85: "AUD/CAD", 86: "AUD/CAD OTC",
    212: "Bitcoin", 220: "Ethereum", 1470: "Ripple (XRP)", 1857: "BNB",
    1861: "Chainlink", 1863: "Polkadot", 1866: "Cardano", 1867: "Uniswap",
    1868: "Aave", 1869: "Maker (MKR)", 1873: "Dogecoin", 1874: "Shiba Inu",
    1876: "Solana", 1878: "Cosmos", 1881: "Avalanche", 1885: "Polygon",
    1897: "Fantom (FTM)", 1898: "Stellar", 1901: "Tron", 1912: "Sandbox",
    1935: "Kava", 1936: "NEAR", 1937: "Fantom", 1941: "Tezos",
    1973: "Pepe", 1974: "Floki", 1975: "Optimism", 1976: "Arbitrum",
    2044: "Arbitrum", 2048: "Sui", 2049: "Render", 2050: "Worldcoin",
    2051: "Sei", 2062: "THORChain", 2063: "Bonk", 2073: "Jupiter",
    2076: "dogwifhat", 2079: "Starknet", 2090: "Ethena", 2097: "BOME",
    2098: "Bittensor", 2099: "Floki", 2100: "Notcoin", 2102: "zkSync",
    2103: "LayerZero", 2105: "LayerZero", 2106: "Blast", 2108: "Dogs",
    2111: "Wen", 2112: "Neiro", 2113: "Catizen", 2114: "Hamster",
    2116: "Scroll", 2117: "Safe", 2118: "Aptos", 2119: "Movement",
    2120: "Goatseus", 2122: "Peanut", 2123: "CoW Protocol", 2124: "Moo Deng",
    2125: "Chillguy", 2128: "Hyperliquid", 2129: "Magic Eden", 2130: "Movement",
    2131: "Vana", 2136: "Usual", 2137: "Pudgy Penguins", 2140: "Usual",
    2141: "ai16z", 2142: "Virtuals", 2144: "Griffain", 2145: "aixbt",
    2148: "Zerebro", 2150: "Eliza", 2151: "Trump", 2152: "Melania",
    2155: "Solv", 2156: "Sonic", 2157: "Ondo", 2163: "Berachain",
    2164: "Berachain", 2166: "Kaito", 2182: "Nil", 2183: "Particle",
    2265: "Form", 2267: "Mantra", 2276: "Alpaca", 2277: "Haedal",
    2279: "Milky Way", 2286: "RFC", 2288: "Gork", 2289: "Dark",
    2290: "Launchcoin", 2299: "Kite AI", 2300: "WalletConnect",
    2304: "Ondo", 2312: "Zora", 2313: "Pump.fun", 2319: "Haedal", 2320: "Fuel",
    1348: "Tesla", 1380: "Intel", 1381: "Intel", 1383: "NVIDIA",
}

ultima_senal = {}

def mostrar_senal(nombre, direccion, probabilidad):
    """Muestra una señal clara y bonita."""
    ahora = datetime.now(RD)
    entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=3)
    expiracion = entrada + timedelta(minutes=2)
    
    print("\n" + "=" * 55)
    if direccion == "CALL":
        print(f"  🟢🟢🟢 SEÑAL: {nombre}")
        print(f"  📈 DIRECCIÓN: CALL (SUBE)")
    else:
        print(f"  🔴🔴🔴 SEÑAL: {nombre}")
        print(f"  📉 DIRECCIÓN: PUT (BAJA)")
    print("=" * 55)
    print(f"  💪 Probabilidad: {probabilidad}%")
    print(f"  ⏰ Hora actual:  {hora()}")
    print(f"  🎯 ENTRAR A:     {entrada.strftime('%H:%M:%S')}")
    print(f"  ⏱️  EXPIRA A:     {expiracion.strftime('%H:%M:%S')}")
    print(f"  ⌛ Duración:     2 minutos")
    print("=" * 55)

async def main():
    ssid = MI_SSID.strip()
    
    if not ssid:
        print("\n" + "=" * 55)
        print("  🔮 BOT DE SEÑALES BULLEX")
        print("=" * 55)
        print("\n  ⚠️  Necesitas tu SSID para conectar.\n")
        print("  📋 CÓMO OBTENERLO:")
        print("  1. Abre Chrome → https://trade.bull-ex.com")
        print("  2. Haz login con tu cuenta")
        print("  3. Presiona F12")
        print("  4. Clic en 'Application' → 'Cookies'")
        print("  5. Busca 'ssid' y copia el valor\n")
        ssid = input("  🔑 Pega tu SSID aquí: ").strip()
        if not ssid:
            print("\n  ❌ No ingresaste SSID. Saliendo...")
            return
    
    print(f"\n🔌 [{hora()}] Conectando a Bullex...")
    
    try:
        ws = await websockets.connect(
            "wss://ws.trade.bull-ex.com/echo/websocket",
            origin="https://trade.bull-ex.com"
        )
        
        await ws.send(json.dumps({'name': 'ssid', 'msg': ssid}))
        await asyncio.sleep(1)
        await ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
        
        print(f"✅ [{hora()}] ¡Conectado!")
        print("\n" + "=" * 55)
        print("  🎯 BOT ACTIVO - Esperando señales fuertes...")
        print("  📊 Solo mostraré señales con >85% probabilidad")
        print("  🇩🇴 Hora: República Dominicana (UTC-4)")
        print("  ⏰ Anticipación: 3 minutos")
        print("  ⌛ Duración: 2 minutos")
        print("=" * 55)
        print("\n  Presiona Ctrl+C para salir\n")
        
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                
                if data.get('name') == 'traders-mood-changed':
                    m = data.get('msg', {})
                    aid = m.get('asset_id', 0)
                    inst = m.get('instrument', '')
                    value = m.get('value', 0.5)
                    
                    # Ignorar blitz
                    if 'blitz' in inst.lower():
                        continue
                    
                    call_pct = value * 100
                    put_pct = 100 - call_pct
                    
                    # Solo señales fuertes (>85%)
                    if call_pct >= 85 or put_pct >= 85:
                        # Control de frecuencia (3 min entre señales del mismo activo)
                        clave = f"{aid}_{inst}"
                        ahora = time.time()
                        if clave in ultima_senal and ahora - ultima_senal[clave] < 180:
                            continue
                        ultima_senal[clave] = ahora
                        
                        # Obtener nombre
                        nombre = ACTIVOS.get(aid, f"Activo #{aid}")
                        
                        # Determinar dirección
                        if call_pct >= 85:
                            mostrar_senal(nombre, "CALL", round(call_pct))
                        else:
                            mostrar_senal(nombre, "PUT", round(put_pct))
                            
            except asyncio.TimeoutError:
                print(f"  [{hora()}] Esperando señales...")
                
    except websockets.exceptions.ConnectionClosed:
        print(f"\n⚠️ Conexión cerrada. Reconectando...")
        await main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Verifica que tu SSID sea válido.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot cerrado. ¡Hasta luego!")
