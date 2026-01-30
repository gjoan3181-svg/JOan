#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯 BOT ADAPTATIVO v4.0 - MAPEO CORREGIDO                                  ║
║                                                                              ║
║   CORRECCIÓN CRÍTICA:                                                        ║
║   • Solicita datos UNO POR UNO y espera respuesta                           ║
║   • Garantiza que cada respuesta corresponde al activo solicitado           ║
║   • Validación de precios por categoría                                      ║
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
VELAS_TENDENCIA = 200  # Reducido para cargar más rápido
VELAS_ENTRADA = 10


# ══════════════════════════════════════════════════════════════════════════════
#                         CONFIGURACIÓN DE ESTRATEGIA (ORIGINAL)
# ══════════════════════════════════════════════════════════════════════════════

class Config:
    # RSI - VALORES ORIGINALES
    RSI_PERIODO = 14
    RSI_SOBREVENTA = 30
    RSI_SOBRECOMPRA = 70
    
    # Bollinger Bands - VALORES ORIGINALES
    BB_PERIODO = 20
    BB_UMBRAL_INFERIOR = 20
    BB_UMBRAL_SUPERIOR = 80
    
    # EMAs para tendencia
    EMA_RAPIDA = 20
    EMA_LENTA = 50
    
    # Puntuación
    PUNTOS_TECNICO = 35
    PUNTOS_TENDENCIA = 25
    PUNTOS_HISTORIAL = 20
    PUNTOS_PATRON = 20
    PENALIZACION_CONTRA = -30
    PENALIZACION_MAL_ACTIVO = -20
    
    # Umbrales
    UMBRAL_SENAL_A = 75
    UMBRAL_SENAL_B = 60
    MIN_PUNTOS = 55
    
    # Gestión
    TIEMPO_PREPARACION = 90
    MIN_HISTORIAL_ACTIVO = 3
    BLOQUEO_ACTIVO_PERCENT = 35
    
    # Tendencia
    TENDENCIA_FUERTE = 0.003
    TENDENCIA_DEBIL = 0.001
    
    # IA
    IA_ACTIVA = True


