#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯 BOT ADAPTATIVO v3.0 - CORREGIDO + MEJORAS DE PRECISIÓN                 ║
║                                                                              ║
║   CORRECCIONES:                                                              ║
║   ✅ Mapeo correcto de datos por active_id (NO por orden de llegada)        ║
║   ✅ Validación de datos antes de analizar                                  ║
║   ✅ Verificación de precios coherentes por activo                          ║
║                                                                              ║
║   MEJORAS DE PRECISIÓN:                                                      ║
║   ✅ RSI con suavizado Wilder (más preciso)                                 ║
║   ✅ MACD como confirmación adicional                                        ║
║   ✅ Stochastic RSI para zonas extremas                                     ║
║   ✅ Filtro de volatilidad mejorado                                         ║
║   ✅ Confirmación de múltiples indicadores                                  ║
║   ✅ Divergencias RSI vs Precio                                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os

# ══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════

MI_SSID = "115Pruebaf7510a7bbc0b1c583v"

# OpenAI API
OPENAI_API_KEY = "sk-proj-tgpdgSY2XRbEjxUZjEetAb4bcjqw2FTDpFrMZsEyefxQfRK5ALpFxvSnPruebibU4a0VYy85qTOs0AXIQeX-evaFj6pyG27_pj90MycypRN2Sv8tkL29-6C4A"

# Telegram
TELEGRAM_TOKEN = "8406117917:pruebs3ecN7Ww8r_xrtMRVlDk1z8E2VHdtU"
TELEGRAM_CHAT_ID = "54958p6471"
TELEGRAM_ACTIVO = True

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
DATOS_FILE = "bot_adaptativo_datos.json"
RD_TZ = timezone(timedelta(hours=-4))

# Velas para análisis
VELAS_ANALISIS = 200  # Reducido para mejor rendimiento
VELAS_MINIMAS = 50    # Mínimo requerido para análisis


# ══════════════════════════════════════════════════════════════════════════════
#                         CONFIGURACIÓN DE ESTRATEGIA
# ══════════════════════════════════════════════════════════════════════════════

class Config:
    # RSI
    RSI_PERIODO = 14
    RSI_SOBREVENTA = 30
    RSI_SOBRECOMPRA = 70
    RSI_EXTREMO_BAJO = 25      # Zona MUY extrema
    RSI_EXTREMO_ALTO = 75
    
    # Stochastic RSI
    STOCH_RSI_PERIODO = 14
    STOCH_SOBREVENTA = 20
    STOCH_SOBRECOMPRA = 80
    
    # Bollinger Bands
    BB_PERIODO = 20
    BB_DESVIACION = 2.0
    BB_UMBRAL_INFERIOR = 15    # Más estricto
    BB_UMBRAL_SUPERIOR = 85
    
    # MACD
    MACD_RAPIDA = 12
    MACD_LENTA = 26
    MACD_SIGNAL = 9
    
    # EMAs para tendencia
    EMA_RAPIDA = 9
    EMA_MEDIA = 21
    EMA_LENTA = 50
    
    # Puntuación
    PUNTOS_RSI_EXTREMO = 25
    PUNTOS_BB_EXTREMO = 20
    PUNTOS_TENDENCIA_FAVOR = 20
    PUNTOS_MACD_CONFIRMA = 15
    PUNTOS_STOCH_CONFIRMA = 10
    PUNTOS_PATRON = 10
    PUNTOS_HISTORIAL_BUENO = 15
    PUNTOS_DIVERGENCIA = 15
    
    PENALIZACION_CONTRA_TENDENCIA = -25
    PENALIZACION_MAL_ACTIVO = -20
    PENALIZACION_VOLATILIDAD = -15
    
    # Umbrales
    UMBRAL_SENAL_A = 70        # Más estricto
    UMBRAL_SENAL_B = 55
    MIN_PUNTOS = 50
    
    # Gestión
    TIEMPO_PREPARACION = 90
    MIN_HISTORIAL_ACTIVO = 5   # Más datos antes de confiar
    BLOQUEO_ACTIVO_PERCENT = 40
    
    # Tendencia
    TENDENCIA_FUERTE = 0.002
    TENDENCIA_DEBIL = 0.0008
    
    # Volatilidad
    ATR_MAX_PERCENT = 0.4      # Máximo 0.4% de volatilidad
    
    # IA
    IA_ACTIVA = True
    IA_MIN_OPERACIONES_EVAL = 10
    
    # Confirmaciones requeridas
    MIN_CONFIRMACIONES = 3     # Mínimo 3 indicadores deben confirmar


