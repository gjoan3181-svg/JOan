#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════
   🏆 BULLEX BOT PRO - VERSIÓN FINAL
══════════════════════════════════════════════════════════════════════

   ✅ Análisis técnico (Tendencia + Momentum)
   ✅ Análisis de sentimiento de traders
   ✅ Solo activos OTC de Bullex
   ✅ Filtros estrictos para máxima precisión
   ✅ Hora República Dominicana (UTC-4)
   ✅ Historial y estadísticas
   ✅ Verificación automática de resultados
   ✅ Alertas de entrada

   Uso: python3 bot_pro_final.py

══════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os
import time
import sys

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# 👇 PEGA TU SSID AQUÍ (o ingrésalo al ejecutar):
MI_SSID = ""

# URLs
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_pro.json"

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))

# ═══════════════════════════════════════════════════════════════════════════════
#                           PARÁMETROS DE TRADING
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # Filtros de señal
    UMBRAL_SENTIMIENTO = 88      # Solo señales con >88% sentimiento
    PROBABILIDAD_MINIMA = 85     # Probabilidad mínima ajustada
    
    # Tiempos
    ANTICIPACION_MINUTOS = 3     # Señal 3 min antes de entrada
    DURACION_OPERACION = 2       # Operación de 2 minutos
    COOLDOWN_ACTIVO = 300        # 5 min entre señales del mismo activo
    
    # Límites
    MAX_SENALES_HORA = 15        # Máximo 15 señales por hora
    
    # Análisis técnico
    VELAS_ANALISIS = 15          # Velas para análisis de tendencia
    CONFIRMAR_TENDENCIA = True   # Rechazar si tendencia contradice

