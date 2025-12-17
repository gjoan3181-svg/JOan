#!/usr/bin/env python3
"""
🎯 BULLEX BOT - SEÑALES PARA REPÚBLICA DOMINICANA
=================================================

- Hora: República Dominicana (UTC-4)
- Tiempo exacto de entrada y expiración
- Solo operaciones binarias (2-3 minutos)
- Historial con verificación de resultados

Uso:
    python3 bot_rd.py
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
import time

# ============= ZONA HORARIA =============
# República Dominicana: UTC-4 (Atlantic Standard Time)
RD_TIMEZONE = timezone(timedelta(hours=-4))

def hora_rd():
    """Retorna la hora actual en República Dominicana."""
    return datetime.now(RD_TIMEZONE)

def formato_hora(dt):
    """Formatea datetime para mostrar."""
    return dt.strftime("%H:%M:%S")

# ============= CREDENCIALES =============
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "/workspace/otc_signals/historial_rd.json"

# ============= BASE DE DATOS DE ACTIVOS =============
ACTIVOS_DB = {
    # FOREX
    1: ("EUR/USD", "FOREX"), 2: ("EUR/GBP", "FOREX"), 3: ("GBP/USD", "FOREX"),
    4: ("EUR/JPY", "FOREX"), 5: ("USD/JPY", "FOREX"), 6: ("AUD/USD", "FOREX"),
    7: ("USD/CAD", "FOREX"), 31: ("AUD/JPY", "FOREX"), 32: ("EUR/AUD", "FOREX"),
    33: ("EUR/CAD", "FOREX"), 34: ("GBP/JPY", "FOREX"), 35: ("GBP/CAD", "FOREX"),
    36: ("GBP/AUD", "FOREX"), 37: ("CAD/JPY", "FOREX"), 38: ("NZD/USD", "FOREX"),
    51: ("EUR/CHF", "FOREX"), 78: ("EUR/NZD", "FOREX"), 84: ("USD/CHF", "FOREX"),
    85: ("AUD/CAD", "FOREX"), 86: ("AUD/CAD OTC", "OTC"),
    
    # CRYPTO TOP
    212: ("Bitcoin (BTC)", "CRYPTO"), 220: ("Ethereum (ETH)", "CRYPTO"),
    1470: ("Ripple (XRP)", "CRYPTO"), 1857: ("Binance Coin (BNB)", "CRYPTO"),
    1861: ("Chainlink (LINK)", "CRYPTO"), 1863: ("Polkadot (DOT)", "CRYPTO"),
    1866: ("Cardano (ADA)", "CRYPTO"), 1867: ("Uniswap (UNI)", "CRYPTO"),
    1868: ("Aave (AAVE)", "CRYPTO"), 1873: ("Dogecoin (DOGE)", "CRYPTO"),
    1874: ("Shiba Inu (SHIB)", "CRYPTO"), 1876: ("Solana (SOL)", "CRYPTO"),
    1881: ("Avalanche (AVAX)", "CRYPTO"), 1885: ("Polygon (MATIC)", "CRYPTO"),
    1912: ("The Sandbox (SAND)", "CRYPTO"), 1936: ("NEAR Protocol", "CRYPTO"),
    1937: ("Fantom (FTM)", "CRYPTO"), 1941: ("Tezos (XTZ)", "CRYPTO"),
    1973: ("Pepe (PEPE)", "CRYPTO"), 1974: ("Floki (FLOKI)", "CRYPTO"),
    1975: ("Optimism (OP)", "CRYPTO"), 1976: ("Arbitrum (ARB)", "CRYPTO"),
    
    # CRYPTO NUEVAS
    2044: ("Arbitrum (ARB)", "CRYPTO"), 2048: ("Sui (SUI)", "CRYPTO"),
    2049: ("Render (RNDR)", "CRYPTO"), 2050: ("Worldcoin (WLD)", "CRYPTO"),
    2051: ("Sei (SEI)", "CRYPTO"), 2063: ("Bonk (BONK)", "CRYPTO"),
    2073: ("Jupiter (JUP)", "CRYPTO"), 2076: ("dogwifhat (WIF)", "CRYPTO"),
    2098: ("Bittensor (TAO)", "CRYPTO"), 2099: ("Floki (FLOKI)", "CRYPTO"),
    2100: ("Notcoin (NOT)", "CRYPTO"), 2108: ("Dogs (DOGS)", "CRYPTO"),
    2114: ("Hamster (HMSTR)", "CRYPTO"), 2122: ("Peanut (PNUT)", "CRYPTO"),
    2137: ("Pudgy Penguins (PENGU)", "CRYPTO"),
    2141: ("ai16z (AI16Z)", "CRYPTO"), 2142: ("Virtuals (VIRTUAL)", "CRYPTO"),
    2144: ("Griffain (GRIFFAIN)", "CRYPTO"), 2145: ("aixbt (AIXBT)", "CRYPTO"),
    2148: ("Zerebro (ZEREBRO)", "CRYPTO"), 2150: ("Eliza (ELIZA)", "CRYPTO"),
    2151: ("Trump (TRUMP)", "CRYPTO"), 2152: ("Melania (MELANIA)", "CRYPTO"),
    2155: ("Solv (SOLV)", "CRYPTO"), 2156: ("Sonic (SONIC)", "CRYPTO"),
    2166: ("Kaito (KAITO)", "CRYPTO"), 2182: ("Nil (NIL)", "CRYPTO"),
    2183: ("Particle (PARTI)", "CRYPTO"), 2313: ("Pump.fun (PUMP)", "CRYPTO"),
    
    # MÁS CRYPTO
    1862: ("VeChain (VET)", "CRYPTO"), 1865: ("FTX Token (FTT)", "CRYPTO"),
    1869: ("Maker (MKR)", "CRYPTO"), 1878: ("Cosmos (ATOM)", "CRYPTO"),
    1897: ("Fantom (FTM)", "CRYPTO"), 1898: ("Stellar (XLM)", "CRYPTO"),
    1901: ("Tron (TRX)", "CRYPTO"), 1935: ("Kava (KAVA)", "CRYPTO"),
    2062: ("THORChain (RUNE)", "CRYPTO"), 2079: ("Starknet (STRK)", "CRYPTO"),
    2090: ("Ethena (ENA)", "CRYPTO"), 2097: ("Book of Meme (BOME)", "CRYPTO"),
    2102: ("zkSync (ZK)", "CRYPTO"), 2103: ("LayerZero (ZRO)", "CRYPTO"),
    2105: ("LayerZero (ZRO)", "CRYPTO"), 2106: ("Blast (BLAST)", "CRYPTO"),
    2111: ("Wen (WEN)", "CRYPTO"), 2112: ("Neiro (NEIRO)", "CRYPTO"),
    2113: ("Catizen (CATI)", "CRYPTO"), 2116: ("Scroll (SCR)", "CRYPTO"),
    2117: ("Safe (SAFE)", "CRYPTO"), 2118: ("Aptos (APT)", "CRYPTO"),
    2119: ("Movement (MOVE)", "CRYPTO"), 2120: ("Goatseus (GOAT)", "CRYPTO"),
    2123: ("CoW Protocol (COW)", "CRYPTO"), 2124: ("Moo Deng (MOODENG)", "CRYPTO"),
    2125: ("Chillguy (CHILLGUY)", "CRYPTO"), 2128: ("Hyperliquid (HYPE)", "CRYPTO"),
    2129: ("Magic Eden (ME)", "CRYPTO"), 2130: ("Movement (MOVE)", "CRYPTO"),
    2131: ("Vana (VANA)", "CRYPTO"), 2136: ("Usual (USUAL)", "CRYPTO"),
    2140: ("Usual (USUAL)", "CRYPTO"), 2157: ("Ondo (ONDO)", "CRYPTO"),
    2164: ("Berachain (BERA)", "CRYPTO"), 2265: ("Form (FORM)", "CRYPTO"),
    2267: ("Mantra (OM)", "CRYPTO"), 2276: ("Alpaca Finance (ALPACA)", "CRYPTO"),
    2277: ("Haedal (HAEDAL)", "CRYPTO"), 2279: ("Milky Way (MILK)", "CRYPTO"),
    2286: ("RFC (RFC)", "CRYPTO"), 2288: ("Gork (GORK)", "CRYPTO"),
    2289: ("Dark (DARK)", "CRYPTO"), 2290: ("Launchcoin (LAUNCH)", "CRYPTO"),
    2299: ("Kite AI (KTA)", "CRYPTO"), 2300: ("WalletConnect (WCT)", "CRYPTO"),
    2304: ("Ondo (ONDO)", "CRYPTO"), 2312: ("Zora (ZORA)", "CRYPTO"),
    2319: ("Haedal (HAEDAL)", "CRYPTO"), 2320: ("Fuel (FUEL)", "CRYPTO"),
    
    # ACCIONES
    1380: ("Intel (INTC)", "ACCIONES"), 1381: ("Intel (INTC)", "ACCIONES"),
    1383: ("NVIDIA (NVDA)", "ACCIONES"), 1348: ("Tesla (TSLA)", "ACCIONES"),
}


class HistorialManager:
    def __init__(self, archivo):
        self.archivo = archivo
        self.senales = []
        self.cargar()
    
    def cargar(self):
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r') as f:
                    self.senales = json.load(f).get('senales', [])
        except:
            self.senales = []
    
    def guardar(self):
        with open(self.archivo, 'w') as f:
            json.dump({'senales': self.senales, 'actualizado': hora_rd().isoformat()}, f, indent=2)
    
    def agregar(self, senal):
        self.senales.append(senal)
        self.guardar()
    
    def actualizar_resultado(self, senal_id, resultado):
        for s in self.senales:
            if s.get('id') == senal_id:
                s['resultado'] = resultado
                s['verificado'] = True
                break
        self.guardar()
    
    def estadisticas(self):
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(verificadas) - len(ganadas),
            'precision': (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        }


class BotRD:
    def __init__(self):
        self.ws = None
        self.ssid = ""
        self.cookies = {}
        self.historial = HistorialManager(HISTORIAL_FILE)
        self.precios = {}
        self.velas = defaultdict(list)
        self.sentimiento = {}
        self.senales_pendientes = {}
        self.balance = 0
    
    async def login(self):
        print(f"\n🔐 [{formato_hora(hora_rd())}] Conectando a Bullex...")
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URL,
                json={'identifier': EMAIL, 'password': PASSWORD},
                headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                self.ssid = data.get('ssid', '')
                self.cookies = {c.key: c.value for c in resp.cookies.values()}
        print(f"   ✅ Login exitoso")
        return True
    
    async def conectar_ws(self):
        print(f"🔌 [{formato_hora(hora_rd())}] Conectando WebSocket...")
        cookie_str = '; '.join([f'{k}={v}' for k,v in self.cookies.items()])
        self.ws = await websockets.connect(WS_URL, origin='https://trade.bull-ex.com',
            extra_headers={'Cookie': cookie_str})
        
        await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
        await asyncio.sleep(1)
        await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
        await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
        print(f"   ✅ Conectado y suscrito")
        return True
    
    def calcular_entrada_expiracion(self, duracion_minutos=2):
        """
        Calcula tiempo exacto de entrada y expiración.
        Entrada: próximo minuto completo + 5 segundos
        Expiración: entrada + duración
        """
        ahora = hora_rd()
        
        # Próximo minuto completo + 5 segundos para dar tiempo de entrar
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=1, seconds=5)
        
        # Si estamos muy cerca del siguiente minuto, usar el que sigue
        if (entrada - ahora).total_seconds() < 10:
            entrada += timedelta(minutes=1)
        
        # Expiración
        expiracion = entrada + timedelta(minutes=duracion_minutos)
        
        return entrada, expiracion
    
    def generar_senal(self, aid, inst, call_pct):
        if aid not in ACTIVOS_DB:
            return None
        
        nombre, mercado = ACTIVOS_DB[aid]
        
        # Calcular tiempos exactos
        entrada, expiracion = self.calcular_entrada_expiracion(duracion_minutos=2)
        
        # Dirección
        if call_pct > 50:
            direccion = "CALL"
            direccion_texto = "📈 SUBE (CALL)"
            pct = call_pct
        else:
            direccion = "PUT"
            direccion_texto = "📉 BAJA (PUT)"
            pct = 100 - call_pct
        
        # Probabilidad ajustada
        prob = min(99, pct + (5 if pct >= 95 else 3 if pct >= 85 else 0))
        
        # Confianza
        if prob >= 90:
            confianza = "🔥 MUY ALTA"
        elif prob >= 80:
            confianza = "✅ ALTA"
        elif prob >= 70:
            confianza = "📊 MEDIA"
        else:
            confianza = "⚠️ BAJA"
        
        return {
            'id': f"{aid}_{int(time.time())}",
            'timestamp': hora_rd().isoformat(),
            'activo_id': aid,
            'activo': nombre,
            'mercado': mercado,
            'direccion': direccion,
            'direccion_texto': direccion_texto,
            'sentimiento': pct,
            'probabilidad': prob,
            'confianza': confianza,
            'entrada': formato_hora(entrada),
            'expiracion': formato_hora(expiracion),
            'duracion': "2 minutos",
            'precio_entrada': self.precios.get(aid, 0),
            'verificado': False,
            'resultado': None
        }
    
    def mostrar_senal(self, s):
        ahora = hora_rd()
        
        print("\n" + "╔" + "═" * 58 + "╗")
        print(f"║  🎯 SEÑAL DE TRADING - {s['confianza']:<30} ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📍 Activo: {s['activo']:<43} ║")
        print(f"║  📊 Mercado: {s['mercado']:<42} ║")
        print("╠" + "═" * 58 + "╣")
        
        if s['direccion'] == 'CALL':
            print(f"║     🟢🟢🟢  {s['direccion_texto']:<40}  ║")
        else:
            print(f"║     🔴🔴🔴  {s['direccion_texto']:<40}  ║")
        
        print("╠" + "═" * 58 + "╣")
        print(f"║  📈 Probabilidad: {s['probabilidad']:.0f}%{' ' * 37}║")
        print(f"║  👥 Sentimiento: {s['sentimiento']:.0f}% de traders{' ' * 25}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  ⏰ ENTRADA:    {s['entrada']:<40} ║")
        print(f"║  ⏱️  EXPIRACIÓN: {s['expiracion']:<40} ║")
        print(f"║  ⌛ DURACIÓN:   {s['duracion']:<40} ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  🕐 Hora RD:    {formato_hora(ahora):<40} ║")
        print("╚" + "═" * 58 + "╝")
    
    def mostrar_estadisticas(self):
        stats = self.historial.estadisticas()
        print("\n┌" + "─" * 40 + "┐")
        print(f"│  📊 ESTADÍSTICAS DE SEÑALES{' ' * 11}│")
        print("├" + "─" * 40 + "┤")
        print(f"│  Total señales:    {stats['total']:<19}│")
        print(f"│  Verificadas:      {stats['verificadas']:<19}│")
        print(f"│  ✅ Ganadas:       {stats['ganadas']:<19}│")
        print(f"│  ❌ Perdidas:      {stats['perdidas']:<19}│")
        print(f"│  📈 Precisión:     {stats['precision']:.1f}%{' ' * 15}│")
        print("└" + "─" * 40 + "┘")
    
    async def verificar_pendientes(self):
        ahora = time.time()
        verificadas = []
        
        for sid, senal in list(self.senales_pendientes.items()):
            tiempo_senal = datetime.fromisoformat(senal['timestamp']).timestamp()
            if ahora - tiempo_senal >= 150:  # 2.5 minutos
                aid = senal['activo_id']
                precio_actual = self.precios.get(aid, 0)
                precio_entrada = senal.get('precio_entrada', 0)
                
                if precio_actual and precio_entrada:
                    subio = precio_actual > precio_entrada
                    if senal['direccion'] == "CALL":
                        resultado = "GANADA" if subio else "PERDIDA"
                    else:
                        resultado = "GANADA" if not subio else "PERDIDA"
                    
                    self.historial.actualizar_resultado(sid, resultado)
                    
                    emoji = "✅" if resultado == "GANADA" else "❌"
                    print(f"\n{emoji} RESULTADO: {senal['activo']} - {resultado}")
                    print(f"   Entrada: {precio_entrada:.6f} → Cierre: {precio_actual:.6f}")
                    
                    verificadas.append(sid)
        
        for sid in verificadas:
            del self.senales_pendientes[sid]
    
    async def procesar_mensaje(self, msg):
        try:
            data = json.loads(msg)
            name = data.get('name', '')
            m = data.get('msg', {})
            
            if name == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                # Filtrar blitz
                if 'blitz' in inst.lower():
                    return
                
                call_pct = value * 100
                put_pct = 100 - call_pct
                
                # Solo señales >80%
                if call_pct >= 80 or put_pct >= 80:
                    ahora = time.time()
                    clave = f"{aid}_{inst}"
                    
                    if clave in self.sentimiento:
                        if ahora - self.sentimiento[clave].get('ts', 0) < 120:
                            return
                    
                    self.sentimiento[clave] = {'ts': ahora}
                    
                    senal = self.generar_senal(aid, inst, call_pct)
                    if senal and senal['probabilidad'] >= 80:
                        self.mostrar_senal(senal)
                        self.historial.agregar(senal)
                        self.senales_pendientes[senal['id']] = senal
            
            elif name == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
            
            elif name == 'profile':
                self.balance = m.get('balance', 0)
                print(f"\n💰 Balance: ${self.balance:.2f}")
            
            elif name == 'balance':
                nuevo = m.get('amount', m.get('current_balance', {}).get('amount', 0))
                if nuevo != self.balance:
                    diff = nuevo - self.balance
                    emoji = "📈" if diff > 0 else "📉"
                    print(f"\n{emoji} Balance: ${self.balance:.2f} → ${nuevo:.2f} ({diff:+.2f})")
                    self.balance = nuevo
                    
        except:
            pass
    
    async def ejecutar(self):
        if not await self.login():
            return
        if not await self.conectar_ws():
            return
        
        ahora = hora_rd()
        
        print("\n" + "═" * 60)
        print("  🎯 BULLEX BOT - SEÑALES PARA REPÚBLICA DOMINICANA")
        print("═" * 60)
        print(f"  🕐 Hora RD: {formato_hora(ahora)} (UTC-4)")
        print(f"  📅 Fecha: {ahora.strftime('%d/%m/%Y')}")
        print("═" * 60)
        print("  📊 Operaciones: BINARIAS (2 minutos)")
        print("  🎯 Umbral: Solo señales >80% de consenso")
        print("  ⏰ Tiempos: Entrada y expiración exactos")
        print("═" * 60)
        print("  Presiona Ctrl+C para ver estadísticas y salir")
        print("═" * 60)
        
        self.mostrar_estadisticas()
        
        ultimo_check = time.time()
        
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    await self.procesar_mensaje(msg)
                    
                    if time.time() - ultimo_check >= 30:
                        await self.verificar_pendientes()
                        ultimo_check = time.time()
                        
                except asyncio.TimeoutError:
                    if time.time() - ultimo_check >= 30:
                        await self.verificar_pendientes()
                        ultimo_check = time.time()
                    # Mostrar hora cada minuto
                    print(f"[{formato_hora(hora_rd())}]", end=" ", flush=True)
                    
                except websockets.exceptions.ConnectionClosed:
                    print(f"\n⚠️ [{formato_hora(hora_rd())}] Reconectando...")
                    if await self.login() and await self.conectar_ws():
                        continue
                    break
                    
        except KeyboardInterrupt:
            pass
        
        print("\n")
        self.mostrar_estadisticas()
        
        ultimas = self.historial.senales[-5:] if self.historial.senales else []
        if ultimas:
            print("\n📋 ÚLTIMAS SEÑALES:")
            print("─" * 50)
            for s in ultimas:
                emoji_r = "✅" if s.get('resultado') == "GANADA" else "❌" if s.get('resultado') == "PERDIDA" else "⏳"
                emoji_d = "🟢" if s['direccion'] == "CALL" else "🔴"
                print(f"  {emoji_r} {s['activo']} | {emoji_d} {s['direccion']} | {s['entrada']} | {s.get('resultado', 'Pendiente')}")
        
        await self.ws.close()
        print(f"\n👋 [{formato_hora(hora_rd())}] Bot cerrado")


async def main():
    bot = BotRD()
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