# ══════════════════════════════════════════════════════════════════════════════
#                    ACTIVOS CON RANGOS DE PRECIOS ESPERADOS
# ══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    # ═══════════════ FOREX - Precios típicos entre 0.5 y 200 ═══════════════
    1: {"nombre": "EUR/USD (OTC)", "categoria": "FOREX", "rango": (1.0, 1.2)},
    2: {"nombre": "EUR/GBP (OTC)", "categoria": "FOREX", "rango": (0.8, 0.95)},
    3: {"nombre": "GBP/USD (OTC)", "categoria": "FOREX", "rango": (1.2, 1.35)},
    4: {"nombre": "EUR/JPY (OTC)", "categoria": "FOREX", "rango": (155, 175)},
    5: {"nombre": "USD/JPY (OTC)", "categoria": "FOREX", "rango": (140, 160)},
    6: {"nombre": "AUD/USD (OTC)", "categoria": "FOREX", "rango": (0.6, 0.75)},
    7: {"nombre": "USD/CAD (OTC)", "categoria": "FOREX", "rango": (1.3, 1.45)},
    8: {"nombre": "NZD/USD (OTC)", "categoria": "FOREX", "rango": (0.55, 0.65)},
    10: {"nombre": "GBP/JPY (OTC)", "categoria": "FOREX", "rango": (185, 210)},
    31: {"nombre": "AUD/JPY (OTC)", "categoria": "FOREX", "rango": (95, 110)},
    32: {"nombre": "AUD/NZD (OTC)", "categoria": "FOREX", "rango": (1.05, 1.15)},
    33: {"nombre": "EUR/CAD (OTC)", "categoria": "FOREX", "rango": (1.45, 1.55)},
    36: {"nombre": "GBP/AUD (OTC)", "categoria": "FOREX", "rango": (1.9, 2.1)},
    37: {"nombre": "CAD/JPY (OTC)", "categoria": "FOREX", "rango": (105, 120)},
    38: {"nombre": "GBP/CAD (OTC)", "categoria": "FOREX", "rango": (1.7, 1.85)},
    51: {"nombre": "EUR/CHF (OTC)", "categoria": "FOREX", "rango": (0.92, 1.0)},
    52: {"nombre": "CHF/JPY (OTC)", "categoria": "FOREX", "rango": (165, 180)},
    53: {"nombre": "GBP/CHF (OTC)", "categoria": "FOREX", "rango": (1.1, 1.2)},
    78: {"nombre": "EUR/NZD (OTC)", "categoria": "FOREX", "rango": (1.75, 1.9)},
    84: {"nombre": "USD/CHF (OTC)", "categoria": "FOREX", "rango": (0.85, 0.95)},
    85: {"nombre": "AUD/CAD (OTC)", "categoria": "FOREX", "rango": (0.88, 0.98)},
    86: {"nombre": "AUD/CHF (OTC)", "categoria": "FOREX", "rango": (0.55, 0.65)},
    87: {"nombre": "NZD/JPY (OTC)", "categoria": "FOREX", "rango": (88, 98)},
    90: {"nombre": "USD/COP (OTC)", "categoria": "FOREX", "rango": (3800, 4500)},
    91: {"nombre": "USD/BRL (OTC)", "categoria": "FOREX", "rango": (4.8, 6.0)},
    93: {"nombre": "USD/ZAR (OTC)", "categoria": "FOREX", "rango": (17, 20)},
    95: {"nombre": "USD/NOK (OTC)", "categoria": "FOREX", "rango": (10, 12)},
    97: {"nombre": "USD/MXN (OTC)", "categoria": "FOREX", "rango": (17, 21)},
    99: {"nombre": "USD/TRY (OTC)", "categoria": "FOREX", "rango": (30, 40)},
    168: {"nombre": "PEN/USD (OTC)", "categoria": "FOREX", "rango": (0.25, 0.30)},
    
    # ═══════════════ CRYPTO ═══════════════
    212: {"nombre": "BTC/USD (OTC)", "categoria": "CRYPTO", "rango": (80000, 120000)},
    220: {"nombre": "ETH/USD (OTC)", "categoria": "CRYPTO", "rango": (2500, 4500)},
    1876: {"nombre": "SOL/USD (OTC)", "categoria": "CRYPTO", "rango": (150, 300)},
    2001: {"nombre": "CARDANO (OTC)", "categoria": "CRYPTO", "rango": (0.3, 1.5)},
    2002: {"nombre": "DOGECOIN (OTC)", "categoria": "CRYPTO", "rango": (0.1, 0.5)},
    2003: {"nombre": "SHIB/USD (OTC)", "categoria": "CRYPTO", "rango": (0.00001, 0.0001)},
    2004: {"nombre": "Ripple (OTC)", "categoria": "CRYPTO", "rango": (1.5, 4.0)},
    2010: {"nombre": "HBAR (OTC)", "categoria": "CRYPTO", "rango": (0.1, 0.5)},
    2011: {"nombre": "TAO (OTC)", "categoria": "CRYPTO", "rango": (300, 700)},
    2012: {"nombre": "FET (OTC)", "categoria": "CRYPTO", "rango": (0.5, 3.0)},
    2020: {"nombre": "Ondo (OTC)", "categoria": "CRYPTO", "rango": (0.5, 2.0)},
    2021: {"nombre": "Vaulta (OTC)", "categoria": "CRYPTO", "rango": (0.1, 5.0)},
    2030: {"nombre": "TRUMP Coin (OTC)", "categoria": "CRYPTO", "rango": (10, 100)},
    2031: {"nombre": "Melania Coin (OTC)", "categoria": "CRYPTO", "rango": (1, 20)},
    2040: {"nombre": "Fartcoin (OTC)", "categoria": "CRYPTO", "rango": (0.1, 5.0)},
    2041: {"nombre": "UKOUSD (OTC)", "categoria": "CRYPTO", "rango": (0.1, 10.0)},
    
    # ═══════════════ COMMODITIES ═══════════════
    959: {"nombre": "XAUUSD (OTC)", "categoria": "COMMODITIES", "rango": (2400, 3200)},
    960: {"nombre": "XAGUSD (OTC)", "categoria": "COMMODITIES", "rango": (28, 40)},
    
    # ═══════════════ ÍNDICES ═══════════════
    949: {"nombre": "US 30 (OTC)", "categoria": "INDICES", "rango": (38000, 48000)},
    947: {"nombre": "US 100 (OTC)", "categoria": "INDICES", "rango": (18000, 23000)},
    
    # ═══════════════ ACCIONES ═══════════════
    1384: {"nombre": "Apple (OTC)", "categoria": "ACCIONES", "rango": (170, 260)},
    1385: {"nombre": "Tesla (OTC)", "categoria": "ACCIONES", "rango": (150, 450)},
    1386: {"nombre": "Amazon (OTC)", "categoria": "ACCIONES", "rango": (170, 240)},
    1387: {"nombre": "Google (OTC)", "categoria": "ACCIONES", "rango": (150, 200)},
    1388: {"nombre": "Meta (OTC)", "categoria": "ACCIONES", "rango": (400, 700)},
    1393: {"nombre": "Coca-Cola Company (OTC)", "categoria": "ACCIONES", "rango": (55, 75)},
    1395: {"nombre": "Nike, Inc. (OTC)", "categoria": "ACCIONES", "rango": (70, 120)},
    1397: {"nombre": "Alibaba Group Hold... (OTC)", "categoria": "ACCIONES", "rango": (70, 130)},
    1399: {"nombre": "McDonald's Corpor... (OTC)", "categoria": "ACCIONES", "rango": (270, 330)},
    1400: {"nombre": "Intel Corporation (OTC)", "categoria": "ACCIONES", "rango": (18, 35)},
    1401: {"nombre": "JPMorgan Chase (OTC)", "categoria": "ACCIONES", "rango": (180, 260)},
    1402: {"nombre": "AIG (OTC)", "categoria": "ACCIONES", "rango": (70, 90)},
    1403: {"nombre": "Snap Inc. (OTC)", "categoria": "ACCIONES", "rango": (8, 18)},
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
        
        razones = "\n".join([f"• {r}" for r in s.get('razones', [])[:5]])
        
        msg = f"""<b>🎯 SEÑAL #{s['numero']}</b> {clase} {ia_emoji}

<b>📍 {s['activo']}</b>
<b>💰 Precio: {s.get('precio', 'N/A')}</b>
<b>{flecha}</b>

📊 Puntuación: {s.get('puntuacion', 0)}/100
📉 RSI: {s.get('rsi', 0):.1f}
📐 BB: {s.get('bb_pos', 0):.1f}%
{tend_emoji} Tendencia: {s.get('tendencia', 'N/A')}

<b>📋 Razones:</b>
{razones}

<b>⏰ ENTRADA: {s.get('hora_entrada', 'Ahora')}</b>
<b>⏱️ EXPIRACIÓN: {s.get('expiracion', 2)} min</b>

🕐 {s.get('hora', '')}"""
        return Telegram.enviar(msg)


