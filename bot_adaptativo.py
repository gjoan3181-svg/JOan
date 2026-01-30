#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯 BOT ADAPTATIVO v2.1 - SISTEMA INTELIGENTE + IA FILTRO                  ║
║                                                                              ║
║   • Detección automática de tendencia                                        ║
║   • IA como FILTRO INTELIGENTE (confirma/rechaza señales)                   ║
║   • Auto-evaluación de efectividad de la IA                                 ║
║   • Aprendizaje por activo, dirección y horario                             ║
║   • 60 activos OTC de Bullex (nombres exactos)                              ║
║   • Análisis de 100 velas para mayor precisión                              ║
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
VELAS_TENDENCIA = 500
VELAS_ENTRADA = 10


# ══════════════════════════════════════════════════════════════════════════════
#                         CONFIGURACIÓN DE ESTRATEGIA
# ══════════════════════════════════════════════════════════════════════════════

class Config:
    # RSI
    RSI_PERIODO = 14
    RSI_SOBREVENTA = 30
    RSI_SOBRECOMPRA = 70
    
    # Bollinger Bands
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
    IA_MIN_OPERACIONES_EVAL = 10  # Mínimo para evaluar efectividad
    IA_UMBRAL_DESACTIVAR = 0.4    # Si < 40% de rechazadas hubieran perdido, desactivar


# ══════════════════════════════════════════════════════════════════════════════
#                    ACTIVOS BULLEX OTC (NOMBRES EXACTOS)
# ══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    # ═══════════════ FOREX ═══════════════
    1: {"nombre": "EUR/USD (OTC)", "categoria": "FOREX"},
    2: {"nombre": "EUR/GBP (OTC)", "categoria": "FOREX"},
    3: {"nombre": "GBP/USD (OTC)", "categoria": "FOREX"},
    4: {"nombre": "EUR/JPY (OTC)", "categoria": "FOREX"},
    5: {"nombre": "USD/JPY (OTC)", "categoria": "FOREX"},
    6: {"nombre": "AUD/USD (OTC)", "categoria": "FOREX"},
    7: {"nombre": "USD/CAD (OTC)", "categoria": "FOREX"},
    8: {"nombre": "NZD/USD (OTC)", "categoria": "FOREX"},
    10: {"nombre": "GBP/JPY (OTC)", "categoria": "FOREX"},
    31: {"nombre": "AUD/JPY (OTC)", "categoria": "FOREX"},
    32: {"nombre": "AUD/NZD (OTC)", "categoria": "FOREX"},
    33: {"nombre": "EUR/CAD (OTC)", "categoria": "FOREX"},
    36: {"nombre": "GBP/AUD (OTC)", "categoria": "FOREX"},
    37: {"nombre": "CAD/JPY (OTC)", "categoria": "FOREX"},
    38: {"nombre": "GBP/CAD (OTC)", "categoria": "FOREX"},
    51: {"nombre": "EUR/CHF (OTC)", "categoria": "FOREX"},
    52: {"nombre": "CHF/JPY (OTC)", "categoria": "FOREX"},
    53: {"nombre": "GBP/CHF (OTC)", "categoria": "FOREX"},
    78: {"nombre": "EUR/NZD (OTC)", "categoria": "FOREX"},
    84: {"nombre": "USD/CHF (OTC)", "categoria": "FOREX"},
    85: {"nombre": "AUD/CAD (OTC)", "categoria": "FOREX"},
    86: {"nombre": "AUD/CHF (OTC)", "categoria": "FOREX"},
    87: {"nombre": "NZD/JPY (OTC)", "categoria": "FOREX"},
    90: {"nombre": "USD/COP (OTC)", "categoria": "FOREX"},
    91: {"nombre": "USD/BRL (OTC)", "categoria": "FOREX"},
    93: {"nombre": "USD/ZAR (OTC)", "categoria": "FOREX"},
    95: {"nombre": "USD/NOK (OTC)", "categoria": "FOREX"},
    97: {"nombre": "USD/MXN (OTC)", "categoria": "FOREX"},
    99: {"nombre": "USD/TRY (OTC)", "categoria": "FOREX"},
    168: {"nombre": "PEN/USD (OTC)", "categoria": "FOREX"},
    
    # ═══════════════ CRYPTO ═══════════════
    212: {"nombre": "BTC/USD (OTC)", "categoria": "CRYPTO"},
    220: {"nombre": "ETH/USD (OTC)", "categoria": "CRYPTO"},
    1876: {"nombre": "SOL/USD (OTC)", "categoria": "CRYPTO"},
    2001: {"nombre": "CARDANO (OTC)", "categoria": "CRYPTO"},
    2002: {"nombre": "DOGECOIN (OTC)", "categoria": "CRYPTO"},
    2003: {"nombre": "SHIB/USD (OTC)", "categoria": "CRYPTO"},
    2004: {"nombre": "Ripple (OTC)", "categoria": "CRYPTO"},
    2010: {"nombre": "HBAR (OTC)", "categoria": "CRYPTO"},
    2011: {"nombre": "TAO (OTC)", "categoria": "CRYPTO"},
    2012: {"nombre": "FET (OTC)", "categoria": "CRYPTO"},
    2020: {"nombre": "Ondo (OTC)", "categoria": "CRYPTO"},
    2021: {"nombre": "Vaulta (OTC)", "categoria": "CRYPTO"},
    2030: {"nombre": "TRUMP Coin (OTC)", "categoria": "CRYPTO"},
    2031: {"nombre": "Melania Coin (OTC)", "categoria": "CRYPTO"},
    2040: {"nombre": "Fartcoin (OTC)", "categoria": "CRYPTO"},
    2041: {"nombre": "UKOUSD (OTC)", "categoria": "CRYPTO"},
    
    # ═══════════════ COMMODITIES ═══════════════
    959: {"nombre": "XAUUSD (OTC)", "categoria": "COMMODITIES"},
    960: {"nombre": "XAGUSD (OTC)", "categoria": "COMMODITIES"},
    
    # ═══════════════ ÍNDICES ═══════════════
    949: {"nombre": "US 30 (OTC)", "categoria": "INDICES"},
    947: {"nombre": "US 100 (OTC)", "categoria": "INDICES"},
    
    # ═══════════════ ACCIONES ═══════════════
    1384: {"nombre": "Apple (OTC)", "categoria": "ACCIONES"},
    1385: {"nombre": "Tesla (OTC)", "categoria": "ACCIONES"},
    1386: {"nombre": "Amazon (OTC)", "categoria": "ACCIONES"},
    1387: {"nombre": "Google (OTC)", "categoria": "ACCIONES"},
    1388: {"nombre": "Meta (OTC)", "categoria": "ACCIONES"},
    1393: {"nombre": "Coca-Cola Company (OTC)", "categoria": "ACCIONES"},
    1395: {"nombre": "Nike, Inc. (OTC)", "categoria": "ACCIONES"},
    1397: {"nombre": "Alibaba Group Hold... (OTC)", "categoria": "ACCIONES"},
    1399: {"nombre": "McDonald's Corpor... (OTC)", "categoria": "ACCIONES"},
    1400: {"nombre": "Intel Corporation (OTC)", "categoria": "ACCIONES"},
    1401: {"nombre": "JPMorgan Chase (OTC)", "categoria": "ACCIONES"},
    1402: {"nombre": "AIG (OTC)", "categoria": "ACCIONES"},
    1403: {"nombre": "Snap Inc. (OTC)", "categoria": "ACCIONES"},
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
<b>{flecha}</b>

