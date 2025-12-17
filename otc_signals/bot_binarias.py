#!/usr/bin/env python3
"""
🎯 BULLEX BOT BINARIAS - Sistema Profesional de Señales
=======================================================

Características:
- Solo operaciones BINARIAS/DIGITALES (no Blitz)
- Análisis combinado: Sentimiento + Técnico
- Señales con tiempo exacto de entrada
- Historial completo con verificación de aciertos
- Estadísticas en tiempo real

Uso:
    python3 bot_binarias.py
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime, timedelta
from collections import defaultdict
import os
import time

# ============= CREDENCIALES =============
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# Archivo de historial
HISTORIAL_FILE = "/workspace/otc_signals/historial_senales.json"

# ============= BASE DE DATOS DE ACTIVOS =============
ACTIVOS_DB = {
    # FOREX PRINCIPALES
    1: ("EUR/USD", "FOREX", "Par Mayor"),
    2: ("EUR/GBP", "FOREX", "Par Mayor"),
    3: ("GBP/USD", "FOREX", "Par Mayor"),
    4: ("EUR/JPY", "FOREX", "Par Mayor"),
    5: ("USD/JPY", "FOREX", "Par Mayor"),
    6: ("AUD/USD", "FOREX", "Par Mayor"),
    7: ("USD/CAD", "FOREX", "Par Mayor"),
    31: ("AUD/JPY", "FOREX", "Par Cruzado"),
    32: ("EUR/AUD", "FOREX", "Par Cruzado"),
    33: ("EUR/CAD", "FOREX", "Par Cruzado"),
    34: ("GBP/JPY", "FOREX", "Par Cruzado"),
    35: ("GBP/CAD", "FOREX", "Par Cruzado"),
    36: ("GBP/AUD", "FOREX", "Par Cruzado"),
    37: ("CAD/JPY", "FOREX", "Par Cruzado"),
    38: ("NZD/USD", "FOREX", "Par Mayor"),
    45: ("NZD/JPY", "FOREX", "Par Cruzado"),
    46: ("CHF/JPY", "FOREX", "Par Cruzado"),
    51: ("EUR/CHF", "FOREX", "Par Cruzado"),
    52: ("GBP/CHF", "FOREX", "Par Cruzado"),
    53: ("AUD/CHF", "FOREX", "Par Cruzado"),
    72: ("USD/MXN", "FOREX", "Par Exótico"),
    76: ("USD/PLN", "FOREX", "Par Exótico"),
    77: ("USD/RUB", "FOREX", "Par Exótico"),
    78: ("EUR/NZD", "FOREX", "Par Cruzado"),
    79: ("USD/CNH", "FOREX", "Par Exótico"),
    80: ("NZD/CAD", "FOREX", "Par Cruzado"),
    81: ("EUR/TRY", "FOREX", "Par Exótico"),
    82: ("USD/TRY", "FOREX", "Par Exótico"),
    84: ("USD/CHF", "FOREX", "Par Mayor"),
    85: ("AUD/CAD", "FOREX", "Par Cruzado"),
    86: ("AUD/CAD OTC", "OTC", "Forex OTC"),
    99: ("USD/SGD", "FOREX", "Par Exótico"),
    100: ("USD/ZAR", "FOREX", "Par Exótico"),
    102: ("GBP/NZD", "FOREX", "Par Cruzado"),
    103: ("AUD/NZD", "FOREX", "Par Cruzado"),
    104: ("USD/SEK", "FOREX", "Par Exótico"),
    105: ("EUR/NOK", "FOREX", "Par Exótico"),
    106: ("EUR/SEK", "FOREX", "Par Exótico"),
    
    # COMMODITIES
    867: ("Oro (XAU)", "COMMODITIES", "Metal Precioso"),
    892: ("Plata (XAG)", "COMMODITIES", "Metal Precioso"),
    
    # CRYPTO TOP 50
    212: ("Bitcoin (BTC)", "CRYPTO", "Layer 1"),
    220: ("Ethereum (ETH)", "CRYPTO", "Layer 1"),
    756: ("Litecoin (LTC)", "CRYPTO", "Layer 1"),
    1470: ("Ripple (XRP)", "CRYPTO", "Pagos"),
    1857: ("Binance Coin (BNB)", "CRYPTO", "Exchange"),
    1858: ("Bitcoin Cash (BCH)", "CRYPTO", "Layer 1"),
    1861: ("Chainlink (LINK)", "CRYPTO", "Oracle"),
    1862: ("VeChain (VET)", "CRYPTO", "Supply Chain"),
    1863: ("Polkadot (DOT)", "CRYPTO", "Layer 0"),
    1864: ("Uniswap (UNI)", "CRYPTO", "DeFi"),
    1865: ("FTX Token (FTT)", "CRYPTO", "Exchange"),
    1866: ("Cardano (ADA)", "CRYPTO", "Layer 1"),
    1867: ("Uniswap (UNI)", "CRYPTO", "DeFi"),
    1868: ("Aave (AAVE)", "CRYPTO", "DeFi"),
    1869: ("Maker (MKR)", "CRYPTO", "DeFi"),
    1873: ("Dogecoin (DOGE)", "CRYPTO", "Memecoin"),
    1874: ("Shiba Inu (SHIB)", "CRYPTO", "Memecoin"),
    1875: ("Stellar (XLM)", "CRYPTO", "Pagos"),
    1876: ("Solana (SOL)", "CRYPTO", "Layer 1"),
    1877: ("Terra (LUNA)", "CRYPTO", "Layer 1"),
    1878: ("Cosmos (ATOM)", "CRYPTO", "Layer 0"),
    1879: ("Algorand (ALGO)", "CRYPTO", "Layer 1"),
    1880: ("Tezos (XTZ)", "CRYPTO", "Layer 1"),
    1881: ("Avalanche (AVAX)", "CRYPTO", "Layer 1"),
    1884: ("Cosmos (ATOM)", "CRYPTO", "Layer 0"),
    1885: ("Polygon (MATIC)", "CRYPTO", "Layer 2"),
    1886: ("Algorand (ALGO)", "CRYPTO", "Layer 1"),
    1897: ("Fantom (FTM)", "CRYPTO", "Layer 1"),
    1898: ("Stellar (XLM)", "CRYPTO", "Pagos"),
    1901: ("Tron (TRX)", "CRYPTO", "Layer 1"),
    1905: ("Hedera (HBAR)", "CRYPTO", "Enterprise"),
    1910: ("Filecoin (FIL)", "CRYPTO", "Storage"),
    1912: ("The Sandbox (SAND)", "CRYPTO", "Metaverso"),
    1916: ("Gala (GALA)", "CRYPTO", "Gaming"),
    1921: ("Decentraland (MANA)", "CRYPTO", "Metaverso"),
    1922: ("Axie Infinity (AXS)", "CRYPTO", "Gaming"),
    1926: ("Curve (CRV)", "CRYPTO", "DeFi"),
    1928: ("Enjin (ENJ)", "CRYPTO", "Gaming"),
    1930: ("Compound (COMP)", "CRYPTO", "DeFi"),
    1931: ("Yearn (YFI)", "CRYPTO", "DeFi"),
    1933: ("1inch (1INCH)", "CRYPTO", "DeFi"),
    1935: ("Kava (KAVA)", "CRYPTO", "DeFi"),
    1936: ("NEAR Protocol", "CRYPTO", "Layer 1"),
    1937: ("Fantom (FTM)", "CRYPTO", "Layer 1"),
    1938: ("Theta (THETA)", "CRYPTO", "Video"),
    1941: ("Tezos (XTZ)", "CRYPTO", "Layer 1"),
    1971: ("Lido DAO (LDO)", "CRYPTO", "DeFi"),
    1972: ("ApeCoin (APE)", "CRYPTO", "Metaverso"),
    1973: ("Pepe (PEPE)", "CRYPTO", "Memecoin"),
    1974: ("Floki (FLOKI)", "CRYPTO", "Memecoin"),
    1975: ("Optimism (OP)", "CRYPTO", "Layer 2"),
    1976: ("Arbitrum (ARB)", "CRYPTO", "Layer 2"),
    1978: ("Injective (INJ)", "CRYPTO", "DeFi"),
    
    # CRYPTO NUEVAS 2024-2025
    2044: ("Arbitrum (ARB)", "CRYPTO", "Layer 2"),
    2045: ("Injective (INJ)", "CRYPTO", "DeFi"),
    2046: ("Lido DAO (LDO)", "CRYPTO", "DeFi"),
    2047: ("Blur (BLUR)", "CRYPTO", "NFT"),
    2048: ("Sui (SUI)", "CRYPTO", "Layer 1"),
    2049: ("Render (RNDR)", "CRYPTO", "GPU/AI"),
    2050: ("Worldcoin (WLD)", "CRYPTO", "Identidad"),
    2051: ("Sei (SEI)", "CRYPTO", "Layer 1"),
    2062: ("THORChain (RUNE)", "CRYPTO", "DeFi"),
    2063: ("Bonk (BONK)", "CRYPTO", "Memecoin"),
    2065: ("Celestia (TIA)", "CRYPTO", "Modular"),
    2067: ("Ordinals (ORDI)", "CRYPTO", "Bitcoin"),
    2070: ("Pyth (PYTH)", "CRYPTO", "Oracle"),
    2073: ("Jupiter (JUP)", "CRYPTO", "DeFi"),
    2074: ("Dymension (DYM)", "CRYPTO", "Modular"),
    2076: ("dogwifhat (WIF)", "CRYPTO", "Memecoin"),
    2079: ("Starknet (STRK)", "CRYPTO", "Layer 2"),
    2080: ("Pixels (PIXEL)", "CRYPTO", "Gaming"),
    2082: ("Dymension (DYM)", "CRYPTO", "Modular"),
    2085: ("Aevo (AEVO)", "CRYPTO", "DeFi"),
    2086: ("Altlayer (ALT)", "CRYPTO", "Layer 2"),
    2090: ("Ethena (ENA)", "CRYPTO", "DeFi"),
    2091: ("Ether.fi (ETHFI)", "CRYPTO", "DeFi"),
    2092: ("Wormhole (W)", "CRYPTO", "Bridge"),
    2097: ("Book of Meme (BOME)", "CRYPTO", "Memecoin"),
    2098: ("Bittensor (TAO)", "CRYPTO", "AI"),
    2099: ("Floki (FLOKI)", "CRYPTO", "Memecoin"),
    2100: ("Notcoin (NOT)", "CRYPTO", "Gaming"),
    2101: ("io.net (IO)", "CRYPTO", "GPU/AI"),
    2102: ("zkSync (ZK)", "CRYPTO", "Layer 2"),
    2103: ("LayerZero (ZRO)", "CRYPTO", "Bridge"),
    2105: ("LayerZero (ZRO)", "CRYPTO", "Bridge"),
    2106: ("Blast (BLAST)", "CRYPTO", "Layer 2"),
    2107: ("Brett (BRETT)", "CRYPTO", "Memecoin"),
    2108: ("Dogs (DOGS)", "CRYPTO", "Memecoin"),
    2109: ("Popcat (POPCAT)", "CRYPTO", "Memecoin"),
    2111: ("Wen (WEN)", "CRYPTO", "Memecoin"),
    2112: ("Neiro (NEIRO)", "CRYPTO", "Memecoin"),
    2113: ("Catizen (CATI)", "CRYPTO", "Gaming"),
    2114: ("Hamster (HMSTR)", "CRYPTO", "Gaming"),
    2115: ("EigenLayer (EIGEN)", "CRYPTO", "Restaking"),
    2116: ("Scroll (SCR)", "CRYPTO", "Layer 2"),
    2117: ("Safe (SAFE)", "CRYPTO", "Wallet"),
    2118: ("Aptos (APT)", "CRYPTO", "Layer 1"),
    2119: ("Movement (MOVE)", "CRYPTO", "Layer 2"),
    2120: ("Goatseus (GOAT)", "CRYPTO", "Memecoin"),
    2121: ("Act I (ACT)", "CRYPTO", "AI"),
    2122: ("Peanut (PNUT)", "CRYPTO", "Memecoin"),
    2123: ("CoW Protocol (COW)", "CRYPTO", "DeFi"),
    2124: ("Moo Deng (MOODENG)", "CRYPTO", "Memecoin"),
    2125: ("Chillguy (CHILLGUY)", "CRYPTO", "Memecoin"),
    2126: ("Grass (GRASS)", "CRYPTO", "DePIN"),
    2127: ("Banana Gun (BANANA)", "CRYPTO", "DeFi"),
    2128: ("Hyperliquid (HYPE)", "CRYPTO", "DeFi"),
    2129: ("Magic Eden (ME)", "CRYPTO", "NFT"),
    2130: ("Movement (MOVE)", "CRYPTO", "Layer 2"),
    2131: ("Vana (VANA)", "CRYPTO", "AI"),
    2132: ("Hyperliquid (HYPE)", "CRYPTO", "DeFi"),
    2136: ("Usual (USUAL)", "CRYPTO", "DeFi"),
    2137: ("Pudgy Penguins (PENGU)", "CRYPTO", "NFT"),
    2138: ("Orca (ORCA)", "CRYPTO", "DeFi"),
    2140: ("Usual (USUAL)", "CRYPTO", "DeFi"),
    2141: ("ai16z (AI16Z)", "CRYPTO", "AI Agent"),
    2142: ("Virtuals (VIRTUAL)", "CRYPTO", "AI Agent"),
    2143: ("Fartcoin (FARTCOIN)", "CRYPTO", "Memecoin"),
    2144: ("Griffain (GRIFFAIN)", "CRYPTO", "AI Agent"),
    2145: ("aixbt (AIXBT)", "CRYPTO", "AI Agent"),
    2146: ("Arc (ARC)", "CRYPTO", "AI"),
    2147: ("Swarms (SWARMS)", "CRYPTO", "AI Agent"),
    2148: ("Zerebro (ZEREBRO)", "CRYPTO", "AI Agent"),
    2149: ("Cookie DAO (COOKIE)", "CRYPTO", "AI"),
    2150: ("Eliza (ELIZA)", "CRYPTO", "AI Agent"),
    2151: ("Trump (TRUMP)", "CRYPTO", "Memecoin Político"),
    2152: ("Melania (MELANIA)", "CRYPTO", "Memecoin Político"),
    2153: ("Vine (VINE)", "CRYPTO", "Social"),
    2155: ("Solv (SOLV)", "CRYPTO", "DeFi"),
    2156: ("Sonic (SONIC)", "CRYPTO", "Layer 1"),
    2157: ("Ondo (ONDO)", "CRYPTO", "RWA"),
    2158: ("Plume (PLUME)", "CRYPTO", "RWA"),
    2159: ("Story Protocol (IP)", "CRYPTO", "IP/NFT"),
    2161: ("Test (TST)", "CRYPTO", "Test"),
    2162: ("Berachain (BERA)", "CRYPTO", "Layer 1"),
    2164: ("Berachain (BERA)", "CRYPTO", "Layer 1"),
    2166: ("Kaito (KAITO)", "CRYPTO", "AI"),
    2168: ("Anime (ANIME)", "CRYPTO", "Entertainment"),
    2181: ("StakeStone (STO)", "CRYPTO", "DeFi"),
    2182: ("Nil (NIL)", "CRYPTO", "Infra"),
    2183: ("Particle (PARTI)", "CRYPTO", "AI"),
    2186: ("Bubblemaps (BMT)", "CRYPTO", "Analytics"),
    2187: ("GoPlus (GPS)", "CRYPTO", "Security"),
    2201: ("Pi Network (PI)", "CRYPTO", "Layer 1"),
    2265: ("Form (FORM)", "CRYPTO", "AI"),
    2267: ("Mantra (OM)", "CRYPTO", "RWA"),
    2270: ("Baby (BABY)", "CRYPTO", "Memecoin"),
    2276: ("Alpaca Finance (ALPACA)", "CRYPTO", "DeFi"),
    2277: ("Haedal (HAEDAL)", "CRYPTO", "DeFi"),
    2279: ("Milky Way (MILK)", "CRYPTO", "DeFi"),
    2286: ("RFC (RFC)", "CRYPTO", "Memecoin"),
    2287: ("Obol (OBOL)", "CRYPTO", "Infra"),
    2288: ("Gork (GORK)", "CRYPTO", "Memecoin"),
    2289: ("Dark (DARK)", "CRYPTO", "Memecoin"),
    2290: ("Launchcoin (LAUNCH)", "CRYPTO", "Launchpad"),
    2291: ("Kekius (KEKIUS)", "CRYPTO", "Memecoin"),
    2298: ("Superform (SCF)", "CRYPTO", "DeFi"),
    2299: ("Kite AI (KTA)", "CRYPTO", "AI"),
    2300: ("WalletConnect (WCT)", "CRYPTO", "Infra"),
    2301: ("JellyJelly (JELLY)", "CRYPTO", "Memecoin"),
    2303: ("Init Capital (INIT)", "CRYPTO", "DeFi"),
    2304: ("Ondo (ONDO)", "CRYPTO", "RWA"),
    2311: ("Virtuals (VIRTUAL)", "CRYPTO", "AI Agent"),
    2312: ("Zora (ZORA)", "CRYPTO", "NFT"),
    2313: ("Pump.fun (PUMP)", "CRYPTO", "Launchpad"),
    2319: ("Haedal (HAEDAL)", "CRYPTO", "DeFi"),
    2320: ("Fuel (FUEL)", "CRYPTO", "Modular"),
    2321: ("Milky Way (MILK)", "CRYPTO", "DeFi"),
    2322: ("RFC (RFC)", "CRYPTO", "Memecoin"),
    2323: ("B2 (B2)", "CRYPTO", "Bitcoin L2"),
    
    # ACCIONES
    1280: ("Amazon (AMZN)", "ACCIONES", "Tech USA"),
    1346: ("Google (GOOGL)", "ACCIONES", "Tech USA"),
    1347: ("Meta (META)", "ACCIONES", "Tech USA"),
    1348: ("Tesla (TSLA)", "ACCIONES", "Tech USA"),
    1379: ("Microsoft (MSFT)", "ACCIONES", "Tech USA"),
    1380: ("Intel (INTC)", "ACCIONES", "Tech USA"),
    1381: ("Intel (INTC)", "ACCIONES", "Tech USA"),
    1383: ("NVIDIA (NVDA)", "ACCIONES", "Tech USA"),
    1543: ("S&P 500 (SPX)", "INDICES", "USA"),
}


class HistorialManager:
    """Gestiona el historial de señales y estadísticas."""
    
    def __init__(self, archivo: str):
        self.archivo = archivo
        self.senales = []
        self.cargar()
    
    def cargar(self):
        """Carga historial desde archivo."""
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r') as f:
                    data = json.load(f)
                    self.senales = data.get('senales', [])
        except:
            self.senales = []
    
    def guardar(self):
        """Guarda historial a archivo."""
        try:
            with open(self.archivo, 'w') as f:
                json.dump({
                    'senales': self.senales,
                    'ultima_actualizacion': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
    def agregar_senal(self, senal: dict):
        """Agrega nueva señal al historial."""
        self.senales.append(senal)
        self.guardar()
    
    def actualizar_resultado(self, senal_id: str, resultado: str, precio_cierre: float):
        """Actualiza el resultado de una señal."""
        for s in self.senales:
            if s.get('id') == senal_id:
                s['resultado'] = resultado
                s['precio_cierre'] = precio_cierre
                s['verificado'] = True
                break
        self.guardar()
    
    def obtener_estadisticas(self) -> dict:
        """Calcula estadísticas de señales."""
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        aciertos = [s for s in verificadas if s.get('resultado') == 'GANADA']
        
        return {
            'total_senales': total,
            'verificadas': len(verificadas),
            'aciertos': len(aciertos),
            'fallos': len(verificadas) - len(aciertos),
            'precision': (len(aciertos) / len(verificadas) * 100) if verificadas else 0,
            'pendientes': total - len(verificadas)
        }
    
    def obtener_ultimas(self, n: int = 10) -> list:
        """Obtiene las últimas n señales."""
        return self.senales[-n:] if self.senales else []


class BotBinarias:
    """Bot de señales para opciones binarias."""
    
    def __init__(self):
        self.ws = None
        self.ssid = ""
        self.cookies = {}
        self.historial = HistorialManager(HISTORIAL_FILE)
        self.precios = {}  # aid -> precio actual
        self.velas = defaultdict(list)  # aid -> lista de velas
        self.sentimiento = {}  # aid -> {call_pct, timestamp}
        self.senales_pendientes = {}  # id -> senal (para verificar)
        self.balance = 0
    
    def get_activo_info(self, aid: int) -> tuple:
        """Obtiene info del activo."""
        if aid in ACTIVOS_DB:
            return ACTIVOS_DB[aid]
        return None  # Retorna None si no es conocido
    
    async def login(self) -> bool:
        """Inicia sesión."""
        print("\n🔐 Conectando a Bullex...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(LOGIN_URL,
                    json={'identifier': EMAIL, 'password': PASSWORD},
                    headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
                    
                    if resp.status != 200:
                        print(f"   ❌ Error: {resp.status}")
                        return False
                    
                    data = await resp.json()
                    self.ssid = data.get('ssid', '')
                    self.cookies = {c.key: c.value for c in resp.cookies.values()}
            
            print("   ✅ Login exitoso")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def conectar_ws(self) -> bool:
        """Conecta al WebSocket."""
        print("🔌 Conectando WebSocket...")
        try:
            cookie_str = '; '.join([f'{k}={v}' for k,v in self.cookies.items()])
            self.ws = await websockets.connect(
                WS_URL,
                origin='https://trade.bull-ex.com',
                extra_headers={'Cookie': cookie_str}
            )
            
            # Auth
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            
            # Suscripciones
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            
            print("   ✅ Conectado y suscrito")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def calcular_probabilidad(self, aid: int, sentimiento_pct: float) -> tuple:
        """
        Calcula probabilidad combinando sentimiento + análisis técnico.
        Retorna (probabilidad, confianza, razon)
        """
        # Base: sentimiento
        base_prob = sentimiento_pct if sentimiento_pct > 50 else (100 - sentimiento_pct)
        direccion = "CALL" if sentimiento_pct > 50 else "PUT"
        
        razones = []
        ajuste = 0
        
        # Análisis técnico si tenemos velas
        if aid in self.velas and len(self.velas[aid]) >= 5:
            closes = [v['c'] for v in self.velas[aid][-14:]]
            
            # RSI
            if len(closes) >= 5:
                gains = [closes[i] - closes[i-1] for i in range(1, len(closes)) if closes[i] > closes[i-1]]
                losses = [closes[i-1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i-1]]
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0.0001
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                # RSI confirma dirección
                if direccion == "CALL" and rsi < 30:
                    ajuste += 10
                    razones.append(f"RSI={rsi:.0f} sobreventa")
                elif direccion == "PUT" and rsi > 70:
                    ajuste += 10
                    razones.append(f"RSI={rsi:.0f} sobrecompra")
                elif direccion == "CALL" and rsi > 70:
                    ajuste -= 15
                    razones.append(f"⚠️ RSI={rsi:.0f} contra tendencia")
                elif direccion == "PUT" and rsi < 30:
                    ajuste -= 15
                    razones.append(f"⚠️ RSI={rsi:.0f} contra tendencia")
            
            # Tendencia
            if len(closes) >= 3:
                tendencia_corta = closes[-1] - closes[-3]
                if direccion == "CALL" and tendencia_corta > 0:
                    ajuste += 5
                    razones.append("Tendencia alcista")
                elif direccion == "PUT" and tendencia_corta < 0:
                    ajuste += 5
                    razones.append("Tendencia bajista")
                elif direccion == "CALL" and tendencia_corta < 0:
                    ajuste -= 10
                    razones.append("⚠️ Contra tendencia")
                elif direccion == "PUT" and tendencia_corta > 0:
                    ajuste -= 10
                    razones.append("⚠️ Contra tendencia")
        
        # Sentimiento extremo es más confiable
        if base_prob >= 95:
            ajuste += 5
            razones.append("Sentimiento extremo")
        elif base_prob >= 85:
            ajuste += 3
            razones.append("Sentimiento fuerte")
        
        # Calcular probabilidad final
        prob_final = min(99, max(50, base_prob + ajuste))
        
        # Nivel de confianza
        if prob_final >= 85:
            confianza = "ALTA"
        elif prob_final >= 75:
            confianza = "MEDIA"
        else:
            confianza = "BAJA"
        
        razon = " | ".join(razones) if razones else "Solo sentimiento"
        
        return prob_final, confianza, razon
    
    def generar_senal(self, aid: int, inst: str, call_pct: float) -> dict:
        """Genera una señal completa."""
        info = self.get_activo_info(aid)
        if info is None:
            return None  # No generar señal para activos desconocidos
        nombre, mercado, categoria = info
        
        # Calcular probabilidad
        prob, confianza, razon = self.calcular_probabilidad(aid, call_pct)
        
        # Dirección
        direccion = "CALL ↑ (SUBE)" if call_pct > 50 else "PUT ↓ (BAJA)"
        
        # Tiempo de entrada (próximo minuto completo + 10 segundos)
        ahora = datetime.now()
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=1, seconds=10)
        
        # Precio actual
        precio = self.precios.get(aid, 0)
        
        # ID único
        senal_id = f"{aid}_{int(time.time())}"
        
        senal = {
            'id': senal_id,
            'timestamp': ahora.isoformat(),
            'activo_id': aid,
            'activo_nombre': nombre,
            'mercado': mercado,
            'categoria': categoria,
            'instrumento': inst,
            'direccion': "CALL" if call_pct > 50 else "PUT",
            'direccion_texto': direccion,
            'sentimiento_pct': call_pct if call_pct > 50 else (100 - call_pct),
            'probabilidad': prob,
            'confianza': confianza,
            'razon': razon,
            'entrada': entrada.strftime("%H:%M:%S"),
            'duracion': "2-3 minutos",
            'precio_entrada': precio,
            'verificado': False,
            'resultado': None
        }
        
        return senal
    
    def mostrar_senal(self, senal: dict):
        """Muestra señal en consola."""
        print("\n" + "=" * 70)
        print(f"🎯 NUEVA SEÑAL - {senal['confianza']} CONFIANZA")
        print("=" * 70)
        print(f"📍 Activo: {senal['activo_nombre']}")
        print(f"📊 Mercado: {senal['mercado']} | {senal['categoria']}")
        print(f"")
        
        if "CALL" in senal['direccion']:
            print(f"   🟢🟢🟢 {senal['direccion_texto']} 🟢🟢🟢")
        else:
            print(f"   🔴🔴🔴 {senal['direccion_texto']} 🔴🔴🔴")
        
        print(f"")
        print(f"📈 Probabilidad: {senal['probabilidad']:.0f}%")
        print(f"👥 Sentimiento: {senal['sentimiento_pct']:.0f}% traders")
        print(f"⏰ Entrada: {senal['entrada']}")
        print(f"⏱️  Duración: {senal['duracion']}")
        
        if senal['precio_entrada']:
            print(f"💰 Precio: {senal['precio_entrada']:.6f}")
        
        print(f"")
        print(f"📝 Análisis: {senal['razon']}")
        print("=" * 70)
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del historial."""
        stats = self.historial.obtener_estadisticas()
        
        print("\n" + "─" * 70)
        print("📊 ESTADÍSTICAS DE SEÑALES")
        print("─" * 70)
        print(f"   Total señales: {stats['total_senales']}")
        print(f"   Verificadas: {stats['verificadas']}")
        print(f"   ✅ Aciertos: {stats['aciertos']}")
        print(f"   ❌ Fallos: {stats['fallos']}")
        print(f"   📈 Precisión: {stats['precision']:.1f}%")
        print(f"   ⏳ Pendientes: {stats['pendientes']}")
        print("─" * 70)
    
    async def verificar_senales_pendientes(self):
        """Verifica señales pasadas contra precio actual."""
        ahora = time.time()
        verificadas = []
        
        for senal_id, senal in list(self.senales_pendientes.items()):
            # Verificar después de 3 minutos
            tiempo_senal = datetime.fromisoformat(senal['timestamp']).timestamp()
            if ahora - tiempo_senal >= 180:  # 3 minutos
                aid = senal['activo_id']
                precio_actual = self.precios.get(aid, 0)
                precio_entrada = senal.get('precio_entrada', 0)
                
                if precio_actual and precio_entrada:
                    # Determinar resultado
                    subio = precio_actual > precio_entrada
                    
                    if senal['direccion'] == "CALL":
                        resultado = "GANADA" if subio else "PERDIDA"
                    else:
                        resultado = "GANADA" if not subio else "PERDIDA"
                    
                    # Actualizar historial
                    self.historial.actualizar_resultado(senal_id, resultado, precio_actual)
                    
                    # Mostrar resultado
                    emoji = "✅" if resultado == "GANADA" else "❌"
                    print(f"\n{emoji} Resultado {senal['activo_nombre']}: {resultado}")
                    print(f"   Entrada: {precio_entrada:.6f} → Cierre: {precio_actual:.6f}")
                    
                    verificadas.append(senal_id)
        
        # Eliminar verificadas
        for sid in verificadas:
            del self.senales_pendientes[sid]
    
    async def procesar_mensaje(self, msg: str):
        """Procesa mensaje del WebSocket."""
        try:
            data = json.loads(msg)
            name = data.get('name', '')
            m = data.get('msg', {})
            
            if name == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                # Filtrar: solo binary, turbo, digital (NO blitz)
                if 'blitz' in inst.lower():
                    return
                
                # Solo binary-option, turbo-option, digital-option
                if not any(x in inst.lower() for x in ['binary', 'turbo', 'digital', 'fx-option']):
                    return
                
                call_pct = value * 100
                put_pct = 100 - call_pct
                
                # Solo señales con >75% de consenso
                if call_pct >= 75 or put_pct >= 75:
                    # Evitar spam - misma señal cada 60 segundos
                    ahora = time.time()
                    clave = f"{aid}_{inst}"
                    
                    if clave in self.sentimiento:
                        ultimo = self.sentimiento[clave].get('timestamp', 0)
                        if ahora - ultimo < 120:  # 2 minutos entre señales del mismo activo
                            return
                    
                    self.sentimiento[clave] = {
                        'call_pct': call_pct,
                        'timestamp': ahora
                    }
                    
                    # Generar señal (solo para activos conocidos)
                    senal = self.generar_senal(aid, inst, call_pct)
                    
                    # Solo mostrar si es activo conocido y probabilidad >= 75%
                    if senal and senal['probabilidad'] >= 75:
                        self.mostrar_senal(senal)
                        
                        # Guardar en historial
                        self.historial.agregar_senal(senal)
                        
                        # Agregar a pendientes para verificar
                        self.senales_pendientes[senal['id']] = senal
            
            elif name == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                
                if close:
                    self.precios[aid] = close
                    self.velas[aid].append({
                        'o': m.get('open', 0),
                        'h': m.get('high', 0),
                        'l': m.get('low', 0),
                        'c': close
                    })
                    if len(self.velas[aid]) > 20:
                        self.velas[aid] = self.velas[aid][-20:]
            
            elif name == 'profile':
                self.balance = m.get('balance', 0)
                print(f"\n💰 Balance: ${self.balance:.2f}")
            
            elif name == 'balance':
                self.balance = m.get('amount', m.get('current_balance', {}).get('amount', 0))
                print(f"\n💰 Balance: ${self.balance:.2f}")
                
        except Exception as e:
            pass
    
    async def ejecutar(self):
        """Ejecuta el bot."""
        if not await self.login():
            return
        
        if not await self.conectar_ws():
            return
        
        # Interfaz
        print("\n" + "═" * 70)
        print("  🎯 BOT BINARIAS - SEÑALES PROFESIONALES")
        print("═" * 70)
        print("  📊 Operaciones: BINARIAS / DIGITALES (2-3 minutos)")
        print("  🎯 Umbral: Solo señales con >75% consenso y >70% probabilidad")
        print("  📝 Historial: Se guarda automáticamente")
        print("  ⏱️  Verificación: Resultados cada 3 minutos")
        print("═" * 70)
        print("  Presiona Ctrl+C para ver estadísticas y salir")
        print("═" * 70)
        
        # Mostrar estadísticas iniciales
        self.mostrar_estadisticas()
        
        ultimo_check = time.time()
        
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    await self.procesar_mensaje(msg)
                    
                    # Verificar señales pendientes cada 30 segundos
                    if time.time() - ultimo_check >= 30:
                        await self.verificar_senales_pendientes()
                        ultimo_check = time.time()
                    
                except asyncio.TimeoutError:
                    # Verificar pendientes en timeout también
                    if time.time() - ultimo_check >= 30:
                        await self.verificar_senales_pendientes()
                        ultimo_check = time.time()
                    print(".", end="", flush=True)
                    
                except websockets.exceptions.ConnectionClosed:
                    print("\n⚠️ Conexión perdida. Reconectando...")
                    if await self.login() and await self.conectar_ws():
                        continue
                    break
                    
        except KeyboardInterrupt:
            pass
        
        # Mostrar estadísticas finales
        print("\n")
        self.mostrar_estadisticas()
        
        # Mostrar últimas señales
        ultimas = self.historial.obtener_ultimas(5)
        if ultimas:
            print("\n📋 ÚLTIMAS SEÑALES:")
            print("─" * 70)
            for s in ultimas:
                emoji = "✅" if s.get('resultado') == "GANADA" else "❌" if s.get('resultado') == "PERDIDA" else "⏳"
                dir_emoji = "🟢" if s['direccion'] == "CALL" else "🔴"
                print(f"  {emoji} {s['activo_nombre']} | {dir_emoji} {s['direccion']} | {s['probabilidad']:.0f}% | {s.get('resultado', 'Pendiente')}")
        
        await self.ws.close()
        print("\n👋 Bot cerrado")


async def main():
    bot = BotBinarias()
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