# ═══════════════════════════════════════════════════════════════════════════════
#                    BASE DE DATOS DE ACTIVOS OTC
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVOS_OTC = {
    # ════════════════ FOREX OTC ════════════════
    1:   {"nombre": "EUR/USD",    "mercado": "FOREX",      "simbolo": "EUR/USD (OTC)"},
    2:   {"nombre": "EUR/GBP",    "mercado": "FOREX",      "simbolo": "EUR/GBP (OTC)"},
    3:   {"nombre": "GBP/USD",    "mercado": "FOREX",      "simbolo": "GBP/USD (OTC)"},
    4:   {"nombre": "EUR/JPY",    "mercado": "FOREX",      "simbolo": "EUR/JPY (OTC)"},
    5:   {"nombre": "USD/JPY",    "mercado": "FOREX",      "simbolo": "USD/JPY (OTC)"},
    6:   {"nombre": "AUD/USD",    "mercado": "FOREX",      "simbolo": "AUD/USD (OTC)"},
    7:   {"nombre": "USD/CAD",    "mercado": "FOREX",      "simbolo": "USD/CAD (OTC)"},
    31:  {"nombre": "AUD/JPY",    "mercado": "FOREX",      "simbolo": "AUD/JPY (OTC)"},
    32:  {"nombre": "EUR/AUD",    "mercado": "FOREX",      "simbolo": "EUR/AUD (OTC)"},
    33:  {"nombre": "EUR/CAD",    "mercado": "FOREX",      "simbolo": "EUR/CAD (OTC)"},
    34:  {"nombre": "GBP/JPY",    "mercado": "FOREX",      "simbolo": "GBP/JPY (OTC)"},
    35:  {"nombre": "GBP/CAD",    "mercado": "FOREX",      "simbolo": "GBP/CAD (OTC)"},
    36:  {"nombre": "GBP/AUD",    "mercado": "FOREX",      "simbolo": "GBP/AUD (OTC)"},
    37:  {"nombre": "CAD/JPY",    "mercado": "FOREX",      "simbolo": "CAD/JPY (OTC)"},
    38:  {"nombre": "NZD/USD",    "mercado": "FOREX",      "simbolo": "NZD/USD (OTC)"},
    51:  {"nombre": "EUR/CHF",    "mercado": "FOREX",      "simbolo": "EUR/CHF (OTC)"},
    78:  {"nombre": "EUR/NZD",    "mercado": "FOREX",      "simbolo": "EUR/NZD (OTC)"},
    84:  {"nombre": "USD/CHF",    "mercado": "FOREX",      "simbolo": "USD/CHF (OTC)"},
    85:  {"nombre": "AUD/CAD",    "mercado": "FOREX",      "simbolo": "AUD/CAD (OTC)"},
    86:  {"nombre": "AUD/CAD",    "mercado": "FOREX",      "simbolo": "AUD/CAD (OTC)"},
    
    # ════════════════ CRYPTO OTC ════════════════
    212:  {"nombre": "Bitcoin",       "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)"},
    220:  {"nombre": "Ethereum",      "mercado": "CRYPTO", "simbolo": "ETH/USD (OTC)"},
    1470: {"nombre": "Ripple",        "mercado": "CRYPTO", "simbolo": "XRP/USD (OTC)"},
    1857: {"nombre": "Binance Coin",  "mercado": "CRYPTO", "simbolo": "BNB/USD (OTC)"},
    1861: {"nombre": "Chainlink",     "mercado": "CRYPTO", "simbolo": "LINK/USD (OTC)"},
    1863: {"nombre": "Polkadot",      "mercado": "CRYPTO", "simbolo": "DOT/USD (OTC)"},
    1866: {"nombre": "Cardano",       "mercado": "CRYPTO", "simbolo": "ADA/USD (OTC)"},
    1867: {"nombre": "Uniswap",       "mercado": "CRYPTO", "simbolo": "UNI/USD (OTC)"},
    1868: {"nombre": "Aave",          "mercado": "CRYPTO", "simbolo": "AAVE/USD (OTC)"},
    1873: {"nombre": "Dogecoin",      "mercado": "CRYPTO", "simbolo": "DOGE/USD (OTC)"},
    1874: {"nombre": "Shiba Inu",     "mercado": "CRYPTO", "simbolo": "SHIB/USD (OTC)"},
    1876: {"nombre": "Solana",        "mercado": "CRYPTO", "simbolo": "SOL/USD (OTC)"},
    1878: {"nombre": "Cosmos",        "mercado": "CRYPTO", "simbolo": "ATOM/USD (OTC)"},
    1881: {"nombre": "Avalanche",     "mercado": "CRYPTO", "simbolo": "AVAX/USD (OTC)"},
    1885: {"nombre": "Polygon",       "mercado": "CRYPTO", "simbolo": "MATIC/USD (OTC)"},
    1898: {"nombre": "Stellar",       "mercado": "CRYPTO", "simbolo": "XLM/USD (OTC)"},
    1901: {"nombre": "Tron",          "mercado": "CRYPTO", "simbolo": "TRX/USD (OTC)"},
    1912: {"nombre": "The Sandbox",   "mercado": "CRYPTO", "simbolo": "SAND/USD (OTC)"},
    1936: {"nombre": "NEAR Protocol", "mercado": "CRYPTO", "simbolo": "NEAR/USD (OTC)"},
    1941: {"nombre": "Tezos",         "mercado": "CRYPTO", "simbolo": "XTZ/USD (OTC)"},
    1973: {"nombre": "Pepe",          "mercado": "CRYPTO", "simbolo": "PEPE/USD (OTC)"},
    2048: {"nombre": "Sui",           "mercado": "CRYPTO", "simbolo": "SUI/USD (OTC)"},
    2049: {"nombre": "Render",        "mercado": "CRYPTO", "simbolo": "RNDR/USD (OTC)"},
    2050: {"nombre": "Worldcoin",     "mercado": "CRYPTO", "simbolo": "WLD/USD (OTC)"},
    2051: {"nombre": "Sei",           "mercado": "CRYPTO", "simbolo": "SEI/USD (OTC)"},
    2063: {"nombre": "Bonk",          "mercado": "CRYPTO", "simbolo": "BONK/USD (OTC)"},
    2076: {"nombre": "dogwifhat",     "mercado": "CRYPTO", "simbolo": "WIF/USD (OTC)"},
    2100: {"nombre": "Notcoin",       "mercado": "CRYPTO", "simbolo": "NOT/USD (OTC)"},
    2151: {"nombre": "TRUMP Coin",    "mercado": "CRYPTO", "simbolo": "TRUMP (OTC)"},
    2152: {"nombre": "MELANIA Coin",  "mercado": "CRYPTO", "simbolo": "MELANIA (OTC)"},
    2157: {"nombre": "Ondo",          "mercado": "CRYPTO", "simbolo": "ONDO/USD (OTC)"},
    
    # ════════════════ COMMODITIES OTC ════════════════
    959:  {"nombre": "Oro",           "mercado": "COMMODITIES", "simbolo": "XAU/USD (OTC)"},
    960:  {"nombre": "Plata",         "mercado": "COMMODITIES", "simbolo": "XAG/USD (OTC)"},
    961:  {"nombre": "Petróleo Brent","mercado": "COMMODITIES", "simbolo": "UKOIL (OTC)"},
    962:  {"nombre": "Petróleo WTI",  "mercado": "COMMODITIES", "simbolo": "USOIL (OTC)"},
    963:  {"nombre": "Gas Natural",   "mercado": "COMMODITIES", "simbolo": "NATGAS (OTC)"},
    
    # ════════════════ ÍNDICES OTC ════════════════
    947:  {"nombre": "Nasdaq 100",    "mercado": "ÍNDICES", "simbolo": "US100 (OTC)"},
    948:  {"nombre": "S&P 500",       "mercado": "ÍNDICES", "simbolo": "US500 (OTC)"},
    949:  {"nombre": "Dow Jones 30",  "mercado": "ÍNDICES", "simbolo": "US30 (OTC)"},
    950:  {"nombre": "FTSE 100",      "mercado": "ÍNDICES", "simbolo": "UK100 (OTC)"},
    951:  {"nombre": "DAX 40",        "mercado": "ÍNDICES", "simbolo": "GER40 (OTC)"},
    952:  {"nombre": "Euro Stoxx 50", "mercado": "ÍNDICES", "simbolo": "EU50 (OTC)"},
    953:  {"nombre": "Nikkei 225",    "mercado": "ÍNDICES", "simbolo": "JP225 (OTC)"},
    954:  {"nombre": "Hang Seng",     "mercado": "ÍNDICES", "simbolo": "HK50 (OTC)"},
    955:  {"nombre": "ASX 200",       "mercado": "ÍNDICES", "simbolo": "AUS200 (OTC)"},
    956:  {"nombre": "CAC 40",        "mercado": "ÍNDICES", "simbolo": "FR40 (OTC)"},
    957:  {"nombre": "IBEX 35",       "mercado": "ÍNDICES", "simbolo": "ES35 (OTC)"},
    958:  {"nombre": "Russell 2000",  "mercado": "ÍNDICES", "simbolo": "US2000 (OTC)"},
    
    # ════════════════ ACCIONES OTC ════════════════
    1348: {"nombre": "Tesla",         "mercado": "ACCIONES", "simbolo": "TSLA (OTC)"},
    1380: {"nombre": "Intel",         "mercado": "ACCIONES", "simbolo": "INTC (OTC)"},
    1381: {"nombre": "Intel",         "mercado": "ACCIONES", "simbolo": "INTC (OTC)"},
    1383: {"nombre": "NVIDIA",        "mercado": "ACCIONES", "simbolo": "NVDA (OTC)"},
    1384: {"nombre": "Microsoft",     "mercado": "ACCIONES", "simbolo": "MSFT (OTC)"},
    1385: {"nombre": "Apple",         "mercado": "ACCIONES", "simbolo": "AAPL (OTC)"},
    1386: {"nombre": "Amazon",        "mercado": "ACCIONES", "simbolo": "AMZN (OTC)"},
    1387: {"nombre": "Google",        "mercado": "ACCIONES", "simbolo": "GOOGL (OTC)"},
    1388: {"nombre": "Meta",          "mercado": "ACCIONES", "simbolo": "META (OTC)"},
    1389: {"nombre": "Netflix",       "mercado": "ACCIONES", "simbolo": "NFLX (OTC)"},
    1390: {"nombre": "JPMorgan",      "mercado": "ACCIONES", "simbolo": "JPM (OTC)"},
    1391: {"nombre": "Goldman Sachs", "mercado": "ACCIONES", "simbolo": "GS (OTC)"},
    1392: {"nombre": "Morgan Stanley","mercado": "ACCIONES", "simbolo": "MS (OTC)"},
    1393: {"nombre": "Coca-Cola",     "mercado": "ACCIONES", "simbolo": "KO (OTC)"},
    1394: {"nombre": "McDonald's",    "mercado": "ACCIONES", "simbolo": "MCD (OTC)"},
    1395: {"nombre": "Nike",          "mercado": "ACCIONES", "simbolo": "NKE (OTC)"},
    1396: {"nombre": "Disney",        "mercado": "ACCIONES", "simbolo": "DIS (OTC)"},
    1397: {"nombre": "Alibaba",       "mercado": "ACCIONES", "simbolo": "BABA (OTC)"},
    1398: {"nombre": "Baidu",         "mercado": "ACCIONES", "simbolo": "BIDU (OTC)"},
}