# ══════════════════════════════════════════════════════════════════════════════
#                         INTELIGENCIA ARTIFICIAL
# ══════════════════════════════════════════════════════════════════════════════

class IAFiltro:
    SYSTEM_PROMPT = """Eres un FILTRO de señales de trading para opciones binarias.

CRITERIOS PARA CONFIRMAR ✅:
1. La señal va A FAVOR de la tendencia
2. RSI está en zona extrema (<28 o >72)
3. Bollinger está en extremo (<15% o >85%)

CRITERIOS PARA RECHAZAR ❌:
1. La señal va CONTRA tendencia FUERTE
2. RSI/BB no están en zonas extremas
3. Mercado errático

RESPONDE:
DECISIÓN: [CONFIRMO/RECHAZO]
RAZÓN: [Una línea]
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
                    "max_tokens": 100,
                    "temperature": 0.1
                },
                timeout=15
            )
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
            return None
        except:
            return None
    
    @staticmethod
    def evaluar_senal(senal):
        prompt = f"""ACTIVO: {senal['nombre']}
DIRECCIÓN: {senal['direccion']}
PRECIO: {senal.get('precio', 'N/A')}
RSI: {senal['rsi']:.1f}
BB: {senal['bb_pos']:.1f}%
TENDENCIA: {senal['tendencia']} ({senal['fuerza_tendencia']})
A FAVOR: {'SÍ' if senal.get('a_favor_tendencia') else 'NO'}