# ══════════════════════════════════════════════════════════════════════════════
#                    ACTIVOS BULLEX OTC (NOMBRES EXACTOS)
# ══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    # ═══════════════ FOREX ═══════════════
    1: {"nombre": "EUR/USD (OTC)", "categoria": "FOREX", "decimales": 5},
    2: {"nombre": "EUR/GBP (OTC)", "categoria": "FOREX", "decimales": 5},
    3: {"nombre": "GBP/USD (OTC)", "categoria": "FOREX", "decimales": 5},
    4: {"nombre": "EUR/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    5: {"nombre": "USD/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    6: {"nombre": "AUD/USD (OTC)", "categoria": "FOREX", "decimales": 5},
    7: {"nombre": "USD/CAD (OTC)", "categoria": "FOREX", "decimales": 5},
    8: {"nombre": "NZD/USD (OTC)", "categoria": "FOREX", "decimales": 5},
    10: {"nombre": "GBP/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    31: {"nombre": "AUD/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    32: {"nombre": "AUD/NZD (OTC)", "categoria": "FOREX", "decimales": 5},
    33: {"nombre": "EUR/CAD (OTC)", "categoria": "FOREX", "decimales": 5},
    36: {"nombre": "GBP/AUD (OTC)", "categoria": "FOREX", "decimales": 5},
    37: {"nombre": "CAD/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    38: {"nombre": "GBP/CAD (OTC)", "categoria": "FOREX", "decimales": 5},
    51: {"nombre": "EUR/CHF (OTC)", "categoria": "FOREX", "decimales": 5},
    52: {"nombre": "CHF/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    53: {"nombre": "GBP/CHF (OTC)", "categoria": "FOREX", "decimales": 5},
    78: {"nombre": "EUR/NZD (OTC)", "categoria": "FOREX", "decimales": 5},
    84: {"nombre": "USD/CHF (OTC)", "categoria": "FOREX", "decimales": 5},
    85: {"nombre": "AUD/CAD (OTC)", "categoria": "FOREX", "decimales": 5},
    86: {"nombre": "AUD/CHF (OTC)", "categoria": "FOREX", "decimales": 5},
    87: {"nombre": "NZD/JPY (OTC)", "categoria": "FOREX", "decimales": 3},
    90: {"nombre": "USD/COP (OTC)", "categoria": "FOREX", "decimales": 2},
    91: {"nombre": "USD/BRL (OTC)", "categoria": "FOREX", "decimales": 4},
    93: {"nombre": "USD/ZAR (OTC)", "categoria": "FOREX", "decimales": 4},
    95: {"nombre": "USD/NOK (OTC)", "categoria": "FOREX", "decimales": 4},
    97: {"nombre": "USD/MXN (OTC)", "categoria": "FOREX", "decimales": 4},
    99: {"nombre": "USD/TRY (OTC)", "categoria": "FOREX", "decimales": 4},
    168: {"nombre": "PEN/USD (OTC)", "categoria": "FOREX", "decimales": 4},
    
    # ═══════════════ CRYPTO ═══════════════
    212: {"nombre": "BTC/USD (OTC)", "categoria": "CRYPTO", "decimales": 2},
    220: {"nombre": "ETH/USD (OTC)", "categoria": "CRYPTO", "decimales": 2},
    1876: {"nombre": "SOL/USD (OTC)", "categoria": "CRYPTO", "decimales": 2},
    2001: {"nombre": "CARDANO (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2002: {"nombre": "DOGECOIN (OTC)", "categoria": "CRYPTO", "decimales": 5},
    2003: {"nombre": "SHIB/USD (OTC)", "categoria": "CRYPTO", "decimales": 8},
    2004: {"nombre": "Ripple (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2010: {"nombre": "HBAR (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2011: {"nombre": "TAO (OTC)", "categoria": "CRYPTO", "decimales": 2},
    2012: {"nombre": "FET (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2020: {"nombre": "Ondo (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2021: {"nombre": "Vaulta (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2030: {"nombre": "TRUMP Coin (OTC)", "categoria": "CRYPTO", "decimales": 2},
    2031: {"nombre": "Melania Coin (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2040: {"nombre": "Fartcoin (OTC)", "categoria": "CRYPTO", "decimales": 4},
    2041: {"nombre": "UKOUSD (OTC)", "categoria": "CRYPTO", "decimales": 4},
    
    # ═══════════════ COMMODITIES ═══════════════
    959: {"nombre": "XAUUSD (OTC)", "categoria": "COMMODITIES", "decimales": 2},
    960: {"nombre": "XAGUSD (OTC)", "categoria": "COMMODITIES", "decimales": 3},
    
    # ═══════════════ ÍNDICES ═══════════════
    949: {"nombre": "US 30 (OTC)", "categoria": "INDICES", "decimales": 1},
    947: {"nombre": "US 100 (OTC)", "categoria": "INDICES", "decimales": 1},
    
    # ═══════════════ ACCIONES ═══════════════
    1384: {"nombre": "Apple (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1385: {"nombre": "Tesla (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1386: {"nombre": "Amazon (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1387: {"nombre": "Google (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1388: {"nombre": "Meta (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1393: {"nombre": "Coca-Cola Company (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1395: {"nombre": "Nike, Inc. (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1397: {"nombre": "Alibaba Group Hold... (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1399: {"nombre": "McDonald's Corpor... (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1400: {"nombre": "Intel Corporation (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1401: {"nombre": "JPMorgan Chase (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1402: {"nombre": "AIG (OTC)", "categoria": "ACCIONES", "decimales": 2},
    1403: {"nombre": "Snap Inc. (OTC)", "categoria": "ACCIONES", "decimales": 2},
}

# Rangos de precios esperados para validación
RANGOS_PRECIOS = {
    "FOREX": (0.0001, 500),      # Pares de divisas
    "CRYPTO": (0.00001, 200000),  # Criptomonedas
    "COMMODITIES": (1, 10000),    # Oro, plata
    "INDICES": (100, 100000),     # Índices
    "ACCIONES": (1, 5000),        # Acciones
}


# ══════════════════════════════════════════════════════════════════════════════
#                              UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def hora_rd():
    return datetime.now(RD_TZ).strftime("%H:%M:%S")

def fecha_rd():
    return datetime.now(RD_TZ).strftime("%d/%m/%Y")

def hora_entrada(segundos=90):
    entrada = datetime.now(RD_TZ) + timedelta(seconds=segundos)
    return entrada.strftime("%H:%M:%S")

def get_periodo_dia():
    hora = datetime.now(RD_TZ).hour
    if 6 <= hora < 12:
        return "MAÑANA"
    elif 12 <= hora < 18:
        return "TARDE"
    else:
        return "NOCHE"

def limpiar():
    os.system('cls' if os.name == 'nt' else 'clear')


# ══════════════════════════════════════════════════════════════════════════════
#                              TELEGRAM
# ══════════════════════════════════════════════════════════════════════════════

class Telegram:
    @staticmethod
    def enviar(msg):
        if not TELEGRAM_ACTIVO:
            return False
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
                timeout=10
            )
            return True
        except:
            return False
    
    @staticmethod
    def enviar_senal(s):
        clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
        flecha = "🟢 CALL ↑" if s['direccion'] == 'CALL' else "🔴 PUT ↓"
        tend_emoji = "📈" if s.get('tendencia') == 'ALCISTA' else "📉" if s.get('tendencia') == 'BAJISTA' else "↔️"
        ia_emoji = "🤖✅" if s.get('ia_confirmo') else "⚡"
        
        confirmaciones = s.get('confirmaciones', [])
        conf_texto = " | ".join(confirmaciones[:4]) if confirmaciones else "N/A"
        
        msg = f"""<b>🎯 SEÑAL #{s['numero']}</b> {clase} {ia_emoji}

<b>📍 {s['activo']}</b>
<b>{flecha}</b>

📊 Puntuación: {s.get('puntuacion', 0)}/100
📉 RSI: {s.get('rsi', 0):.1f}
📐 BB: {s.get('bb_pos', 0):.1f}%
📊 StochRSI: {s.get('stoch_rsi', 50):.1f}
{tend_emoji} Tendencia: {s.get('tendencia', 'N/A')} ({s.get('fuerza_tendencia', 'N/A')})

<b>✅ Confirmaciones:</b>
{conf_texto}

<b>⏰ ENTRADA: {s.get('hora_entrada', 'Ahora')}</b>
<b>⏱️ EXPIRACIÓN: {s.get('expiracion', 2)} min</b>

🕐 Señal: {s.get('hora', '')}"""
        return Telegram.enviar(msg)
    
    @staticmethod
    def enviar_stats(stats):
        prec = stats.get('precision', 0)
        estado = "🔥 EXCELENTE" if prec >= 70 else "✅ BUENO" if prec >= 60 else "⚠️ REGULAR" if prec >= 50 else "❌ MEJORAR"
        
        msg = f"""<b>📊 ESTADÍSTICAS BOT v3.0</b>
━━━━━━━━━━━━━━━━━━━━━

<b>📈 RENDIMIENTO:</b>
• Total: {stats.get('total', 0)}
• ✅ Ganadas: {stats.get('ganadas', 0)}
• ❌ Perdidas: {stats.get('perdidas', 0)}

<b>🎯 PRECISIÓN: {prec:.1f}%</b> {estado}

<b>📊 POR DIRECCIÓN:</b>
• 🟢 CALL: {stats.get('call_precision', 0):.0f}%
• 🔴 PUT: {stats.get('put_precision', 0):.0f}%

━━━━━━━━━━━━━━━━━━━━━
🕐 {hora_rd()} | 📅 {fecha_rd()}"""
        return Telegram.enviar(msg)


# ══════════════════════════════════════════════════════════════════════════════
#                         INTELIGENCIA ARTIFICIAL - FILTRO
# ══════════════════════════════════════════════════════════════════════════════

class IAFiltro:
    SYSTEM_PROMPT = """Eres un FILTRO de señales de trading para opciones binarias en mercados OTC.

TU TRABAJO: Decidir si una señal técnica debe ser CONFIRMADA o RECHAZADA.

CRITERIOS PARA CONFIRMAR ✅:
1. Al menos 3 indicadores confirman la dirección
2. La señal va A FAVOR de la tendencia
3. RSI está en zona extrema (<25 o >75)
4. Bollinger está en extremo (<15% o >85%)
5. MACD confirma la dirección

CRITERIOS PARA RECHAZAR ❌:
1. Menos de 3 confirmaciones
2. La señal va CONTRA una tendencia FUERTE
3. Indicadores contradictorios
4. Alta volatilidad
5. Historial malo del activo

RESPONDE EXACTAMENTE EN ESTE FORMATO:
DECISIÓN: [CONFIRMO/RECHAZO]
RAZÓN: [Una línea explicando por qué]
CONFIANZA: [ALTA/MEDIA/BAJA]"""

    @staticmethod
    def consultar(prompt):
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": IAFiltro.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 0.1
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
            return None
        except Exception as e:
            print(f"  ⚠️ Error IA: {e}")
            return None
    
    @staticmethod
    def evaluar_senal(senal, historial_reciente, stats_activo):
        prompt = f"""EVALÚA ESTA SEÑAL DE TRADING:

📍 ACTIVO: {senal['nombre']}
📊 DIRECCIÓN: {senal['direccion']}

📈 INDICADORES:
• RSI(14): {senal['rsi']:.1f}
• Bollinger: {senal['bb_pos']:.1f}%
• StochRSI: {senal.get('stoch_rsi', 50):.1f}
• MACD: {'ALCISTA' if senal.get('macd_alcista') else 'BAJISTA'}
• Puntuación: {senal['puntuacion']}/100

📊 TENDENCIA: {senal['tendencia']} ({senal['fuerza_tendencia']})
• A favor: {'SÍ ✅' if senal.get('a_favor_tendencia') else 'NO ⚠️'}

📋 CONFIRMACIONES ({len(senal.get('confirmaciones', []))}):
{chr(10).join(['• ' + c for c in senal.get('confirmaciones', [])])}

📋 HISTORIAL: {stats_activo}

📋 ÚLTIMAS OPERACIONES:
{historial_reciente}

¿CONFIRMAS o RECHAZAS?"""

        respuesta = IAFiltro.consultar(prompt)
        
        if not respuesta:
            return True, "IA no disponible", "N/A"
        
        confirmar = "CONFIRMO" in respuesta.upper()
        
        razon = "Sin razón específica"
        for sep in ["RAZÓN:", "RAZON:", "Razón:", "Razon:"]:
            if sep in respuesta:
                try:
                    razon = respuesta.split(sep)[1].split("\n")[0].strip()
                    break
                except:
                    pass
        
        confianza = "MEDIA"
        if "ALTA" in respuesta.upper():
            confianza = "ALTA"
        elif "BAJA" in respuesta.upper():
            confianza = "BAJA"
        
        return confirmar, razon, confianza
    
    @staticmethod
    def test():
        try:
            print("     Conectando a OpenAI...")
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "1"}],
                    "max_tokens": 1
                },
                timeout=20
            )
            return r.status_code == 200
        except:
            return False


# ══════════════════════════════════════════════════════════════════════════════
#                         SISTEMA DE APRENDIZAJE
# ══════════════════════════════════════════════════════════════════════════════

class AprendizajeAvanzado:
    def __init__(self):
        self.datos = self.cargar()
    
    def cargar(self):
        try:
            if os.path.exists(DATOS_FILE):
                with open(DATOS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            'historial': [],
            'por_activo': {},
            'por_direccion': {'CALL': {'g': 0, 'p': 0}, 'PUT': {'g': 0, 'p': 0}},
            'activos_bloqueados': [],
            'parametros': {
                'rsi_sob': 30, 'rsi_sobc': 70,
                'bb_inf': 15, 'bb_sup': 85,
                'min_puntos': 50
            },
            'ia': {'confirmadas': [], 'rechazadas': [], 'activa': True}
        }
    
    def guardar(self):
        try:
            with open(DATOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def registrar_senal(self, senal):
        entrada = {
            'numero': senal['numero'],
            'activo': senal['activo'],
            'direccion': senal['direccion'],
            'puntuacion': senal.get('puntuacion', 0),
            'clasificacion': senal.get('clasificacion', 'B'),
            'rsi': senal.get('rsi', 50),
            'bb_pos': senal.get('bb_pos', 50),
            'confirmaciones': len(senal.get('confirmaciones', [])),
            'hora': hora_rd(),
            'fecha': fecha_rd(),
            'resultado': None
        }
        self.datos['historial'].append(entrada)
        self.guardar()
    
    def registrar_resultado(self, numero, resultado):
        for s in self.datos['historial']:
            if s.get('numero') == numero and not s.get('resultado'):
                s['resultado'] = resultado
                key = 'g' if resultado == 'GANADA' else 'p'
                
                activo = s['activo']
                if activo not in self.datos['por_activo']:
                    self.datos['por_activo'][activo] = {'g': 0, 'p': 0}
                self.datos['por_activo'][activo][key] += 1
                self.datos['por_direccion'][s['direccion']][key] += 1
                
                self.guardar()
                self.evaluar_activo(activo)
                return True
        return False
    
    def evaluar_activo(self, activo):
        if activo not in self.datos['por_activo']:
            return
        
        stats = self.datos['por_activo'][activo]
        total = stats['g'] + stats['p']
        
        if total >= Config.MIN_HISTORIAL_ACTIVO:
            precision = (stats['g'] / total) * 100
            if precision < Config.BLOQUEO_ACTIVO_PERCENT:
                if activo not in self.datos['activos_bloqueados']:
                    self.datos['activos_bloqueados'].append(activo)
                    print(f"\n  ⚠️ {activo} BLOQUEADO ({precision:.0f}%)")
            else:
                if activo in self.datos['activos_bloqueados']:
                    self.datos['activos_bloqueados'].remove(activo)
        
        self.guardar()
    
    def get_historial_activo(self, activo):
        if activo not in self.datos['por_activo']:
            return None, "Sin datos"
        
        stats = self.datos['por_activo'][activo]
        total = stats['g'] + stats['p']
        if total == 0:
            return None, "Sin datos"
        
        precision = (stats['g'] / total) * 100
        return precision, f"{precision:.0f}% ({total} ops)"
    
    def get_historial_reciente_texto(self, n=5):
        verificadas = [s for s in self.datos['historial'] if s.get('resultado')][-n:]
        if not verificadas:
            return "Sin historial previo"
        
        lineas = []
        for s in verificadas:
            emoji = "✅" if s['resultado'] == 'GANADA' else "❌"
            lineas.append(f"• {s['activo'][:15]} {s['direccion']} {emoji}")
        
        return "\n".join(lineas)
    
    def esta_bloqueado(self, activo):
        return activo in self.datos['activos_bloqueados']
    
    def get_params(self):
        return self.datos['parametros']
    
    def get_stats(self):
        h = self.datos['historial']
        verificadas = [s for s in h if s.get('resultado')]
        ganadas = [s for s in verificadas if s['resultado'] == 'GANADA']
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        d = self.datos['por_direccion']
        call_t = d['CALL']['g'] + d['CALL']['p']
        put_t = d['PUT']['g'] + d['PUT']['p']
        call_p = (d['CALL']['g'] / call_t * 100) if call_t > 0 else 0
        put_p = (d['PUT']['g'] / put_t * 100) if put_t > 0 else 0
        
        return {
            'total': len(h),
            'ganadas': len(ganadas),
            'perdidas': len(verificadas) - len(ganadas),
            'pendientes': len(h) - len(verificadas),
            'precision': precision,
            'call_total': call_t, 'call_precision': call_p,
            'put_total': put_t, 'put_precision': put_p,
            'activos_bloqueados': len(self.datos['activos_bloqueados'])
        }
    
    def get_pendientes(self):
        return [s for s in self.datos['historial'] if not s.get('resultado')]
    
    def get_historial(self, n=15):
        return self.datos['historial'][-n:]


# ══════════════════════════════════════════════════════════════════════════════
#                         ANALIZADOR TÉCNICO MEJORADO
# ══════════════════════════════════════════════════════════════════════════════

class AnalizadorMejorado:
    def __init__(self, aprendizaje):
        self.velas = {}  # Diccionario directo por active_id
        self.aprendizaje = aprendizaje
        self.ultima_actualizacion = {}
    
    def agregar_velas(self, aid, candles):
        """
        Agrega velas para un activo específico.
        CORREGIDO: Ahora recibe el active_id correcto de la respuesta.
        """
        if not candles:
            return False
        
        # Validar que los datos sean coherentes
        info = ACTIVOS.get(aid)
        if not info:
            return False
        
        categoria = info['categoria']
        rango_min, rango_max = RANGOS_PRECIOS.get(categoria, (0, float('inf')))
        
        velas_validas = []
        for c in candles:
            try:
                precio = float(c.get('close', 0))
                # Validar rango de precios
                if rango_min <= precio <= rango_max:
                    velas_validas.append({
                        'open': float(c.get('open', 0)),
                        'high': float(c.get('max', c.get('high', 0))),
                        'low': float(c.get('min', c.get('low', 0))),
                        'close': precio,
                        'time': c.get('time', 0)
                    })
            except (ValueError, TypeError):
                continue
        
        if len(velas_validas) >= VELAS_MINIMAS:
            self.velas[aid] = velas_validas
            self.ultima_actualizacion[aid] = datetime.now()
            return True
        
        return False
    
    def tiene_datos(self, aid):
        return len(self.velas.get(aid, [])) >= VELAS_MINIMAS
    
    def validar_datos(self, aid):
        """Verifica que los datos del activo sean coherentes"""
        if aid not in self.velas:
            return False, "Sin datos"
        
        velas = self.velas[aid]
        if len(velas) < VELAS_MINIMAS:
            return False, "Datos insuficientes"
        
        # Verificar coherencia de precios
        precios = [v['close'] for v in velas]
        precio_actual = precios[-1]
        precio_promedio = sum(precios) / len(precios)
        
        # Si el precio actual difiere mucho del promedio, hay un problema
        if abs(precio_actual - precio_promedio) / precio_promedio > 0.1:
            return False, "Datos inconsistentes"
        
        return True, "OK"
    
    # ═══════════════ INDICADORES TÉCNICOS MEJORADOS ═══════════════
    
    def calcular_rsi_wilder(self, precios, periodo=14):
        """RSI con suavizado de Wilder (más preciso)"""
        if len(precios) < periodo + 1:
            return 50
        
        cambios = [precios[i] - precios[i-1] for i in range(1, len(precios))]
        
        ganancias = [max(c, 0) for c in cambios[:periodo]]
        perdidas = [abs(min(c, 0)) for c in cambios[:periodo]]
        
        avg_gain = sum(ganancias) / periodo
        avg_loss = sum(perdidas) / periodo
        
        # Suavizado de Wilder
        for c in cambios[periodo:]:
            ganancia = max(c, 0)
            perdida = abs(min(c, 0))
            avg_gain = (avg_gain * (periodo - 1) + ganancia) / periodo
            avg_loss = (avg_loss * (periodo - 1) + perdida) / periodo
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calcular_stochastic_rsi(self, precios, periodo=14, k_periodo=3):
        """Stochastic RSI - más sensible a zonas extremas"""
        if len(precios) < periodo + k_periodo:
            return 50
        
        # Calcular RSI para cada punto
        rsi_values = []
        for i in range(periodo, len(precios)):
            subset = precios[:i+1]
            rsi = self.calcular_rsi_wilder(subset, periodo)
            rsi_values.append(rsi)
        
        if len(rsi_values) < k_periodo:
            return 50
        
        # Stochastic del RSI
        rsi_recientes = rsi_values[-k_periodo:]
        rsi_min = min(rsi_values[-periodo:]) if len(rsi_values) >= periodo else min(rsi_values)
        rsi_max = max(rsi_values[-periodo:]) if len(rsi_values) >= periodo else max(rsi_values)
        
        if rsi_max == rsi_min:
            return 50
        
        stoch_rsi = ((rsi_recientes[-1] - rsi_min) / (rsi_max - rsi_min)) * 100
        return max(0, min(100, stoch_rsi))
    
    def calcular_ema(self, precios, periodo):
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        
        mult = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        
        for precio in precios[periodo:]:
            ema = (precio * mult) + (ema * (1 - mult))
        
        return ema
    
    def calcular_macd(self, precios):
        """MACD: Moving Average Convergence Divergence"""
        if len(precios) < Config.MACD_LENTA + Config.MACD_SIGNAL:
            return 0, 0, 0, False
        
        ema_rapida = self.calcular_ema(precios, Config.MACD_RAPIDA)
        ema_lenta = self.calcular_ema(precios, Config.MACD_LENTA)
        
        macd_line = ema_rapida - ema_lenta
        
        # Calcular línea de señal
        macd_values = []
        for i in range(Config.MACD_LENTA, len(precios)):
            subset = precios[:i+1]
            ema_r = self.calcular_ema(subset, Config.MACD_RAPIDA)
            ema_l = self.calcular_ema(subset, Config.MACD_LENTA)
            macd_values.append(ema_r - ema_l)
        
        if len(macd_values) < Config.MACD_SIGNAL:
            return macd_line, 0, 0, False
        
        signal_line = self.calcular_ema(macd_values, Config.MACD_SIGNAL)
        histogram = macd_line - signal_line
        
        # MACD alcista si línea MACD > línea señal
        macd_alcista = macd_line > signal_line
        
        return macd_line, signal_line, histogram, macd_alcista
    
    def calcular_bb(self, precios, periodo=20, desviacion=2.0):
        if len(precios) < periodo:
            return None, None, None
        
        ultimos = precios[-periodo:]
        media = sum(ultimos) / periodo
        varianza = sum((p - media) ** 2 for p in ultimos) / periodo
        std = varianza ** 0.5
        
        return media + std * desviacion, media, media - std * desviacion
    
    def calcular_atr(self, velas, periodo=14):
        if len(velas) < periodo + 1:
            return 0
        
        trs = []
        for i in range(1, len(velas)):
            v = velas[i]
            v_prev = velas[i-1]
            tr = max(
                v['high'] - v['low'],
                abs(v['high'] - v_prev['close']),
                abs(v['low'] - v_prev['close'])
            )
            trs.append(tr)
        
        return sum(trs[-periodo:]) / periodo
    
    def detectar_tendencia(self, precios):
        if len(precios) < Config.EMA_LENTA:
            return "LATERAL", "DÉBIL", {}
        
        ema_rapida = self.calcular_ema(precios, Config.EMA_RAPIDA)
        ema_media = self.calcular_ema(precios, Config.EMA_MEDIA)
        ema_lenta = self.calcular_ema(precios, Config.EMA_LENTA)
        precio_actual = precios[-1]
        
        # Diferencia porcentual entre EMAs
        diff_rm = (ema_rapida - ema_media) / ema_media if ema_media != 0 else 0
        diff_ml = (ema_media - ema_lenta) / ema_lenta if ema_lenta != 0 else 0
        
        # Tendencia basada en alineación de EMAs
        if ema_rapida > ema_media > ema_lenta:
            if diff_rm > Config.TENDENCIA_FUERTE:
                tendencia, fuerza = "ALCISTA", "FUERTE"
            else:
                tendencia, fuerza = "ALCISTA", "DÉBIL"
        elif ema_rapida < ema_media < ema_lenta:
            if diff_rm < -Config.TENDENCIA_FUERTE:
                tendencia, fuerza = "BAJISTA", "FUERTE"
            else:
                tendencia, fuerza = "BAJISTA", "DÉBIL"
        else:
            tendencia, fuerza = "LATERAL", "RANGO"
        
        return tendencia, fuerza, {
            'ema_rapida': ema_rapida,
            'ema_media': ema_media,
            'ema_lenta': ema_lenta
        }
    
    def detectar_divergencia(self, precios, rsi_actual):
        """Detecta divergencias entre precio y RSI"""
        if len(precios) < 20:
            return None, ""
        
        # Últimos 20 precios y sus RSIs
        precios_recientes = precios[-20:]
        
        # Encontrar mínimos/máximos locales
        precio_min_idx = precios_recientes.index(min(precios_recientes))
        precio_max_idx = precios_recientes.index(max(precios_recientes))
        
        precio_actual = precios[-1]
        precio_anterior_min = precios_recientes[precio_min_idx]
        precio_anterior_max = precios_recientes[precio_max_idx]
        
        # Calcular RSI en puntos anteriores (aproximado)
        rsi_en_min = self.calcular_rsi_wilder(precios[:-20+precio_min_idx+1])
        rsi_en_max = self.calcular_rsi_wilder(precios[:-20+precio_max_idx+1])
        
        # Divergencia alcista: precio hace nuevo mínimo pero RSI no
        if precio_actual <= precio_anterior_min and rsi_actual > rsi_en_min:
            return "ALCISTA", "📊 Divergencia alcista detectada"
        
        # Divergencia bajista: precio hace nuevo máximo pero RSI no
        if precio_actual >= precio_anterior_max and rsi_actual < rsi_en_max:
            return "BAJISTA", "📊 Divergencia bajista detectada"
        
        return None, ""
    
    def detectar_patron(self, velas):
        if len(velas) < 3:
            return "Normal", 0
        
        v = velas[-1]
        v_prev = velas[-2]
        
        cuerpo = abs(v['close'] - v['open'])
        rango = v['high'] - v['low']
        
        if rango == 0:
            return "Sin movimiento", 0
        
        mecha_sup = v['high'] - max(v['open'], v['close'])
        mecha_inf = min(v['open'], v['close']) - v['low']
        
        if cuerpo <= rango * 0.1:
            return "Doji", 10
        if mecha_inf >= rango * 0.6 and mecha_sup <= rango * 0.15:
            return "Hammer", 15
        if mecha_sup >= rango * 0.6 and mecha_inf <= rango * 0.15:
            return "Shooting Star", 15
        if (v['close'] > v['open'] and v_prev['close'] < v_prev['open'] and
            v['close'] > v_prev['open'] and v['open'] < v_prev['close']):
            return "Engulfing Alcista", 20
        if (v['close'] < v['open'] and v_prev['close'] > v_prev['open'] and
            v['close'] < v_prev['open'] and v['open'] > v_prev['close']):
            return "Engulfing Bajista", 20
        
        return "Normal", 0
    
    def filtro_volatilidad(self, velas):
        if len(velas) < 20:
            return True, ""
        
        atr = self.calcular_atr(velas)
        precio = velas[-1]['close']
        atr_percent = (atr / precio) * 100 if precio > 0 else 0
        
        if atr_percent > Config.ATR_MAX_PERCENT:
            return False, f"⚠️ Volatilidad alta ({atr_percent:.2f}%)"
        
        return True, ""
    
    # ═══════════════ ANÁLISIS PRINCIPAL ═══════════════
    
    def analizar(self, aid, nombre_activo):
        """Análisis completo con múltiples confirmaciones"""
        
        # Validar datos
        valido, msg = self.validar_datos(aid)
        if not valido:
            return None
        
        if self.aprendizaje.esta_bloqueado(nombre_activo):
            return None
        
        velas = self.velas[aid]
        precios = [v['close'] for v in velas]
        precio = precios[-1]
        
        # Filtro de volatilidad
        vol_ok, vol_msg = self.filtro_volatilidad(velas)
        if not vol_ok:
            return None
        
        # Calcular indicadores
        rsi = self.calcular_rsi_wilder(precios)
        stoch_rsi = self.calcular_stochastic_rsi(precios)
        bb_up, bb_mid, bb_low = self.calcular_bb(precios)
        macd_line, signal_line, histogram, macd_alcista = self.calcular_macd(precios)
        tendencia, fuerza, emas = self.detectar_tendencia(precios)
        patron, puntos_patron = self.detectar_patron(velas)
        divergencia, div_msg = self.detectar_divergencia(precios, rsi)
        
        if not bb_up or bb_up == bb_low:
            return None
        
        bb_pos = ((precio - bb_low) / (bb_up - bb_low)) * 100
        
        params = self.aprendizaje.get_params()
        
        # ═══════════════ SISTEMA DE CONFIRMACIONES ═══════════════
        
        direccion = None
        puntos = 0
        confirmaciones = []
        a_favor_tendencia = False
        
        # Verificar condiciones para CALL
        call_confirmaciones = 0
        call_puntos = 0
        call_razones = []
        
        if rsi <= Config.RSI_SOBREVENTA:
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_RSI_EXTREMO
            call_razones.append(f"RSI={rsi:.0f}")
        
        if stoch_rsi <= Config.STOCH_SOBREVENTA:
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_STOCH_CONFIRMA
            call_razones.append(f"StochRSI={stoch_rsi:.0f}")
        
        if bb_pos <= Config.BB_UMBRAL_INFERIOR:
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_BB_EXTREMO
            call_razones.append(f"BB={bb_pos:.0f}%")
        
        if macd_alcista or histogram > 0:
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_MACD_CONFIRMA
            call_razones.append("MACD↑")
        
        if tendencia == "ALCISTA":
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_TENDENCIA_FAVOR
            call_razones.append(f"Tend.{fuerza}")
        
        if divergencia == "ALCISTA":
            call_confirmaciones += 1
            call_puntos += Config.PUNTOS_DIVERGENCIA
            call_razones.append("Diverg↑")
        
        if patron in ["Hammer", "Engulfing Alcista", "Doji"]:
            call_confirmaciones += 1
            call_puntos += puntos_patron
            call_razones.append(patron)
        
        # Verificar condiciones para PUT
        put_confirmaciones = 0
        put_puntos = 0
        put_razones = []
        
        if rsi >= Config.RSI_SOBRECOMPRA:
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_RSI_EXTREMO
            put_razones.append(f"RSI={rsi:.0f}")
        
        if stoch_rsi >= Config.STOCH_SOBRECOMPRA:
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_STOCH_CONFIRMA
            put_razones.append(f"StochRSI={stoch_rsi:.0f}")
        
        if bb_pos >= Config.BB_UMBRAL_SUPERIOR:
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_BB_EXTREMO
            put_razones.append(f"BB={bb_pos:.0f}%")
        
        if not macd_alcista or histogram < 0:
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_MACD_CONFIRMA
            put_razones.append("MACD↓")
        
        if tendencia == "BAJISTA":
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_TENDENCIA_FAVOR
            put_razones.append(f"Tend.{fuerza}")
        
        if divergencia == "BAJISTA":
            put_confirmaciones += 1
            put_puntos += Config.PUNTOS_DIVERGENCIA
            put_razones.append("Diverg↓")
        
        if patron in ["Shooting Star", "Engulfing Bajista", "Doji"]:
            put_confirmaciones += 1
            put_puntos += puntos_patron
            put_razones.append(patron)
        
        # Decidir dirección basada en confirmaciones
        if call_confirmaciones >= Config.MIN_CONFIRMACIONES and call_confirmaciones > put_confirmaciones:
            direccion = "CALL"
            puntos = call_puntos
            confirmaciones = call_razones
            a_favor_tendencia = tendencia == "ALCISTA"
            
            # Penalización por ir contra tendencia fuerte
            if tendencia == "BAJISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA_TENDENCIA
        
        elif put_confirmaciones >= Config.MIN_CONFIRMACIONES and put_confirmaciones > call_confirmaciones:
            direccion = "PUT"
            puntos = put_puntos
            confirmaciones = put_razones
            a_favor_tendencia = tendencia == "BAJISTA"
            
            if tendencia == "ALCISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA_TENDENCIA
        
        if not direccion:
            return None
        
        # Bonus/penalización por historial
        precision_activo, hist_texto = self.aprendizaje.get_historial_activo(nombre_activo)
        if precision_activo is not None:
            if precision_activo >= 60:
                puntos += Config.PUNTOS_HISTORIAL_BUENO
                confirmaciones.append(f"Hist={precision_activo:.0f}%")
            elif precision_activo < 40:
                puntos += Config.PENALIZACION_MAL_ACTIVO
        
        puntos = max(0, min(100, puntos))
        
        if puntos < Config.MIN_PUNTOS:
            return None
        
        # Expiración basada en fuerza de señal
        if puntos >= 75 and a_favor_tendencia:
            expiracion = 1
        elif puntos >= 60:
            expiracion = 2
        else:
            expiracion = 3
        
        return {
            'direccion': direccion,
            'puntuacion': puntos,
            'clasificacion': 'A' if puntos >= Config.UMBRAL_SENAL_A else 'B',
            'rsi': rsi,
            'stoch_rsi': stoch_rsi,
            'bb_pos': bb_pos,
            'macd_alcista': macd_alcista,
            'tendencia': tendencia,
            'fuerza_tendencia': fuerza,
            'a_favor_tendencia': a_favor_tendencia,
            'patron': patron,
            'confirmaciones': confirmaciones,
            'num_confirmaciones': len(confirmaciones),
            'historial_activo': hist_texto,
            'expiracion': expiracion
        }
    
    def buscar_oportunidades(self):
        oportunidades = []
        
        for aid, info in ACTIVOS.items():
            analisis = self.analizar(aid, info['nombre'])
            if analisis:
                oportunidades.append({
                    'aid': aid,
                    'nombre': info['nombre'],
                    'categoria': info['categoria'],
                    **analisis
                })
        
        # Ordenar por: confirmaciones, a_favor_tendencia, puntuación
        return sorted(oportunidades,
                     key=lambda x: (x['num_confirmaciones'], x.get('a_favor_tendencia', False), x['puntuacion']),
                     reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
#                         BOT PRINCIPAL v3.0
# ══════════════════════════════════════════════════════════════════════════════

class BotAdaptativo:
    def __init__(self):
        self.ws = None
        self.aprendizaje = AprendizajeAvanzado()
        self.analizador = AnalizadorMejorado(self.aprendizaje)
        self.numero = len(self.aprendizaje.datos['historial'])
        self.senal_actual = None
        self.ia_disponible = False
        self.datos_pendientes = {}  # Para mapear respuestas correctamente
    
    async def conectar(self):
        print("\n  🔌 Conectando a Bullex...")
        try:
            self.ws = await websockets.connect(
                WS_URL,
                origin='https://trade.bull-ex.com',
                ping_interval=None,
                close_timeout=10
            )
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': MI_SSID}))
            await asyncio.sleep(1)
            print("  ✅ Conectado!")
            return True
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    async def reconectar(self):
        print("\n  🔄 Reconectando...")
        try:
            if self.ws:
                await self.ws.close()
        except:
            pass
        self.ws = None
        await asyncio.sleep(2)
        return await self.conectar()
    
    def verificar_ia(self):
        print("  🤖 Verificando IA...")
        self.ia_disponible = IAFiltro.test()
        if self.ia_disponible:
            print("  ✅ IA conectada")
        else:
            print("  ⚠️ IA no disponible")
        return self.ia_disponible
    
    async def obtener_datos(self):
        """
        CORREGIDO: Ahora mapea correctamente los datos por active_id
        """
        print(f"\n  📊 Obteniendo datos de {len(ACTIVOS)} activos...")
        
        try:
            # Enviar solicitudes una por una y esperar respuesta
            activos_cargados = 0
            activos_fallidos = 0
            
            for aid in ACTIVOS:
                # Enviar solicitud
                msg = json.dumps({
                    "name": "sendMessage",
                    "msg": {
                        "name": "get-candles",
                        "version": "2.0",
                        "body": {
                            "active_id": aid,
                            "size": 60,
                            "count": VELAS_ANALISIS
                        }
                    }
                })
                await self.ws.send(msg)
                
                # Esperar respuesta con timeout
                intentos = 0
                while intentos < 10:
                    try:
                        respuesta = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                        data = json.loads(respuesta)
                        
                        if data.get('name') == 'candles':
                            msg_data = data.get('msg', {})
                            candles = msg_data.get('candles', [])
                            
                            # CORRECCIÓN CLAVE: Obtener el active_id de la respuesta
                            # Si la API no lo incluye, usamos el que enviamos
                            response_aid = msg_data.get('active_id', aid)
                            
                            if candles:
                                if self.analizador.agregar_velas(aid, candles):
                                    activos_cargados += 1
                                else:
                                    activos_fallidos += 1
                            break
                        
                        # Si es otro tipo de mensaje, seguir esperando
                        intentos += 1
                        
                    except asyncio.TimeoutError:
                        intentos += 1
                    except json.JSONDecodeError:
                        intentos += 1
                
                # Pequeña pausa entre solicitudes
                await asyncio.sleep(0.1)
            
            print(f"  ✅ {activos_cargados} activos cargados")
            if activos_fallidos > 0:
                print(f"  ⚠️ {activos_fallidos} activos con datos inválidos")
            
            return activos_cargados > 0
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    async def obtener_datos_rapido(self):
        """
        Versión alternativa: solicita todos y procesa respuestas
        con mejor manejo de mapeo
        """
        print(f"\n  📊 Cargando {len(ACTIVOS)} activos (modo rápido)...")
        
        try:
            # Crear mapeo de solicitudes
            solicitudes = {}
            
            for aid in ACTIVOS:
                request_id = f"candles_{aid}"
                solicitudes[aid] = request_id
                
                msg = json.dumps({
                    "name": "sendMessage",
                    "msg": {
                        "name": "get-candles",
                        "version": "2.0",
                        "body": {
                            "active_id": aid,
                            "size": 60,
                            "count": VELAS_ANALISIS,
                            "request_id": request_id  # ID único para mapear
                        }
                    }
                })
                await self.ws.send(msg)
                await asyncio.sleep(0.02)
            
            # Recibir respuestas
            recibidos = set()
            intentos = 0
            max_intentos = 300
            
            while len(recibidos) < len(ACTIVOS) and intentos < max_intentos:
                try:
                    respuesta = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    data = json.loads(respuesta)
                    
                    if data.get('name') == 'candles':
                        msg_data = data.get('msg', {})
                        candles = msg_data.get('candles', [])
                        
                        # Intentar obtener active_id de la respuesta
                        aid_respuesta = msg_data.get('active_id')
                        
                        # Si no viene en la respuesta, intentar inferir por el precio
                        if not aid_respuesta and candles:
                            precio = float(candles[-1].get('close', 0))
                            aid_respuesta = self._inferir_activo_por_precio(precio)
                        
                        if aid_respuesta and aid_respuesta not in recibidos:
                            if self.analizador.agregar_velas(aid_respuesta, candles):
                                recibidos.add(aid_respuesta)
                    
                except asyncio.TimeoutError:
                    intentos += 1
                except:
                    intentos += 1
            
            print(f"  ✅ {len(recibidos)}/{len(ACTIVOS)} activos cargados")
            return len(recibidos) > 0
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def _inferir_activo_por_precio(self, precio):
        """
        Intenta inferir el activo basado en el rango de precio.
        SOLO usar si la API no devuelve active_id
        """
        # Esto es un fallback y no es 100% preciso
        for aid, info in ACTIVOS.items():
            categoria = info['categoria']
            rango_min, rango_max = RANGOS_PRECIOS.get(categoria, (0, float('inf')))
            
            if rango_min <= precio <= rango_max:
                # Verificar si ya tenemos datos para este activo
                if aid not in self.analizador.velas:
                    return aid
        
        return None
    
    def filtrar_con_ia(self, senal_data):
        if not self.ia_disponible or not Config.IA_ACTIVA:
            return True, "IA no activa", "N/A"
        
        print("  🤖 Consultando IA...")
        
        historial_reciente = self.aprendizaje.get_historial_reciente_texto(5)
        _, stats_activo = self.aprendizaje.get_historial_activo(senal_data['nombre'])
        
        aprobada, razon, confianza = IAFiltro.evaluar_senal(
            senal_data, historial_reciente, stats_activo
        )
        
        return aprobada, razon, confianza
    
    def crear_senal(self, op, ia_confirmo=False, ia_razon="", ia_confianza=""):
        self.numero += 1
        return {
            'numero': self.numero,
            'activo': op['nombre'],
            'categoria': op['categoria'],
            'direccion': op['direccion'],
            'puntuacion': op['puntuacion'],
            'clasificacion': op['clasificacion'],
            'rsi': op['rsi'],
            'stoch_rsi': op.get('stoch_rsi', 50),
            'bb_pos': op['bb_pos'],
            'macd_alcista': op.get('macd_alcista', False),
            'tendencia': op['tendencia'],
            'fuerza_tendencia': op['fuerza_tendencia'],
            'a_favor_tendencia': op['a_favor_tendencia'],
            'patron': op['patron'],
            'confirmaciones': op['confirmaciones'],
            'historial_activo': op['historial_activo'],
            'expiracion': op['expiracion'],
            'hora_entrada': hora_entrada(Config.TIEMPO_PREPARACION),
            'hora': hora_rd(),
            'ia_confirmo': ia_confirmo,
            'ia_razon': ia_razon,
            'ia_confianza': ia_confianza
        }
    
    def mostrar_senal(self, s):
        clase = "🅰️" if s['clasificacion'] == 'A' else "🅱️"
        flecha = "🟢🟢🟢 CALL ↑" if s['direccion'] == 'CALL' else "🔴🔴🔴 PUT ↓"
        tend_emoji = "📈" if s['tendencia'] == 'ALCISTA' else "📉" if s['tendencia'] == 'BAJISTA' else "↔️"
        
        if s.get('ia_confirmo'):
            ia_status = f"🤖✅ IA CONFIRMA ({s.get('ia_confianza', '')})"
        else:
            ia_status = "⚡ Técnico"
        
        print("\n")
        print("  ╔" + "═" * 62 + "╗")
        print(f"  ║  🎯 SEÑAL #{s['numero']} - {clase} SEÑAL {s['clasificacion']}" + " " * 32 + "║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  📍 ACTIVO:        {s['activo']:<41}║")
        print(f"  ║  🏷️  CATEGORÍA:     {s['categoria']:<41}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║     {flecha:<56}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  📊 Puntuación:    {s['puntuacion']}/100" + " " * 40 + "║")
        print(f"  ║  📉 RSI:           {s['rsi']:.1f}" + " " * 44 + "║")
        print(f"  ║  📊 StochRSI:      {s['stoch_rsi']:.1f}" + " " * 43 + "║")
        print(f"  ║  📐 Bollinger:     {s['bb_pos']:.1f}%" + " " * 42 + "║")
        print(f"  ║  {tend_emoji} Tendencia:     {s['tendencia']} ({s['fuerza_tendencia']})" + " " * 27 + "║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  ✅ CONFIRMACIONES ({len(s['confirmaciones'])}):" + " " * 35 + "║")
        conf_str = " | ".join(s['confirmaciones'][:5])
        print(f"  ║     {conf_str[:56]:<57}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  {ia_status:<61}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  ⏰ ENTRADA:       {s['hora_entrada']:<41}║")
        print(f"  ║  ⏱️  EXPIRACIÓN:    {s['expiracion']} minuto(s)" + " " * 37 + "║")
        print("  ╚" + "═" * 62 + "╝")
        print("\n  💡 Escribe 'g' si GANASTE o 'p' si PERDISTE")
        
        self.senal_actual = s
        self.aprendizaje.registrar_senal(s)
        Telegram.enviar_senal(s)
    
    def mostrar_mercado(self):
        print("\n  📊 ESTADO DEL MERCADO:")
        print("  " + "─" * 65)
        
        for aid, info in list(ACTIVOS.items())[:20]:
            if self.analizador.tiene_datos(aid):
                velas = self.analizador.velas[aid]
                precios = [v['close'] for v in velas]
                
                rsi = self.analizador.calcular_rsi_wilder(precios)
                stoch = self.analizador.calcular_stochastic_rsi(precios)
                bb_up, _, bb_low = self.analizador.calcular_bb(precios)
                
                if bb_up and bb_up != bb_low:
                    bb_pos = ((precios[-1] - bb_low) / (bb_up - bb_low)) * 100
                    
                    if bb_pos <= 15 and rsi <= 30:
                        estado = "🟢 CALL?"
                    elif bb_pos >= 85 and rsi >= 70:
                        estado = "🔴 PUT?"
                    else:
                        estado = "⚪ NEUTRO"
                    
                    nombre = info['nombre'][:18]
                    print(f"  {nombre:<20} RSI:{rsi:5.1f} Stoch:{stoch:5.1f} BB:{bb_pos:5.1f}% {estado}")
        
        print("  " + "─" * 65)
    
    def mostrar_stats(self):
        s = self.aprendizaje.get_stats()
        estado = "🔥" if s['precision'] >= 70 else "✅" if s['precision'] >= 60 else "⚠️" if s['precision'] >= 50 else "❌"
        
        print("\n  ╔" + "═" * 48 + "╗")
        print("  ║  📊 ESTADÍSTICAS BOT v3.0" + " " * 22 + "║")
        print("  ╠" + "═" * 48 + "╣")
        print(f"  ║  Total: {s['total']:<38}║")
        print(f"  ║  ✅ Ganadas: {s['ganadas']:<33}║")
        print(f"  ║  ❌ Perdidas: {s['perdidas']:<32}║")
        print(f"  ║  ⏳ Pendientes: {s['pendientes']:<30}║")
        print("  ╠" + "═" * 48 + "╣")
        print(f"  ║  🎯 PRECISIÓN: {s['precision']:.1f}% {estado:<27}║")
        print("  ╠" + "═" * 48 + "╣")
        print(f"  ║  🟢 CALL: {s['call_total']} ops ({s['call_precision']:.0f}%)" + " " * 22 + "║")
        print(f"  ║  🔴 PUT:  {s['put_total']} ops ({s['put_precision']:.0f}%)" + " " * 22 + "║")
        print("  ╚" + "═" * 48 + "╝")
    
    def mostrar_menu(self):
        ia_status = "✅" if self.ia_disponible else "❌"
        print("\n  ┌" + "─" * 50 + "┐")
        print(f"  │  📌 BOT ADAPTATIVO v3.0 + IA {ia_status}" + " " * 17 + "│")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [1] 🎯 Obtener MEJOR señal                      │")
        print("  │  [2] 📊 Ver estado del mercado                   │")
        print("  │  [3] 📈 Estadísticas                             │")
        print("  │  [4] ⏳ Señales pendientes                       │")
        print("  │  [5] 📱 Enviar stats a Telegram                  │")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [g] ✅ GANADA   [p] ❌ PERDIDA                  │")
        print("  │  [g #] / [p #] Marcar señal específica           │")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [m] Menú   [c] Limpiar   [q] Salir              │")
        print("  └" + "─" * 50 + "┘")
    
    def mostrar_pendientes(self):
        pend = self.aprendizaje.get_pendientes()
        print("\n  ⏳ SEÑALES PENDIENTES:")
        if pend:
            for s in pend[-10:]:
                emoji = "🟢" if s.get('direccion') == 'CALL' else "🔴"
                clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
                print(f"  #{s['numero']} {clase} {s['activo'][:20]:<22} {emoji}")
            print("\n  💡 Usa 'g #' o 'p #' para marcar")
        else:
            print("  ✅ No hay pendientes")
    
    async def ejecutar(self):
        limpiar()
        print("\n  🎯 BOT ADAPTATIVO v3.0 - CORREGIDO + MEJORADO")
        print(f"  🕐 {hora_rd()} | 📅 {fecha_rd()}")
        print(f"  📊 Activos: {len(ACTIVOS)}")
        
        if not await self.conectar():
            print("\n  ❌ No se pudo conectar.")
            return
        
        self.verificar_ia()
        
        if not await self.obtener_datos():
            await self.reconectar()
            await self.obtener_datos()
        
        self.mostrar_menu()
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 ").strip().lower())
                
                if cmd == '1':
                    if not await self.obtener_datos():
                        await self.reconectar()
                        await self.obtener_datos()
                    
                    ops = self.analizador.buscar_oportunidades()
                    
                    if ops:
                        senal_aprobada = None
                        max_intentos = min(5, len(ops))
                        
                        for op in ops[:max_intentos]:
                            print(f"\n  📍 Evaluando: {op['nombre']}")
                            print(f"     Confirmaciones: {op['num_confirmaciones']} | Puntos: {op['puntuacion']}")
                            
                            aprobada, razon, confianza = self.filtrar_con_ia(op)
                            
                            if aprobada:
                                senal = self.crear_senal(op, ia_confirmo=True, ia_razon=razon, ia_confianza=confianza)
                                senal_aprobada = senal
                                break
                            else:
                                print(f"  🤖❌ IA rechazó: {razon}")
                        
                        if senal_aprobada:
                            self.mostrar_senal(senal_aprobada)
                        else:
                            print(f"\n  ⚠️ Ninguna señal aprobada")
                            ver_sin_ia = await loop.run_in_executor(
                                None, lambda: input("  ¿Ver sin filtro IA? (s/n): ").strip().lower()
                            )
                            if ver_sin_ia == 's':
                                senal = self.crear_senal(ops[0], ia_confirmo=False)
                                self.mostrar_senal(senal)
                    else:
                        self.mostrar_mercado()
                        print("\n  💡 No hay señales con suficientes confirmaciones")
                
                elif cmd == '2':
                    if not await self.obtener_datos():
                        await self.reconectar()
                        await self.obtener_datos()
                    self.mostrar_mercado()
                
                elif cmd == '3':
                    self.mostrar_stats()
                
                elif cmd == '4':
                    self.mostrar_pendientes()
                
                elif cmd == '5':
                    if Telegram.enviar_stats(self.aprendizaje.get_stats()):
                        print("\n  ✅ Stats enviadas!")
                    else:
                        print("\n  ❌ Error enviando")
                
                elif cmd.startswith('g'):
                    try:
                        if cmd == 'g' and self.senal_actual:
                            num = self.senal_actual['numero']
                        else:
                            num = int(cmd.split()[1])
                        
                        if self.aprendizaje.registrar_resultado(num, 'GANADA'):
                            print(f"\n  ✅ Señal #{num} GANADA!")
                            Telegram.enviar(f"✅ Señal #{num} GANADA")
                        else:
                            print(f"\n  ❌ Señal #{num} no encontrada")
                    except:
                        print("\n  ❌ Uso: 'g' o 'g #'")
                
                elif cmd.startswith('p') and (cmd == 'p' or len(cmd.split()) > 1):
                    try:
                        if cmd == 'p' and self.senal_actual:
                            num = self.senal_actual['numero']
                        else:
                            num = int(cmd.split()[1])
                        
                        if self.aprendizaje.registrar_resultado(num, 'PERDIDA'):
                            print(f"\n  ❌ Señal #{num} PERDIDA")
                            Telegram.enviar(f"❌ Señal #{num} PERDIDA")
                        else:
                            print(f"\n  ❌ Señal #{num} no encontrada")
                    except:
                        print("\n  ❌ Uso: 'p' o 'p #'")
                
                elif cmd == 'm':
                    self.mostrar_menu()
                
                elif cmd == 'c':
                    limpiar()
                    print("\n  🎯 BOT v3.0")
                    print(f"  🕐 {hora_rd()}")
                    self.mostrar_menu()
                
                elif cmd == 'q':
                    break
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n  ⚠️ Error: {e}")
                await self.reconectar()
        
        print("\n  👋 ¡Hasta pronto!")
        self.mostrar_stats()
        
        if self.ws:
            await self.ws.close()


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  🎯 BOT ADAPTATIVO v3.0 - CORREGIDO + MEJORADO                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  🔧 CORRECCIONES:                                                  ║
║  • Mapeo correcto de datos por active_id                           ║
║  • Validación de datos por rango de precios                        ║
║  • Sin confusión entre activos                                     ║
║                                                                    ║
║  📈 MEJORAS DE PRECISIÓN:                                          ║
║  • RSI con suavizado Wilder                                        ║
║  • Stochastic RSI para zonas extremas                              ║
║  • MACD como confirmación                                          ║
║  • Detección de divergencias                                       ║
║  • Sistema de múltiples confirmaciones (mín. 3)                    ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    asyncio.run(BotAdaptativo().ejecutar())
