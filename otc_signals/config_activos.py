#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   📋 CONFIGURACIÓN DE ACTIVOS - PERSONALIZADO PARA TU CUENTA
══════════════════════════════════════════════════════════════════════════════════

   ✅ Estos son los activos que tienes disponibles en Bullex
   
   👉 Cambia "activo": True  a  "activo": False  para deshabilitar uno

══════════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════════
#                    🎮 TUS ACTIVOS DISPONIBLES
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        FOREX OTC (Pares de divisas)
    # ════════════════════════════════════════════════════════════════════════════
    
    1:   {"nombre": "EUR/USD",     "mercado": "FOREX",  "simbolo": "EUR/USD (OTC)",   "activo": True},
    2:   {"nombre": "EUR/GBP",     "mercado": "FOREX",  "simbolo": "EUR/GBP (OTC)",   "activo": True},
    3:   {"nombre": "GBP/USD",     "mercado": "FOREX",  "simbolo": "GBP/USD (OTC)",   "activo": True},
    4:   {"nombre": "EUR/JPY",     "mercado": "FOREX",  "simbolo": "EUR/JPY (OTC)",   "activo": True},
    5:   {"nombre": "USD/JPY",     "mercado": "FOREX",  "simbolo": "USD/JPY (OTC)",   "activo": True},
    6:   {"nombre": "AUD/USD",     "mercado": "FOREX",  "simbolo": "AUD/USD (OTC)",   "activo": True},
    7:   {"nombre": "USD/CAD",     "mercado": "FOREX",  "simbolo": "USD/CAD (OTC)",   "activo": True},
    31:  {"nombre": "AUD/JPY",     "mercado": "FOREX",  "simbolo": "AUD/JPY (OTC)",   "activo": True},
    33:  {"nombre": "EUR/CAD",     "mercado": "FOREX",  "simbolo": "EUR/CAD (OTC)",   "activo": True},
    36:  {"nombre": "GBP/AUD",     "mercado": "FOREX",  "simbolo": "GBP/AUD (OTC)",   "activo": True},
    37:  {"nombre": "CAD/JPY",     "mercado": "FOREX",  "simbolo": "CAD/JPY (OTC)",   "activo": True},
    51:  {"nombre": "EUR/CHF",     "mercado": "FOREX",  "simbolo": "EUR/CHF (OTC)",   "activo": True},
    78:  {"nombre": "EUR/NZD",     "mercado": "FOREX",  "simbolo": "EUR/NZD (OTC)",   "activo": True},
    84:  {"nombre": "USD/CHF",     "mercado": "FOREX",  "simbolo": "USD/CHF (OTC)",   "activo": True},
    85:  {"nombre": "AUD/CAD",     "mercado": "FOREX",  "simbolo": "AUD/CAD (OTC)",   "activo": True},
    52:  {"nombre": "CHF/JPY",     "mercado": "FOREX",  "simbolo": "CHF/JPY (OTC)",   "activo": True},
    
    # Pares exóticos
    90:  {"nombre": "USD/COP",     "mercado": "FOREX",  "simbolo": "USD/COP (OTC)",   "activo": True},
    91:  {"nombre": "USD/BRL",     "mercado": "FOREX",  "simbolo": "USD/BRL (OTC)",   "activo": True},
    92:  {"nombre": "PEN/USD",     "mercado": "FOREX",  "simbolo": "PEN/USD (OTC)",   "activo": True},
    93:  {"nombre": "USD/ZAR",     "mercado": "FOREX",  "simbolo": "USD/ZAR (OTC)",   "activo": True},
    94:  {"nombre": "USD/PLN",     "mercado": "FOREX",  "simbolo": "USD/PLN (OTC)",   "activo": True},
    95:  {"nombre": "USD/SEK",     "mercado": "FOREX",  "simbolo": "USD/SEK (OTC)",   "activo": True},
    96:  {"nombre": "CAD/CHF",     "mercado": "FOREX",  "simbolo": "CAD/CHF (OTC)",   "activo": True},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        CRYPTO OTC (Criptomonedas)
    # ════════════════════════════════════════════════════════════════════════════
    
    212:  {"nombre": "Bitcoin",       "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)",    "activo": True},
    220:  {"nombre": "Ethereum",      "mercado": "CRYPTO", "simbolo": "ETH/USD (OTC)",    "activo": True},
    1876: {"nombre": "Solana",        "mercado": "CRYPTO", "simbolo": "SOL/USD (OTC)",    "activo": True},
    2151: {"nombre": "TRUMP Coin",    "mercado": "CRYPTO", "simbolo": "TRUMP (OTC)",      "activo": True},
    2152: {"nombre": "MELANIA Coin",  "mercado": "CRYPTO", "simbolo": "MELANIA (OTC)",    "activo": True},
    2048: {"nombre": "Sui",           "mercado": "CRYPTO", "simbolo": "SUI/USD (OTC)",    "activo": True},
    2049: {"nombre": "Render",        "mercado": "CRYPTO", "simbolo": "RNDR/USD (OTC)",   "activo": True},
    2060: {"nombre": "Raydium",       "mercado": "CRYPTO", "simbolo": "RAY/USD (OTC)",    "activo": True},
    2070: {"nombre": "DYDX",          "mercado": "CRYPTO", "simbolo": "DYDX/USD (OTC)",   "activo": True},
    2080: {"nombre": "Fartcoin",      "mercado": "CRYPTO", "simbolo": "FART/USD (OTC)",   "activo": True},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        COMMODITIES OTC (Materias primas)
    # ════════════════════════════════════════════════════════════════════════════
    
    959:  {"nombre": "Oro",            "mercado": "COMMODITIES", "simbolo": "XAU/USD (OTC)",  "activo": True},
    960:  {"nombre": "Plata",          "mercado": "COMMODITIES", "simbolo": "XAG/USD (OTC)",  "activo": True},
    961:  {"nombre": "Petróleo Brent", "mercado": "COMMODITIES", "simbolo": "UKO/USD (OTC)",  "activo": True},
    962:  {"nombre": "Petróleo WTI",   "mercado": "COMMODITIES", "simbolo": "USO/USD (OTC)",  "activo": True},
    963:  {"nombre": "Gas Natural",    "mercado": "COMMODITIES", "simbolo": "NATGAS (OTC)",   "activo": True},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        ÍNDICES OTC (Índices bursátiles)
    # ════════════════════════════════════════════════════════════════════════════
    
    947:  {"nombre": "Nasdaq 100",     "mercado": "ÍNDICES", "simbolo": "US 100 (OTC)",   "activo": True},
    948:  {"nombre": "S&P 500",        "mercado": "ÍNDICES", "simbolo": "US 500 (OTC)",   "activo": True},
    949:  {"nombre": "Dow Jones 30",   "mercado": "ÍNDICES", "simbolo": "US 30 (OTC)",    "activo": True},
    952:  {"nombre": "Euro Stoxx 50",  "mercado": "ÍNDICES", "simbolo": "EU 50 (OTC)",    "activo": True},
    955:  {"nombre": "ASX 200",        "mercado": "ÍNDICES", "simbolo": "AUS 200 (OTC)",  "activo": True},
    956:  {"nombre": "CAC 40",         "mercado": "ÍNDICES", "simbolo": "FR 40 (OTC)",    "activo": True},
    958:  {"nombre": "Russell 2000",   "mercado": "ÍNDICES", "simbolo": "US2000 (OTC)",   "activo": True},
    970:  {"nombre": "JPY Currency",   "mercado": "ÍNDICES", "simbolo": "JPY Index (OTC)","activo": True},
    971:  {"nombre": "USD Currency",   "mercado": "ÍNDICES", "simbolo": "USD Index (OTC)","activo": True},
    
    # ════════════════════════════════════════════════════════════════════════════
    #                        ACCIONES OTC (Stocks)
    # ════════════════════════════════════════════════════════════════════════════
    
    1384: {"nombre": "Microsoft",      "mercado": "ACCIONES", "simbolo": "MSFT (OTC)",    "activo": True},
    1391: {"nombre": "Goldman Sachs",  "mercado": "ACCIONES", "simbolo": "GS (OTC)",      "activo": True},
    1393: {"nombre": "Coca-Cola",      "mercado": "ACCIONES", "simbolo": "KO (OTC)",      "activo": True},
    1395: {"nombre": "Nike",           "mercado": "ACCIONES", "simbolo": "NKE (OTC)",     "activo": True},
    1397: {"nombre": "Alibaba",        "mercado": "ACCIONES", "simbolo": "BABA (OTC)",    "activo": True},
    1398: {"nombre": "Baidu",          "mercado": "ACCIONES", "simbolo": "BIDU (OTC)",    "activo": True},
    1400: {"nombre": "AIG",            "mercado": "ACCIONES", "simbolo": "AIG (OTC)",     "activo": True},
    1401: {"nombre": "Snap Inc",       "mercado": "ACCIONES", "simbolo": "SNAP (OTC)",    "activo": True},
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
    
    for mercado, activos in sorted(por_mercado.items()):
        print(f"  {mercado} ({len(activos)}):")
        for a in activos:
            print(f"    • {a['simbolo']}")
        print()


if __name__ == '__main__':
    listar_activos()
