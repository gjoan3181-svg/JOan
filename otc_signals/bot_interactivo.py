#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   🎯 BULLEX BOT - ESTRATEGIA MEAN REVERSION + TELEGRAM
══════════════════════════════════════════════════════════════════════════════════

   ✅ ESTRATEGIA MEAN REVERSION:
   ─────────────────────────────────────────────────────────────────────────────
   • EMA 20 (la media a la que el precio regresa)
   • RSI 14 (extremos: ≤25 sobreventa, ≥75 sobrecompra)
   • Bollinger Bands 20,2 (detectar extremos)
   • Vela de freno (rechazo del precio)
   • Confirmación (no nuevo high/low)
   • Filtro de volatilidad (rechaza mercado loco)
   • Máximo 2 trades por par
   ─────────────────────────────────────────────────────────────────────────────

   ✅ CARACTERÍSTICAS:
   • Pedir señales manualmente
   • Modo automático
   • Marcar ganadas/perdidas
   • Alertas por Telegram
   • Explicación del PORQUÉ

   Uso: python3 bot_interactivo.py

══════════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional, List, Dict
import os
import time

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# 👇 TU SSID DE BULLEX:
MI_SSID = "e8b7b6185348833f922e675fe840fc3f"

# 👇 TELEGRAM (para alertas):
# Nota: Verifica tu token en @BotFather de Telegram
TELEGRAM_TOKEN = "8406117917:AAEJ7s3ecN7Ww8r_xrtMRVDklz8E2VHdTU"
TELEGRAM_CHAT_ID = "5495826471"
TELEGRAM_ACTIVO = False  # Desactivado hasta corregir token

# URLs
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_meanrev.json"

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))


# ═══════════════════════════════════════════════════════════════════════════════
#                    🎯 CONFIGURACIÓN DE ESTRATEGIA MEAN REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # ══════════ INDICADORES MEAN REVERSION ══════════
    EMA_PERIODO = 20           # EMA 20 (la media)
    RSI_PERIODO = 14           # RSI 14
    RSI_SOBREVENTA = 25        # RSI ≤ 25 para CALL
    RSI_SOBRECOMPRA = 75       # RSI ≥ 75 para PUT
    BB_PERIODO = 20            # Bollinger Bands periodo
    BB_STD = 2                 # Bollinger Bands desviación
    
    # ══════════ FILTROS ══════════
    UMBRAL_SENTIMIENTO = 65    # Sentimiento mínimo (más bajo porque usamos mean reversion)
    MIN_VELAS = 25             # Mínimo de velas para analizar
    
    # ══════════ FILTRO VOLATILIDAD ══════════
    MAX_VELA_RATIO = 2.5       # Rechazar si vela es 2.5x más grande que promedio
    VELAS_GRANDES_MAX = 2      # Máx velas grandes seguidas permitidas
    
    # ══════════ GESTIÓN DE RIESGO ══════════
    MAX_TRADES_POR_PAR = 2     # Máximo 2 trades por par
    PAUSA_TRAS_PERDIDAS = 2    # Pausar tras 2 pérdidas seguidas
    TIEMPO_PAUSA = 900         # 15 minutos de pausa (en segundos)
    
    # ══════════ TIEMPOS ══════════
    DURACION_OPERACION = 1     # 1 minuto expiración
    COOLDOWN_ACTIVO = 120      # 2 min entre señales del mismo activo


# ═══════════════════════════════════════════════════════════════════════════════
#               🎮 ACTIVOS PERMITIDOS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config_activos import get_activos_habilitados, ACTIVOS
except ImportError:
    ACTIVOS = {
        1:   {"nombre": "EUR/USD",     "mercado": "FOREX",  "simbolo": "EUR/USD (OTC)",   "activo": True},
        212: {"nombre": "Bitcoin",     "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)",   "activo": True},
    }
    def get_activos_habilitados():
        return {k: v for k, v in ACTIVOS.items() if v.get("activo", True)}


# ═══════════════════════════════════════════════════════════════════════════════
#                              FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════════

def hora_rd():
    return datetime.now(RD_TZ)

def fmt_hora(dt=None):
    if dt is None:
        dt = hora_rd()
    return dt.strftime("%H:%M:%S")

def fmt_fecha(dt=None):
    if dt is None:
        dt = hora_rd()
    return dt.strftime("%d/%m/%Y")

def limpiar():
    os.system('cls' if os.name == 'nt' else 'clear')


# ═══════════════════════════════════════════════════════════════════════════════
#                              📱 TELEGRAM
# ═══════════════════════════════════════════════════════════════════════════════

def enviar_telegram(mensaje: str):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_ACTIVO or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"  ⚠️ Error Telegram: {e}")
        return False


