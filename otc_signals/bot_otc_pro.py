#!/usr/bin/env python3
"""
🎯 BULLEX BOT PRO - SOLO OTC CON ANÁLISIS AVANZADO
==================================================

- Solo activos OTC de Bullex
- Análisis de tendencia + sentimiento
- Menos señales, más precisas
- Especifica OTC o REAL
- Hora República Dominicana (UTC-4)

Uso:
    python3 bot_otc_pro.py
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
import time

# ═══════════════════════════════════════════════════════════════
# 👇 PEGA TU SSID AQUÍ:
MI_SSID = ""
# ═══════════════════════════════════════════════════════════════

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))

def hora_rd():
    return datetime.now(RD_TZ)

def fmt_hora(dt):
    return dt.strftime("%H:%M:%S")

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_otc.json"

# Configuración - MÁS ESTRICTA
MINUTOS_ANTICIPACION = 3
DURACION_OPERACION = 2
UMBRAL_SENAL = 90          # Solo señales >90%
COOLDOWN_ACTIVO = 300      # 5 minutos entre señales del mismo activo
MAX_SENALES_HORA = 10      # Máximo 10 señales por hora

# ═══════════════════════════════════════════════════════════════
# BASE DE DATOS - SOLO ACTIVOS OTC DE BULLEX
# ═══════════════════════════════════════════════════════════════

ACTIVOS_OTC = {
    # ══════════ FOREX OTC ══════════
    "EUR/USD OTC": {"nombre": "EUR/USD", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/USD OTC": {"nombre": "GBP/USD", "mercado": "FOREX", "tipo": "OTC"},
    "USD/CHF OTC": {"nombre": "USD/CHF", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/JPY OTC": {"nombre": "EUR/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "USD/JPY OTC": {"nombre": "USD/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "AUD/USD OTC": {"nombre": "AUD/USD", "mercado": "FOREX", "tipo": "OTC"},
    "AUD/CAD OTC": {"nombre": "AUD/CAD", "mercado": "FOREX", "tipo": "OTC"},
    "AUD/JPY OTC": {"nombre": "AUD/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "AUD/CHF OTC": {"nombre": "AUD/CHF", "mercado": "FOREX", "tipo": "OTC"},
    "AUD/NZD OTC": {"nombre": "AUD/NZD", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/GBP OTC": {"nombre": "EUR/GBP", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/AUD OTC": {"nombre": "EUR/AUD", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/CAD OTC": {"nombre": "EUR/CAD", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/CHF OTC": {"nombre": "EUR/CHF", "mercado": "FOREX", "tipo": "OTC"},
    "EUR/NZD OTC": {"nombre": "EUR/NZD", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/JPY OTC": {"nombre": "GBP/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/AUD OTC": {"nombre": "GBP/AUD", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/CAD OTC": {"nombre": "GBP/CAD", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/CHF OTC": {"nombre": "GBP/CHF", "mercado": "FOREX", "tipo": "OTC"},
    "GBP/NZD OTC": {"nombre": "GBP/NZD", "mercado": "FOREX", "tipo": "OTC"},
    "USD/CAD OTC": {"nombre": "USD/CAD", "mercado": "FOREX", "tipo": "OTC"},
    "USD/COP OTC": {"nombre": "USD/COP", "mercado": "FOREX", "tipo": "OTC"},
    "USD/BRL OTC": {"nombre": "USD/BRL", "mercado": "FOREX", "tipo": "OTC"},
    "USD/ZAR OTC": {"nombre": "USD/ZAR", "mercado": "FOREX", "tipo": "OTC"},
    "USD/PLN OTC": {"nombre": "USD/PLN", "mercado": "FOREX", "tipo": "OTC"},
    "USD/SEK OTC": {"nombre": "USD/SEK", "mercado": "FOREX", "tipo": "OTC"},
    "USD/SGD OTC": {"nombre": "USD/SGD", "mercado": "FOREX", "tipo": "OTC"},
    "USD/HKD OTC": {"nombre": "USD/HKD", "mercado": "FOREX", "tipo": "OTC"},
    "USD/NOK OTC": {"nombre": "USD/NOK", "mercado": "FOREX", "tipo": "OTC"},
    "USD/TRY OTC": {"nombre": "USD/TRY", "mercado": "FOREX", "tipo": "OTC"},
    "CAD/JPY OTC": {"nombre": "CAD/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "CAD/CHF OTC": {"nombre": "CAD/CHF", "mercado": "FOREX", "tipo": "OTC"},
    "CHF/JPY OTC": {"nombre": "CHF/JPY", "mercado": "FOREX", "tipo": "OTC"},
    "NZD/CAD OTC": {"nombre": "NZD/CAD", "mercado": "FOREX", "tipo": "OTC"},
    "NZD/USD OTC": {"nombre": "NZD/USD", "mercado": "FOREX", "tipo": "OTC"},
    "PEN/USD OTC": {"nombre": "PEN/USD", "mercado": "FOREX", "tipo": "OTC"},
    
    # ══════════ CRYPTO OTC ══════════
    "BTC/USD OTC": {"nombre": "Bitcoin (BTC)", "mercado": "CRYPTO", "tipo": "OTC"},
    "ETH/USD OTC": {"nombre": "Ethereum (ETH)", "mercado": "CRYPTO", "tipo": "OTC"},
    "SOL/USD OTC": {"nombre": "Solana (SOL)", "mercado": "CRYPTO", "tipo": "OTC"},
    "XRP/USD OTC": {"nombre": "Ripple (XRP)", "mercado": "CRYPTO", "tipo": "OTC"},
    "LTC/USD OTC": {"nombre": "Litecoin (LTC)", "mercado": "CRYPTO", "tipo": "OTC"},
    "TRUMP OTC": {"nombre": "TRUMP Coin", "mercado": "CRYPTO", "tipo": "OTC"},
    "MELANIA OTC": {"nombre": "MELANIA Coin", "mercado": "CRYPTO", "tipo": "OTC"},
    "ONDO OTC": {"nombre": "Ondo (ONDO)", "mercado": "CRYPTO", "tipo": "OTC"},
    "SUI OTC": {"nombre": "Sui (SUI)", "mercado": "CRYPTO", "tipo": "OTC"},
    "DYDX OTC": {"nombre": "dYdX (DYDX)", "mercado": "CRYPTO", "tipo": "OTC"},
    "RENDER OTC": {"nombre": "Render (RNDR)", "mercado": "CRYPTO", "tipo": "OTC"},
    "RAYDIUM OTC": {"nombre": "Raydium (RAY)", "mercado": "CRYPTO", "tipo": "OTC"},
    "VAULTA OTC": {"nombre": "Vaulta", "mercado": "CRYPTO", "tipo": "OTC"},
    "FARTCOIN OTC": {"nombre": "Fartcoin", "mercado": "CRYPTO", "tipo": "OTC"},
    
    # ══════════ COMMODITIES OTC ══════════
    "XAUUSD OTC": {"nombre": "Oro (XAU/USD)", "mercado": "COMMODITIES", "tipo": "OTC"},
    "XAGUSD OTC": {"nombre": "Plata (XAG/USD)", "mercado": "COMMODITIES", "tipo": "OTC"},
    "UKOUSD OTC": {"nombre": "Petróleo Brent", "mercado": "COMMODITIES", "tipo": "OTC"},
    "USOUSD OTC": {"nombre": "Petróleo WTI", "mercado": "COMMODITIES", "tipo": "OTC"},
    "GAS OTC": {"nombre": "Gas Natural", "mercado": "COMMODITIES", "tipo": "OTC"},
    
    # ══════════ ÍNDICES OTC ══════════
    "US100 OTC": {"nombre": "Nasdaq 100", "mercado": "ÍNDICES", "tipo": "OTC"},
    "US500 OTC": {"nombre": "S&P 500", "mercado": "ÍNDICES", "tipo": "OTC"},
    "US30 OTC": {"nombre": "Dow Jones 30", "mercado": "ÍNDICES", "tipo": "OTC"},
    "US2000 OTC": {"nombre": "Russell 2000", "mercado": "ÍNDICES", "tipo": "OTC"},
    "UK100 OTC": {"nombre": "FTSE 100 (UK)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "GER30 OTC": {"nombre": "DAX 30 (Alemania)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "EU50 OTC": {"nombre": "Euro Stoxx 50", "mercado": "ÍNDICES", "tipo": "OTC"},
    "FR40 OTC": {"nombre": "CAC 40 (Francia)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "SP35 OTC": {"nombre": "IBEX 35 (España)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "JP225 OTC": {"nombre": "Nikkei 225 (Japón)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "HK33 OTC": {"nombre": "Hang Seng (HK)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "AUS200 OTC": {"nombre": "ASX 200 (Australia)", "mercado": "ÍNDICES", "tipo": "OTC"},
    "USD INDEX": {"nombre": "USD Currency Index", "mercado": "ÍNDICES", "tipo": "OTC"},
    "JPY INDEX": {"nombre": "JPY Currency Index", "mercado": "ÍNDICES", "tipo": "OTC"},
    
    # ══════════ ACCIONES OTC ══════════
    "MSFT OTC": {"nombre": "Microsoft", "mercado": "ACCIONES", "tipo": "OTC"},
    "AAPL OTC": {"nombre": "Apple", "mercado": "ACCIONES", "tipo": "OTC"},
    "GOOGL OTC": {"nombre": "Google", "mercado": "ACCIONES", "tipo": "OTC"},
    "AMZN OTC": {"nombre": "Amazon", "mercado": "ACCIONES", "tipo": "OTC"},
    "TSLA OTC": {"nombre": "Tesla", "mercado": "ACCIONES", "tipo": "OTC"},
    "NVDA OTC": {"nombre": "NVIDIA", "mercado": "ACCIONES", "tipo": "OTC"},
    "META OTC": {"nombre": "Meta (Facebook)", "mercado": "ACCIONES", "tipo": "OTC"},
    "NFLX OTC": {"nombre": "Netflix", "mercado": "ACCIONES", "tipo": "OTC"},
    "JPM OTC": {"nombre": "JPMorgan Chase", "mercado": "ACCIONES", "tipo": "OTC"},
    "GS OTC": {"nombre": "Goldman Sachs", "mercado": "ACCIONES", "tipo": "OTC"},
    "MS OTC": {"nombre": "Morgan Stanley", "mercado": "ACCIONES", "tipo": "OTC"},
    "C OTC": {"nombre": "Citigroup", "mercado": "ACCIONES", "tipo": "OTC"},
    "BAC OTC": {"nombre": "Bank of America", "mercado": "ACCIONES", "tipo": "OTC"},
    "NKE OTC": {"nombre": "Nike", "mercado": "ACCIONES", "tipo": "OTC"},
    "MCD OTC": {"nombre": "McDonald's", "mercado": "ACCIONES", "tipo": "OTC"},
    "KO OTC": {"nombre": "Coca-Cola", "mercado": "ACCIONES", "tipo": "OTC"},
    "DIS OTC": {"nombre": "Disney", "mercado": "ACCIONES", "tipo": "OTC"},
    "SNAP OTC": {"nombre": "Snap Inc.", "mercado": "ACCIONES", "tipo": "OTC"},
    "BABA OTC": {"nombre": "Alibaba", "mercado": "ACCIONES", "tipo": "OTC"},
    "BIDU OTC": {"nombre": "Baidu", "mercado": "ACCIONES", "tipo": "OTC"},
    "AIG OTC": {"nombre": "AIG", "mercado": "ACCIONES", "tipo": "OTC"},
    
    # ══════════ FOREX REAL (no OTC) ══════════
    "EUR/USD": {"nombre": "EUR/USD", "mercado": "FOREX", "tipo": "REAL"},
    "GBP/USD": {"nombre": "GBP/USD", "mercado": "FOREX", "tipo": "REAL"},
    "EUR/JPY": {"nombre": "EUR/JPY", "mercado": "FOREX", "tipo": "REAL"},
    "USD/JPY": {"nombre": "USD/JPY", "mercado": "FOREX", "tipo": "REAL"},
}

# Mapeo de asset_id a nombre del activo
ASSET_ID_MAP = {
    # FOREX OTC
    1: "EUR/USD OTC", 2: "EUR/GBP OTC", 3: "GBP/USD OTC", 4: "EUR/JPY OTC",
    5: "USD/JPY OTC", 6: "AUD/USD OTC", 7: "USD/CAD OTC", 31: "AUD/JPY OTC",
    32: "EUR/AUD OTC", 33: "EUR/CAD OTC", 34: "GBP/JPY OTC", 35: "GBP/CAD OTC",
    36: "GBP/AUD OTC", 37: "CAD/JPY OTC", 38: "NZD/USD OTC", 51: "EUR/CHF OTC",
    78: "EUR/NZD OTC", 84: "USD/CHF OTC", 85: "AUD/CAD OTC", 86: "AUD/CAD OTC",
    
    # CRYPTO OTC
    212: "BTC/USD OTC", 220: "ETH/USD OTC", 1470: "XRP/USD OTC",
    1876: "SOL/USD OTC", 2151: "TRUMP OTC", 2152: "MELANIA OTC",
    2157: "ONDO OTC", 2048: "SUI OTC", 2049: "RENDER OTC",
    
    # COMMODITIES
    959: "XAUUSD OTC", 960: "XAGUSD OTC",
    
    # ÍNDICES
    947: "US100 OTC", 948: "US500 OTC", 949: "US30 OTC",
    950: "UK100 OTC", 951: "GER30 OTC", 952: "EU50 OTC",
    953: "JP225 OTC", 954: "HK33 OTC", 955: "AUS200 OTC",
    
    # ACCIONES
    1383: "NVDA OTC", 1348: "TSLA OTC", 1380: "MSFT OTC",
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
    
    def senales_ultima_hora(self):
        ahora = time.time()
        return len([s for s in self.senales 
                   if ahora - datetime.fromisoformat(s['timestamp']).timestamp() < 3600])


class AnalizadorTecnico:
    """Análisis técnico básico para mejorar precisión"""
    
    def __init__(self):
        self.velas = defaultdict(list)  # {asset_id: [candles]}
        self.max_velas = 20
    
    def agregar_vela(self, aid, vela):
        self.velas[aid].append(vela)
        if len(self.velas[aid]) > self.max_velas:
            self.velas[aid].pop(0)
    
    def calcular_tendencia(self, aid):
        """Calcula tendencia: 1=alcista, -1=bajista, 0=lateral"""
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 0
        
        precios = [v.get('close', 0) for v in velas[-10:]]
        if not precios or precios[0] == 0:
            return 0
        
        cambio = (precios[-1] - precios[0]) / precios[0] * 100
        
        if cambio > 0.1:
            return 1   # Alcista
        elif cambio < -0.1:
            return -1  # Bajista
        return 0       # Lateral
    
    def calcular_fuerza(self, aid):
        """Calcula fuerza de la tendencia (0-100)"""
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 50
        
        # Contar velas verdes vs rojas
        verdes = sum(1 for v in velas[-10:] if v.get('close', 0) > v.get('open', 0))
        return verdes * 10


class BotOTCPro:
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.historial = HistorialManager(HISTORIAL_FILE)
        self.analizador = AnalizadorTecnico()
        self.precios = {}
        self.senales_programadas = {}
        self.senales_activas = {}
        self.ultima_senal = {}
        self.senales_hora = 0
        self.hora_reset = time.time()
    
    async def conectar(self):
        print(f"\n🔌 [{fmt_hora(hora_rd())}] Conectando a Bullex...")
        
        try:
            self.ws = await websockets.connect(WS_URL, origin='https://trade.bull-ex.com')
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            print(f"   ✅ Conectado")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def obtener_activo(self, aid):
        """Obtiene info del activo si está en nuestra lista OTC"""
        nombre_clave = ASSET_ID_MAP.get(aid)
        if nombre_clave and nombre_clave in ACTIVOS_OTC:
            return ACTIVOS_OTC[nombre_clave]
        return None
    
    def calcular_tiempos(self):
        ahora = hora_rd()
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=MINUTOS_ANTICIPACION + 1)
        expiracion = entrada + timedelta(minutes=DURACION_OPERACION)
        segundos = (entrada - ahora).total_seconds()
        return entrada, expiracion, segundos
    
    def analizar_senal(self, aid, sentimiento_pct):
        """
        Análisis combinado: Sentimiento + Tendencia
        Retorna: probabilidad ajustada y recomendación
        """
        tendencia = self.analizador.calcular_tendencia(aid)
        fuerza = self.analizador.calcular_fuerza(aid)
        
        # Dirección basada en sentimiento
        if sentimiento_pct > 50:
            direccion_sent = 1  # CALL
            pct_sent = sentimiento_pct
        else:
            direccion_sent = -1  # PUT
            pct_sent = 100 - sentimiento_pct
        
        # Ajustar probabilidad según tendencia
        prob = pct_sent
        
        # Si tendencia confirma sentimiento: +5%
        if tendencia == direccion_sent:
            prob = min(99, prob + 5)
            confirmacion = "✅ CONFIRMADA"
        # Si tendencia contradice sentimiento: -10%
        elif tendencia == -direccion_sent:
            prob = max(50, prob - 10)
            confirmacion = "⚠️ DIVERGENCIA"
        else:
            confirmacion = "➡️ NEUTRAL"
        
        return {
            'direccion': "CALL" if direccion_sent == 1 else "PUT",
            'probabilidad': prob,
            'sentimiento': pct_sent,
            'tendencia': "ALCISTA" if tendencia == 1 else "BAJISTA" if tendencia == -1 else "LATERAL",
            'confirmacion': confirmacion,
            'fuerza': fuerza
        }
    
    def generar_senal(self, aid, analisis):
        activo = self.obtener_activo(aid)
        if not activo:
            return None
        
        ahora = hora_rd()
        entrada, expiracion, segundos = self.calcular_tiempos()
        
        if analisis['direccion'] == "CALL":
            texto = "📈 SUBE (CALL)"
        else:
            texto = "📉 BAJA (PUT)"
        
        prob = analisis['probabilidad']
        if prob >= 95:
            confianza = "🔥 EXTREMA"
        elif prob >= 90:
            confianza = "✅ MUY ALTA"
        elif prob >= 85:
            confianza = "📊 ALTA"
        else:
            confianza = "⚠️ MEDIA"
        
        return {
            'id': f"{aid}_{int(time.time())}",
            'timestamp': ahora.isoformat(),
            'activo_id': aid,
            'activo': activo['nombre'],
            'mercado': activo['mercado'],
            'tipo': activo['tipo'],
            'direccion': analisis['direccion'],
            'direccion_texto': texto,
            'probabilidad': prob,
            'sentimiento': analisis['sentimiento'],
            'tendencia': analisis['tendencia'],
            'confirmacion': analisis['confirmacion'],
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
        
        # Color del tipo
        tipo_emoji = "🟠" if s['tipo'] == "OTC" else "🟢"
        
        print("\n" + "╔" + "═" * 60 + "╗")
        print(f"║  🎯 SEÑAL {s['tipo']} - {s['confianza']:<40} ║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  {tipo_emoji} {s['activo']:<55} ║")
        print(f"║  📊 {s['mercado']:<55} ║")
        print(f"║  🏷️  Tipo: {s['tipo']:<50} ║")
        print("╠" + "═" * 60 + "╣")
        
        if s['direccion'] == 'CALL':
            print(f"║     🟢🟢🟢  {s['direccion_texto']:<43}  ║")
        else:
            print(f"║     🔴🔴🔴  {s['direccion_texto']:<43}  ║")
        
        print("╠" + "═" * 60 + "╣")
        print(f"║  📈 Probabilidad:  {s['probabilidad']:.0f}%{' ' * 38}║")
        print(f"║  👥 Sentimiento:   {s['sentimiento']:.0f}% traders{' ' * 31}║")
        print(f"║  📉 Tendencia:     {s['tendencia']:<40}║")
        print(f"║  🔍 Análisis:      {s['confirmacion']:<40}║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  ⏰ ENTRAR EN:     {mins}:{segs:02d} minutos{' ' * 31}║")
        print(f"║  🎯 HORA ENTRADA:  {s['entrada']:<40} ║")
        print(f"║  ⏱️  EXPIRACIÓN:    {s['expiracion']:<40} ║")
        print(f"║  ⌛ DURACIÓN:      {s['duracion']:<40} ║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  🕐 Hora RD:       {fmt_hora(hora_rd()):<40} ║")
        print("╚" + "═" * 60 + "╝")
    
    def mostrar_alerta(self, s):
        tipo_emoji = "🟠 OTC" if s['tipo'] == "OTC" else "🟢 REAL"
        print("\n" + "🔔" * 25)
        print("╔" + "═" * 52 + "╗")
        print(f"║  ⚡ ¡¡¡ ENTRAR AHORA !!! ⚡  [{tipo_emoji}]{' ' * 15}║")
        print("╠" + "═" * 52 + "╣")
        print(f"║  📍 {s['activo']:<46}║")
        
        if s['direccion'] == 'CALL':
            print(f"║  🟢 COMPRA (CALL) - SUBE{' ' * 27}║")
        else:
            print(f"║  🔴 VENTA (PUT) - BAJA{' ' * 29}║")
        
        print(f"║  📈 Probabilidad: {s['probabilidad']:.0f}%{' ' * 31}║")
        print(f"║  ⏱️  Expira: {s['expiracion']}{' ' * 35}║")
        print("╚" + "═" * 52 + "╝")
        print("🔔" * 25 + "\n")
    
    def mostrar_stats(self):
        stats = self.historial.estadisticas()
        senales_hora = self.historial.senales_ultima_hora()
        
        print("\n┌" + "─" * 44 + "┐")
        print(f"│  📊 ESTADÍSTICAS - Solo OTC{' ' * 15}│")
        print("├" + "─" * 44 + "┤")
        print(f"│  Señales última hora: {senales_hora}/{MAX_SENALES_HORA}{' ' * 16}│")
        print(f"│  Total señales:       {stats['total']:<19}│")
        print(f"│  ✅ Ganadas:          {stats['ganadas']:<19}│")
        print(f"│  ❌ Perdidas:         {stats['perdidas']:<19}│")
        print(f"│  📈 Precisión:        {stats['precision']:.1f}%{' ' * 16}│")
        print("└" + "─" * 44 + "┘")
    
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
                print(f"   ⏳ [{s['tipo']}] {s['activo']}: {emoji} {s['direccion']} en {mins} min")
        
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
                    print(f"\n{emoji} [{s['tipo']}] {s['activo']} - {resultado}")
                    verificadas.append(sid)
        
        for sid in verificadas:
            del self.senales_activas[sid]
    
    async def procesar(self, msg):
        try:
            data = json.loads(msg)
            name = data.get('name', '')
            m = data.get('msg', {})
            
            if name == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
                    self.analizador.agregar_vela(aid, m)
            
            elif name == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                # Filtrar blitz
                if 'blitz' in inst.lower():
                    return
                
                # Verificar que es un activo OTC que queremos
                activo = self.obtener_activo(aid)
                if not activo:
                    return
                
                # Control de límite por hora
                if time.time() - self.hora_reset >= 3600:
                    self.senales_hora = 0
                    self.hora_reset = time.time()
                
                if self.senales_hora >= MAX_SENALES_HORA:
                    return
                
                # Calcular porcentaje
                call_pct = value * 100
                
                # Solo señales muy fuertes (>90%)
                if call_pct < UMBRAL_SENAL and (100 - call_pct) < UMBRAL_SENAL:
                    return
                
                # Control de cooldown
                ahora = time.time()
                clave = f"{aid}_{inst}"
                if clave in self.ultima_senal:
                    if ahora - self.ultima_senal[clave] < COOLDOWN_ACTIVO:
                        return
                
                # Analizar señal
                analisis = self.analizar_senal(aid, call_pct)
                
                # Solo si probabilidad ajustada >= 88%
                if analisis['probabilidad'] < 88:
                    return
                
                # Solo si tendencia confirma o es neutral (no divergencia)
                if analisis['confirmacion'] == "⚠️ DIVERGENCIA":
                    return
                
                self.ultima_senal[clave] = ahora
                
                senal = self.generar_senal(aid, analisis)
                if senal:
                    self.mostrar_senal(senal)
                    self.historial.agregar(senal)
                    self.senales_programadas[senal['id']] = senal
                    self.senales_hora += 1
                    
        except:
            pass
    
    async def ejecutar(self):
        if not await self.conectar():
            return
        
        ahora = hora_rd()
        
        print("\n" + "═" * 62)
        print("  🎯 BULLEX BOT PRO - SOLO OTC")
        print("═" * 62)
        print(f"  🕐 Hora RD: {fmt_hora(ahora)} (UTC-4)")
        print(f"  📅 {ahora.strftime('%d/%m/%Y')}")
        print("═" * 62)
        print(f"  🎯 Umbral mínimo:     {UMBRAL_SENAL}% sentimiento")
        print(f"  📊 Análisis:          Tendencia + Sentimiento")
        print(f"  ⏰ Anticipación:      {MINUTOS_ANTICIPACION} minutos")
        print(f"  ⌛ Duración:          {DURACION_OPERACION} minutos")
        print(f"  🔄 Cooldown:          {COOLDOWN_ACTIVO//60} min entre señales")
        print(f"  📈 Máx señales/hora:  {MAX_SENALES_HORA}")
        print("═" * 62)
        print("  🟠 OTC = Mercado sintético de Bullex")
        print("  🟢 REAL = Mercado real")
        print("═" * 62)
        print("  Ctrl+C para salir")
        print("═" * 62)
        
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
            print(f"\n⚠️ Reconectando...")
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
║           🎯 BULLEX BOT PRO - CONFIGURACIÓN                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📋 PASOS:                                                   ║
║                                                              ║
║  1. Abre Bullex en Chrome y haz login                        ║
║  2. Presiona F12 → Application → Cookies                     ║
║  3. Copia el valor de "ssid"                                 ║
║  4. Pégalo cuando el bot lo pida                             ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ Solo activos OTC de tu lista                             ║
║  ✅ Análisis de tendencia + sentimiento                      ║
║  ✅ Menos señales, más precisas                              ║
║  ✅ Indica OTC o REAL en cada señal                          ║
╚══════════════════════════════════════════════════════════════╝
""")


async def main():
    ssid = MI_SSID.strip()
    
    if not ssid:
        mostrar_instrucciones()
        ssid = input("\n🔑 Pega tu SSID: ").strip()
        if not ssid:
            print("\n❌ No se ingresó SSID")
            return
    
    bot = BotOTCPro(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido")