📊 Puntuación: {s.get('puntuacion', 0)}/100
📉 RSI: {s.get('rsi', 0):.1f}
📐 BB: {s.get('bb_pos', 0):.1f}%
{tend_emoji} Tendencia: {s.get('tendencia', 'N/A')} ({s.get('fuerza_tendencia', 'N/A')})
📈 Historial: {s.get('historial_activo', 'Sin datos')}

<b>📋 Razones:</b>
{razones}

<b>⏰ ENTRADA: {s.get('hora_entrada', 'Ahora')}</b>
<b>⏱️ EXPIRACIÓN: {s.get('expiracion', 2)} min</b>

🕐 Señal: {s.get('hora', '')}"""
        return Telegram.enviar(msg)
    
    @staticmethod
    def enviar_stats(stats):
        prec = stats.get('precision', 0)
        estado = "🔥 EXCELENTE" if prec >= 70 else "✅ BUENO" if prec >= 60 else "⚠️ REGULAR" if prec >= 50 else "❌ MEJORAR"
        
        msg = f"""<b>📊 ESTADÍSTICAS BOT ADAPTATIVO + IA</b>
━━━━━━━━━━━━━━━━━━━━━

<b>📈 RENDIMIENTO:</b>
• Total: {stats.get('total', 0)}
• ✅ Ganadas: {stats.get('ganadas', 0)}
• ❌ Perdidas: {stats.get('perdidas', 0)}

<b>🎯 PRECISIÓN: {prec:.1f}%</b> {estado}

<b>📊 POR DIRECCIÓN:</b>
• 🟢 CALL: {stats.get('call_precision', 0):.0f}%
• 🔴 PUT: {stats.get('put_precision', 0):.0f}%

<b>🤖 EFECTIVIDAD IA:</b>
• Confirmadas: {stats.get('ia_confirmadas', 0)} ({stats.get('ia_precision_confirmadas', 0):.0f}%)
• Rechazadas: {stats.get('ia_rechazadas', 0)}
• IA útil: {stats.get('ia_util', 'Evaluando...')}

━━━━━━━━━━━━━━━━━━━━━
🕐 {hora_rd()} | 📅 {fecha_rd()}"""
        return Telegram.enviar(msg)


# ══════════════════════════════════════════════════════════════════════════════
#                         INTELIGENCIA ARTIFICIAL - FILTRO
# ══════════════════════════════════════════════════════════════════════════════

class IAFiltro:
    """
    IA como filtro inteligente que confirma o rechaza señales
    basándose en el contexto y historial.
    """
    
    SYSTEM_PROMPT = """Eres un FILTRO de señales de trading para opciones binarias en mercados OTC.

TU TRABAJO: Decidir si una señal técnica debe ser CONFIRMADA o RECHAZADA.

CRITERIOS PARA CONFIRMAR ✅:
1. La señal va A FAVOR de la tendencia
2. El activo tiene buen historial (>55%)
3. RSI está en zona extrema real (<28 o >72)
4. Bollinger está en extremo (<15% o >85%)
5. El patrón de últimas operaciones es positivo

CRITERIOS PARA RECHAZAR ❌:
1. La señal va CONTRA una tendencia FUERTE
2. El activo tiene mal historial (<45%)
3. Hay racha de pérdidas recientes
4. RSI/BB no están en zonas suficientemente extremas
5. El mercado muestra comportamiento errático

IMPORTANTE:
- Sé ESTRICTO. Es mejor rechazar una señal dudosa.
- Prefiere CALL en tendencia alcista, PUT en tendencia bajista.
- Si el historial del activo es malo, RECHAZA.
- Si va contra tendencia fuerte, RECHAZA.

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
                    "temperature": 0.1  # Muy bajo para consistencia
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
    def evaluar_senal(senal, historial_reciente, stats_activo, stats_direccion):
        """
        Evalúa una señal candidata y decide si confirmarla o rechazarla.
        
        Returns: (confirmar: bool, razon: str, confianza: str)
        """
        # Construir prompt con contexto
        prompt = f"""EVALÚA ESTA SEÑAL DE TRADING:

📍 ACTIVO: {senal['nombre']}
📊 DIRECCIÓN: {senal['direccion']}

📈 INDICADORES TÉCNICOS:
• RSI(14): {senal['rsi']:.1f}
• Bollinger: {senal['bb_pos']:.1f}%
• Puntuación técnica: {senal['puntuacion']}/100

📊 TENDENCIA DEL MERCADO:
• Dirección: {senal['tendencia']}
• Fuerza: {senal['fuerza_tendencia']}
• ¿A favor?: {'SÍ ✅' if senal.get('a_favor_tendencia') else 'NO ⚠️'}

📋 HISTORIAL DEL ACTIVO:
{stats_activo}

📋 HISTORIAL DE {senal['direccion']} EN ESTE ACTIVO:
{stats_direccion}

📋 ÚLTIMAS 5 OPERACIONES DEL BOT:
{historial_reciente}

🕯️ PATRÓN DE VELA: {senal.get('patron', 'Normal')}

¿CONFIRMAS o RECHAZAS esta señal?"""

        respuesta = IAFiltro.consultar(prompt)
        
        if not respuesta:
            # Si la IA no responde, confirmar por defecto (no bloquear)
            return True, "IA no disponible - señal aprobada por técnico", "N/A"
        
        # Parsear respuesta
        confirmar = "CONFIRMO" in respuesta.upper()
        
        # Extraer razón
        razon = "Sin razón específica"
        if "RAZÓN:" in respuesta.upper():
            try:
                razon = respuesta.split("RAZÓN:")[1].split("\n")[0].strip()
            except:
                pass
        elif "RAZON:" in respuesta.upper():
            try:
                razon = respuesta.split("RAZON:")[1].split("\n")[0].strip()
            except:
                pass
        
        # Extraer confianza
        confianza = "MEDIA"
        if "ALTA" in respuesta.upper():
            confianza = "ALTA"
        elif "BAJA" in respuesta.upper():
            confianza = "BAJA"
        
        return confirmar, razon, confianza
    
    @staticmethod
    def test():
        """Verifica que la IA esté funcionando"""
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
                timeout=20  # Timeout más largo
            )
            if r.status_code == 200:
                return True
            elif r.status_code == 401:
                print(f"     ❌ API Key inválida")
                return False
            elif r.status_code == 429:
                print(f"     ❌ Sin créditos en OpenAI")
                return False
            else:
                print(f"     ❌ Error HTTP: {r.status_code}")
                print(f"     {r.text[:100]}")
                return False
        except requests.exceptions.Timeout:
            print("     ❌ TIMEOUT - Conexión muy lenta")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"     ❌ Sin conexión a OpenAI")
            print(f"     Verifica tu internet o firewall")
            return False
        except Exception as e:
            print(f"     ❌ Error: {type(e).__name__}: {e}")
            return False


