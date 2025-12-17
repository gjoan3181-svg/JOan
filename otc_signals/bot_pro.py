#!/usr/bin/env python3
"""
🎯 BULLEX BOT PRO - Análisis Técnico + Sentimiento
===================================================

Combina:
- Sentimiento de traders en tiempo real
- Análisis técnico (RSI, MACD, tendencia)
- Solo genera señales cuando AMBOS coinciden

Uso:
    python3 bot_pro.py
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
from collections import defaultdict
import os

# ============= CREDENCIALES =============
EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# ============= BASE DE DATOS DE ACTIVOS =============
# Formato: id -> (nombre, símbolo_tv, mercado, categoría)
ACTIVOS_DB = {
    # ========== FOREX ==========
    1: ("Euro / Dólar", "EURUSD", "FOREX", "Par Mayor"),
    2: ("Euro / Libra", "EURGBP", "FOREX", "Par Mayor"),
    3: ("Libra / Dólar", "GBPUSD", "FOREX", "Par Mayor"),
    4: ("Euro / Yen", "EURJPY", "FOREX", "Par Mayor"),
    5: ("Dólar / Yen", "USDJPY", "FOREX", "Par Mayor"),
    6: ("Aussie / Dólar", "AUDUSD", "FOREX", "Par Mayor"),
    7: ("Dólar / Canadiense", "USDCAD", "FOREX", "Par Mayor"),
    31: ("Aussie / Yen", "AUDJPY", "FOREX", "Par Cruzado"),
    32: ("Euro / Aussie", "EURAUD", "FOREX", "Par Cruzado"),
    33: ("Euro / Canadiense", "EURCAD", "FOREX", "Par Cruzado"),
    34: ("Libra / Yen", "GBPJPY", "FOREX", "Par Cruzado"),
    35: ("Libra / Canadiense", "GBPCAD", "FOREX", "Par Cruzado"),
    36: ("Libra / Aussie", "GBPAUD", "FOREX", "Par Cruzado"),
    37: ("Canadiense / Yen", "CADJPY", "FOREX", "Par Cruzado"),
    38: ("Kiwi / Dólar", "NZDUSD", "FOREX", "Par Mayor"),
    45: ("Kiwi / Yen", "NZDJPY", "FOREX", "Par Cruzado"),
    46: ("Franco / Yen", "CHFJPY", "FOREX", "Par Cruzado"),
    51: ("Euro / Franco", "EURCHF", "FOREX", "Par Cruzado"),
    52: ("Libra / Franco", "GBPCHF", "FOREX", "Par Cruzado"),
    53: ("Aussie / Franco", "AUDCHF", "FOREX", "Par Cruzado"),
    72: ("Dólar / Peso MX", "USDMXN", "FOREX", "Par Exótico"),
    74: ("Dólar / Corona NO", "USDNOK", "FOREX", "Par Exótico"),
    76: ("Dólar / Zloty", "USDPLN", "FOREX", "Par Exótico"),
    77: ("Dólar / Rublo", "USDRUB", "FOREX", "Par Exótico"),
    78: ("Euro / Kiwi", "EURNZD", "FOREX", "Par Cruzado"),
    79: ("Dólar / Yuan", "USDCNH", "FOREX", "Par Exótico"),
    80: ("Kiwi / Canadiense", "NZDCAD", "FOREX", "Par Cruzado"),
    81: ("Euro / Lira Turca", "EURTRY", "FOREX", "Par Exótico"),
    82: ("Dólar / Lira Turca", "USDTRY", "FOREX", "Par Exótico"),
    84: ("Dólar / Franco", "USDCHF", "FOREX", "Par Mayor"),
    85: ("Aussie / Canadiense", "AUDCAD", "FOREX", "Par Cruzado"),
    86: ("Aussie / Canadiense OTC", "AUDCAD", "OTC", "Forex OTC"),
    99: ("Dólar / Singapur", "USDSGD", "FOREX", "Par Exótico"),
    100: ("Dólar / Rand", "USDZAR", "FOREX", "Par Exótico"),
    102: ("Libra / Kiwi", "GBPNZD", "FOREX", "Par Cruzado"),
    103: ("Aussie / Kiwi", "AUDNZD", "FOREX", "Par Cruzado"),
    104: ("Dólar / Corona SE", "USDSEK", "FOREX", "Par Exótico"),
    105: ("Euro / Corona NO", "EURNOK", "FOREX", "Par Exótico"),
    106: ("Euro / Corona SE", "EURSEK", "FOREX", "Par Exótico"),
    107: ("Dólar / HK", "USDHKD", "FOREX", "Par Exótico"),
    108: ("Dólar / Zloty", "USDPLN", "FOREX", "Par Exótico"),
    168: ("Euro / Zloty", "EURPLN", "FOREX", "Par Exótico"),
    816: ("Canadiense / Franco", "CADCHF", "FOREX", "Par Cruzado"),
    817: ("Euro / HK", "EURHKD", "FOREX", "Par Exótico"),
    818: ("Euro / Singapur", "EURSGD", "FOREX", "Par Exótico"),
    893: ("Kiwi / Franco", "NZDCHF", "FOREX", "Par Cruzado"),
    
    # ========== COMMODITIES ==========
    867: ("Oro / Dólar", "XAUUSD", "COMMODITIES", "Metal Precioso"),
    892: ("Plata / Dólar", "XAGUSD", "COMMODITIES", "Metal Precioso"),
    
    # ========== CRYPTO TOP ==========
    212: ("Bitcoin", "BTCUSD", "CRYPTO", "Layer 1"),
    220: ("Ethereum", "ETHUSD", "CRYPTO", "Layer 1"),
    756: ("Litecoin", "LTCUSD", "CRYPTO", "Layer 1"),
    971: ("Dash", "DASHUSD", "CRYPTO", "Privacy"),
    1062: ("EOS", "EOSUSD", "CRYPTO", "Layer 1"),
    1470: ("Ripple", "XRPUSD", "CRYPTO", "Pagos"),
    1857: ("Binance Coin", "BNBUSD", "CRYPTO", "Exchange"),
    1858: ("Bitcoin Cash", "BCHUSD", "CRYPTO", "Layer 1"),
    1861: ("Chainlink", "LINKUSD", "CRYPTO", "Oracle"),
    1862: ("VeChain", "VETUSD", "CRYPTO", "Supply Chain"),
    1863: ("Polkadot", "DOTUSD", "CRYPTO", "Layer 0"),
    1864: ("Uniswap", "UNIUSD", "CRYPTO", "DeFi"),
    1865: ("FTX Token", "FTTUSD", "CRYPTO", "Exchange"),
    1866: ("Cardano", "ADAUSD", "CRYPTO", "Layer 1"),
    1867: ("Uniswap", "UNIUSD", "CRYPTO", "DeFi"),
    1868: ("Aave", "AAVEUSD", "CRYPTO", "DeFi"),
    1869: ("Maker", "MKRUSD", "CRYPTO", "DeFi"),
    1872: ("SushiSwap", "SUSHIUSD", "CRYPTO", "DeFi"),
    1873: ("Dogecoin", "DOGEUSD", "CRYPTO", "Memecoin"),
    1874: ("Shiba Inu", "SHIBUSD", "CRYPTO", "Memecoin"),
    1875: ("Stellar", "XLMUSD", "CRYPTO", "Pagos"),
    1876: ("Solana", "SOLUSD", "CRYPTO", "Layer 1"),
    1877: ("Terra Luna", "LUNAUSD", "CRYPTO", "Layer 1"),
    1878: ("Cosmos", "ATOMUSD", "CRYPTO", "Layer 0"),
    1879: ("Algorand", "ALGOUSD", "CRYPTO", "Layer 1"),
    1880: ("Tezos", "XTZUSD", "CRYPTO", "Layer 1"),
    1881: ("Avalanche", "AVAXUSD", "CRYPTO", "Layer 1"),
    1884: ("Cosmos", "ATOMUSD", "CRYPTO", "Layer 0"),
    1885: ("Polygon", "MATICUSD", "CRYPTO", "Layer 2"),
    1886: ("Algorand", "ALGOUSD", "CRYPTO", "Layer 1"),
    1896: ("Harmony", "ONEUSD", "CRYPTO", "Layer 1"),
    1897: ("Fantom", "FTMUSD", "CRYPTO", "Layer 1"),
    1898: ("Stellar", "XLMUSD", "CRYPTO", "Pagos"),
    1901: ("Tron", "TRXUSD", "CRYPTO", "Layer 1"),
    1910: ("Filecoin", "FILUSD", "CRYPTO", "Storage"),
    1912: ("The Sandbox", "SANDUSD", "CRYPTO", "Metaverso"),
    1916: ("Gala", "GALAUSD", "CRYPTO", "Gaming"),
    1917: ("ENS", "ENSUSD", "CRYPTO", "Infraestructura"),
    1921: ("Decentraland", "MANAUSD", "CRYPTO", "Metaverso"),
    1922: ("Axie Infinity", "AXSUSD", "CRYPTO", "Gaming"),
    1925: ("SushiSwap", "SUSHIUSD", "CRYPTO", "DeFi"),
    1926: ("Curve", "CRVUSD", "CRYPTO", "DeFi"),
    1928: ("Enjin", "ENJUSD", "CRYPTO", "Gaming"),
    1930: ("Compound", "COMPUSD", "CRYPTO", "DeFi"),
    1931: ("Yearn Finance", "YFIUSD", "CRYPTO", "DeFi"),
    1933: ("1inch", "1INCHUSD", "CRYPTO", "DeFi"),
    1935: ("Kava", "KAVAUSD", "CRYPTO", "DeFi"),
    1936: ("NEAR Protocol", "NEARUSD", "CRYPTO", "Layer 1"),
    1937: ("Fantom", "FTMUSD", "CRYPTO", "Layer 1"),
    1938: ("Theta", "THETAUSD", "CRYPTO", "Video"),
    1941: ("Tezos", "XTZUSD", "CRYPTO", "Layer 1"),
    1971: ("Lido DAO", "LDOUSD", "CRYPTO", "DeFi"),
    1972: ("ApeCoin", "APEUSD", "CRYPTO", "Metaverso"),
    1973: ("Pepe", "PEPEUSD", "CRYPTO", "Memecoin"),
    1974: ("Floki", "FLOKIUSD", "CRYPTO", "Memecoin"),
    1975: ("Optimism", "OPUSD", "CRYPTO", "Layer 2"),
    1976: ("Arbitrum", "ARBUSD", "CRYPTO", "Layer 2"),
    1977: ("Blur", "BLURUSD", "CRYPTO", "NFT"),
    1978: ("Injective", "INJUSD", "CRYPTO", "DeFi"),
    
    # ========== CRYPTO NUEVAS ==========
    2044: ("Arbitrum", "ARBUSD", "CRYPTO", "Layer 2"),
    2045: ("Injective", "INJUSD", "CRYPTO", "DeFi"),
    2046: ("Lido DAO", "LDOUSD", "CRYPTO", "DeFi"),
    2047: ("Blur", "BLURUSD", "CRYPTO", "NFT"),
    2048: ("Sui", "SUIUSD", "CRYPTO", "Layer 1"),
    2049: ("Render", "RNDRUSD", "CRYPTO", "GPU/AI"),
    2050: ("Worldcoin", "WLDUSD", "CRYPTO", "Identidad"),
    2051: ("Sei", "SEIUSD", "CRYPTO", "Layer 1"),
    2062: ("THORChain", "RUNEUSD", "CRYPTO", "DeFi"),
    2063: ("Bonk", "BONKUSD", "CRYPTO", "Memecoin"),
    2064: ("Jito", "JTOUSD", "CRYPTO", "DeFi"),
    2065: ("Celestia", "TIAUSD", "CRYPTO", "Modular"),
    2067: ("Ordinals", "ORDIUSD", "CRYPTO", "Bitcoin"),
    2069: ("Memecoin", "MEMEUSD", "CRYPTO", "Memecoin"),
    2070: ("Pyth Network", "PYTHUSD", "CRYPTO", "Oracle"),
    2073: ("Jupiter", "JUPUSD", "CRYPTO", "DeFi"),
    2074: ("Dymension", "DYMUSD", "CRYPTO", "Modular"),
    2076: ("dogwifhat", "WIFUSD", "CRYPTO", "Memecoin"),
    2078: ("Myro", "MYROUSD", "CRYPTO", "Memecoin"),
    2079: ("Starknet", "STRKUSD", "CRYPTO", "Layer 2"),
    2080: ("Pixels", "PIXELUSD", "CRYPTO", "Gaming"),
    2082: ("Dymension", "DYMUSD", "CRYPTO", "Modular"),
    2083: ("Pixels", "PIXELUSD", "CRYPTO", "Gaming"),
    2084: ("Portal", "PORTALUSD", "CRYPTO", "Gaming"),
    2085: ("Aevo", "AEVOUSD", "CRYPTO", "DeFi"),
    2086: ("Altlayer", "ALTUSD", "CRYPTO", "Layer 2"),
    2087: ("Memecoin", "MEMEUSD", "CRYPTO", "Memecoin"),
    2088: ("Pandora", "PANDORAUSD", "CRYPTO", "NFT"),
    2089: ("Aevo", "AEVOUSD", "CRYPTO", "DeFi"),
    2090: ("Ethena", "ENAUSD", "CRYPTO", "DeFi"),
    2091: ("Ether.fi", "ETHFIUSD", "CRYPTO", "DeFi"),
    2092: ("Wormhole", "WUSD", "CRYPTO", "Bridge"),
    2093: ("Tensor", "TNSRUSD", "CRYPTO", "NFT"),
    2096: ("Renzo", "REZUSD", "CRYPTO", "DeFi"),
    2097: ("Book of Meme", "BOMEUSD", "CRYPTO", "Memecoin"),
    2098: ("Bittensor", "TAOUSD", "CRYPTO", "AI"),
    2099: ("Floki", "FLOKIUSD", "CRYPTO", "Memecoin"),
    2100: ("Notcoin", "NOTUSD", "CRYPTO", "Gaming"),
    2101: ("io.net", "IOUSD", "CRYPTO", "GPU/AI"),
    2102: ("zkSync", "ZKUSD", "CRYPTO", "Layer 2"),
    2103: ("LayerZero", "ZROUSD", "CRYPTO", "Bridge"),
    2104: ("Lista DAO", "LISTAUSD", "CRYPTO", "DeFi"),
    2105: ("LayerZero", "ZROUSD", "CRYPTO", "Bridge"),
    2106: ("Blast", "BLASTUSD", "CRYPTO", "Layer 2"),
    2107: ("Brett", "BRETTUSD", "CRYPTO", "Memecoin"),
    2108: ("Dogs", "DOGSUSD", "CRYPTO", "Memecoin"),
    2109: ("Popcat", "POPCATUSD", "CRYPTO", "Memecoin"),
    2110: ("Sun", "SUNUSD", "CRYPTO", "DeFi"),
    2111: ("Wen", "WENUSD", "CRYPTO", "Memecoin"),
    2112: ("Neiro", "NEIROUSD", "CRYPTO", "Memecoin"),
    2113: ("Catizen", "CATIUSD", "CRYPTO", "Gaming"),
    2114: ("Hamster Kombat", "HMSTRUSD", "CRYPTO", "Gaming"),
    2115: ("EigenLayer", "EIGENUSD", "CRYPTO", "Restaking"),
    2116: ("Scroll", "SCRUSD", "CRYPTO", "Layer 2"),
    2117: ("Safe", "SAFEUSD", "CRYPTO", "Wallet"),
    2118: ("Aptos", "APTUSD", "CRYPTO", "Layer 1"),
    2119: ("Movement", "MOVEUSD", "CRYPTO", "Layer 2"),
    2120: ("Goatseus Maximus", "GOATUSD", "CRYPTO", "Memecoin"),
    2121: ("Act I", "ACTUSD", "CRYPTO", "AI"),
    2122: ("Peanut", "PNUTUSD", "CRYPTO", "Memecoin"),
    2123: ("CoW Protocol", "COWUSD", "CRYPTO", "DeFi"),
    2124: ("Moo Deng", "MOODENGUSD", "CRYPTO", "Memecoin"),
    2125: ("Chillguy", "CHILLGUYUSD", "CRYPTO", "Memecoin"),
    2126: ("Grass", "GRASSUSD", "CRYPTO", "DePIN"),
    2127: ("Banana Gun", "BANANUSD", "CRYPTO", "DeFi"),
    2128: ("Hyperliquid", "HYPEUSD", "CRYPTO", "DeFi"),
    2129: ("Magic Eden", "MEUSD", "CRYPTO", "NFT"),
    2130: ("Movement", "MOVEUSD", "CRYPTO", "Layer 2"),
    2131: ("Vana", "VANAUSD", "CRYPTO", "AI"),
    2132: ("Hyperliquid", "HYPEUSD", "CRYPTO", "DeFi"),
    2136: ("Usual", "USUALUSD", "CRYPTO", "DeFi"),
    2137: ("Pudgy Penguins", "PENGUUSD", "CRYPTO", "NFT"),
    2138: ("Orca", "ORCAUSD", "CRYPTO", "DeFi"),
    2139: ("Bio Protocol", "BIOUSD", "CRYPTO", "DeSci"),
    2140: ("Usual", "USUALUSD", "CRYPTO", "DeFi"),
    2141: ("ai16z", "AI16ZUSD", "CRYPTO", "AI Agent"),
    2142: ("Virtuals Protocol", "VIRTUALUSD", "CRYPTO", "AI Agent"),
    2143: ("Fartcoin", "FARTCOINUSD", "CRYPTO", "Memecoin"),
    2144: ("Griffain", "GRIFFAINUSD", "CRYPTO", "AI Agent"),
    2145: ("aixbt", "AIXBTUSD", "CRYPTO", "AI Agent"),
    2146: ("Arc", "ARCUSD", "CRYPTO", "AI"),
    2147: ("Swarms", "SWARMSUSD", "CRYPTO", "AI Agent"),
    2148: ("Zerebro", "ZEREBROUSD", "CRYPTO", "AI Agent"),
    2149: ("Cookie DAO", "COOKIEUSD", "CRYPTO", "AI"),
    2150: ("Eliza", "ELIZAUSD", "CRYPTO", "AI Agent"),
    2151: ("Trump", "TRUMPUSD", "CRYPTO", "Memecoin Político"),
    2152: ("Melania", "MELANIAUSD", "CRYPTO", "Memecoin Político"),
    2153: ("Vine", "VINEUSD", "CRYPTO", "Social"),
    2154: ("Anon", "ANONUSD", "CRYPTO", "Privacy"),
    2155: ("Solv Protocol", "SOLVUSD", "CRYPTO", "DeFi"),
    2156: ("Sonic", "SONICUSD", "CRYPTO", "Layer 1"),
    2157: ("Ondo Finance", "ONDOUSD", "CRYPTO", "RWA"),
    2158: ("Plume", "PLUMEUSD", "CRYPTO", "RWA"),
    2159: ("Story Protocol", "IPUSD", "CRYPTO", "IP/NFT"),
    2160: ("Layer", "LAYERUSD", "CRYPTO", "Layer 2"),
    2161: ("Test", "TSTUSD", "CRYPTO", "Test"),
    2162: ("Berachain", "BERAUSD", "CRYPTO", "Layer 1"),
    2164: ("Berachain", "BERAUSD", "CRYPTO", "Layer 1"),
    2165: ("Layer", "LAYERUSD", "CRYPTO", "Layer 2"),
    2166: ("Kaito", "KAITOUSD", "CRYPTO", "AI"),
    2167: ("Shell Protocol", "SHELLUSD", "CRYPTO", "DeFi"),
    2168: ("Anime", "ANIMEUSD", "CRYPTO", "Entertainment"),
    2181: ("StakeStone", "STOUSD", "CRYPTO", "DeFi"),
    2182: ("Nil", "NILUSD", "CRYPTO", "Infrastructure"),
    2183: ("Particle", "PARTIUSD", "CRYPTO", "AI"),
    2186: ("Bubblemaps", "BMTUSD", "CRYPTO", "Analytics"),
    2187: ("GoPlus", "GPSUSD", "CRYPTO", "Security"),
    2188: ("Shell Protocol", "SHELLUSD", "CRYPTO", "DeFi"),
    2200: ("Red", "REDUSD", "CRYPTO", "Social"),
    2201: ("Pi Network", "PIUSD", "CRYPTO", "Layer 1"),
    2202: ("Red", "REDUSD", "CRYPTO", "Social"),
    2265: ("Form", "FORMUSD", "CRYPTO", "AI"),
    2267: ("Mantra", "OMUSD", "CRYPTO", "RWA"),
    2270: ("Baby", "BABYUSD", "CRYPTO", "Memecoin"),
    2276: ("Alpaca Finance", "ALPACAUSD", "CRYPTO", "DeFi"),
    2277: ("Haedal", "HAEDALUSD", "CRYPTO", "DeFi"),
    2278: ("Sign", "SIGNUSD", "CRYPTO", "Identity"),
    2279: ("Milky Way", "MILKUSD", "CRYPTO", "DeFi"),
    2286: ("RFC", "RFCUSD", "CRYPTO", "Memecoin"),
    2287: ("Obol", "OBOLUSD", "CRYPTO", "Infrastructure"),
    2288: ("Gork", "GORKUSD", "CRYPTO", "Memecoin"),
    2289: ("Dark", "DARKUSD", "CRYPTO", "Memecoin"),
    2290: ("Launchcoin", "LAUNCHCOINUSD", "CRYPTO", "Launchpad"),
    2291: ("Kekius Maximus", "KEKIUSUSD", "CRYPTO", "Memecoin"),
    2293: ("Kilo", "KILOUSD", "CRYPTO", "DeFi"),
    2294: ("SkyAI", "SKYAIUSD", "CRYPTO", "AI"),
    2298: ("Superform", "SCFUSD", "CRYPTO", "DeFi"),
    2299: ("Kite AI", "KTAUSD", "CRYPTO", "AI"),
    2300: ("WalletConnect", "WCTUSD", "CRYPTO", "Infrastructure"),
    2301: ("JellyJelly", "JELLYUSD", "CRYPTO", "Memecoin"),
    2303: ("Init Capital", "INITUSD", "CRYPTO", "DeFi"),
    2304: ("Ondo Finance", "ONDOUSD", "CRYPTO", "RWA"),
    2311: ("Virtuals Protocol", "VIRTUALUSD", "CRYPTO", "AI Agent"),
    2312: ("Zora", "ZORAUSD", "CRYPTO", "NFT"),
    2313: ("Pump.fun", "PUMPUSD", "CRYPTO", "Launchpad"),
    2319: ("Haedal", "HAEDALUSD", "CRYPTO", "DeFi"),
    2320: ("Fuel", "FUELUSD", "CRYPTO", "Modular"),
    2321: ("Milky Way", "MILKUSD", "CRYPTO", "DeFi"),
    2322: ("RFC", "RFCUSD", "CRYPTO", "Memecoin"),
    2323: ("B2", "B2USD", "CRYPTO", "Bitcoin L2"),
    
    # ========== ACCIONES ==========
    1280: ("Amazon", "AMZN", "ACCIONES", "Tech USA"),
    1281: ("Microsoft", "MSFT", "ACCIONES", "Tech USA"),
    1285: ("Apple", "AAPL", "ACCIONES", "Tech USA"),
    1287: ("Apple", "AAPL", "ACCIONES", "Tech USA"),
    1345: ("Netflix", "NFLX", "ACCIONES", "Tech USA"),
    1346: ("Google", "GOOGL", "ACCIONES", "Tech USA"),
    1347: ("Meta (Facebook)", "META", "ACCIONES", "Tech USA"),
    1348: ("Tesla", "TSLA", "ACCIONES", "Tech USA"),
    1379: ("Microsoft", "MSFT", "ACCIONES", "Tech USA"),
    1380: ("Intel", "INTC", "ACCIONES", "Tech USA"),
    1381: ("Intel", "INTC", "ACCIONES", "Tech USA"),
    1382: ("Cisco", "CSCO", "ACCIONES", "Tech USA"),
    1383: ("NVIDIA", "NVDA", "ACCIONES", "Tech USA"),
    1473: ("Alibaba", "BABA", "ACCIONES", "Tech China"),
    1474: ("Baidu", "BIDU", "ACCIONES", "Tech China"),
    1475: ("IBM", "IBM", "ACCIONES", "Tech USA"),
    1476: ("Nike", "NKE", "ACCIONES", "Consumo"),
    1477: ("McDonald's", "MCD", "ACCIONES", "Consumo"),
    1478: ("Visa", "V", "ACCIONES", "Finanzas"),
    1481: ("Mastercard", "MA", "ACCIONES", "Finanzas"),
    1487: ("Boeing", "BA", "ACCIONES", "Industrial"),
    1520: ("Disney", "DIS", "ACCIONES", "Entertainment"),
    1536: ("Twitter/X", "X", "ACCIONES", "Tech USA"),
    1543: ("S&P 500", "SPX", "INDICES", "USA"),
}

# ============= COLORES Y FORMATO =============
class Colores:
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def get_activo_info(aid: int) -> tuple:
    """Obtiene información completa del activo."""
    if aid in ACTIVOS_DB:
        return ACTIVOS_DB[aid]
    return (f"Activo #{aid}", f"ID{aid}", "DESCONOCIDO", "Sin categoría")


def banner():
    """Muestra banner inicial."""
    c = Colores
    print(f"\n{c.CYAN}{'═' * 70}")
    print(f"  {c.BOLD}🎯 BULLEX BOT PRO - Análisis Técnico + Sentimiento{c.RESET}")
    print(f"  {c.CYAN}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 70}{c.RESET}")


def mostrar_senal(aid: int, inst: str, call_pct: float, datos_tecnicos: dict = None):
    """Muestra señal con información completa."""
    c = Colores
    hora = datetime.now().strftime("%H:%M:%S")
    put_pct = 100 - call_pct
    
    # Info del activo
    nombre, simbolo, mercado, categoria = get_activo_info(aid)
    
    # Tipo de instrumento
    if "blitz" in inst:
        tipo_inst = "⚡ BLITZ 5s"
    elif "turbo" in inst:
        tipo_inst = "🚀 TURBO 1m"
    elif "binary" in inst:
        tipo_inst = "📊 BINARY"
    else:
        tipo_inst = "📈 STANDARD"
    
    # Determinar dirección y fuerza
    if call_pct >= 95:
        emoji = "🟢" * 5
        direccion = "CALL ↑"
        nivel = "EXTREMO"
        color = c.VERDE
    elif call_pct >= 85:
        emoji = "🟢" * 4
        direccion = "CALL ↑"
        nivel = "FUERTE"
        color = c.VERDE
    elif call_pct >= 75:
        emoji = "🟢" * 3
        direccion = "CALL ↑"
        nivel = "BUENA"
        color = c.VERDE
    elif call_pct >= 65:
        emoji = "🟢" * 2
        direccion = "CALL ↑"
        nivel = "NORMAL"
        color = c.VERDE
    elif put_pct >= 95:
        emoji = "🔴" * 5
        direccion = "PUT ↓"
        nivel = "EXTREMO"
        color = c.ROJO
    elif put_pct >= 85:
        emoji = "🔴" * 4
        direccion = "PUT ↓"
        nivel = "FUERTE"
        color = c.ROJO
    elif put_pct >= 75:
        emoji = "🔴" * 3
        direccion = "PUT ↓"
        nivel = "BUENA"
        color = c.ROJO
    elif put_pct >= 65:
        emoji = "🔴" * 2
        direccion = "PUT ↓"
        nivel = "NORMAL"
        color = c.ROJO
    else:
        return  # No mostrar señales débiles
    
    # Porcentaje para mostrar
    pct = call_pct if call_pct > 50 else put_pct
    
    # Imprimir señal
    print(f"\n{color}{c.BOLD}{emoji} [{hora}] {nivel}{c.RESET}")
    print(f"   {c.BOLD}📍 {nombre}{c.RESET} ({simbolo})")
    print(f"   📊 Mercado: {mercado} | Categoría: {categoria}")
    print(f"   🎯 Señal: {color}{direccion} {pct:.0f}%{c.RESET}")
    print(f"   ⏱️  Instrumento: {tipo_inst}")
    
    # Análisis técnico si está disponible
    if datos_tecnicos:
        rsi = datos_tecnicos.get('rsi', 50)
        tendencia = datos_tecnicos.get('tendencia', 'NEUTRAL')
        
        rsi_color = c.ROJO if rsi > 70 else c.VERDE if rsi < 30 else c.AMARILLO
        print(f"   📈 RSI: {rsi_color}{rsi:.0f}{c.RESET} | Tendencia: {tendencia}")
        
        # Coincidencia
        sentimiento_dir = "CALL" if call_pct > 50 else "PUT"
        tecnico_dir = datos_tecnicos.get('direccion', 'NEUTRAL')
        
        if sentimiento_dir == tecnico_dir:
            print(f"   {c.VERDE}✅ CONFIRMADO: Sentimiento + Técnico coinciden{c.RESET}")
        else:
            print(f"   {c.AMARILLO}⚠️ DIVERGENCIA: Sentimiento vs Técnico{c.RESET}")


async def main():
    banner()
    c = Colores
    
    # ===== LOGIN =====
    print(f"\n{c.CYAN}🔐 Conectando a Bullex...{c.RESET}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URL,
                json={'identifier': EMAIL, 'password': PASSWORD},
                headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
                
                if resp.status != 200:
                    print(f"   {c.ROJO}❌ Error de login: {resp.status}{c.RESET}")
                    return
                    
                data = await resp.json()
                ssid = data.get('ssid', '')
                cookies = {c.key: c.value for c in resp.cookies.values()}
        
        print(f"   {c.VERDE}✅ Login exitoso{c.RESET}")
        
    except Exception as e:
        print(f"   {c.ROJO}❌ Error: {e}{c.RESET}")
        return
    
    # ===== WEBSOCKET =====
    print(f"{c.CYAN}🔌 Conectando WebSocket...{c.RESET}")
    try:
        cookie_str = '; '.join([f'{k}={v}' for k,v in cookies.items()])
        ws = await websockets.connect(
            WS_URL,
            origin='https://trade.bull-ex.com',
            extra_headers={'Cookie': cookie_str}
        )
        print(f"   {c.VERDE}✅ Conectado{c.RESET}")
        
    except Exception as e:
        print(f"   {c.ROJO}❌ Error: {e}{c.RESET}")
        return
    
    # ===== AUTH Y SUSCRIPCIÓN =====
    await ws.send(json.dumps({'name': 'ssid', 'msg': ssid}))
    await asyncio.sleep(1)
    await ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
    await ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
    
    # ===== INTERFAZ =====
    print(f"\n{c.CYAN}{'═' * 70}")
    print(f"  📡 SEÑALES EN TIEMPO REAL")
    print(f"{'═' * 70}{c.RESET}")
    print(f"  {c.AMARILLO}Mostrando solo señales con sentimiento > 65%")
    print(f"  🟢 CALL = Subida esperada    🔴 PUT = Bajada esperada")
    print(f"  ⚡ Blitz (5s)  🚀 Turbo (1m)  📊 Binary{c.RESET}")
    print(f"{c.CYAN}{'─' * 70}{c.RESET}")
    
    vistas = {}
    stats = {"total": 0, "call": 0, "put": 0, "extremos": 0}
    velas = defaultdict(list)  # Para análisis técnico
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
                    
                    # Solo señales significativas
                    if call_pct >= 65 or put_pct >= 65:
                        clave = f"{aid}_{inst}"
                        ahora = asyncio.get_event_loop().time()
                        
                        # Evitar spam
                        if clave not in vistas or ahora - vistas[clave] > 30:
                            vistas[clave] = ahora
                            
                            # Calcular análisis técnico simple
                            datos_tec = None
                            if aid in velas and len(velas[aid]) >= 5:
                                closes = [v['c'] for v in velas[aid][-14:]]
                                if len(closes) >= 5:
                                    # RSI simplificado
                                    gains = [closes[i] - closes[i-1] for i in range(1, len(closes)) if closes[i] > closes[i-1]]
                                    losses = [closes[i-1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i-1]]
                                    avg_gain = sum(gains) / len(gains) if gains else 0
                                    avg_loss = sum(losses) / len(losses) if losses else 0.0001
                                    rs = avg_gain / avg_loss
                                    rsi = 100 - (100 / (1 + rs))
                                    
                                    # Tendencia
                                    if closes[-1] > closes[0]:
                                        tendencia = "ALCISTA ↑"
                                        tec_dir = "CALL"
                                    elif closes[-1] < closes[0]:
                                        tendencia = "BAJISTA ↓"
                                        tec_dir = "PUT"
                                    else:
                                        tendencia = "LATERAL →"
                                        tec_dir = "NEUTRAL"
                                    
                                    datos_tec = {
                                        'rsi': rsi,
                                        'tendencia': tendencia,
                                        'direccion': tec_dir
                                    }
                            
                            mostrar_senal(aid, inst, call_pct, datos_tec)
                            
                            stats["total"] += 1
                            if call_pct > 50:
                                stats["call"] += 1
                            else:
                                stats["put"] += 1
                            if call_pct >= 95 or put_pct >= 95:
                                stats["extremos"] += 1
                
                elif name == 'candle-generated':
                    m = data.get('msg', {})
                    aid = m.get('active_id', 0)
                    velas[aid].append({
                        'o': m.get('open', 0),
                        'h': m.get('high', 0),
                        'l': m.get('low', 0),
                        'c': m.get('close', 0)
                    })
                    # Mantener solo últimas 20 velas
                    if len(velas[aid]) > 20:
                        velas[aid] = velas[aid][-20:]
                
                elif name == 'profile':
                    balance = data.get('msg', {}).get('balance', 0)
                    print(f"\n{c.AMARILLO}💰 Balance: ${balance:.2f}{c.RESET}\n")
                    
                elif name == 'balance':
                    m = data.get('msg', {})
                    balance = m.get('amount', m.get('current_balance', {}).get('amount', 0))
                    print(f"\n{c.AMARILLO}💰 Balance: ${balance:.2f}{c.RESET}\n")
                    
            except asyncio.TimeoutError:
                print(".", end="", flush=True)
                
            except websockets.exceptions.ConnectionClosed:
                print(f"\n{c.ROJO}⚠️ Conexión perdida{c.RESET}")
                break
                
    except KeyboardInterrupt:
        pass
    
    # ===== RESUMEN =====
    print(f"\n\n{c.CYAN}{'═' * 70}")
    print(f"  📊 RESUMEN DE SESIÓN")
    print(f"{'═' * 70}{c.RESET}")
    print(f"   Total señales: {stats['total']}")
    print(f"   🟢 CALL: {stats['call']}")
    print(f"   🔴 PUT: {stats['put']}")
    print(f"   ⭐ Extremos: {stats['extremos']}")
    if balance:
        print(f"   💰 Balance: ${balance:.2f}")
    print(f"{c.CYAN}{'═' * 70}{c.RESET}")
    
    await ws.close()
    print(f"\n{c.AMARILLO}👋 Bot cerrado{c.RESET}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
