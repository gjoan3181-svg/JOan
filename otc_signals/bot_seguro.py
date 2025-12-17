#!/usr/bin/env python3
"""
🔮 BULLEX BOT SEGURO - SIN LOGIN AUTOMÁTICO
============================================

Este bot NO hace login automático.
Usa las cookies de tu sesión del navegador.

PASO A PASO:
1. Abre Bullex en tu navegador y haz login normal
2. Abre DevTools (F12) → Application → Cookies
3. Copia el valor de 'ssid' y pégalo abajo
4. Ejecuta el bot

Uso:
    python3 bot_seguro.py
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
import time

# ═══════════════════════════════════════════════════════════════
# 📋 INSTRUCCIONES PARA OBTENER TU SSID:
# ═══════════════════════════════════════════════════════════════
# 
# 1. Abre Chrome/Firefox y ve a https://trade.bull-ex.com
# 2. Haz login con tu cuenta normalmente
# 3. Presiona F12 para abrir DevTools
# 4. Ve a la pestaña "Application" (Chrome) o "Storage" (Firefox)
# 5. En el panel izquierdo, expande "Cookies"
# 6. Haz clic en "https://trade.bull-ex.com"
# 7. Busca la cookie llamada "ssid"
# 8. Copia el valor (es un texto largo)
# 9. Pégalo abajo entre las comillas
#
# ═══════════════════════════════════════════════════════════════

# 👇 PEGA TU SSID AQUÍ (entre las comillas):
MI_SSID = ""

# ═══════════════════════════════════════════════════════════════

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))

def hora_rd():
    return datetime.now(RD_TZ)

def fmt_hora(dt):
    return dt.strftime("%H:%M:%S")

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_senales.json"

# Configuración
MINUTOS_ANTICIPACION = 3
DURACION_OPERACION = 2

# Base de datos de activos
ACTIVOS_DB = {
    # FOREX
    1: ("EUR/USD", "FOREX"), 2: ("EUR/GBP", "FOREX"), 3: ("GBP/USD", "FOREX"),
    4: ("EUR/JPY", "FOREX"), 5: ("USD/JPY", "FOREX"), 6: ("AUD/USD", "FOREX"),
    7: ("USD/CAD", "FOREX"), 31: ("AUD/JPY", "FOREX"), 32: ("EUR/AUD", "FOREX"),
    33: ("EUR/CAD", "FOREX"), 34: ("GBP/JPY", "FOREX"), 35: ("GBP/CAD", "FOREX"),
    36: ("GBP/AUD", "FOREX"), 37: ("CAD/JPY", "FOREX"), 38: ("NZD/USD", "FOREX"),
    51: ("EUR/CHF", "FOREX"), 78: ("EUR/NZD", "FOREX"), 84: ("USD/CHF", "FOREX"),
    85: ("AUD/CAD", "FOREX"), 86: ("AUD/CAD OTC", "OTC"),
    
    # CRYPTO
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


class BotSeguro:
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.historial = HistorialManager(HISTORIAL_FILE)
        self.precios = {}
        self.senales_programadas = {}
        self.senales_activas = {}
        self.ultima_senal = {}
    
    async def conectar(self):
        print(f"\n🔌 [{fmt_hora(hora_rd())}] Conectando a Bullex...")
        
        try:
            self.ws = await websockets.connect(
                WS_URL,
                origin='https://trade.bull-ex.com'
            )
            
            # Autenticar con SSID
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            
            # Suscribirse a datos
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            
            print(f"   ✅ Conectado exitosamente")
            return True
            
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")
            return False
    
    def calcular_tiempos(self):
        ahora = hora_rd()
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=MINUTOS_ANTICIPACION + 1)
        expiracion = entrada + timedelta(minutes=DURACION_OPERACION)
        segundos = (entrada - ahora).total_seconds()
        return entrada, expiracion, segundos
    
    def generar_senal(self, aid, call_pct):
        if aid not in ACTIVOS_DB:
            return None
        
        nombre, mercado = ACTIVOS_DB[aid]
        ahora = hora_rd()
        entrada, expiracion, segundos = self.calcular_tiempos()
        
        if call_pct > 50:
            direccion, texto, pct = "CALL", "📈 SUBE (CALL)", call_pct
        else:
            direccion, texto, pct = "PUT", "📉 BAJA (PUT)", 100 - call_pct
        
        prob = min(99, pct + (5 if pct >= 95 else 3 if pct >= 85 else 0))
        
        if prob >= 90: confianza = "🔥 EXTREMA"
        elif prob >= 85: confianza = "✅ MUY ALTA"
        elif prob >= 80: confianza = "📊 ALTA"
        else: confianza = "⚠️ MEDIA"
        
        return {
            'id': f"{aid}_{int(time.time())}",
            'timestamp': ahora.isoformat(),
            'activo_id': aid,
            'activo': nombre,
            'mercado': mercado,
            'direccion': direccion,
            'direccion_texto': texto,
            'sentimiento': pct,
            'probabilidad': prob,
            'confianza': confianza,
            'hora_generada': fmt_hora(ahora),
            'entrada': fmt_hora(entrada),
            'entrada_dt': entrada.isoformat(),
            'expiracion': fmt_hora(expiracion),
            'expiracion_dt': expiracion.isoformat(),
            'duracion': f"{DURACION_OPERACION} minutos",
            'segundos_hasta_entrada': int(segundos),
            'precio_entrada': self.precios.get(aid, 0),
            'verificado': False,
            'resultado': None
        }
    
    def mostrar_senal(self, s):
        mins = s['segundos_hasta_entrada'] // 60
        segs = s['segundos_hasta_entrada'] % 60
        
        print("\n" + "╔" + "═" * 58 + "╗")
        print(f"║  🔮 SEÑAL - {s['confianza']:<42} ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📍 {s['activo']:<52} ║")
        print(f"║  📊 {s['mercado']:<52} ║")
        print("╠" + "═" * 58 + "╣")
        
        if s['direccion'] == 'CALL':
            print(f"║     🟢🟢🟢  {s['direccion_texto']:<41}  ║")
        else:
            print(f"║     🔴🔴🔴  {s['direccion_texto']:<41}  ║")
        
        print("╠" + "═" * 58 + "╣")
        print(f"║  📈 Probabilidad: {s['probabilidad']:.0f}%{' ' * 36}║")
        print(f"║  👥 Sentimiento:  {s['sentimiento']:.0f}% traders{' ' * 29}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  ⏰ ENTRAR EN:    {mins}:{segs:02d} minutos{' ' * 29}║")
        print(f"║  🎯 HORA ENTRADA: {s['entrada']:<38} ║")
        print(f"║  ⏱️  EXPIRACIÓN:   {s['expiracion']:<38} ║")
        print(f"║  ⌛ DURACIÓN:     {s['duracion']:<38} ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  🕐 Hora RD:      {fmt_hora(hora_rd()):<38} ║")
        print("╚" + "═" * 58 + "╝")
    
    def mostrar_alerta(self, s):
        print("\n" + "🔔" * 25)
        print("╔" + "═" * 50 + "╗")
        print(f"║  ⚡ ¡¡¡ ENTRAR AHORA !!! ⚡{' ' * 22}║")
        print("╠" + "═" * 50 + "╣")
        print(f"║  📍 {s['activo']:<44}║")
        
        if s['direccion'] == 'CALL':
            print(f"║  🟢 COMPRA (CALL) - SUBE{' ' * 25}║")
        else:
            print(f"║  🔴 VENTA (PUT) - BAJA{' ' * 27}║")
        
        print(f"║  ⏱️  Expira: {s['expiracion']}{' ' * 33}║")
        print("╚" + "═" * 50 + "╝")
        print("🔔" * 25 + "\n")
    
    def mostrar_stats(self):
        stats = self.historial.estadisticas()
        print("\n┌" + "─" * 40 + "┐")
        print(f"│  📊 ESTADÍSTICAS{' ' * 23}│")
        print("├" + "─" * 40 + "┤")
        print(f"│  Total:     {stats['total']:<26}│")
        print(f"│  ✅ Ganadas: {stats['ganadas']:<25}│")
        print(f"│  ❌ Perdidas: {stats['perdidas']:<24}│")
        print(f"│  📈 Precisión: {stats['precision']:.1f}%{' ' * 21}│")
        print("└" + "─" * 40 + "┘")
    
    async def verificar_alertas(self):
        ahora = hora_rd()
        alertar = []
        
        for sid, s in list(self.senales_programadas.items()):
            entrada_dt = datetime.fromisoformat(s['entrada_dt'])
            restante = (entrada_dt - ahora).total_seconds()
            
            if restante <= 10:
                self.mostrar_alerta(s)
                s['precio_entrada'] = self.precios.get(s['activo_id'], 0)
                self.senales_activas[sid] = s
                alertar.append(sid)
            elif int(restante) % 60 == 0 and restante > 30:
                emoji = "🟢" if s['direccion'] == 'CALL' else "🔴"
                mins = int(restante) // 60
                print(f"   ⏳ {s['activo']}: {emoji} {s['direccion']} en {mins} min")
        
        for sid in alertar:
            del self.senales_programadas[sid]
    
    async def verificar_resultados(self):
        ahora = hora_rd()
        verificadas = []
        
        for sid, s in list(self.senales_activas.items()):
            exp = datetime.fromisoformat(s['expiracion_dt'])
            
            if ahora >= exp + timedelta(seconds=5):
                aid = s['activo_id']
                precio_actual = self.precios.get(aid, 0)
                precio_entrada = s.get('precio_entrada', 0)
                
                if precio_actual and precio_entrada:
                    subio = precio_actual > precio_entrada
                    if s['direccion'] == "CALL":
                        resultado = "GANADA" if subio else "PERDIDA"
                    else:
                        resultado = "GANADA" if not subio else "PERDIDA"
                    
                    self.historial.actualizar_resultado(sid, resultado)
                    
                    emoji = "✅" if resultado == "GANADA" else "❌"
                    print(f"\n{emoji} RESULTADO: {s['activo']} - {resultado}")
                    verificadas.append(sid)
        
        for sid in verificadas:
            del self.senales_activas[sid]
    
    async def procesar(self, msg):
        try:
            data = json.loads(msg)
            name = data.get('name', '')
            m = data.get('msg', {})
            
            if name == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                if 'blitz' in inst.lower():
                    return
                
                call_pct = value * 100
                put_pct = 100 - call_pct
                
                if call_pct >= 85 or put_pct >= 85:
                    ahora = time.time()
                    clave = f"{aid}_{inst}"
                    
                    if clave in self.ultima_senal:
                        if ahora - self.ultima_senal[clave] < 180:
                            return
                    
                    self.ultima_senal[clave] = ahora
                    
                    senal = self.generar_senal(aid, call_pct)
                    if senal and senal['probabilidad'] >= 85:
                        self.mostrar_senal(senal)
                        self.historial.agregar(senal)
                        self.senales_programadas[senal['id']] = senal
            
            elif name == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
                    
        except:
            pass
    
    async def ejecutar(self):
        if not await self.conectar():
            return
        
        ahora = hora_rd()
        
        print("\n" + "═" * 60)
        print("  🔮 BULLEX BOT SEGURO")
        print("═" * 60)
        print(f"  🕐 Hora RD: {fmt_hora(ahora)} (UTC-4)")
        print(f"  📅 {ahora.strftime('%d/%m/%Y')}")
        print("═" * 60)
        print(f"  ⏰ Anticipación: {MINUTOS_ANTICIPACION} minutos")
        print(f"  ⌛ Duración: {DURACION_OPERACION} minutos")
        print(f"  🎯 Solo señales >85%")
        print("═" * 60)
        print("  Ctrl+C para salir")
        print("═" * 60)
        
        self.mostrar_stats()
        ultimo_check = time.time()
        
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=1)
                    await self.procesar(msg)
                except asyncio.TimeoutError:
                    pass
                
                await self.verificar_alertas()
                
                if time.time() - ultimo_check >= 5:
                    await self.verificar_resultados()
                    ultimo_check = time.time()
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n⚠️ Conexión perdida. Reconectando...")
            if await self.conectar():
                await self.ejecutar()
        except KeyboardInterrupt:
            pass
        
        print("\n")
        self.mostrar_stats()
        
        if self.ws:
            await self.ws.close()
        print(f"\n👋 Bot cerrado")


def mostrar_instrucciones():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🔮 BULLEX BOT SEGURO - CONFIGURACIÓN              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Este bot NO hace login automático.                          ║
║  Necesitas copiar tu SSID del navegador.                     ║
║                                                              ║
║  📋 PASOS PARA OBTENER TU SSID:                              ║
║                                                              ║
║  1. Abre Chrome y ve a: https://trade.bull-ex.com            ║
║  2. Haz login con tu cuenta normalmente                      ║
║  3. Presiona F12 (abre DevTools)                             ║
║  4. Haz clic en "Application" (arriba)                       ║
║  5. En el panel izquierdo, busca "Cookies"                   ║
║  6. Expande y clic en "https://trade.bull-ex.com"            ║
║  7. Busca la fila que dice "ssid"                            ║
║  8. Haz doble clic en el "Value" y copia (Ctrl+C)            ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  Tu SSID expira cuando cierras sesión en el navegador    ║
║  ⚠️  Si el bot no conecta, obtén un nuevo SSID               ║
╚══════════════════════════════════════════════════════════════╝
""")


async def main():
    # Verificar si hay SSID configurado
    ssid = MI_SSID.strip()
    
    if not ssid:
        mostrar_instrucciones()
        print("\n❌ ERROR: No has configurado tu SSID")
        print("\n📝 Opciones:")
        print("   1. Edita este archivo y pega tu SSID en la línea MI_SSID = \"\"")
        print("   2. O ingresa tu SSID ahora:\n")
        
        ssid = input("🔑 Pega tu SSID aquí: ").strip()
        
        if not ssid:
            print("\n❌ No se ingresó SSID. Saliendo...")
            return
    
    bot = BotSeguro(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