# ══════════════════════════════════════════════════════════════════════════════
#                         SISTEMA DE APRENDIZAJE AVANZADO
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
            'por_tendencia': {'A_FAVOR': {'g': 0, 'p': 0}, 'CONTRA': {'g': 0, 'p': 0}, 'LATERAL': {'g': 0, 'p': 0}},
            'por_horario': {'MAÑANA': {'g': 0, 'p': 0}, 'TARDE': {'g': 0, 'p': 0}, 'NOCHE': {'g': 0, 'p': 0}},
            'activos_bloqueados': [],
            'parametros': {
                'rsi_sob': 30, 'rsi_sobc': 70,
                'bb_inf': 20, 'bb_sup': 80,
                'min_puntos': 55
            },
            # Tracking de IA
            'ia': {
                'confirmadas': [],  # Señales que la IA confirmó
                'rechazadas': [],   # Señales que la IA rechazó (guardamos para evaluar)
                'activa': True
            }
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
            'tendencia': senal.get('tendencia', 'LATERAL'),
            'a_favor': senal.get('a_favor_tendencia', False),
            'rsi': senal.get('rsi', 50),
            'bb_pos': senal.get('bb_pos', 50),
            'hora': hora_rd(),
            'fecha': fecha_rd(),
            'horario': get_periodo_dia(),
            'ia_confirmo': senal.get('ia_confirmo', False),
            'ia_razon': senal.get('ia_razon', ''),
            'ia_confianza': senal.get('ia_confianza', ''),
            'resultado': None
        }
        self.datos['historial'].append(entrada)
        
        # Registrar en tracking de IA
        if senal.get('ia_confirmo'):
            self.datos['ia']['confirmadas'].append(senal['numero'])
        
        self.guardar()
    
    def registrar_senal_rechazada(self, senal_data):
        """Guarda señales rechazadas por la IA para evaluar después"""
        self.datos['ia']['rechazadas'].append({
            'activo': senal_data['nombre'],
            'direccion': senal_data['direccion'],
            'puntuacion': senal_data['puntuacion'],
            'rsi': senal_data['rsi'],
            'bb_pos': senal_data['bb_pos'],
            'tendencia': senal_data['tendencia'],
            'hora': hora_rd(),
            'fecha': fecha_rd(),
            # Esto lo llenaremos manualmente si queremos evaluar
            'hubiera_ganado': None
        })
        self.guardar()
    
    def registrar_resultado(self, numero, resultado):
        for s in self.datos['historial']:
            if s.get('numero') == numero and not s.get('resultado'):
                s['resultado'] = resultado
                key = 'g' if resultado == 'GANADA' else 'p'
                
                # Por activo
                activo = s['activo']
                if activo not in self.datos['por_activo']:
                    self.datos['por_activo'][activo] = {
                        'g': 0, 'p': 0,
                        'direccion': {'CALL': {'g': 0, 'p': 0}, 'PUT': {'g': 0, 'p': 0}}
                    }
                self.datos['por_activo'][activo][key] += 1
                self.datos['por_activo'][activo]['direccion'][s['direccion']][key] += 1
                
                # Por dirección global
                self.datos['por_direccion'][s['direccion']][key] += 1
                
                # Por tendencia
                tendencia_key = 'A_FAVOR' if s.get('a_favor') else 'CONTRA' if s.get('tendencia') != 'LATERAL' else 'LATERAL'
                self.datos['por_tendencia'][tendencia_key][key] += 1
                
                # Por horario
                horario = s.get('horario', 'TARDE')
                if horario in self.datos['por_horario']:
                    self.datos['por_horario'][horario][key] += 1
                
                self.guardar()
                self.evaluar_activo(activo)
                self.evaluar_efectividad_ia()
                self.ajustar_parametros()
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
                    print(f"\n  ⚠️ {activo} BLOQUEADO (precisión: {precision:.0f}%)")
            else:
                if activo in self.datos['activos_bloqueados']:
                    self.datos['activos_bloqueados'].remove(activo)
        
        self.guardar()
    
    def evaluar_efectividad_ia(self):
        """
        Evalúa si la IA está siendo útil comparando:
        - Precisión de señales confirmadas
        - Si las rechazadas hubieran ganado o perdido
        """
        confirmadas = self.datos['ia']['confirmadas']
        if len(confirmadas) < Config.IA_MIN_OPERACIONES_EVAL:
            return
        
        # Calcular precisión de confirmadas
        confirmadas_verificadas = [
            s for s in self.datos['historial']
            if s['numero'] in confirmadas and s.get('resultado')
        ]
        
        if len(confirmadas_verificadas) < 5:
            return
        
        ganadas = sum(1 for s in confirmadas_verificadas if s['resultado'] == 'GANADA')
        precision_confirmadas = (ganadas / len(confirmadas_verificadas)) * 100
        
        # Si la precisión de confirmadas es muy baja, algo está mal
        if precision_confirmadas < 45 and len(confirmadas_verificadas) >= 10:
            print(f"\n  ⚠️ IA: Precisión de confirmadas muy baja ({precision_confirmadas:.0f}%)")
    
    def ajustar_parametros(self):
        verificadas = [s for s in self.datos['historial'] if s.get('resultado')]
        if len(verificadas) < 15:
            return
        
        ultimas = verificadas[-25:]
        ganadas = sum(1 for s in ultimas if s['resultado'] == 'GANADA')
        precision = ganadas / len(ultimas) * 100
        
        p = self.datos['parametros']
        
        if precision < 45:
            p['min_puntos'] = min(75, p['min_puntos'] + 5)
            p['rsi_sob'] = max(20, p['rsi_sob'] - 2)
            p['rsi_sobc'] = min(80, p['rsi_sobc'] + 2)
            print(f"\n  🧠 Parámetros más ESTRICTOS (precisión: {precision:.0f}%)")
        elif precision > 70:
            p['min_puntos'] = max(50, p['min_puntos'] - 2)
            print(f"\n  🧠 Parámetros RELAJADOS (precisión: {precision:.0f}%)")
        
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
    
    def get_historial_direccion(self, activo, direccion):
        if activo not in self.datos['por_activo']:
            return None, "Sin datos"
        
        stats = self.datos['por_activo'][activo].get('direccion', {}).get(direccion, {'g': 0, 'p': 0})
        total = stats['g'] + stats['p']
        if total < 2:
            return None, "Pocos datos"
        
        precision = (stats['g'] / total) * 100
        return precision, f"{precision:.0f}% ({total} ops)"
    
    def get_historial_reciente_texto(self, n=5):
        """Retorna las últimas n operaciones como texto para la IA"""
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
    
    def ia_esta_activa(self):
        return self.datos['ia'].get('activa', True) and Config.IA_ACTIVA
    
    def get_params(self):
        return self.datos['parametros']
    
    def get_stats(self):
        h = self.datos['historial']
        verificadas = [s for s in h if s.get('resultado')]
        ganadas = [s for s in verificadas if s['resultado'] == 'GANADA']
        pendientes = [s for s in h if not s.get('resultado')]
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        # Por dirección
        d = self.datos['por_direccion']
        call_t = d['CALL']['g'] + d['CALL']['p']
        put_t = d['PUT']['g'] + d['PUT']['p']
        call_p = (d['CALL']['g'] / call_t * 100) if call_t > 0 else 0
        put_p = (d['PUT']['g'] / put_t * 100) if put_t > 0 else 0
        
        # Por tendencia
        t = self.datos['por_tendencia']
        af_t = t['A_FAVOR']['g'] + t['A_FAVOR']['p']
        c_t = t['CONTRA']['g'] + t['CONTRA']['p']
        af_p = (t['A_FAVOR']['g'] / af_t * 100) if af_t > 0 else 0
        c_p = (t['CONTRA']['g'] / c_t * 100) if c_t > 0 else 0
        
        # Racha
        racha = 0
        for s in reversed(verificadas):
            if s['resultado'] == 'GANADA':
                racha += 1
            else:
                break
        
        # Stats de IA
        ia_confirmadas = len(self.datos['ia']['confirmadas'])
        ia_rechazadas = len(self.datos['ia']['rechazadas'])
        
        # Precisión de señales confirmadas por IA
        confirmadas_verificadas = [
            s for s in verificadas
            if s['numero'] in self.datos['ia']['confirmadas']
        ]
        ia_precision = 0
        if confirmadas_verificadas:
            ia_ganadas = sum(1 for s in confirmadas_verificadas if s['resultado'] == 'GANADA')
            ia_precision = (ia_ganadas / len(confirmadas_verificadas)) * 100
        
        # Evaluar si IA es útil
        ia_util = "Evaluando..."
        if len(confirmadas_verificadas) >= 10:
            if ia_precision >= 65:
                ia_util = "✅ SÍ, mejora precisión"
            elif ia_precision >= 55:
                ia_util = "⚠️ Neutral"
            else:
                ia_util = "❌ NO, considerar desactivar"
        
        return {
            'total': len(h), 'ganadas': len(ganadas),
            'perdidas': len(verificadas) - len(ganadas),
            'pendientes': len(pendientes), 'precision': precision,
            'call_total': call_t, 'call_precision': call_p,
            'put_total': put_t, 'put_precision': put_p,
            'a_favor_precision': af_p, 'contra_precision': c_p,
            'racha': racha,
            'activos_bloqueados': len(self.datos['activos_bloqueados']),
            'ia_confirmadas': ia_confirmadas,
            'ia_rechazadas': ia_rechazadas,
            'ia_precision_confirmadas': ia_precision,
            'ia_util': ia_util
        }
    
    def get_pendientes(self):
        return [s for s in self.datos['historial'] if not s.get('resultado')]
    
    def get_historial(self, n=15):
        return self.datos['historial'][-n:]
    
    def get_rechazadas_ia(self, n=10):
        return self.datos['ia']['rechazadas'][-n:]
    
    def get_mejores_activos(self, n=5):
        mejores = []
        for activo, stats in self.datos['por_activo'].items():
            total = stats['g'] + stats['p']
            if total >= 3:
                p = stats['g'] / total * 100
                mejores.append((activo, p, total))
        return sorted(mejores, key=lambda x: x[1], reverse=True)[:n]
    
    def get_peores_activos(self, n=5):
        peores = []
        for activo, stats in self.datos['por_activo'].items():
            total = stats['g'] + stats['p']
            if total >= 3:
                p = stats['g'] / total * 100
                peores.append((activo, p, total))
        return sorted(peores, key=lambda x: x[1])[:n]