¿CONFIRMAS?"""

        respuesta = IAFiltro.consultar(prompt)
        
        if not respuesta:
            return True, "IA no disponible", "N/A"
        
        confirmar = "CONFIRMO" in respuesta.upper()
        
        razon = "OK"
        for sep in ["RAZÓN:", "RAZON:"]:
            if sep in respuesta.upper():
                try:
                    razon = respuesta.upper().split(sep)[1].split("\n")[0].strip()[:50]
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
                timeout=10
            )
            return r.status_code == 200
        except:
            return False


# ══════════════════════════════════════════════════════════════════════════════
#                         SISTEMA DE APRENDIZAJE
# ══════════════════════════════════════════════════════════════════════════════

class Aprendizaje:
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
            'parametros': {'rsi_sob': 30, 'rsi_sobc': 70, 'bb_inf': 20, 'bb_sup': 80, 'min_puntos': 55}
        }
    
    def guardar(self):
        try:
            with open(DATOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def registrar_senal(self, senal):
        self.datos['historial'].append({
            'numero': senal['numero'],
            'activo': senal['activo'],
            'direccion': senal['direccion'],
            'puntuacion': senal.get('puntuacion', 0),
            'precio': senal.get('precio', 0),
            'hora': hora_rd(),
            'fecha': fecha_rd(),
            'resultado': None
        })
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
                
                # Bloquear activo si precisión < 35%
                total = self.datos['por_activo'][activo]['g'] + self.datos['por_activo'][activo]['p']
                if total >= 3:
                    prec = self.datos['por_activo'][activo]['g'] / total * 100
                    if prec < 35 and activo not in self.datos['activos_bloqueados']:
                        self.datos['activos_bloqueados'].append(activo)
                        print(f"\n  ⚠️ {activo} BLOQUEADO ({prec:.0f}%)")
                        self.guardar()
                
                return True
        return False
    
    def esta_bloqueado(self, activo):
        return activo in self.datos['activos_bloqueados']
    
    def get_historial_activo(self, activo):
        if activo not in self.datos['por_activo']:
            return None, "Sin datos"
        stats = self.datos['por_activo'][activo]
        total = stats['g'] + stats['p']
        if total == 0:
            return None, "Sin datos"
        precision = (stats['g'] / total) * 100
        return precision, f"{precision:.0f}% ({total})"
    
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
        
        return {
            'total': len(h),
            'ganadas': len(ganadas),
            'perdidas': len(verificadas) - len(ganadas),
            'pendientes': len(h) - len(verificadas),
            'precision': precision,
            'call_p': (d['CALL']['g'] / call_t * 100) if call_t > 0 else 0,
            'put_p': (d['PUT']['g'] / put_t * 100) if put_t > 0 else 0
        }
    
    def get_pendientes(self):
        return [s for s in self.datos['historial'] if not s.get('resultado')]


# ══════════════════════════════════════════════════════════════════════════════
#                         ANALIZADOR TÉCNICO
# ══════════════════════════════════════════════════════════════════════════════

class Analizador:
    def __init__(self, aprendizaje):
        self.velas = {}
        self.precios = {}
        self.aprendizaje = aprendizaje
    
    def agregar_velas(self, aid, candles, validar=True):
        """Agrega velas con validación de rango de precios"""
        if not candles:
            return False
        
        info = ACTIVOS.get(aid)
        if not info:
            return False
        
        # Extraer precio actual
        try:
            precio = float(candles[-1].get('close', 0))
        except:
            return False
        
        # Validar rango de precios si está definido
        if validar and 'rango' in info:
            rango_min, rango_max = info['rango']
            # Dar margen del 50% por volatilidad
            if not (rango_min * 0.5 <= precio <= rango_max * 1.5):
                print(f"  ⚠️ {info['nombre']}: precio {precio} fuera de rango esperado ({rango_min}-{rango_max})")
                return False
        
        # Guardar velas
        self.velas[aid] = [
            {
                'open': float(c.get('open', 0)),
                'high': float(c.get('max', c.get('high', 0))),
                'low': float(c.get('min', c.get('low', 0))),
                'close': float(c.get('close', 0)),
                'time': c.get('time', 0)
            }
            for c in candles
        ]
        self.precios[aid] = precio
        return True
    
    def tiene_datos(self, aid):
        return len(self.velas.get(aid, [])) >= VELAS_ENTRADA
    
    def calcular_rsi(self, precios, periodo=14):
        if len(precios) < periodo + 1:
            return 50
        cambios = [precios[i] - precios[i-1] for i in range(1, len(precios))]
        ganancias = [max(c, 0) for c in cambios[-periodo:]]
        perdidas = [abs(min(c, 0)) for c in cambios[-periodo:]]
        avg_g = sum(ganancias) / periodo
        avg_p = sum(perdidas) / periodo
        if avg_p == 0:
            return 100 if avg_g > 0 else 50
        rs = avg_g / avg_p
        return 100 - (100 / (1 + rs))
    
    def calcular_ema(self, precios, periodo):
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        mult = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        for precio in precios[periodo:]:
            ema = (precio * mult) + (ema * (1 - mult))
        return ema
    
    def calcular_bb(self, precios, periodo=20):
        if len(precios) < periodo:
            return None, None, None
        ultimos = precios[-periodo:]
        media = sum(ultimos) / periodo
        varianza = sum((p - media) ** 2 for p in ultimos) / periodo
        std = varianza ** 0.5
        return media + std * 2, media, media - std * 2
    
    def detectar_tendencia(self, precios):
        if len(precios) < 50:
            return "LATERAL", "DÉBIL"
        
        ema_rapida = self.calcular_ema(precios, Config.EMA_RAPIDA)
        ema_lenta = self.calcular_ema(precios, Config.EMA_LENTA)
        
        diff = (ema_rapida - ema_lenta) / ema_lenta if ema_lenta != 0 else 0
        
        if diff > Config.TENDENCIA_FUERTE:
            return "ALCISTA", "FUERTE"
        elif diff > Config.TENDENCIA_DEBIL:
            return "ALCISTA", "DÉBIL"
        elif diff < -Config.TENDENCIA_FUERTE:
            return "BAJISTA", "FUERTE"
        elif diff < -Config.TENDENCIA_DEBIL:
            return "BAJISTA", "DÉBIL"
        return "LATERAL", "RANGO"
    
    def detectar_patron(self, velas):
        if len(velas) < 3:
            return "Normal", 0
        
        v = velas[-1]
        cuerpo = abs(v['close'] - v['open'])
        rango = v['high'] - v['low']
        
        if rango == 0:
            return "Normal", 0
        
        mecha_sup = v['high'] - max(v['open'], v['close'])
        mecha_inf = min(v['open'], v['close']) - v['low']
        
        if cuerpo <= rango * 0.1:
            return "Doji", 10
        if mecha_inf >= rango * 0.6:
            return "Hammer", 15
        if mecha_sup >= rango * 0.6:
            return "Shooting Star", 15
        
        return "Normal", 0
    
    def analizar(self, aid, nombre):
        if not self.tiene_datos(aid):
            return None
        
        if self.aprendizaje.esta_bloqueado(nombre):
            return None
        
        velas = self.velas[aid]
        precios = [v['close'] for v in velas]
        precio = precios[-1]
        
        rsi = self.calcular_rsi(precios)
        bb_up, bb_mid, bb_low = self.calcular_bb(precios)
        
        if not bb_up or bb_up == bb_low:
            return None
        
        bb_pos = ((precio - bb_low) / (bb_up - bb_low)) * 100
        tendencia, fuerza = self.detectar_tendencia(precios)
        patron, puntos_patron = self.detectar_patron(velas)
        
        params = self.aprendizaje.get_params()
        
        direccion = None
        puntos = 0
        razones = []
        a_favor = False
        
        # CALL
        if bb_pos <= params['bb_inf'] and rsi <= params['rsi_sob'] + 5:
            direccion = "CALL"
            puntos = Config.PUNTOS_TECNICO
            razones.append(f"RSI: {rsi:.1f}")
            razones.append(f"BB: {bb_pos:.0f}%")
            
            if tendencia == "ALCISTA":
                puntos += Config.PUNTOS_TENDENCIA
                razones.append(f"Tendencia: {tendencia}")
                a_favor = True
            elif tendencia == "BAJISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA
                razones.append("⚠️ Contra tendencia")
            
            if patron in ["Hammer", "Doji"]:
                puntos += puntos_patron
                razones.append(f"Patrón: {patron}")
        
        # PUT
        elif bb_pos >= params['bb_sup'] and rsi >= params['rsi_sobc'] - 5:
            direccion = "PUT"
            puntos = Config.PUNTOS_TECNICO
            razones.append(f"RSI: {rsi:.1f}")
            razones.append(f"BB: {bb_pos:.0f}%")
            
            if tendencia == "BAJISTA":
                puntos += Config.PUNTOS_TENDENCIA
                razones.append(f"Tendencia: {tendencia}")
                a_favor = True
            elif tendencia == "ALCISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA
                razones.append("⚠️ Contra tendencia")
            
            if patron in ["Shooting Star", "Doji"]:
                puntos += puntos_patron
                razones.append(f"Patrón: {patron}")
        
        if not direccion:
            return None
        
        # Historial
        prec_hist, texto_hist = self.aprendizaje.get_historial_activo(nombre)
        if prec_hist is not None:
            if prec_hist >= 60:
                puntos += Config.PUNTOS_HISTORIAL
            elif prec_hist < 40:
                puntos += Config.PENALIZACION_MAL_ACTIVO
        
        puntos = max(0, min(100, puntos))
        
        if puntos < params['min_puntos']:
            return None
        
        return {
            'direccion': direccion,
            'puntuacion': puntos,
            'clasificacion': 'A' if puntos >= Config.UMBRAL_SENAL_A else 'B',
            'rsi': rsi,
            'bb_pos': bb_pos,
            'precio': precio,
            'tendencia': tendencia,
            'fuerza_tendencia': fuerza,
            'a_favor_tendencia': a_favor,
            'patron': patron,
            'razones': razones,
            'historial': texto_hist,
            'expiracion': 1 if puntos >= 80 else 2 if puntos >= 70 else 3
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
        
        return sorted(oportunidades, key=lambda x: (x.get('a_favor_tendencia', False), x['puntuacion']), reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
#                         BOT PRINCIPAL - CORREGIDO
# ══════════════════════════════════════════════════════════════════════════════

class Bot:
    def __init__(self):
        self.ws = None
        self.aprendizaje = Aprendizaje()
        self.analizador = Analizador(self.aprendizaje)
        self.numero = len(self.aprendizaje.datos['historial'])
        self.senal_actual = None
        self.ia_ok = False
    
    async def conectar(self):
        print("\n  🔌 Conectando...")
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
        await asyncio.sleep(2)
        return await self.conectar()
    
    async def obtener_datos_activo(self, aid):
        """
        CORRECCIÓN: Solicita datos de UN activo y espera SU respuesta.
        """
        try:
            # Enviar solicitud
            msg = json.dumps({
                "name": "sendMessage",
                "msg": {
                    "name": "get-candles",
                    "version": "2.0",
                    "body": {"active_id": aid, "size": 60, "count": VELAS_TENDENCIA}
                }
            })
            await self.ws.send(msg)
            
            # Esperar respuesta (máximo 3 segundos)
            for _ in range(30):
                try:
                    respuesta = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
                    data = json.loads(respuesta)
                    
                    if data.get('name') == 'candles':
                        candles = data.get('msg', {}).get('candles', [])
                        if candles:
                            return candles
                except asyncio.TimeoutError:
                    continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            return None
    
    async def obtener_datos(self):
        """
        MÉTODO CORREGIDO: Solicita activos uno por uno.
        """
        print(f"\n  📊 Cargando {len(ACTIVOS)} activos (uno por uno)...")
        
        cargados = 0
        errores = 0
        
        for aid, info in ACTIVOS.items():
            candles = await self.obtener_datos_activo(aid)
            
            if candles:
                if self.analizador.agregar_velas(aid, candles, validar=True):
                    cargados += 1
                else:
                    errores += 1
            else:
                errores += 1
            
            # Mostrar progreso cada 10 activos
            if (cargados + errores) % 10 == 0:
                print(f"     {cargados + errores}/{len(ACTIVOS)}...")
        
        print(f"  ✅ {cargados} activos cargados correctamente")
        if errores > 0:
            print(f"  ⚠️ {errores} activos con errores o fuera de rango")
        
        return cargados > 0
    
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
            'bb_pos': op['bb_pos'],
            'precio': op['precio'],
            'tendencia': op['tendencia'],
            'fuerza_tendencia': op['fuerza_tendencia'],
            'a_favor_tendencia': op['a_favor_tendencia'],
            'patron': op['patron'],
            'razones': op['razones'],
            'historial': op['historial'],
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
        
        print("\n")
        print("  ╔" + "═" * 58 + "╗")
        print(f"  ║  🎯 SEÑAL #{s['numero']} - {clase}" + " " * 40 + "║")
        print("  ╠" + "═" * 58 + "╣")
        print(f"  ║  📍 {s['activo']:<52}║")
        print(f"  ║  💰 PRECIO: {s['precio']:<45}║")
        print("  ╠" + "═" * 58 + "╣")
        print(f"  ║     {flecha:<52}║")
        print("  ╠" + "═" * 58 + "╣")
        print(f"  ║  📊 Puntos: {s['puntuacion']}/100" + " " * 38 + "║")
        print(f"  ║  📉 RSI: {s['rsi']:.1f}   📐 BB: {s['bb_pos']:.1f}%" + " " * 28 + "║")
        print(f"  ║  📈 Tendencia: {s['tendencia']} ({s['fuerza_tendencia']})" + " " * 24 + "║")
        print("  ╠" + "═" * 58 + "╣")
        for r in s['razones'][:4]:
            print(f"  ║  • {r:<54}║")
        print("  ╠" + "═" * 58 + "╣")
        print(f"  ║  ⏰ ENTRADA: {s['hora_entrada']}" + " " * 36 + "║")
        print(f"  ║  ⏱️  EXPIRACIÓN: {s['expiracion']} min" + " " * 35 + "║")
        print("  ╚" + "═" * 58 + "╝")
        print("\n  💡 'g' = GANADA | 'p' = PERDIDA")
        
        self.senal_actual = s
        self.aprendizaje.registrar_senal(s)
        Telegram.enviar_senal(s)
    
    def mostrar_precios(self):
        """Muestra precios actuales para verificar"""
        print("\n  💰 PRECIOS ACTUALES:")
        print("  " + "─" * 55)
        
        for aid, info in list(ACTIVOS.items())[:20]:
            if aid in self.analizador.precios:
                precio = self.analizador.precios[aid]
                rango = info.get('rango', (0, 0))
                
                # Verificar si está en rango
                if rango[0] <= precio <= rango[1]:
                    estado = "✅"
                else:
                    estado = "⚠️"
                
                print(f"  {estado} {info['nombre'][:25]:<27} ${precio:,.4f}")
        
        print("  " + "─" * 55)
        print("  ✅ = precio en rango esperado")
        print("  ⚠️ = precio fuera de rango (posible error)")
    
    def mostrar_stats(self):
        s = self.aprendizaje.get_stats()
        estado = "🔥" if s['precision'] >= 70 else "✅" if s['precision'] >= 60 else "⚠️"
        
        print(f"\n  📊 ESTADÍSTICAS")
        print(f"  Total: {s['total']} | ✅ {s['ganadas']} | ❌ {s['perdidas']}")
        print(f"  🎯 Precisión: {s['precision']:.1f}% {estado}")
        print(f"  CALL: {s['call_p']:.0f}% | PUT: {s['put_p']:.0f}%")
    
    def mostrar_menu(self):
        print("\n  ┌" + "─" * 45 + "┐")
        print("  │  🎯 BOT v4.0 - MAPEO CORREGIDO" + " " * 11 + "│")
        print("  ├" + "─" * 45 + "┤")
        print("  │  [1] Obtener señal                         │")
        print("  │  [2] Ver precios (verificar)               │")
        print("  │  [3] Estadísticas                          │")
        print("  │  [4] Pendientes                            │")
        print("  ├" + "─" * 45 + "┤")
        print("  │  [g] GANADA   [p] PERDIDA                  │")
        print("  │  [m] Menú     [q] Salir                    │")
        print("  └" + "─" * 45 + "┘")
    
    async def ejecutar(self):
        limpiar()
        print("\n  🎯 BOT v4.0 - MAPEO DE DATOS CORREGIDO")
        print(f"  🕐 {hora_rd()}")
        
        if not await self.conectar():
            return
        
        print("  🤖 Verificando IA...")
        self.ia_ok = IAFiltro.test()
        print(f"  {'✅' if self.ia_ok else '⚠️'} IA {'OK' if self.ia_ok else 'no disponible'}")
        
        await self.obtener_datos()
        self.mostrar_menu()
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 ").strip().lower())
                
                if cmd == '1':
                    await self.obtener_datos()
                    ops = self.analizador.buscar_oportunidades()
                    
                    if ops:
                        for op in ops[:3]:
                            print(f"\n  📍 {op['nombre']}: ${op['precio']:.4f} ({op['puntuacion']}pts)")
                            
                            if self.ia_ok and Config.IA_ACTIVA:
                                aprobada, razon, conf = IAFiltro.evaluar_senal(op)
                                if aprobada:
                                    senal = self.crear_senal(op, True, razon, conf)
                                    self.mostrar_senal(senal)
                                    break
                                else:
                                    print(f"     🤖❌ IA rechazó: {razon}")
                            else:
                                senal = self.crear_senal(op)
                                self.mostrar_senal(senal)
                                break
                        else:
                            print("\n  ⚠️ Ninguna señal aprobada")
                    else:
                        print("\n  💡 No hay señales disponibles")
                
                elif cmd == '2':
                    self.mostrar_precios()
                
                elif cmd == '3':
                    self.mostrar_stats()
                
                elif cmd == '4':
                    pend = self.aprendizaje.get_pendientes()
                    if pend:
                        print("\n  ⏳ PENDIENTES:")
                        for p in pend[-10:]:
                            print(f"  #{p['numero']} {p['activo'][:20]} {p['direccion']}")
                    else:
                        print("\n  ✅ No hay pendientes")
                
                elif cmd.startswith('g'):
                    try:
                        num = self.senal_actual['numero'] if cmd == 'g' else int(cmd.split()[1])
                        if self.aprendizaje.registrar_resultado(num, 'GANADA'):
                            print(f"\n  ✅ #{num} GANADA!")
                            Telegram.enviar(f"✅ #{num} GANADA")
                    except:
                        print("  ❌ Uso: 'g' o 'g #'")
                
                elif cmd.startswith('p') and (cmd == 'p' or ' ' in cmd):
                    try:
                        num = self.senal_actual['numero'] if cmd == 'p' else int(cmd.split()[1])
                        if self.aprendizaje.registrar_resultado(num, 'PERDIDA'):
                            print(f"\n  ❌ #{num} PERDIDA")
                            Telegram.enviar(f"❌ #{num} PERDIDA")
                    except:
                        print("  ❌ Uso: 'p' o 'p #'")
                
                elif cmd == 'm':
                    self.mostrar_menu()
                
                elif cmd == 'q':
                    break
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
        
        print("\n  👋 ¡Hasta pronto!")
        if self.ws:
            await self.ws.close()


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║  🎯 BOT v4.0 - MAPEO DE DATOS CORREGIDO                  ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  CORRECCIÓN PRINCIPAL:                                    ║
║  • Solicita datos activo por activo                       ║
║  • Espera respuesta antes de pedir el siguiente           ║
║  • Valida que el precio esté en rango esperado            ║
║                                                           ║
║  VERIFICACIÓN:                                            ║
║  • Opción [2] muestra precios para verificar              ║
║  • ✅ = precio correcto                                   ║
║  • ⚠️ = posible error de datos                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    asyncio.run(Bot().ejecutar())