def formato_telegram(senal: dict) -> str:
    """Formatea señal para Telegram"""
    direccion = senal['direccion']
    emoji_dir = "🟢" if direccion == "CALL" else "🔴"
    
    msg = f"""
{emoji_dir} <b>SEÑAL #{senal['numero']}</b> {emoji_dir}

📍 <b>{senal['nombre']}</b>
🏷️ {senal['simbolo']}

{'🟢🟢🟢 COMPRAR (CALL) ↑' if direccion == 'CALL' else '🔴🔴🔴 VENDER (PUT) ↓'}

📊 <b>Análisis:</b>
• RSI: {senal.get('rsi', 'N/A')}
• Precio vs EMA20: {senal.get('precio_vs_ema', 'N/A')}
• Bollinger: {senal.get('bollinger_pos', 'N/A')}

📋 <b>¿Por qué?</b>
"""
    for razon in senal.get('razones', [])[:4]:
        msg += f"• {razon}\n"
    
    msg += f"""
⏱️ Expiración: {Config.DURACION_OPERACION} minuto(s)
🕐 Hora: {senal['hora']}

💡 <i>Responde G si GANASTE o P si PERDISTE</i>
"""
    return msg


# ═══════════════════════════════════════════════════════════════════════════════
#                    🔬 ANALIZADOR MEAN REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorMeanReversion:
    """
    Analizador basado en Mean Reversion (Reversión a la Media)
    
    Lógica: El precio en OTC tiende a volver a la media (EMA20).
    Esperamos que se estire a un extremo y vuelva.
    """
    
    def __init__(self):
        self.velas = defaultdict(list)
        self.max_velas = 50
    
    def agregar_vela(self, aid: int, vela: dict):
        """Agrega una vela al historial"""
        datos = {
            'open': float(vela.get('open', 0)),
            'high': float(vela.get('max', vela.get('high', 0))),
            'low': float(vela.get('min', vela.get('low', 0))),
            'close': float(vela.get('close', 0)),
            'time': vela.get('time', time.time())
        }
        
        # Solo agregar si tiene datos válidos
        if datos['close'] > 0:
            self.velas[aid].append(datos)
            if len(self.velas[aid]) > self.max_velas:
                self.velas[aid].pop(0)
    
    def calcular_ema(self, precios: List[float], periodo: int) -> float:
        """Calcula EMA"""
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        
        multiplicador = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        
        for precio in precios[periodo:]:
            ema = (precio * multiplicador) + (ema * (1 - multiplicador))
        
        return ema
    
    def calcular_rsi(self, precios: List[float], periodo: int = 14) -> float:
        """Calcula RSI"""
        if len(precios) < periodo + 1:
            return 50
        
        cambios = [precios[i] - precios[i-1] for i in range(1, len(precios))]
        ganancias = [max(c, 0) for c in cambios[-periodo:]]
        perdidas = [abs(min(c, 0)) for c in cambios[-periodo:]]
        
        avg_ganancia = sum(ganancias) / periodo
        avg_perdida = sum(perdidas) / periodo
        
        if avg_perdida == 0:
            return 100 if avg_ganancia > 0 else 50
        
        rs = avg_ganancia / avg_perdida
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calcular_bollinger(self, precios: List[float], periodo: int = 20, std_mult: float = 2) -> tuple:
        """Calcula Bandas de Bollinger. Retorna (upper, middle, lower)"""
        if len(precios) < periodo:
            return None, None, None
        
        ultimos = precios[-periodo:]
        media = sum(ultimos) / periodo
        
        # Desviación estándar
        varianza = sum((p - media) ** 2 for p in ultimos) / periodo
        std = varianza ** 0.5
        
        upper = media + (std * std_mult)
        lower = media - (std * std_mult)
        
        return upper, media, lower
    
    def detectar_vela_freno(self, velas: List[dict], direccion: str) -> bool:
        """
        Detecta vela de freno (rechazo).
        
        Para CALL (rebote desde abajo):
        - Cuerpo pequeño con mecha inferior larga, o
        - Vela verde después de roja fuerte
        
        Para PUT (rebote desde arriba):
        - Cuerpo pequeño con mecha superior larga, o
        - Vela roja después de verde fuerte
        """
        if len(velas) < 2:
            return False
        
        ultima = velas[-1]
        anterior = velas[-2]
        
        # Tamaño del cuerpo y mechas
        cuerpo = abs(ultima['close'] - ultima['open'])
        mecha_superior = ultima['high'] - max(ultima['open'], ultima['close'])
        mecha_inferior = min(ultima['open'], ultima['close']) - ultima['low']
        rango_total = ultima['high'] - ultima['low']
        
        if rango_total == 0:
            return False
        
        # Ratios
        ratio_cuerpo = cuerpo / rango_total
        ratio_mecha_inf = mecha_inferior / rango_total
        ratio_mecha_sup = mecha_superior / rango_total
        
        if direccion == "CALL":
            # Vela de freno alcista: mecha inferior larga o verde tras roja
            if ratio_mecha_inf >= 0.5 and ratio_cuerpo <= 0.4:
                return True  # Pin bar / hammer
            
            # Vela verde después de roja fuerte
            if (ultima['close'] > ultima['open'] and 
                anterior['close'] < anterior['open'] and
                abs(anterior['close'] - anterior['open']) > cuerpo):
                return True
        
        elif direccion == "PUT":
            # Vela de freno bajista: mecha superior larga o roja tras verde
            if ratio_mecha_sup >= 0.5 and ratio_cuerpo <= 0.4:
                return True  # Shooting star
            
            # Vela roja después de verde fuerte
            if (ultima['close'] < ultima['open'] and 
                anterior['close'] > anterior['open'] and
                abs(anterior['close'] - anterior['open']) > cuerpo):
                return True
        
        return False
    
    def confirmar_no_nuevo_extremo(self, velas: List[dict], direccion: str) -> bool:
        """
        Confirma que la última vela NO hizo nuevo mínimo (CALL) o nuevo máximo (PUT).
        Esto indica que el rebote está empezando.
        """
        if len(velas) < 3:
            return False
        
        ultima = velas[-1]
        anterior = velas[-2]
        
        if direccion == "CALL":
            # Para CALL: la última vela NO debe hacer nuevo mínimo
            return ultima['low'] >= anterior['low']
        
        elif direccion == "PUT":
            # Para PUT: la última vela NO debe hacer nuevo máximo
            return ultima['high'] <= anterior['high']
        
        return False
    
    def filtrar_mercado_loco(self, velas: List[dict]) -> tuple:
        """
        Filtra mercados con alta volatilidad.
        Retorna (es_tranquilo, razon)
        """
        if len(velas) < 10:
            return True, "Datos insuficientes"
        
        # Calcular tamaño promedio de velas
        rangos = [v['high'] - v['low'] for v in velas[-10:]]
        promedio = sum(rangos) / len(rangos)
        
        # Verificar últimas 3 velas
        ultimas_3 = velas[-3:]
        velas_grandes = 0
        
        for v in ultimas_3:
            rango = v['high'] - v['low']
            if promedio > 0 and rango > promedio * Config.MAX_VELA_RATIO:
                velas_grandes += 1
        
        if velas_grandes >= Config.VELAS_GRANDES_MAX:
            return False, f"Mercado volátil ({velas_grandes} velas grandes)"
        
        return True, "Mercado tranquilo ✓"
    
    def analizar_mean_reversion(self, aid: int, sentimiento_pct: float = None) -> Optional[dict]:
        """
        Analiza usando estrategia Mean Reversion.
        
        CALL si:
        - Precio < EMA20 (estirado abajo)
        - RSI ≤ 25 (sobreventa)
        - Precio cerca/toca banda inferior
        - Vela de freno detectada
        - Confirmación: no nuevo mínimo
        - Mercado tranquilo
        
        PUT si:
        - Precio > EMA20 (estirado arriba)
        - RSI ≥ 75 (sobrecompra)
        - Precio cerca/toca banda superior
        - Vela de freno detectada
        - Confirmación: no nuevo máximo
        - Mercado tranquilo
        """
        velas = self.velas.get(aid, [])
        
        if len(velas) < Config.MIN_VELAS:
            return None
        
        # Datos
        precios_close = [v['close'] for v in velas]
        precio_actual = precios_close[-1]
        
        # Calcular indicadores
        ema20 = self.calcular_ema(precios_close, Config.EMA_PERIODO)
        rsi = self.calcular_rsi(precios_close, Config.RSI_PERIODO)
        bb_upper, bb_middle, bb_lower = self.calcular_bollinger(
            precios_close, Config.BB_PERIODO, Config.BB_STD
        )
        
        if bb_upper is None:
            return None
        
        # Filtrar mercado loco
        es_tranquilo, razon_mercado = self.filtrar_mercado_loco(velas)
        if not es_tranquilo:
            return None
        
        # Determinar dirección y verificar condiciones
        razones = []
        direccion = None
        puntuacion = 0
        
        # ═══════════ ANÁLISIS PARA CALL (rebote desde abajo) ═══════════
        if precio_actual < ema20:
            # Precio por debajo de EMA20 ✓
            diff_ema = ((ema20 - precio_actual) / ema20) * 100
            
            if rsi <= Config.RSI_SOBREVENTA:
                # RSI en sobreventa ✓
                
                # Verificar cercanía a banda inferior
                dist_lower = ((precio_actual - bb_lower) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50
                
                if dist_lower <= 15:  # Está en el 15% inferior
                    # Verificar vela de freno
                    tiene_freno = self.detectar_vela_freno(velas, "CALL")
                    
                    # Verificar confirmación
                    tiene_confirmacion = self.confirmar_no_nuevo_extremo(velas, "CALL")
                    
                    if tiene_freno or tiene_confirmacion:
                        direccion = "CALL"
                        puntuacion = 85
                        
                        razones.append(f"✅ Precio {diff_ema:.2f}% debajo de EMA20")
                        razones.append(f"✅ RSI en sobreventa: {rsi:.1f} (≤{Config.RSI_SOBREVENTA})")
                        razones.append(f"✅ Precio en zona inferior Bollinger")
                        
                        if tiene_freno:
                            razones.append(f"✅ Vela de freno detectada")
                            puntuacion += 5
                        
                        if tiene_confirmacion:
                            razones.append(f"✅ Confirmación: no nuevo mínimo")
                            puntuacion += 5
                        
                        razones.append(f"✅ {razon_mercado}")
        
        # ═══════════ ANÁLISIS PARA PUT (rebote desde arriba) ═══════════
        elif precio_actual > ema20:
            # Precio por encima de EMA20 ✓
            diff_ema = ((precio_actual - ema20) / ema20) * 100
            
            if rsi >= Config.RSI_SOBRECOMPRA:
                # RSI en sobrecompra ✓
                
                # Verificar cercanía a banda superior
                dist_upper = ((bb_upper - precio_actual) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50
                
                if dist_upper <= 15:  # Está en el 15% superior
                    # Verificar vela de freno
                    tiene_freno = self.detectar_vela_freno(velas, "PUT")
                    
                    # Verificar confirmación
                    tiene_confirmacion = self.confirmar_no_nuevo_extremo(velas, "PUT")
                    
                    if tiene_freno or tiene_confirmacion:
                        direccion = "PUT"
                        puntuacion = 85
                        
                        razones.append(f"✅ Precio {diff_ema:.2f}% encima de EMA20")
                        razones.append(f"✅ RSI en sobrecompra: {rsi:.1f} (≥{Config.RSI_SOBRECOMPRA})")
                        razones.append(f"✅ Precio en zona superior Bollinger")
                        
                        if tiene_freno:
                            razones.append(f"✅ Vela de freno detectada")
                            puntuacion += 5
                        
                        if tiene_confirmacion:
                            razones.append(f"✅ Confirmación: no nuevo máximo")
                            puntuacion += 5
                        
                        razones.append(f"✅ {razon_mercado}")
        
        # Si no cumple condiciones de mean reversion, no hay señal
        if direccion is None:
            return None
        
        # Bonus por sentimiento si está disponible
        if sentimiento_pct is not None:
            if direccion == "CALL" and sentimiento_pct > 50:
                sent_fuerza = sentimiento_pct
            elif direccion == "PUT" and sentimiento_pct < 50:
                sent_fuerza = 100 - sentimiento_pct
            else:
                sent_fuerza = 50
            
            if sent_fuerza >= Config.UMBRAL_SENTIMIENTO:
                puntuacion += 5
                razones.append(f"✅ Sentimiento confirma: {sent_fuerza:.0f}%")
        
        return {
            'direccion': direccion,
            'puntuacion': puntuacion,
            'rsi': f"{rsi:.1f}",
            'precio_vs_ema': f"{'Debajo' if precio_actual < ema20 else 'Encima'} ({abs((precio_actual-ema20)/ema20*100):.2f}%)",
            'bollinger_pos': f"{'Inferior' if direccion == 'CALL' else 'Superior'}",
            'razones': razones,
            'ema20': ema20,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              GESTOR DE HISTORIAL
# ═══════════════════════════════════════════════════════════════════════════════

class Historial:
    def __init__(self, archivo):
        self.archivo = archivo
        self.senales = []
        self.trades_por_par = defaultdict(int)
        self.perdidas_seguidas = 0
        self.en_pausa = False
        self.pausa_hasta = 0
        self.cargar()
    
    def cargar(self):
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.senales = data.get('senales', [])
        except:
            self.senales = []
    
    def guardar(self):
        try:
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump({
                    'senales': self.senales,
                    'actualizado': hora_rd().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def puede_operar_par(self, simbolo: str) -> tuple:
        """Verifica si se puede operar este par"""
        # Verificar pausa
        if self.en_pausa and time.time() < self.pausa_hasta:
            restante = int(self.pausa_hasta - time.time())
            return False, f"En pausa por {restante//60}:{restante%60:02d} min"
        else:
            self.en_pausa = False
        
        # Contar trades de hoy en este par
        hoy = hora_rd().date()
        trades_hoy = sum(1 for s in self.senales 
                        if s.get('simbolo') == simbolo 
                        and datetime.fromisoformat(s['timestamp']).date() == hoy)
        
        if trades_hoy >= Config.MAX_TRADES_POR_PAR:
            return False, f"Máximo {Config.MAX_TRADES_POR_PAR} trades/día en {simbolo}"
        
        return True, "OK"
    
    def agregar(self, senal: dict) -> int:
        self.senales.append(senal)
        self.guardar()
        return len(self.senales)
    
    def marcar_resultado(self, numero: int, resultado: str) -> bool:
        for s in self.senales:
            if s.get('numero') == numero:
                s['resultado'] = resultado
                s['verificado'] = True
                s['fecha_verificacion'] = hora_rd().isoformat()
                
                # Gestión de rachas
                if resultado == 'PERDIDA':
                    self.perdidas_seguidas += 1
                    if self.perdidas_seguidas >= Config.PAUSA_TRAS_PERDIDAS:
                        self.en_pausa = True
                        self.pausa_hasta = time.time() + Config.TIEMPO_PAUSA
                        print(f"\n  ⚠️ {Config.PAUSA_TRAS_PERDIDAS} pérdidas seguidas. Pausa de {Config.TIEMPO_PAUSA//60} minutos.")
                else:
                    self.perdidas_seguidas = 0
                
                self.guardar()
                return True
        return False
    
    def obtener_pendientes(self) -> List[dict]:
        return [s for s in self.senales if not s.get('verificado')]
    
    def estadisticas(self) -> dict:
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        perdidas = [s for s in verificadas if s.get('resultado') == 'PERDIDA']
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        racha = 0
        for s in reversed(verificadas):
            if s.get('resultado') == 'GANADA':
                racha += 1
            else:
                break
        
        hoy = hora_rd().date()
        hoy_senales = [s for s in self.senales 
                       if datetime.fromisoformat(s['timestamp']).date() == hoy]
        hoy_verificadas = [s for s in hoy_senales if s.get('verificado')]
        hoy_ganadas = [s for s in hoy_verificadas if s.get('resultado') == 'GANADA']
        
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(perdidas),
            'pendientes': total - len(verificadas),
            'precision': precision,
            'racha': racha,
            'hoy_total': len(hoy_senales),
            'hoy_ganadas': len(hoy_ganadas),
            'hoy_verificadas': len(hoy_verificadas),
            'perdidas_seguidas': self.perdidas_seguidas,
            'en_pausa': self.en_pausa
        }
    
    def ultimas(self, n=10) -> List[dict]:
        return self.senales[-n:] if self.senales else []


# ═══════════════════════════════════════════════════════════════════════════════
#                         🏆 BOT INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════════════

class BotInteractivo:
    def __init__(self, ssid: str):
        self.ssid = ssid
        self.ws = None
        self.conectado = False
        
        # Componentes
        self.historial = Historial(HISTORIAL_FILE)
        self.analizador = AnalizadorMeanReversion()
        self.activos = get_activos_habilitados()
        
        # Estado
        self.precios = {}
        self.sentimientos = {}
        self.ultima_senal = None
        self.senal_actual = None
        self.modo_auto = False
        self.ejecutando = True
        self.numero_senal = len(self.historial.senales)
        self.ultima_senal_activo = {}
        
        # Candidatas para señal
        self.candidatas = {}
        
        print(f"\n  📊 Activos habilitados: {len(self.activos)}")
    
    async def conectar(self):
        print(f"\n  🔌 Conectando a Bullex...")
        
        try:
            self.ws = await websockets.connect(
                WS_URL,
                origin='https://trade.bull-ex.com',
                ping_interval=30,
                ping_timeout=10
            )
            
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            
            await self.ws.send(json.dumps({
                'name': 'subscribeMessage',
                'msg': {'name': 'traders-mood-changed'}
            }))
            await self.ws.send(json.dumps({
                'name': 'subscribeMessage',
                'msg': {'name': 'candle-generated'}
            }))
            
            self.conectado = True
            print(f"  ✅ Conectado exitosamente")
            
            # Test Telegram
            if TELEGRAM_ACTIVO:
                if enviar_telegram("🤖 <b>Bot Iniciado</b>\n\nConectado a Bullex.\nEstrategia: Mean Reversion"):
                    print(f"  📱 Telegram conectado")
                else:
                    print(f"  ⚠️ Telegram no disponible")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def evaluar_senal(self, aid: int) -> Optional[dict]:
        """Evalúa si hay señal válida para un activo"""
        if aid not in self.activos:
            return None
        
        activo = self.activos[aid]
        
        # Verificar si se puede operar
        puede, razon = self.historial.puede_operar_par(activo['simbolo'])
        if not puede:
            return None
        
        # Cooldown por activo
        if aid in self.ultima_senal_activo:
            if time.time() - self.ultima_senal_activo[aid] < Config.COOLDOWN_ACTIVO:
                return None
        
        # Obtener sentimiento
        sentimiento = self.sentimientos.get(aid, 50)
        
        # Analizar con Mean Reversion
        analisis = self.analizador.analizar_mean_reversion(aid, sentimiento)
        
        if analisis is None:
            return None
        
        ahora = hora_rd()
        
        return {
            'activo_id': aid,
            'nombre': activo['nombre'],
            'simbolo': activo['simbolo'],
            'mercado': activo['mercado'],
            'direccion': analisis['direccion'],
            'puntuacion': analisis['puntuacion'],
            'rsi': analisis['rsi'],
            'precio_vs_ema': analisis['precio_vs_ema'],
            'bollinger_pos': analisis['bollinger_pos'],
            'razones': analisis['razones'],
            'sentimiento': sentimiento,
            'precio': self.precios.get(aid, 0),
            'timestamp': ahora.isoformat(),
            'hora': fmt_hora(ahora)
        }
    
    def obtener_mejor_senal(self) -> Optional[dict]:
        """Busca la mejor señal entre todos los activos"""
        mejor = None
        mejor_punt = 0
        
        for aid in self.activos.keys():
            senal = self.evaluar_senal(aid)
            if senal and senal['puntuacion'] > mejor_punt:
                mejor = senal
                mejor_punt = senal['puntuacion']
        
        # También revisar candidatas recientes
        for aid, senal in self.candidatas.items():
            if senal['puntuacion'] > mejor_punt:
                mejor = senal
                mejor_punt = senal['puntuacion']
        
        return mejor
    
    def mostrar_senal(self, s: dict, numero: int = None):
        """Muestra señal en consola y envía a Telegram"""
        if numero is None:
            self.numero_senal += 1
            numero = self.numero_senal
        
        s['numero'] = numero
        
        direccion = s['direccion']
        if direccion == 'CALL':
            dir_emoji = "🟢🟢🟢"
            dir_texto = "COMPRAR (CALL) ↑"
        else:
            dir_emoji = "🔴🔴🔴"
            dir_texto = "VENDER (PUT) ↓"
        
        punt = s['puntuacion']
        if punt >= 90:
            nivel = "🔥 EXCELENTE"
            estrellas = "★★★★★"
        elif punt >= 80:
            nivel = "✅ MUY BUENA"
            estrellas = "★★★★☆"
        else:
            nivel = "📊 BUENA"
            estrellas = "★★★☆☆"
        
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print(f"║  🎯 SEÑAL #{numero} - {nivel:<44}║")
        print(f"║  {estrellas:<62}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  📍 Activo:       {s['nombre']:<46}║")
        print(f"║  🏷️  Símbolo:      {s['simbolo']:<46}║")
        print(f"║  📊 Mercado:      {s['mercado']:<46}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║     {dir_emoji}  {dir_texto:<50}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  📈 Puntuación:      {s['puntuacion']:.0f}/100{' ' * 40}║")
        print(f"║  📉 RSI:             {s['rsi']:<44}║")
        print(f"║  📊 Precio vs EMA:   {s['precio_vs_ema']:<44}║")
        print(f"║  📐 Bollinger:       {s['bollinger_pos']:<44}║")
        print("╠" + "═" * 66 + "╣")
        print("║  📋 ¿POR QUÉ ESTA SEÑAL? (Mean Reversion)" + " " * 22 + "║")
        print("║  " + "─" * 62 + "  ║")
        
        for razon in s['razones'][:6]:
            texto = razon[:60]
            print(f"║  {texto:<64}║")
        
        print("╠" + "═" * 66 + "╣")
        print(f"║  ⏱️  Expiración:      {Config.DURACION_OPERACION} minuto(s){' ' * 38}║")
        print(f"║  🕐 Hora:            {s['hora']:<44}║")
        print("╚" + "═" * 66 + "╝")
        print("\n  💡 Usa 'g' para GANADA o 'p' para PERDIDA cuando termine")
        
        # Enviar a Telegram
        if TELEGRAM_ACTIVO:
            msg = formato_telegram(s)
            enviar_telegram(msg)
        
        # Marcar cooldown
        self.ultima_senal_activo[s['activo_id']] = time.time()
        
        return s
    
    def mostrar_estadisticas(self):
        stats = self.historial.estadisticas()
        
        pausa_txt = ""
        if stats['en_pausa']:
            restante = int(self.historial.pausa_hasta - time.time())
            if restante > 0:
                pausa_txt = f" (Pausa: {restante//60}:{restante%60:02d})"
        
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║  📊 ESTADÍSTICAS - MEAN REVERSION" + " " * 22 + "║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📅 HOY:{' ' * 49}║")
        print(f"║     Señales:        {stats['hoy_total']:<36}║")
        print(f"║     Verificadas:    {stats['hoy_verificadas']:<36}║")
        print(f"║     Ganadas:        {stats['hoy_ganadas']:<36}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📈 HISTÓRICO:{' ' * 43}║")
        print(f"║     Total señales:  {stats['total']:<36}║")
        print(f"║     ✅ Ganadas:     {stats['ganadas']:<36}║")
        print(f"║     ❌ Perdidas:    {stats['perdidas']:<36}║")
        print(f"║     ⏳ Pendientes:  {stats['pendientes']:<36}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  🎯 PRECISIÓN:      {stats['precision']:.1f}%{' ' * 33}║")
        print(f"║  🔥 Racha actual:   {stats['racha']} ganadas{' ' * 26}║")
        print(f"║  ⚠️  Pérdidas seg:   {stats['perdidas_seguidas']}{pausa_txt:<34}║")
        print("╚" + "═" * 58 + "╝")
    
    def mostrar_pendientes(self):
        pendientes = self.historial.obtener_pendientes()
        
        if not pendientes:
            print("\n  ✅ No hay señales pendientes\n")
            return
        
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║  ⏳ SEÑALES PENDIENTES" + " " * 34 + "║")
        print("╠" + "═" * 58 + "╣")
        
        for s in pendientes[-10:]:
            num = s.get('numero', '?')
            simbolo = s.get('simbolo', 'N/A')[:18]
            direccion = s.get('direccion', 'N/A')
            hora = s.get('hora', 'N/A')
            emoji = "🟢" if direccion == "CALL" else "🔴"
            
            print(f"║  #{num:<4} {simbolo:<20} {emoji} {direccion:<6} {hora:<8}║")
        
        print("╚" + "═" * 58 + "╝")
        print("\n  💡 Usa 'g #' para GANADA o 'p #' para PERDIDA")
    
    def mostrar_ultimas(self):
        ultimas = self.historial.ultimas(10)
        
        if not ultimas:
            print("\n  📭 No hay señales en el historial\n")
            return
        
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print("║  📋 ÚLTIMAS 10 SEÑALES" + " " * 42 + "║")
        print("╠" + "═" * 66 + "╣")
        
        for s in ultimas:
            num = s.get('numero', '?')
            simbolo = s.get('simbolo', 'N/A')[:18]
            direccion = s.get('direccion', 'N/A')
            resultado = s.get('resultado', 'PENDIENTE')
            
            dir_emoji = "🟢" if direccion == "CALL" else "🔴"
            
            if resultado == 'GANADA':
                res_emoji = "✅"
            elif resultado == 'PERDIDA':
                res_emoji = "❌"
            else:
                res_emoji = "⏳"
            
            print(f"║  #{num:<4} {simbolo:<20} {dir_emoji} {direccion:<6} {res_emoji} {resultado:<12}║")
        
        print("╚" + "═" * 66 + "╝")
    
    def mostrar_menu(self):
        print("\n")
        print("┌" + "─" * 54 + "┐")
        print("│  📌 MENÚ - BOT MEAN REVERSION" + " " * 22 + "│")
        print("├" + "─" * 54 + "┤")
        print("│  [1] o [s] → Pedir SEÑAL ahora" + " " * 21 + "│")
        print("│  [2] o [e] → Ver ESTADÍSTICAS" + " " * 22 + "│")
        print("│  [3]       → Ver PENDIENTES" + " " * 24 + "│")
        print("│  [4] o [h] → Ver HISTORIAL" + " " * 25 + "│")
        print("│  [5] o [a] → Modo AUTO on/off" + " " * 22 + "│")
        print("├" + "─" * 54 + "┤")
        print("│  [g #] → Marcar # como GANADA" + " " * 22 + "│")
        print("│  [p #] → Marcar # como PERDIDA" + " " * 21 + "│")
        print("│  [g] / [p] → Marcar última señal" + " " * 18 + "│")
        print("├" + "─" * 54 + "┤")
        print("│  [q] → SALIR" + " " * 39 + "│")
        print("└" + "─" * 54 + "┘")
        
        modo = "🟢 ACTIVADO" if self.modo_auto else "⚪ DESACTIVADO"
        print(f"\n  🤖 Modo automático: {modo}")
        print(f"  📱 Telegram: {'🟢 Activo' if TELEGRAM_ACTIVO else '⚪ Inactivo'}")
        print(f"  🕐 Hora RD: {fmt_hora()}")
    
    def procesar_comando(self, cmd: str) -> bool:
        cmd = cmd.strip().lower()
        
        if cmd in ['q', 'salir', 'exit']:
            return False
        
        elif cmd in ['1', 's', 'senal', 'señal']:
            mejor = self.obtener_mejor_senal()
            if mejor:
                senal = self.mostrar_senal(mejor)
                self.historial.agregar(senal)
                self.senal_actual = senal
                self.candidatas.clear()
            else:
                print("\n  ⏳ No hay señales válidas ahora.")
                print("  💡 La estrategia Mean Reversion espera:")
                print("     • RSI en extremos (≤25 o ≥75)")
                print("     • Precio alejado de EMA20")
                print("     • Vela de confirmación")
                print("  ⏳ Espera unos minutos...")
        
        elif cmd in ['2', 'e', 'stats']:
            self.mostrar_estadisticas()
        
        elif cmd in ['3', 'pendientes']:
            self.mostrar_pendientes()
        
        elif cmd in ['4', 'h', 'historial']:
            self.mostrar_ultimas()
        
        elif cmd in ['5', 'a', 'auto']:
            self.modo_auto = not self.modo_auto
            estado = "ACTIVADO ✅" if self.modo_auto else "DESACTIVADO ⚪"
            print(f"\n  🤖 Modo automático: {estado}")
        
        elif cmd.startswith('g'):
            try:
                if cmd == 'g' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                
                if self.historial.marcar_resultado(num, 'GANADA'):
                    print(f"\n  ✅ Señal #{num} marcada como GANADA!")
                    if TELEGRAM_ACTIVO:
                        enviar_telegram(f"✅ Señal #{num} GANADA!")
                else:
                    print(f"\n  ❌ No se encontró la señal #{num}")
            except:
                print("\n  ❌ Uso: g [número] - Ejemplo: g 5")
        
        elif cmd.startswith('p') and (cmd == 'p' or cmd.startswith('p ')):
            try:
                if cmd == 'p' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                
                if self.historial.marcar_resultado(num, 'PERDIDA'):
                    print(f"\n  ❌ Señal #{num} marcada como PERDIDA")
                    if TELEGRAM_ACTIVO:
                        enviar_telegram(f"❌ Señal #{num} PERDIDA")
                else:
                    print(f"\n  ❌ No se encontró la señal #{num}")
            except:
                print("\n  ❌ Uso: p [número] - Ejemplo: p 5")
        
        elif cmd in ['m', 'menu']:
            self.mostrar_menu()
        
        elif cmd in ['l', 'limpiar', 'cls', 'clear']:
            limpiar()
            self.mostrar_encabezado()
        
        else:
            if cmd:
                print(f"\n  ❓ Comando no reconocido: '{cmd}'")
                print("  💡 Escribe 'm' para ver el menú")
        
        return True
    
    async def procesar_mensaje(self, msg: str):
        try:
            data = json.loads(msg)
            nombre = data.get('name', '')
            m = data.get('msg', {})
            
            if nombre == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
                    self.analizador.agregar_vela(aid, m)
            
            elif nombre == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                valor = m.get('value', 0.5)
                
                if 'blitz' in inst.lower():
                    return
                
                self.sentimientos[aid] = valor * 100
                
                # Evaluar señal
                senal = self.evaluar_senal(aid)
                if senal:
                    self.candidatas[aid] = senal
                    
                    # Si modo auto, mostrar automáticamente
                    if self.modo_auto and senal['puntuacion'] >= 85:
                        senal_mostrada = self.mostrar_senal(senal)
                        self.historial.agregar(senal_mostrada)
                        self.senal_actual = senal_mostrada
                        if aid in self.candidatas:
                            del self.candidatas[aid]
                        
        except:
            pass
    
    def mostrar_encabezado(self):
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print("║" + " " * 66 + "║")
        print("║     🎯  BOT MEAN REVERSION - BULLEX  🎯" + " " * 24 + "║")
        print("║" + " " * 66 + "║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  🕐 Hora:           {fmt_hora()} (Rep. Dominicana){' ' * 18}║")
        print(f"║  📅 Fecha:          {fmt_fecha():<44}║")
        print("╠" + "═" * 66 + "╣")
        print("║  📊 ESTRATEGIA MEAN REVERSION:" + " " * 33 + "║")
        print(f"║     • EMA: {Config.EMA_PERIODO} periodos{' ' * 43}║")
        print(f"║     • RSI: ≤{Config.RSI_SOBREVENTA} (CALL) / ≥{Config.RSI_SOBRECOMPRA} (PUT){' ' * 28}║")
        print(f"║     • Bollinger: {Config.BB_PERIODO},{Config.BB_STD}{' ' * 39}║")
        print(f"║     • Max trades/par: {Config.MAX_TRADES_POR_PAR}{' ' * 36}║")
        print("╠" + "═" * 66 + "╣")
        print("║  💡 Escribe 'm' para ver el menú" + " " * 31 + "║")
        print("╚" + "═" * 66 + "╝")
    
    async def loop_entrada(self):
        loop = asyncio.get_event_loop()
        
        while self.ejecutando:
            try:
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 Comando: "))
                
                if not self.procesar_comando(cmd):
                    self.ejecutando = False
                    break
                    
            except EOFError:
                break
            except:
                pass
    
    async def loop_websocket(self):
        while self.ejecutando and self.conectado:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                await self.procesar_mensaje(msg)
            except asyncio.TimeoutError:
                pass
            except websockets.exceptions.ConnectionClosed:
                print("\n  ⚠️ Conexión perdida. Reconectando...")
                if await self.conectar():
                    continue
                else:
                    break
            except:
                pass
    
    async def ejecutar(self):
        if not await self.conectar():
            print("\n  ❌ No se pudo conectar. Verifica tu SSID.")
            return
        
        limpiar()
        self.mostrar_encabezado()
        self.mostrar_estadisticas()
        self.mostrar_menu()
        
        try:
            await asyncio.gather(
                self.loop_websocket(),
                self.loop_entrada()
            )
        except:
            pass
        
        print("\n\n" + "═" * 66)
        print("  📊 RESUMEN FINAL")
        print("═" * 66)
        self.mostrar_estadisticas()
        
        if TELEGRAM_ACTIVO:
            stats = self.historial.estadisticas()
            enviar_telegram(f"👋 <b>Bot Cerrado</b>\n\nPrecisión: {stats['precision']:.1f}%\nGanadas: {stats['ganadas']}\nPerdidas: {stats['perdidas']}")
        
        if self.ws:
            await self.ws.close()
        
        print(f"\n  👋 ¡Hasta pronto! - {fmt_hora()}")
        print("═" * 66 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                              PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def mostrar_bienvenida():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🎯  BOT MEAN REVERSION - ESTRATEGIA OTC  🎯                      ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   📊 ESTRATEGIA:                                                     ║
║      • Espera que el precio se estire a un extremo                   ║
║      • RSI ≤25 (sobreventa) → CALL                                   ║
║      • RSI ≥75 (sobrecompra) → PUT                                   ║
║      • Confirmación con vela de freno                                ║
║      • Filtro de mercado volátil                                     ║
║                                                                      ║
║   📱 TELEGRAM: Alertas automáticas                                   ║
║                                                                      ║
║   📋 COMANDOS:                                                       ║
║      [1] Pedir señal    [g] Ganada    [p] Perdida    [q] Salir       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")


async def main():
    mostrar_bienvenida()
    
    ssid = MI_SSID.strip()
    
    if not ssid:
        ssid = input("  🔑 SSID: ").strip()
    
    if not ssid:
        print("\n  ❌ Necesitas un SSID válido.")
        return
    
    bot = BotInteractivo(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot detenido\n")
