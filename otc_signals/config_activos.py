#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   📋 CONFIGURACIÓN DE ACTIVOS PERMITIDOS
══════════════════════════════════════════════════════════════════════════════════

   Edita este archivo para seleccionar qué activos quieres recibir señales.
   
   👉 Cambia "activo": True  a  "activo": False  para deshabilitar un activo
   👉 O simplemente elimina la línea del activo que no quieras

══════════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                    🎮 ACTIVOS HABILITADOS
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        FOREX OTC (Pares de divisas)
    # ════════════════════════════════════════════════════════════════════════════
    # Los pares Forex OTC suelen ser más estables y predecibles
    
    1:   {"nombre": "EUR/USD",     "mercado": "FOREX",  "simbolo": "EUR/USD (OTC)",  "activo": True},
    2:   {"nombre": "EUR/GBP",     "mercado": "FOREX",  "simbolo": "EUR/GBP (OTC)",  "activo": True},
    3:   {"nombre": "GBP/USD",     "mercado": "FOREX",  "simbolo": "GBP/USD (OTC)",  "activo": True},
    4:   {"nombre": "EUR/JPY",     "mercado": "FOREX",  "simbolo": "EUR/JPY (OTC)",  "activo": True},
    5:   {"nombre": "USD/JPY",     "mercado": "FOREX",  "simbolo": "USD/JPY (OTC)",  "activo": True},
    6:   {"nombre": "AUD/USD",     "mercado": "FOREX",  "simbolo": "AUD/USD (OTC)",  "activo": True},
    7:   {"nombre": "USD/CAD",     "mercado": "FOREX",  "simbolo": "USD/CAD (OTC)",  "activo": True},
    31:  {"nombre": "AUD/JPY",     "mercado": "FOREX",  "simbolo": "AUD/JPY (OTC)",  "activo": False},
    32:  {"nombre": "EUR/AUD",     "mercado": "FOREX",  "simbolo": "EUR/AUD (OTC)",  "activo": False},
    33:  {"nombre": "EUR/CAD",     "mercado": "FOREX",  "simbolo": "EUR/CAD (OTC)",  "activo": False},
    34:  {"nombre": "GBP/JPY",     "mercado": "FOREX",  "simbolo": "GBP/JPY (OTC)",  "activo": False},
    35:  {"nombre": "GBP/CAD",     "mercado": "FOREX",  "simbolo": "GBP/CAD (OTC)",  "activo": False},
    36:  {"nombre": "GBP/AUD",     "mercado": "FOREX",  "simbolo": "GBP/AUD (OTC)",  "activo": False},
    37:  {"nombre": "CAD/JPY",     "mercado": "FOREX",  "simbolo": "CAD/JPY (OTC)",  "activo": False},
    38:  {"nombre": "NZD/USD",     "mercado": "FOREX",  "simbolo": "NZD/USD (OTC)",  "activo": False},
    51:  {"nombre": "EUR/CHF",     "mercado": "FOREX",  "simbolo": "EUR/CHF (OTC)",  "activo": False},
    78:  {"nombre": "EUR/NZD",     "mercado": "FOREX",  "simbolo": "EUR/NZD (OTC)",  "activo": False},
    84:  {"nombre": "USD/CHF",     "mercado": "FOREX",  "simbolo": "USD/CHF (OTC)",  "activo": False},
    85:  {"nombre": "AUD/CAD",     "mercado": "FOREX",  "simbolo": "AUD/CAD (OTC)",  "activo": False},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        CRYPTO OTC (Criptomonedas)
    # ════════════════════════════════════════════════════════════════════════════
    # Las crypto OTC son más volátiles pero pueden dar buenas señales
    
    212:  {"nombre": "Bitcoin",       "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)",   "activo": True},
    220:  {"nombre": "Ethereum",      "mercado": "CRYPTO", "simbolo": "ETH/USD (OTC)",   "activo": True},
    1470: {"nombre": "Ripple",        "mercado": "CRYPTO", "simbolo": "XRP/USD (OTC)",   "activo": False},
    1857: {"nombre": "Binance Coin",  "mercado": "CRYPTO", "simbolo": "BNB/USD (OTC)",   "activo": False},
    1861: {"nombre": "Chainlink",     "mercado": "CRYPTO", "simbolo": "LINK/USD (OTC)",  "activo": False},
    1863: {"nombre": "Polkadot",      "mercado": "CRYPTO", "simbolo": "DOT/USD (OTC)",   "activo": False},
    1866: {"nombre": "Cardano",       "mercado": "CRYPTO", "simbolo": "ADA/USD (OTC)",   "activo": False},
    1867: {"nombre": "Uniswap",       "mercado": "CRYPTO", "simbolo": "UNI/USD (OTC)",   "activo": False},
    1868: {"nombre": "Aave",          "mercado": "CRYPTO", "simbolo": "AAVE/USD (OTC)",  "activo": False},
    1873: {"nombre": "Dogecoin",      "mercado": "CRYPTO", "simbolo": "DOGE/USD (OTC)",  "activo": True},
    1874: {"nombre": "Shiba Inu",     "mercado": "CRYPTO", "simbolo": "SHIB/USD (OTC)",  "activo": False},
    1876: {"nombre": "Solana",        "mercado": "CRYPTO", "simbolo": "SOL/USD (OTC)",   "activo": True},
    1878: {"nombre": "Cosmos",        "mercado": "CRYPTO", "simbolo": "ATOM/USD (OTC)",  "activo": False},
    1881: {"nombre": "Avalanche",     "mercado": "CRYPTO", "simbolo": "AVAX/USD (OTC)",  "activo": False},
    1885: {"nombre": "Polygon",       "mercado": "CRYPTO", "simbolo": "MATIC/USD (OTC)", "activo": False},
    1898: {"nombre": "Stellar",       "mercado": "CRYPTO", "simbolo": "XLM/USD (OTC)",   "activo": False},
    1901: {"nombre": "Tron",          "mercado": "CRYPTO", "simbolo": "TRX/USD (OTC)",   "activo": False},
    1912: {"nombre": "The Sandbox",   "mercado": "CRYPTO", "simbolo": "SAND/USD (OTC)",  "activo": False},
    1936: {"nombre": "NEAR Protocol", "mercado": "CRYPTO", "simbolo": "NEAR/USD (OTC)", "activo": False},
    1941: {"nombre": "Tezos",         "mercado": "CRYPTO", "simbolo": "XTZ/USD (OTC)",   "activo": False},
    1973: {"nombre": "Pepe",          "mercado": "CRYPTO", "simbolo": "PEPE/USD (OTC)",  "activo": False},
    2048: {"nombre": "Sui",           "mercado": "CRYPTO", "simbolo": "SUI/USD (OTC)",   "activo": False},
    2049: {"nombre": "Render",        "mercado": "CRYPTO", "simbolo": "RNDR/USD (OTC)",  "activo": False},
    2050: {"nombre": "Worldcoin",     "mercado": "CRYPTO", "simbolo": "WLD/USD (OTC)",   "activo": False},
    2051: {"nombre": "Sei",           "mercado": "CRYPTO", "simbolo": "SEI/USD (OTC)",   "activo": False},
    2063: {"nombre": "Bonk",          "mercado": "CRYPTO", "simbolo": "BONK/USD (OTC)",  "activo": False},
    2076: {"nombre": "dogwifhat",     "mercado": "CRYPTO", "simbolo": "WIF/USD (OTC)",   "activo": False},
    2100: {"nombre": "Notcoin",       "mercado": "CRYPTO", "simbolo": "NOT/USD (OTC)",   "activo": False},
    2151: {"nombre": "TRUMP Coin",    "mercado": "CRYPTO", "simbolo": "TRUMP (OTC)",     "activo": False},
    2152: {"nombre": "MELANIA Coin",  "mercado": "CRYPTO", "simbolo": "MELANIA (OTC)",   "activo": False},
    2157: {"nombre": "Ondo",          "mercado": "CRYPTO", "simbolo": "ONDO/USD (OTC)",  "activo": False},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        COMMODITIES OTC (Materias primas)
    # ════════════════════════════════════════════════════════════════════════════
    # Oro y Plata suelen ser buenos para señales técnicas
    
    959:  {"nombre": "Oro",            "mercado": "COMMODITIES", "simbolo": "XAU/USD (OTC)",  "activo": True},
    960:  {"nombre": "Plata",          "mercado": "COMMODITIES", "simbolo": "XAG/USD (OTC)",  "activo": True},
    961:  {"nombre": "Petróleo Brent", "mercado": "COMMODITIES", "simbolo": "UKOIL (OTC)",    "activo": False},
    962:  {"nombre": "Petróleo WTI",   "mercado": "COMMODITIES", "simbolo": "USOIL (OTC)",    "activo": False},
    963:  {"nombre": "Gas Natural",    "mercado": "COMMODITIES", "simbolo": "NATGAS (OTC)",   "activo": False},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        ÍNDICES OTC (Índices bursátiles)
    # ════════════════════════════════════════════════════════════════════════════
    
    947:  {"nombre": "Nasdaq 100",     "mercado": "ÍNDICES", "simbolo": "US100 (OTC)",   "activo": True},
    948:  {"nombre": "S&P 500",        "mercado": "ÍNDICES", "simbolo": "US500 (OTC)",   "activo": True},
    949:  {"nombre": "Dow Jones 30",   "mercado": "ÍNDICES", "simbolo": "US30 (OTC)",    "activo": False},
    950:  {"nombre": "FTSE 100",       "mercado": "ÍNDICES", "simbolo": "UK100 (OTC)",   "activo": False},
    951:  {"nombre": "DAX 40",         "mercado": "ÍNDICES", "simbolo": "GER40 (OTC)",   "activo": False},
    952:  {"nombre": "Euro Stoxx 50",  "mercado": "ÍNDICES", "simbolo": "EU50 (OTC)",    "activo": False},
    953:  {"nombre": "Nikkei 225",     "mercado": "ÍNDICES", "simbolo": "JP225 (OTC)",   "activo": False},
    954:  {"nombre": "Hang Seng",      "mercado": "ÍNDICES", "simbolo": "HK50 (OTC)",    "activo": False},
    955:  {"nombre": "ASX 200",        "mercado": "ÍNDICES", "simbolo": "AUS200 (OTC)",  "activo": False},
    956:  {"nombre": "CAC 40",         "mercado": "ÍNDICES", "simbolo": "FR40 (OTC)",    "activo": False},
    957:  {"nombre": "IBEX 35",        "mercado": "ÍNDICES", "simbolo": "ES35 (OTC)",    "activo": False},
    958:  {"nombre": "Russell 2000",   "mercado": "ÍNDICES", "simbolo": "US2000 (OTC)",  "activo": False},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        ACCIONES OTC (Stocks)
    # ════════════════════════════════════════════════════════════════════════════
    
    1348: {"nombre": "Tesla",          "mercado": "ACCIONES", "simbolo": "TSLA (OTC)",   "activo": False},
    1383: {"nombre": "NVIDIA",         "mercado": "ACCIONES", "simbolo": "NVDA (OTC)",   "activo": False},
    1384: {"nombre": "Microsoft",      "mercado": "ACCIONES", "simbolo": "MSFT (OTC)",   "activo": False},
    1385: {"nombre": "Apple",          "mercado": "ACCIONES", "simbolo": "AAPL (OTC)",   "activo": False},
    1386: {"nombre": "Amazon",         "mercado": "ACCIONES", "simbolo": "AMZN (OTC)",   "activo": False},
    1387: {"nombre": "Google",         "mercado": "ACCIONES", "simbolo": "GOOGL (OTC)",  "activo": False},
    1388: {"nombre": "Meta",           "mercado": "ACCIONES", "simbolo": "META (OTC)",   "activo": False},
    1389: {"nombre": "Netflix",        "mercado": "ACCIONES", "simbolo": "NFLX (OTC)",   "activo": False},
    1390: {"nombre": "JPMorgan",       "mercado": "ACCIONES", "simbolo": "JPM (OTC)",    "activo": False},
    1391: {"nombre": "Goldman Sachs",  "mercado": "ACCIONES", "simbolo": "GS (OTC)",     "activo": False},
    1392: {"nombre": "Morgan Stanley", "mercado": "ACCIONES", "simbolo": "MS (OTC)",     "activo": False},
    1393: {"nombre": "Coca-Cola",      "mercado": "ACCIONES", "simbolo": "KO (OTC)",     "activo": False},
    1394: {"nombre": "McDonald's",     "mercado": "ACCIONES", "simbolo": "MCD (OTC)",    "activo": False},
    1395: {"nombre": "Nike",           "mercado": "ACCIONES", "simbolo": "NKE (OTC)",    "activo": False},
    1396: {"nombre": "Disney",         "mercado": "ACCIONES", "simbolo": "DIS (OTC)",    "activo": False},
    1397: {"nombre": "Alibaba",        "mercado": "ACCIONES", "simbolo": "BABA (OTC)",   "activo": False},
    1398: {"nombre": "Baidu",          "mercado": "ACCIONES", "simbolo": "BIDU (OTC)",   "activo": False},
}


def get_activos_habilitados():
    """Retorna solo los activos con 'activo': True"""
    return {k: v for k, v in ACTIVOS.items() if v.get("activo", True)}


def listar_activos():
    """Muestra lista de activos habilitados"""
    habilitados = get_activos_habilitados()
    print(f"\n📊 Activos habilitados: {len(habilitados)}\n")
    
    por_mercado = {}
    for aid, info in habilitados.items():
        mercado = info['mercado']
        if mercado not in por_mercado:
            por_mercado[mercado] = []
        por_mercado[mercado].append(info)
    
    for mercado, activos in por_mercado.items():
        print(f"  {mercado}:")
        for a in activos:
            print(f"    • {a['simbolo']}")
        print()


if __name__ == '__main__':
    listar_activos()