# ═══════════════════════════════════════════════════════════════════════════════
#                              FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def hora_rd():
    """Retorna datetime actual en República Dominicana"""
    return datetime.now(RD_TZ)

def fmt_hora(dt=None):
    """Formatea hora HH:MM:SS"""
    if dt is None:
        dt = hora_rd()
    return dt.strftime("%H:%M:%S")

def fmt_fecha(dt=None):
    """Formatea fecha DD/MM/YYYY"""
    if dt is None:
        dt = hora_rd()
    return dt.strftime("%d/%m/%Y")

def limpiar_pantalla():
    """Limpia la pantalla de la terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

# ═══════════════════════════════════════════════════════════════════════════════
#                              ANALIZADOR TÉCNICO
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorTecnico:
    """Análisis técnico para mejorar precisión de señales"""
    
    def __init__(self):
        self.velas = defaultdict(list)
        self.max_velas = Config.VELAS_ANALISIS
    
    def agregar_vela(self, aid, vela):
        """Agrega una vela al historial del activo"""
        self.velas[aid].append({
            'open': vela.get('open', 0),
            'high': vela.get('max', vela.get('high', 0)),
            'low': vela.get('min', vela.get('low', 0)),
            'close': vela.get('close', 0),
            'time': vela.get('time', time.time())
        })
        # Mantener solo las últimas N velas
        if len(self.velas[aid]) > self.max_velas:
            self.velas[aid].pop(0)
    
    def calcular_tendencia(self, aid):
        """
        Calcula la tendencia actual del activo
        Retorna: 1 (alcista), -1 (bajista), 0 (lateral)
        """
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 0
        
        # Usar últimas 10 velas o las disponibles
        ultimas = velas[-10:]
        
        # Calcular cambio porcentual
        precio_inicio = ultimas[0]['close']
        precio_fin = ultimas[-1]['close']
        
        if precio_inicio == 0:
            return 0
        
        cambio = ((precio_fin - precio_inicio) / precio_inicio) * 100
        
        # Contar velas alcistas vs bajistas
        alcistas = sum(1 for v in ultimas if v['close'] > v['open'])
        bajistas = len(ultimas) - alcistas
        
        # Determinar tendencia
        if cambio > 0.05 and alcistas >= 6:
            return 1   # Alcista fuerte
        elif cambio < -0.05 and bajistas >= 6:
            return -1  # Bajista fuerte
        elif cambio > 0.02:
            return 1   # Alcista moderada
        elif cambio < -0.02:
            return -1  # Bajista moderada
        else:
            return 0   # Lateral
    
    def calcular_momentum(self, aid):
        """
        Calcula el momentum (fuerza del movimiento)
        Retorna: valor de 0 a 100
        """
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 50
        
        ultimas = velas[-5:]
        
        # Calcular promedio de cambios
        cambios = []
        for i in range(1, len(ultimas)):
            if ultimas[i-1]['close'] != 0:
                cambio = ((ultimas[i]['close'] - ultimas[i-1]['close']) / ultimas[i-1]['close']) * 100
                cambios.append(cambio)
        
        if not cambios:
            return 50
        
        promedio = sum(cambios) / len(cambios)
        
        # Convertir a escala 0-100
        momentum = 50 + (promedio * 500)  # Escalar
        return max(0, min(100, momentum))
    
    def obtener_analisis(self, aid):
        """Retorna análisis completo del activo"""
        tendencia = self.calcular_tendencia(aid)
        momentum = self.calcular_momentum(aid)
        
        if tendencia == 1:
            tendencia_texto = "ALCISTA ↑"
        elif tendencia == -1:
            tendencia_texto = "BAJISTA ↓"
        else:
            tendencia_texto = "LATERAL →"
        
        return {
            'tendencia': tendencia,
            'tendencia_texto': tendencia_texto,
            'momentum': momentum
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              GESTOR DE HISTORIAL
# ═══════════════════════════════════════════════════════════════════════════════

class HistorialManager:
    """Gestiona el historial de señales y estadísticas"""
    
    def __init__(self, archivo):
        self.archivo = archivo
        self.senales = []
        self.cargar()
    
    def cargar(self):
        """Carga historial desde archivo"""
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.senales = data.get('senales', [])
        except:
            self.senales = []
    
    def guardar(self):
        """Guarda historial a archivo"""
        try:
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump({
                    'senales': self.senales,
                    'actualizado': hora_rd().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def agregar(self, senal):
        """Agrega una señal al historial"""
        self.senales.append(senal)
        self.guardar()
    
    def actualizar_resultado(self, senal_id, resultado, precio_cierre):
        """Actualiza el resultado de una señal"""
        for s in self.senales:
            if s.get('id') == senal_id:
                s['resultado'] = resultado
                s['precio_cierre'] = precio_cierre
                s['verificado'] = True
                break
        self.guardar()
    
    def estadisticas(self):
        """Calcula estadísticas del historial"""
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        perdidas = [s for s in verificadas if s.get('resultado') == 'PERDIDA']
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(perdidas),
            'pendientes': total - len(verificadas),
            'precision': precision
        }
    
    def senales_hoy(self):
        """Retorna señales de hoy"""
        hoy = hora_rd().date()
        return [s for s in self.senales 
                if datetime.fromisoformat(s['timestamp']).date() == hoy]
    
    def ultimas(self, n=10):
        """Retorna las últimas N señales"""
        return self.senales[-n:] if self.senales else []

# ═══════════════════════════════════════════════════════════════════════════════
#                              BOT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class BotPro:
    """Bot profesional de señales OTC"""
    
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.conectado = False
        
        # Componentes
        self.historial = HistorialManager(HISTORIAL_FILE)
        self.analizador = AnalizadorTecnico()
        
        # Estado
        self.precios = {}
        self.senales_programadas = {}
        self.senales_activas = {}
        self.ultima_senal = {}
        self.senales_hora_actual = 0
        self.hora_reset = time.time()
        
        # Contadores
        self.total_senales = len(self.historial.senales)
    
    async def conectar(self):
        """Establece conexión con Bullex"""
        print(f"\n  🔌 [{fmt_hora()}] Conectando a Bullex...")
        
        try:
            self.ws = await websockets.connect(
                WS_URL,
                origin='https://trade.bull-ex.com',
                ping_interval=30,
                ping_timeout=10
            )
            
            # Autenticar
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            
            # Suscribirse a datos
            await self.ws.send(json.dumps({
                'name': 'subscribeMessage',
                'msg': {'name': 'traders-mood-changed'}
            }))
            await self.ws.send(json.dumps({
                'name': 'subscribeMessage',
                'msg': {'name': 'candle-generated'}
            }))
            
            self.conectado = True
            print(f"  ✅ Conectado exitosamente\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Error de conexión: {e}\n")
            self.conectado = False
            return False
    
    def calcular_tiempos(self):
        """Calcula tiempos de entrada y expiración"""
        ahora = hora_rd()
        
        # Entrada al próximo minuto + anticipación
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=Config.ANTICIPACION_MINUTOS + 1)
        
        # Expiración
        expiracion = entrada + timedelta(minutes=Config.DURACION_OPERACION)
        
        # Segundos hasta entrada
        segundos = (entrada - ahora).total_seconds()
        
        return entrada, expiracion, int(segundos)
    
    def analizar_senal(self, aid, sentimiento_pct):
        """
        Analiza la calidad de una señal combinando sentimiento y técnico
        """
        # Obtener análisis técnico
        tecnico = self.analizador.obtener_analisis(aid)
        
        # Determinar dirección por sentimiento
        if sentimiento_pct > 50:
            direccion = "CALL"
            pct_base = sentimiento_pct
            direccion_num = 1
        else:
            direccion = "PUT"
            pct_base = 100 - sentimiento_pct
            direccion_num = -1
        
        # Calcular probabilidad ajustada
        probabilidad = pct_base
        
        # Bonus si tendencia confirma (+5%)
        if tecnico['tendencia'] == direccion_num:
            probabilidad = min(99, probabilidad + 5)
            confirmacion = "✅ CONFIRMADA"
            calidad = "ALTA"
        # Penalización si tendencia contradice (-15%)
        elif tecnico['tendencia'] == -direccion_num:
            probabilidad = max(50, probabilidad - 15)
            confirmacion = "⚠️ DIVERGENCIA"
            calidad = "BAJA"
        else:
            confirmacion = "➡️ NEUTRAL"
            calidad = "MEDIA"
        
        # Ajuste por momentum
        if tecnico['momentum'] > 60 and tecnico['tendencia'] == direccion_num:
            probabilidad = min(99, probabilidad + 3)
        
        return {
            'direccion': direccion,
            'probabilidad': probabilidad,
            'sentimiento': pct_base,
            'tendencia': tecnico['tendencia_texto'],
            'momentum': tecnico['momentum'],
            'confirmacion': confirmacion,
            'calidad': calidad
        }
    
    def generar_senal(self, aid, analisis):
        """Genera objeto de señal completo"""
        activo = ACTIVOS_OTC.get(aid)
        if not activo:
            return None
        
        ahora = hora_rd()
        entrada, expiracion, segundos = self.calcular_tiempos()
        
        # Determinar nivel de confianza
        prob = analisis['probabilidad']
        if prob >= 95:
            confianza = "🔥 EXTREMA"
            estrellas = "★★★★★"
        elif prob >= 90:
            confianza = "✅ MUY ALTA"
            estrellas = "★★★★☆"
        elif prob >= 85:
            confianza = "📊 ALTA"
            estrellas = "★★★☆☆"
        else:
            confianza = "⚠️ MEDIA"
            estrellas = "★★☆☆☆"
        
        self.total_senales += 1
        
        return {
            'id': f"{aid}_{int(time.time())}",
            'numero': self.total_senales,
            'timestamp': ahora.isoformat(),
            'activo_id': aid,
            'nombre': activo['nombre'],
            'simbolo': activo['simbolo'],
            'mercado': activo['mercado'],
            'direccion': analisis['direccion'],
            'probabilidad': prob,
            'sentimiento': analisis['sentimiento'],
            'tendencia': analisis['tendencia'],
            'confirmacion': analisis['confirmacion'],
            'confianza': confianza,
            'estrellas': estrellas,
            'calidad': analisis['calidad'],
            'hora_senal': fmt_hora(ahora),
            'entrada': fmt_hora(entrada),
            'entrada_dt': entrada.isoformat(),
            'expiracion': fmt_hora(expiracion),
            'expiracion_dt': expiracion.isoformat(),
            'segundos_hasta_entrada': segundos,
            'precio_entrada': self.precios.get(aid, 0),
            'verificado': False,
            'resultado': None
        }
    
    def mostrar_senal(self, s):
        """Muestra una señal en formato profesional"""
        mins = s['segundos_hasta_entrada'] // 60
        segs = s['segundos_hasta_entrada'] % 60
        
        # Colores según dirección
        if s['direccion'] == 'CALL':
            dir_emoji = "🟢🟢🟢"
            dir_texto = "COMPRAR (CALL) ↑"
        else:
            dir_emoji = "🔴🔴🔴"
            dir_texto = "VENDER (PUT) ↓"
        
        print("\n")
        print("╔" + "═" * 62 + "╗")
        print(f"║  🎯 SEÑAL #{s['numero']} - {s['confianza']:<40}  ║")
        print(f"║  {s['estrellas']:<58}  ║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  📍 Activo:      {s['nombre']:<43}║")
        print(f"║  🏷️  Símbolo:     {s['simbolo']:<43}║")
        print(f"║  📊 Mercado:     {s['mercado']:<43}║")
        print("╠" + "═" * 62 + "╣")
        print(f"║     {dir_emoji}  {dir_texto:<44}  ║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  📈 Probabilidad:   {s['probabilidad']:.0f}%{' ' * 39}║")
        print(f"║  👥 Sentimiento:    {s['sentimiento']:.0f}% de traders{' ' * 27}║")
        print(f"║  📉 Tendencia:      {s['tendencia']:<41}║")
        print(f"║  🔍 Análisis:       {s['confirmacion']:<41}║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  ⏰ ENTRAR EN:      {mins} min {segs:02d} seg{' ' * 33}║")
        print(f"║  🎯 HORA ENTRADA:   {s['entrada']:<41}║")
        print(f"║  ⏱️  EXPIRACIÓN:     {s['expiracion']:<41}║")
        print(f"║  ⌛ DURACIÓN:       {Config.DURACION_OPERACION} minutos{' ' * 35}║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  🕐 Hora RD:        {fmt_hora():<41}║")
        print("╚" + "═" * 62 + "╝")
    
    def mostrar_alerta_entrada(self, s):
        """Muestra alerta cuando es momento de entrar"""
        if s['direccion'] == 'CALL':
            dir_texto = "🟢 COMPRAR (CALL)"
        else:
            dir_texto = "🔴 VENDER (PUT)"
        
        print("\n")
        print("🔔" * 25)
        print("╔" + "═" * 54 + "╗")
        print(f"║  ⚡⚡⚡ ¡¡¡ ENTRAR AHORA !!! ⚡⚡⚡{' ' * 16}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║  📍 {s['nombre']:<48}║")
        print(f"║  🏷️  {s['simbolo']:<48}║")
        print(f"║  {dir_texto:<52}║")
        print(f"║  📈 Probabilidad: {s['probabilidad']:.0f}%{' ' * 32}║")
        print(f"║  ⏱️  Expira: {s['expiracion']}{' ' * 37}║")
        print("╚" + "═" * 54 + "╝")
        print("🔔" * 25)
        print("")
    
    def mostrar_resultado(self, s, resultado, precio_cierre):
        """Muestra el resultado de una operación"""
        if resultado == 'GANADA':
            emoji = "✅"
            texto = "¡GANADA!"
        else:
            emoji = "❌"
            texto = "PERDIDA"
        
        precio_entrada = s.get('precio_entrada', 0)
        if precio_entrada and precio_cierre:
            cambio = ((precio_cierre - precio_entrada) / precio_entrada) * 100
            cambio_texto = f"{cambio:+.4f}%"
        else:
            cambio_texto = "N/A"
        
        print(f"\n{emoji} RESULTADO: {s['nombre']} ({s['simbolo']}) - {texto}")
        print(f"   Dirección: {s['direccion']} | Cambio: {cambio_texto}")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas completas"""
        stats = self.historial.estadisticas()
        hoy = len(self.historial.senales_hoy())
        
        print("\n")
        print("┌" + "─" * 50 + "┐")
        print(f"│  📊 ESTADÍSTICAS{' ' * 33}│")
        print("├" + "─" * 50 + "┤")
        print(f"│  Señales hoy:          {hoy:<24}│")
        print(f"│  Señales esta hora:    {self.senales_hora_actual}/{Config.MAX_SENALES_HORA}{' ' * 18}│")
        print("├" + "─" * 50 + "┤")
        print(f"│  Total histórico:      {stats['total']:<24}│")
        print(f"│  Verificadas:          {stats['verificadas']:<24}│")
        print(f"│  ✅ Ganadas:           {stats['ganadas']:<24}│")
        print(f"│  ❌ Perdidas:          {stats['perdidas']:<24}│")
        print(f"│  ⏳ Pendientes:        {stats['pendientes']:<24}│")
        print("├" + "─" * 50 + "┤")
        print(f"│  📈 PRECISIÓN:         {stats['precision']:.1f}%{' ' * 21}│")
        print("└" + "─" * 50 + "┘")
    
    def mostrar_encabezado(self):
        """Muestra el encabezado del bot"""
        ahora = hora_rd()
        
        print("\n")
        print("╔" + "═" * 62 + "╗")
        print("║" + " " * 62 + "║")
        print("║     🏆  BULLEX BOT PRO - SEÑALES OTC  🏆" + " " * 18 + "║")
        print("║" + " " * 62 + "║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  🕐 Hora:           {fmt_hora(ahora)} (Rep. Dominicana){' ' * 14}║")
        print(f"║  📅 Fecha:          {fmt_fecha(ahora):<40}║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  📊 Umbral mínimo:  {Config.UMBRAL_SENTIMIENTO}% sentimiento{' ' * 24}║")
        print(f"║  🎯 Prob. mínima:   {Config.PROBABILIDAD_MINIMA}%{' ' * 37}║")
        print(f"║  ⏰ Anticipación:   {Config.ANTICIPACION_MINUTOS} minutos{' ' * 34}║")
        print(f"║  ⌛ Duración:       {Config.DURACION_OPERACION} minutos{' ' * 34}║")
        print(f"║  🔄 Cooldown:       {Config.COOLDOWN_ACTIVO//60} minutos entre señales{' ' * 19}║")
        print(f"║  📈 Máx/hora:       {Config.MAX_SENALES_HORA} señales{' ' * 33}║")
        print("╠" + "═" * 62 + "╣")
        print("║  ⌨️  Ctrl+C = Salir y ver estadísticas" + " " * 22 + "║")
        print("╚" + "═" * 62 + "╝")
    
    async def verificar_alertas(self):
        """Verifica señales programadas para alertar"""
        ahora = hora_rd()
        alertar = []
        
        for sid, senal in list(self.senales_programadas.items()):
            entrada_dt = datetime.fromisoformat(senal['entrada_dt'])
            restante = (entrada_dt - ahora).total_seconds()
            
            # Alertar 5 segundos antes
            if restante <= 5:
                self.mostrar_alerta_entrada(senal)
                senal['precio_entrada'] = self.precios.get(senal['activo_id'], 0)
                self.senales_activas[sid] = senal
                alertar.append(sid)
            
            # Recordatorio cada minuto
            elif int(restante) % 60 == 0 and restante > 30:
                emoji = "🟢" if senal['direccion'] == 'CALL' else "🔴"
                mins = int(restante) // 60
                print(f"  ⏳ {senal['simbolo']}: {emoji} {senal['direccion']} en {mins} min")
        
        for sid in alertar:
            del self.senales_programadas[sid]
    
    async def verificar_resultados(self):
        """Verifica resultados de operaciones expiradas"""
        ahora = hora_rd()
        verificadas = []
        
        for sid, senal in list(self.senales_activas.items()):
            expiracion = datetime.fromisoformat(senal['expiracion_dt'])
            
            # Verificar 5 segundos después de expiración
            if ahora >= expiracion + timedelta(seconds=5):
                aid = senal['activo_id']
                precio_cierre = self.precios.get(aid, 0)
                precio_entrada = senal.get('precio_entrada', 0)
                
                if precio_cierre and precio_entrada:
                    subio = precio_cierre > precio_entrada
                    
                    if senal['direccion'] == "CALL":
                        resultado = "GANADA" if subio else "PERDIDA"
                    else:
                        resultado = "GANADA" if not subio else "PERDIDA"
                    
                    self.historial.actualizar_resultado(sid, resultado, precio_cierre)
                    self.mostrar_resultado(senal, resultado, precio_cierre)
                    
                verificadas.append(sid)
        
        for sid in verificadas:
            del self.senales_activas[sid]
    
    async def procesar_mensaje(self, msg):
        """Procesa mensajes del WebSocket"""
        try:
            data = json.loads(msg)
            nombre = data.get('name', '')
            m = data.get('msg', {})
            
            # Actualizar velas y precios
            if nombre == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
                    self.analizador.agregar_vela(aid, m)
            
            # Procesar cambios de sentimiento
            elif nombre == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                valor = m.get('value', 0.5)
                
                # Filtrar blitz
                if 'blitz' in inst.lower():
                    return
                
                # Solo activos OTC permitidos
                if aid not in ACTIVOS_OTC:
                    return
                
                # Reset contador cada hora
                if time.time() - self.hora_reset >= 3600:
                    self.senales_hora_actual = 0
                    self.hora_reset = time.time()
                
                # Límite de señales por hora
                if self.senales_hora_actual >= Config.MAX_SENALES_HORA:
                    return
                
                # Calcular porcentaje
                call_pct = valor * 100
                
                # Filtro de sentimiento mínimo
                if call_pct < Config.UMBRAL_SENTIMIENTO and (100 - call_pct) < Config.UMBRAL_SENTIMIENTO:
                    return
                
                # Cooldown por activo
                ahora = time.time()
                clave = f"{aid}_{inst}"
                if clave in self.ultima_senal:
                    if ahora - self.ultima_senal[clave] < Config.COOLDOWN_ACTIVO:
                        return
                
                # Analizar señal
                analisis = self.analizar_senal(aid, call_pct)
                
                # Filtro de probabilidad mínima
                if analisis['probabilidad'] < Config.PROBABILIDAD_MINIMA:
                    return
                
                # Filtro de divergencia (opcional)
                if Config.CONFIRMAR_TENDENCIA and analisis['calidad'] == 'BAJA':
                    return
                
                # Generar y mostrar señal
                self.ultima_senal[clave] = ahora
                senal = self.generar_senal(aid, analisis)
                
                if senal:
                    self.mostrar_senal(senal)
                    self.historial.agregar(senal)
                    self.senales_programadas[senal['id']] = senal
                    self.senales_hora_actual += 1
                    
        except Exception as e:
            pass
    
    async def ejecutar(self):
        """Bucle principal del bot"""
        if not await self.conectar():
            print("\n  ❌ No se pudo conectar. Verifica tu SSID.")
            return
        
        self.mostrar_encabezado()
        self.mostrar_estadisticas()
        
        print("\n  🔍 Buscando señales de alta calidad...")
        print("  ⏳ Las señales aparecerán automáticamente\n")
        
        ultimo_check = time.time()
        
        try:
            while True:
                try:
                    # Recibir mensaje
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=1)
                    await self.procesar_mensaje(msg)
                    
                except asyncio.TimeoutError:
                    pass
                
                # Verificar alertas cada segundo
                await self.verificar_alertas()
                
                # Verificar resultados cada 5 segundos
                if time.time() - ultimo_check >= 5:
                    await self.verificar_resultados()
                    ultimo_check = time.time()
                
        except websockets.exceptions.ConnectionClosed:
            print(f"\n  ⚠️ [{fmt_hora()}] Conexión perdida. Reconectando...")
            self.conectado = False
            await asyncio.sleep(2)
            if await self.conectar():
                await self.ejecutar()
                
        except KeyboardInterrupt:
            pass
        
        # Mostrar resumen al salir
        print("\n\n" + "═" * 64)
        print("  📊 RESUMEN DE SESIÓN")
        print("═" * 64)
        self.mostrar_estadisticas()
        
        # Mostrar últimas señales
        ultimas = self.historial.ultimas(5)
        if ultimas:
            print("\n  📋 ÚLTIMAS SEÑALES:")
            print("  " + "─" * 58)
            for s in ultimas:
                resultado = s.get('resultado', 'PENDIENTE')
                if resultado == 'GANADA':
                    emoji = "✅"
                elif resultado == 'PERDIDA':
                    emoji = "❌"
                else:
                    emoji = "⏳"
                dir_emoji = "🟢" if s['direccion'] == 'CALL' else "🔴"
                print(f"  {emoji} {s['simbolo']:<20} {dir_emoji} {s['direccion']:<5} {resultado}")
        
        # Cerrar conexión
        if self.ws:
            await self.ws.close()
        
        print(f"\n  👋 [{fmt_hora()}] Bot cerrado")
        print("═" * 64 + "\n")