# ══════════════════════════════════════════════════════════════════════════════
#                         ANALIZADOR TÉCNICO AVANZADO
# ══════════════════════════════════════════════════════════════════════════════

class AnalizadorAvanzado:
    def __init__(self, aprendizaje):
        self.velas = defaultdict(list)
        self.aprendizaje = aprendizaje
    
    def agregar_velas(self, aid, candles):
        self.velas[aid] = [
            {'open': float(c.get('open', 0)), 'high': float(c.get('max', 0)),
             'low': float(c.get('min', 0)), 'close': float(c.get('close', 0)),
             'time': c.get('time', 0)}
            for c in candles
        ]
    
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
        if len(precios) < 50:
            return "LATERAL", "DÉBIL", False
        
        ema_rapida = self.calcular_ema(precios, Config.EMA_RAPIDA)
        ema_lenta = self.calcular_ema(precios, Config.EMA_LENTA)
        precio_actual = precios[-1]
        
        diff_emas = (ema_rapida - ema_lenta) / ema_lenta if ema_lenta != 0 else 0
        
        if diff_emas > Config.TENDENCIA_FUERTE:
            tendencia = "ALCISTA"
            fuerza = "FUERTE"
        elif diff_emas > Config.TENDENCIA_DEBIL:
            tendencia = "ALCISTA"
            fuerza = "DÉBIL"
        elif diff_emas < -Config.TENDENCIA_FUERTE:
            tendencia = "BAJISTA"
            fuerza = "FUERTE"
        elif diff_emas < -Config.TENDENCIA_DEBIL:
            tendencia = "BAJISTA"
            fuerza = "DÉBIL"
        else:
            tendencia = "LATERAL"
            fuerza = "RANGO"
        
        precio_sobre_emas = precio_actual > ema_rapida and precio_actual > ema_lenta
        precio_bajo_emas = precio_actual < ema_rapida and precio_actual < ema_lenta
        
        if tendencia == "ALCISTA" and not precio_sobre_emas:
            fuerza = "DÉBIL"
        if tendencia == "BAJISTA" and not precio_bajo_emas:
            fuerza = "DÉBIL"
        
        return tendencia, fuerza, {'ema_rapida': ema_rapida, 'ema_lenta': ema_lenta, 'diff': diff_emas}
    
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
            return "Doji ⚖️", 10
        if mecha_inf >= rango * 0.6 and mecha_sup <= rango * 0.1:
            return "Hammer 🔨", 15
        if mecha_sup >= rango * 0.6 and mecha_inf <= rango * 0.1:
            return "Shooting Star ⭐", 15
        if (v['close'] > v['open'] and v_prev['close'] < v_prev['open'] and
            v['close'] > v_prev['open'] and v['open'] < v_prev['close']):
            return "Engulfing Alcista 🟢", 20
        if (v['close'] < v['open'] and v_prev['close'] > v_prev['open'] and
            v['close'] < v_prev['open'] and v['open'] > v_prev['close']):
            return "Engulfing Bajista 🔴", 20
        if cuerpo <= rango * 0.3:
            return "Rechazo 🛑", 10
        
        return "Normal", 0
    
    def filtro_volatilidad(self, velas):
        if len(velas) < 20:
            return True, ""
        
        atr = self.calcular_atr(velas)
        precio = velas[-1]['close']
        atr_percent = (atr / precio) * 100 if precio > 0 else 0
        
        if atr_percent > 0.5:
            return False, "⚠️ Volatilidad MUY ALTA"
        
        for v in velas[-3:]:
            rango = v['high'] - v['low']
            if rango > atr * 2.5:
                return False, "⚠️ Spike detectado"
        
        return True, ""
    
    def filtro_bandwalk(self, velas, bb_up, bb_low):
        if len(velas) < 5:
            return True, ""
        
        fuera_superior = sum(1 for v in velas[-3:] if v['close'] > bb_up)
        fuera_inferior = sum(1 for v in velas[-3:] if v['close'] < bb_low)
        
        if fuera_superior >= 3:
            return False, "⚠️ Band-walk superior"
        if fuera_inferior >= 3:
            return False, "⚠️ Band-walk inferior"
        
        return True, ""
    
    def analizar(self, aid, nombre_activo):
        velas = self.velas.get(aid, [])
        if len(velas) < VELAS_ENTRADA:
            return None
        
        if self.aprendizaje.esta_bloqueado(nombre_activo):
            return None
        
        precios = [v['close'] for v in velas]
        precio = precios[-1]
        
        rsi = self.calcular_rsi(precios)
        bb_up, bb_mid, bb_low = self.calcular_bb(precios)
        
        if not bb_up or bb_up == bb_low:
            return None
        
        bb_pos = ((precio - bb_low) / (bb_up - bb_low)) * 100
        
        tendencia, fuerza, emas = self.detectar_tendencia(precios)
        patron, puntos_patron = self.detectar_patron(velas)
        
        vol_ok, vol_msg = self.filtro_volatilidad(velas)
        bw_ok, bw_msg = self.filtro_bandwalk(velas, bb_up, bb_low)
        
        if not vol_ok or not bw_ok:
            return None
        
        params = self.aprendizaje.get_params()
        
        direccion = None
        puntos = 0
        razones = []
        a_favor_tendencia = False
        
        # SEÑAL CALL
        if bb_pos <= params['bb_inf'] and rsi <= params['rsi_sob'] + 5:
            direccion = "CALL"
            puntos += Config.PUNTOS_TECNICO
            razones.append(f"✅ RSI bajo: {rsi:.1f}")
            razones.append(f"✅ BB inferior: {bb_pos:.0f}%")
            
            if tendencia == "ALCISTA":
                puntos += Config.PUNTOS_TENDENCIA
                razones.append(f"✅ A FAVOR tendencia {fuerza}")
                a_favor_tendencia = True
            elif tendencia == "BAJISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA
                razones.append(f"⚠️ CONTRA tendencia fuerte")
            elif tendencia == "LATERAL":
                puntos += 10
                razones.append("✅ Mercado lateral")
            
            if patron in ["Hammer 🔨", "Engulfing Alcista 🟢", "Doji ⚖️"]:
                puntos += puntos_patron
                razones.append(f"✅ Patrón: {patron}")
            
            if velas[-1]['close'] > velas[-1]['open']:
                puntos += 10
                razones.append("✅ Vela verde")
        
        # SEÑAL PUT
        elif bb_pos >= params['bb_sup'] and rsi >= params['rsi_sobc'] - 5:
            direccion = "PUT"
            puntos += Config.PUNTOS_TECNICO
            razones.append(f"✅ RSI alto: {rsi:.1f}")
            razones.append(f"✅ BB superior: {bb_pos:.0f}%")
            
            if tendencia == "BAJISTA":
                puntos += Config.PUNTOS_TENDENCIA
                razones.append(f"✅ A FAVOR tendencia {fuerza}")
                a_favor_tendencia = True
            elif tendencia == "ALCISTA" and fuerza == "FUERTE":
                puntos += Config.PENALIZACION_CONTRA
                razones.append(f"⚠️ CONTRA tendencia fuerte")
            elif tendencia == "LATERAL":
                puntos += 10
                razones.append("✅ Mercado lateral")
            
            if patron in ["Shooting Star ⭐", "Engulfing Bajista 🔴", "Doji ⚖️"]:
                puntos += puntos_patron
                razones.append(f"✅ Patrón: {patron}")
            
            if velas[-1]['close'] < velas[-1]['open']:
                puntos += 10
                razones.append("✅ Vela roja")
        
        if not direccion:
            return None
        
        # Historial
        precision_activo, hist_texto = self.aprendizaje.get_historial_activo(nombre_activo)
        if precision_activo is not None:
            if precision_activo >= 60:
                puntos += Config.PUNTOS_HISTORIAL
                razones.append(f"✅ Buen historial: {hist_texto}")
            elif precision_activo < 40:
                puntos += Config.PENALIZACION_MAL_ACTIVO
                razones.append(f"⚠️ Mal historial: {hist_texto}")
        
        precision_dir, hist_dir_texto = self.aprendizaje.get_historial_direccion(nombre_activo, direccion)
        if precision_dir is not None:
            if precision_dir >= 65:
                puntos += 10
                razones.append(f"✅ {direccion} funciona aquí")
            elif precision_dir < 35:
                puntos -= 15
                razones.append(f"⚠️ {direccion} falla aquí")
        
        puntos = max(0, min(100, puntos))
        
        if puntos < params['min_puntos']:
            return None
        
        if puntos >= 80 and a_favor_tendencia:
            expiracion = 1
        elif puntos >= 70:
            expiracion = 2
        else:
            expiracion = 3
        
        return {
            'direccion': direccion,
            'puntuacion': puntos,
            'clasificacion': 'A' if puntos >= Config.UMBRAL_SENAL_A else 'B',
            'rsi': rsi,
            'bb_pos': bb_pos,
            'tendencia': tendencia,
            'fuerza_tendencia': fuerza,
            'a_favor_tendencia': a_favor_tendencia,
            'patron': patron,
            'razones': razones,
            'historial_activo': hist_texto,
            'historial_direccion': hist_dir_texto,
            'expiracion': expiracion,
            'emas': emas
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
        
        return sorted(oportunidades,
                     key=lambda x: (x.get('a_favor_tendencia', False), x['puntuacion']),
                     reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
#                         BOT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class BotAdaptativo:
    def __init__(self):
        self.ws = None
        self.aprendizaje = AprendizajeAvanzado()
        self.analizador = AnalizadorAvanzado(self.aprendizaje)
        self.numero = len(self.aprendizaje.datos['historial'])
        self.senal_actual = None
        self.ia_disponible = False
    
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
            print("  ✅ IA conectada y funcionando")
        else:
            print("  ⚠️ IA no disponible (señales solo técnicas)")
        return self.ia_disponible
    
    async def obtener_datos(self):
        print(f"\n  📊 Analizando {len(ACTIVOS)} activos...")
        
        try:
            for aid in ACTIVOS:
                msg = json.dumps({
                    "name": "sendMessage",
                    "msg": {
                        "name": "get-candles",
                        "version": "2.0",
                        "body": {"active_id": aid, "size": 60, "count": VELAS_TENDENCIA}
                    }
                })
                await self.ws.send(msg)
                await asyncio.sleep(0.05)
            
            recibidos = 0
            aid_list = list(ACTIVOS.keys())
            intentos = 0
            max_intentos = 200
            
            while recibidos < len(aid_list) and intentos < max_intentos:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    
                    if data.get('name') == 'candles':
                        candles = data.get('msg', {}).get('candles', [])
                        if candles and recibidos < len(aid_list):
                            self.analizador.agregar_velas(aid_list[recibidos], candles)
                            recibidos += 1
                except asyncio.TimeoutError:
                    intentos += 1
                except:
                    intentos += 1
            
            print(f"  ✅ {recibidos}/{len(ACTIVOS)} activos cargados")
            return recibidos > 0
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def filtrar_con_ia(self, senal_data):
        """
        Pasa la señal por el filtro de IA.
        Retorna: (aprobada, razon, confianza)
        """
        if not self.ia_disponible or not self.aprendizaje.ia_esta_activa():
            return True, "IA no activa", "N/A"
        
        print("  🤖 Consultando IA...")
        
        # Preparar contexto
        historial_reciente = self.aprendizaje.get_historial_reciente_texto(5)
        _, stats_activo = self.aprendizaje.get_historial_activo(senal_data['nombre'])
        _, stats_direccion = self.aprendizaje.get_historial_direccion(
            senal_data['nombre'], senal_data['direccion']
        )
        
        # Consultar IA
        aprobada, razon, confianza = IAFiltro.evaluar_senal(
            senal_data, historial_reciente, stats_activo, stats_direccion
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
            'bb_pos': op['bb_pos'],
            'tendencia': op['tendencia'],
            'fuerza_tendencia': op['fuerza_tendencia'],
            'a_favor_tendencia': op['a_favor_tendencia'],
            'patron': op['patron'],
            'razones': op['razones'],
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
        favor = "✅ A FAVOR" if s.get('a_favor_tendencia') else "⚠️ CONTRA" if s['tendencia'] != 'LATERAL' else "↔️ LATERAL"
        
        # IA status
        if s.get('ia_confirmo'):
            ia_status = f"🤖✅ IA CONFIRMA ({s.get('ia_confianza', '')})"
        elif s.get('ia_razon'):
            ia_status = f"⚡ Sin filtro IA"
        else:
            ia_status = "⚡ Solo técnico"
        
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
        print(f"  ║  📐 Bollinger:     {s['bb_pos']:.1f}%" + " " * 42 + "║")
        print(f"  ║  {tend_emoji} Tendencia:     {s['tendencia']} ({s['fuerza_tendencia']})" + " " * 27 + "║")
        print(f"  ║  🎯 Posición:      {favor:<42}║")
        print(f"  ║  📈 Historial:     {s['historial_activo']:<41}║")
        print(f"  ║  🕯️  Patrón:        {s['patron']:<41}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  {ia_status:<61}║")
        if s.get('ia_razon') and s.get('ia_confirmo'):
            razon_corta = s['ia_razon'][:55]
            print(f"  ║  💬 {razon_corta:<57}║")
        print("  ╠" + "═" * 62 + "╣")
        print("  ║  📋 RAZONES:" + " " * 49 + "║")
        for r in s['razones'][:5]:
            print(f"  ║     {r[:56]:<57}║")
        print("  ╠" + "═" * 62 + "╣")
        print(f"  ║  ⏰ HORA ENTRADA:  {s['hora_entrada']:<41}║")
        print(f"  ║  ⏱️  EXPIRACIÓN:    {s['expiracion']} minuto(s)" + " " * 37 + "║")
        print("  ╚" + "═" * 62 + "╝")
        print("\n  ⏳ Tienes ~1.5 minutos para preparar la operación")
        print("  💡 Escribe 'g' si GANASTE o 'p' si PERDISTE")
        
        self.senal_actual = s
        self.aprendizaje.registrar_senal(s)
        Telegram.enviar_senal(s)
    
    def mostrar_mercado(self):
        print("\n  📊 ESTADO DEL MERCADO:")
        print("  " + "─" * 60)
        
        for aid, info in list(ACTIVOS.items())[:15]:
            if self.analizador.tiene_datos(aid):
                velas = self.analizador.velas[aid]
                precios = [v['close'] for v in velas]
                
                rsi = self.analizador.calcular_rsi(precios)
                bb_up, _, bb_low = self.analizador.calcular_bb(precios)
                tendencia, fuerza, _ = self.analizador.detectar_tendencia(precios)
                
                if bb_up and bb_up != bb_low:
                    bb_pos = ((precios[-1] - bb_low) / (bb_up - bb_low)) * 100
                    
                    if bb_pos <= 20:
                        estado = "🟢 CALL?"
                    elif bb_pos >= 80:
                        estado = "🔴 PUT?"
                    else:
                        estado = "⚪ NEUTRO"
                    
                    tend_e = "↗️" if tendencia == "ALCISTA" else "↘️" if tendencia == "BAJISTA" else "↔️"
                    
                    nombre_corto = info['nombre'][:20]
                    print(f"  {nombre_corto:<22} RSI:{rsi:5.1f} BB:{bb_pos:5.1f}% {tend_e} {estado}")
        
        print("  " + "─" * 60)
    
    def mostrar_stats(self):
        s = self.aprendizaje.get_stats()
        estado = "🔥" if s['precision'] >= 70 else "✅" if s['precision'] >= 60 else "⚠️" if s['precision'] >= 50 else "❌"
        
        print("\n  ╔" + "═" * 52 + "╗")
        print("  ║  📊 ESTADÍSTICAS BOT ADAPTATIVO + IA" + " " * 14 + "║")
        print("  ╠" + "═" * 52 + "╣")
        print(f"  ║  Total: {s['total']:<42}║")
        print(f"  ║  ✅ Ganadas: {s['ganadas']:<37}║")
        print(f"  ║  ❌ Perdidas: {s['perdidas']:<36}║")
        print(f"  ║  ⏳ Pendientes: {s['pendientes']:<34}║")
        print("  ╠" + "═" * 52 + "╣")
        print(f"  ║  🎯 PRECISIÓN: {s['precision']:.1f}% {estado:<31}║")
        print(f"  ║  🔥 Racha: {s['racha']} ganadas" + " " * 29 + "║")
        print("  ╠" + "═" * 52 + "╣")
        print(f"  ║  🟢 CALL: {s['call_total']} ops ({s['call_precision']:.0f}%)" + " " * 26 + "║")
        print(f"  ║  🔴 PUT:  {s['put_total']} ops ({s['put_precision']:.0f}%)" + " " * 26 + "║")
        print("  ╠" + "═" * 52 + "╣")
        print(f"  ║  📈 A favor tendencia: {s['a_favor_precision']:.0f}%" + " " * 24 + "║")
        print(f"  ║  📉 Contra tendencia:  {s['contra_precision']:.0f}%" + " " * 24 + "║")
        print("  ╠" + "═" * 52 + "╣")
        print("  ║  🤖 INTELIGENCIA ARTIFICIAL:" + " " * 22 + "║")
        print(f"  ║     Confirmadas: {s['ia_confirmadas']} ({s['ia_precision_confirmadas']:.0f}%)" + " " * 22 + "║")
        print(f"  ║     Rechazadas: {s['ia_rechazadas']}" + " " * 32 + "║")
        print(f"  ║     IA útil: {s['ia_util']:<36}║")
        print("  ╠" + "═" * 52 + "╣")
        print(f"  ║  🚫 Activos bloqueados: {s['activos_bloqueados']}" + " " * 25 + "║")
        print("  ╚" + "═" * 52 + "╝")
    
    def mostrar_rechazadas_ia(self):
        rechazadas = self.aprendizaje.get_rechazadas_ia(10)
        print("\n  🤖❌ SEÑALES RECHAZADAS POR IA:")
        if rechazadas:
            for r in rechazadas:
                emoji = "🟢" if r['direccion'] == 'CALL' else "🔴"
                print(f"  {r['activo'][:20]:<22} {emoji} {r['puntuacion']}pts | {r['hora']}")
            print("\n  💡 Estas señales fueron filtradas por la IA")
        else:
            print("  ✅ No hay señales rechazadas")
    
    def mostrar_activos_ranking(self):
        print("\n  ⭐ MEJORES ACTIVOS:")
        mejores = self.aprendizaje.get_mejores_activos(5)
        for activo, precision, total in mejores:
            print(f"  ✅ {activo}: {precision:.0f}% ({total} ops)")
        
        print("\n  💀 PEORES ACTIVOS:")
        peores = self.aprendizaje.get_peores_activos(5)
        for activo, precision, total in peores:
            emoji = "🚫" if precision < 40 else "⚠️"
            print(f"  {emoji} {activo}: {precision:.0f}% ({total} ops)")
        
        bloqueados = self.aprendizaje.datos['activos_bloqueados']
        if bloqueados:
            print("\n  🚫 ACTIVOS BLOQUEADOS:")
            for activo in bloqueados:
                print(f"     • {activo}")
    
    def mostrar_pendientes(self):
        pend = self.aprendizaje.get_pendientes()
        print("\n  ⏳ SEÑALES PENDIENTES:")
        if pend:
            for s in pend[-10:]:
                emoji = "🟢" if s.get('direccion') == 'CALL' else "🔴"
                clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
                ia = "🤖" if s.get('ia_confirmo') else ""
                print(f"  #{s['numero']} {clase}{ia} {s['activo'][:20]:<22} {emoji}")
            print("\n  💡 Usa 'g #' o 'p #' para marcar")
        else:
            print("  ✅ No hay pendientes")
    
    def mostrar_historial(self):
        hist = self.aprendizaje.get_historial()
        print("\n  📋 HISTORIAL RECIENTE:")
        for s in hist:
            emoji = "🟢" if s.get('direccion') == 'CALL' else "🔴"
            clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
            res = s.get('resultado')
            res_e = "✅" if res == 'GANADA' else "❌" if res == 'PERDIDA' else "⏳"
            ia = "🤖" if s.get('ia_confirmo') else "⚡"
            nombre = s['activo'][:15]
            print(f"  #{s['numero']:>3} {clase}{ia} {nombre:<17} {emoji} {res_e}")
    
    def mostrar_aprendizaje(self):
        p = self.aprendizaje.get_params()
        s = self.aprendizaje.get_stats()
        
        print("\n  🧠 SISTEMA DE APRENDIZAJE:")
        print("  " + "─" * 45)
        print(f"  RSI Sobreventa:  ≤{p['rsi_sob']}")
        print(f"  RSI Sobrecompra: ≥{p['rsi_sobc']}")
        print(f"  BB Inferior:     ≤{p['bb_inf']}%")
        print(f"  BB Superior:     ≥{p['bb_sup']}%")
        print(f"  Puntos mínimos:  {p['min_puntos']}")
        print("  " + "─" * 45)
        print(f"  IA activa: {'✅ SÍ' if self.ia_disponible else '❌ NO'}")
        print(f"  Activos bloqueados: {s['activos_bloqueados']}")
    
    def mostrar_menu(self):
        ia_status = "✅" if self.ia_disponible else "❌"
        print("\n  ┌" + "─" * 50 + "┐")
        print(f"  │  📌 BOT ADAPTATIVO + IA {ia_status}" + " " * 22 + "│")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [1] 🎯 Obtener MEJOR señal (con filtro IA)      │")
        print("  │  [2] 📊 Ver estado del mercado                   │")
        print("  │  [3] 📈 Estadísticas completas                   │")
        print("  │  [4] ⭐ Ranking de activos                       │")
        print("  │  [5] 📱 Enviar stats a Telegram                  │")
        print("  │  [6] ⏳ Señales pendientes                       │")
        print("  │  [7] 📋 Historial reciente                       │")
        print("  │  [8] 🧠 Ver aprendizaje                          │")
        print("  │  [9] 🤖 Ver rechazadas por IA                    │")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [g] ✅ GANADA   [p] ❌ PERDIDA                  │")
        print("  │  [g #] / [p #] Marcar señal específica           │")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [m] Menú   [c] Limpiar   [q] Salir              │")
        print("  └" + "─" * 50 + "┘")
    
    async def ejecutar(self):
        limpiar()
        print("\n  🎯 BOT ADAPTATIVO v2.1 - SISTEMA INTELIGENTE + IA")
        print(f"  🕐 {hora_rd()} | 📅 {fecha_rd()}")
        print(f"  📊 Activos: {len(ACTIVOS)} | Velas: {VELAS_TENDENCIA}")
        
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
                        # Intentar con las mejores oportunidades hasta que IA apruebe una
                        senal_aprobada = None
                        intentos = 0
                        max_intentos = min(5, len(ops))
                        
                        for op in ops[:max_intentos]:
                            intentos += 1
                            print(f"\n  📍 Evaluando: {op['nombre']} ({op['puntuacion']}pts)")
                            
                            # Filtrar con IA
                            aprobada, razon, confianza = self.filtrar_con_ia(op)
                            
                            if aprobada:
                                senal = self.crear_senal(op, ia_confirmo=True, ia_razon=razon, ia_confianza=confianza)
                                senal_aprobada = senal
                                break
                            else:
                                print(f"  🤖❌ IA rechazó: {razon}")
                                self.aprendizaje.registrar_senal_rechazada(op)
                        
                        if senal_aprobada:
                            self.mostrar_senal(senal_aprobada)
                        else:
                            print(f"\n  ⚠️ La IA rechazó las {intentos} mejores oportunidades")
                            print("  💡 El mercado puede no estar en buenas condiciones")
                            
                            # Opción de ver sin filtro IA
                            ver_sin_ia = await loop.run_in_executor(
                                None, lambda: input("  ¿Ver mejor señal sin filtro IA? (s/n): ").strip().lower()
                            )
                            if ver_sin_ia == 's':
                                senal = self.crear_senal(ops[0], ia_confirmo=False, ia_razon="Sin filtro IA")
                                self.mostrar_senal(senal)
                    else:
                        self.mostrar_mercado()
                        print("\n  💡 No hay señales que cumplan criterios técnicos")
                
                elif cmd == '2':
                    if not await self.obtener_datos():
                        await self.reconectar()
                        await self.obtener_datos()
                    self.mostrar_mercado()
                
                elif cmd == '3':
                    self.mostrar_stats()
                
                elif cmd == '4':
                    self.mostrar_activos_ranking()
                
                elif cmd == '5':
                    if Telegram.enviar_stats(self.aprendizaje.get_stats()):
                        print("\n  ✅ Stats enviadas a Telegram!")
                    else:
                        print("\n  ❌ Error enviando")
                
                elif cmd == '6':
                    self.mostrar_pendientes()
                
                elif cmd == '7':
                    self.mostrar_historial()
                
                elif cmd == '8':
                    self.mostrar_aprendizaje()
                
                elif cmd == '9':
                    self.mostrar_rechazadas_ia()
                
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
                    print("\n  🎯 BOT ADAPTATIVO v2.1 + IA")
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
#                              MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  🎯 BOT ADAPTATIVO v2.1 - INTELIGENCIA ARTIFICIAL + APRENDIZAJE   ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  🆕 SISTEMA DE IA COMO FILTRO:                                     ║
║  • La IA CONFIRMA o RECHAZA señales técnicas                       ║
║  • Analiza contexto: tendencia, historial, patrones                ║
║  • Auto-evaluación de efectividad                                  ║
║  • Tracking de señales rechazadas                                  ║
║                                                                    ║
║  📊 APRENDIZAJE:                                                   ║
║  • Por activo (bloquea < 35%)                                      ║
║  • Por dirección (CALL vs PUT)                                     ║
║  • Por tendencia (a favor vs contra)                               ║
║  • Ajuste automático de parámetros                                 ║
║                                                                    ║
║  📈 ANÁLISIS:                                                      ║
║  • 100 velas para detectar tendencia                               ║
║  • RSI, Bollinger, EMA, Patrones                                   ║
║  • 60 activos OTC de Bullex                                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    asyncio.run(BotAdaptativo().ejecutar())