# ═══════════════════════════════════════════════════════════════════════════════
#                              PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def mostrar_bienvenida():
    """Muestra pantalla de bienvenida"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🏆  BULLEX BOT PRO - VERSIÓN FINAL  🏆                  ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   ✅ Análisis técnico (Tendencia + Momentum)                         ║
║   ✅ Análisis de sentimiento de traders                              ║
║   ✅ Solo activos OTC de Bullex                                      ║
║   ✅ Filtros estrictos = menos señales, más precisas                 ║
║   ✅ Hora República Dominicana (UTC-4)                               ║
║   ✅ Historial y estadísticas automáticas                            ║
║   ✅ Verificación de resultados                                      ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   📋 PASOS PARA OBTENER TU SSID:                                     ║
║                                                                      ║
║   1. Abre Chrome → https://trade.bull-ex.com                         ║
║   2. Haz login con tu cuenta                                         ║
║   3. Presiona F12 (DevTools)                                         ║
║   4. Click en "Application" → "Cookies"                              ║
║   5. Click en "https://trade.bull-ex.com"                            ║
║   6. Busca "ssid" y copia el valor                                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")


async def main():
    """Función principal"""
    mostrar_bienvenida()
    
    # Obtener SSID
    ssid = MI_SSID.strip()
    
    if not ssid:
        ssid = input("  🔑 Pega tu SSID aquí: ").strip()
    
    if not ssid:
        print("\n  ❌ Error: Necesitas un SSID válido para conectar.")
        print("  💡 Sigue los pasos de arriba para obtenerlo.\n")
        return
    
    # Iniciar bot
    bot = BotPro(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot detenido por el usuario\n")
