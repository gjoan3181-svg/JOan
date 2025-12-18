#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   🎯 BOT MEAN REVERSION - ESTRATEGIA BULLEX OPTIMIZADA
══════════════════════════════════════════════════════════════════════════════════

   SISTEMA DE PUNTUACIÓN:
   ┌─────────────────────────────────────┬────────┐
   │ Toca banda                          │  +35   │
   │ RSI extremo (≤28 / ≥72)             │  +25   │
   │ Rechazo (mecha/vela freno)          │  +20   │
   │ Confirmación (no nuevo high/low)    │  +20   │
   │ Penalización volatilidad alta       │  -40   │
   │ Penalización band-walk              │  -30   │
   └─────────────────────────────────────┴────────┘

   CLASIFICACIÓN:
   🅰️ Señal A (≥70 pts) → OPERAR - Mejor calidad
   🅱️ Señal B (60-69 pts) → OPERAR - Más riesgo
   🅲️ Señal C (<60 pts) → NO OPERAR

══════════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional, List, Dict, Tuple
import os
import time

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

MI_SSID = "e8b7b6185348833f922e675fe840fc3f"

# TELEGRAM
TELEGRAM_TOKEN = "8406117917:AAEJ7s3ecN7Ww8r_xrtMRVlDk1z8E2VHdtU"
TELEGRAM_CHAT_ID = "5495826471"
TELEGRAM_ACTIVO = True

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_senales.json"
RD_TZ = timezone(timedelta(hours=-4))


# ═══════════════════════════════════════════════════════════════════════════════
#                    🎯 CONFIGURACIÓN ESTRATEGIA
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # RSI
    RSI_PERIODO = 14
    RSI_SOBREVENTA_A = 28      # Señal A
    RSI_SOBRECOMPRA_A = 72     # Señal A
    RSI_SOBREVENTA_B = 32      # Señal B
    RSI_SOBRECOMPRA_B = 68     # Señal B
    
    # Bollinger Bands
    BB_PERIODO = 20
    BB_STD = 2.0
    BB_CERCA_BANDA = 10        # % del ancho para "cerca de banda"
    
    # EMA
    EMA_PERIODO = 20
    
    # Filtros
    MIN_VELAS = 25
    VOLATILIDAD_MULT = 1.8     # Vela > 1.8x promedio = volatilidad alta
    
    # Puntuación
    PUNTOS_TOCA_BANDA = 35
    PUNTOS_RSI_EXTREMO = 25
    PUNTOS_RECHAZO = 20
    PUNTOS_CONFIRMACION = 20
    PENALIZACION_VOLATILIDAD = -40
    PENALIZACION_BANDWALK = -30
    
    # Umbrales
    UMBRAL_SENAL_A = 70
    UMBRAL_SENAL_B = 60
    
    # Gestión de riesgo
    MAX_ENTRADAS_PAR = 2       # Máximo 2 entradas seguidas por par
    PAUSA_TRAS_PERDIDAS = 2    # Pausa después de 2 pérdidas
    TIEMPO_PAUSA = 900         # 15 minutos en segundos
    COOLDOWN_ACTIVO = 60       # 1 minuto entre señales del mismo activo
    
    # Operación
    DURACION_OP = 1            # 1 minuto


# ═══════════════════════════════════════════════════════════════════════════════
#               🎮 ACTIVOS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config_activos import get_activos_habilitados
except:
    def get_activos_habilitados():
        return {
            1: {"nombre": "EUR/USD", "mercado": "FOREX", "simbolo": "EUR/USD (OTC)", "activo": True},
            212: {"nombre": "Bitcoin", "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)", "activo": True},
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                              UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════

def hora_rd():
    return datetime.now(RD_TZ)

def fmt_hora(dt=None):
    return (dt or hora_rd()).strftime("%H:%M:%S")

def fmt_fecha(dt=None):
    return (dt or hora_rd()).strftime("%d/%m/%Y")

def limpiar():
    os.system('cls' if os.name == 'nt' else 'clear')

def enviar_telegram(msg):
    if not TELEGRAM_ACTIVO or not TELEGRAM_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        return True
    except:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#                    🔬 ANALIZADOR MEAN REVERSION BULLEX
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorMeanReversion:
    """
    Estrategia Mean Reversion optimizada para Bullex
    
    SEÑAL A (≥70 pts):
    - Precio toca/sale de banda
    - RSI ≤28 (CALL) o ≥72 (PUT)
    - Rechazo claro
    - Confirmación: no nuevo extremo
    
    SEÑAL B (60-69 pts):
    - Precio cerca de banda (≤10% del ancho)
    - RSI ≤32 (CALL) o ≥68 (PUT)
    - Vela de freno
    
    FILTROS:
    - Volatilidad: vela > 1.8x promedio → NO OPERAR
    - Band-walk: 2 velas fuera de banda → NO OPERAR
    """
    
    def __init__(self):
        self.velas = defaultdict(list)
        self.max_velas = 100
    
    def agregar_vela(self, aid: int, vela: dict):
        datos = {
            'open': float(vela.get('open', 0)),
            'high': float(vela.get('max', vela.get('high', 0))),
            'low': float(vela.get('min', vela.get('low', 0))),
            'close': float(vela.get('close', 0)),
            'time': vela.get('time', time.time())
        }
        if datos['close'] > 0 and datos['high'] > 0:
            self.velas[aid].append(datos)
            if len(self.velas[aid]) > self.max_velas:
                self.velas[aid].pop(0)
    
    def tiene_datos(self, aid: int) -> bool:
        return len(self.velas.get(aid, [])) >= Config.MIN_VELAS
    
    # ═══════════════════════════════════════════════════════════════════════
    #                         INDICADORES
    # ═══════════════════════════════════════════════════════════════════════
    
    def calcular_ema(self, precios: List[float], periodo: int) -> float:
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        mult = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        for p in precios[periodo:]:
            ema = (p * mult) + (ema * (1 - mult))
        return ema
    
    def calcular_rsi(self, precios: List[float], periodo: int = 14) -> float:
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
    
    def calcular_bollinger(self, precios: List[float], periodo: int = 20, std_mult: float = 2) -> Tuple:
        if len(precios) < periodo:
            return None, None, None
        ultimos = precios[-periodo:]
        media = sum(ultimos) / periodo
        varianza = sum((p - media) ** 2 for p in ultimos) / periodo
        std = varianza ** 0.5
        return media + (std * std_mult), media, media - (std * std_mult)
    
    # ═══════════════════════════════════════════════════════════════════════
    #                         FILTROS ANTI-TRAMPA
    # ═══════════════════════════════════════════════════════════════════════
    
    def filtro_volatilidad(self, velas: List[dict]) -> Tuple[bool, str]:
        """
        NO operar si en las últimas 3 velas hay una con rango > 1.8x promedio
        """
        if len(velas) < 20:
            return True, ""
        
        # Rango promedio de últimas 20 velas
        rangos = [v['high'] - v['low'] for v in velas[-20:]]
        rango_promedio = sum(rangos) / len(rangos)
        
        if rango_promedio == 0:
            return True, ""
        
        # Verificar últimas 3 velas
        for v in velas[-3:]:
            rango = v['high'] - v['low']
            if rango > rango_promedio * Config.VOLATILIDAD_MULT:
                return False, f"⚠️ Volatilidad alta: vela {rango/rango_promedio:.1f}x promedio"
        
        return True, ""
    
    def filtro_bandwalk(self, velas: List[dict], bb_upper: float, bb_lower: float) -> Tuple[bool, str]:
        """
        NO operar si 2 velas seguidas cierran fuera de la banda en la misma dirección
        (Band-walk = precio pegado a banda, reversión falla)
        """
        if len(velas) < 2:
            return True, ""
        
        v1 = velas[-2]
        v2 = velas[-1]
        
        # 2 velas seguidas arriba de banda superior
        if v1['close'] > bb_upper and v2['close'] > bb_upper:
            return False, "⚠️ Band-walk superior: precio pegado a banda"
        
        # 2 velas seguidas debajo de banda inferior
        if v1['close'] < bb_lower and v2['close'] < bb_lower:
            return False, "⚠️ Band-walk inferior: precio pegado a banda"
        
        return True, ""
    
    # ═══════════════════════════════════════════════════════════════════════
    #                         DETECCIÓN DE PATRONES
    # ═══════════════════════════════════════════════════════════════════════
    
    def detectar_rechazo(self, velas: List[dict], direccion: str) -> Tuple[bool, str]:
        """
        Detecta rechazo: mecha larga o vela de color opuesto tras toque
        """
        if len(velas) < 2:
            return False, ""
        
        v_actual = velas[-1]
        v_anterior = velas[-2]
        
        cuerpo = abs(v_actual['close'] - v_actual['open'])
        rango = v_actual['high'] - v_actual['low']
        
        if rango == 0:
            return False, ""
        
        mecha_sup = v_actual['high'] - max(v_actual['open'], v_actual['close'])
        mecha_inf = min(v_actual['open'], v_actual['close']) - v_actual['low']
        
        if direccion == "CALL":
            # Mecha inferior larga (rechazo de mínimos)
            if mecha_inf >= rango * 0.5:
                return True, "Mecha inferior (rechazo de mínimos)"
            
            # Vela verde después de vela roja (reversión)
            if v_actual['close'] > v_actual['open'] and v_anterior['close'] < v_anterior['open']:
                return True, "Vela verde tras roja (reversión)"
            
            # Vela de freno (cuerpo pequeño)
            if cuerpo <= rango * 0.3:
                return True, "Vela de freno (cuerpo pequeño)"
        
        elif direccion == "PUT":
            # Mecha superior larga (rechazo de máximos)
            if mecha_sup >= rango * 0.5:
                return True, "Mecha superior (rechazo de máximos)"
            
            # Vela roja después de vela verde (reversión)
            if v_actual['close'] < v_actual['open'] and v_anterior['close'] > v_anterior['open']:
                return True, "Vela roja tras verde (reversión)"
            
            # Vela de freno (cuerpo pequeño)
            if cuerpo <= rango * 0.3:
                return True, "Vela de freno (cuerpo pequeño)"
        
        return False, ""
    
    def detectar_confirmacion(self, velas: List[dict], direccion: str) -> Tuple[bool, str]:
        """
        Confirmación: la siguiente vela no hace nuevo extremo
        """
        if len(velas) < 2:
            return False, ""
        
        v_actual = velas[-1]
        v_anterior = velas[-2]
        
        if direccion == "CALL":
            # No hace mínimo nuevo (precio no sigue cayendo)
            if v_actual['low'] >= v_anterior['low']:
                return True, "No nuevo mínimo (confirmación)"
        
        elif direccion == "PUT":
            # No hace máximo nuevo (precio no sigue subiendo)
            if v_actual['high'] <= v_anterior['high']:
                return True, "No nuevo máximo (confirmación)"
        
        return False, ""
    
    # ═══════════════════════════════════════════════════════════════════════
    #                         ANÁLISIS PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════
    
    def analizar_activo(self, aid: int) -> Optional[dict]:
        """
        Analiza un activo y retorna oportunidad clasificada (A/B/C)
        """
        velas = self.velas.get(aid, [])
        if len(velas) < Config.MIN_VELAS:
            return None
        
        precios = [v['close'] for v in velas]
        precio = precios[-1]
        
        # Calcular indicadores
        rsi = self.calcular_rsi(precios, Config.RSI_PERIODO)
        ema = self.calcular_ema(precios, Config.EMA_PERIODO)
        bb_upper, bb_middle, bb_lower = self.calcular_bollinger(precios, Config.BB_PERIODO, Config.BB_STD)
        
        if not bb_upper:
            return None
        
        # Ancho de banda
        bb_ancho = bb_upper - bb_lower
        if bb_ancho == 0:
            return None
        
        # Posición en Bollinger (0-100)
        bb_pos = ((precio - bb_lower) / bb_ancho) * 100
        
        # Distancia a bandas (% del ancho)
        dist_banda_inf = ((precio - bb_lower) / bb_ancho) * 100
        dist_banda_sup = ((bb_upper - precio) / bb_ancho) * 100
        
        # ════════════════════════════════════════════════════════════════════
        #                    FILTROS ANTI-TRAMPA
        # ════════════════════════════════════════════════════════════════════
        
        penalizaciones = []
        puntos_penalizacion = 0
        
        # Filtro volatilidad
        vol_ok, vol_msg = self.filtro_volatilidad(velas)
        if not vol_ok:
            penalizaciones.append(vol_msg)
            puntos_penalizacion += Config.PENALIZACION_VOLATILIDAD
        
        # Filtro band-walk
        bw_ok, bw_msg = self.filtro_bandwalk(velas, bb_upper, bb_lower)
        if not bw_ok:
            penalizaciones.append(bw_msg)
            puntos_penalizacion += Config.PENALIZACION_BANDWALK
        
        # ════════════════════════════════════════════════════════════════════
        #                    DETERMINAR DIRECCIÓN
        # ════════════════════════════════════════════════════════════════════
        
        direccion = None
        puntos = 0
        razones = []
        
        # ═══════════════ CALL (COMPRA) ═══════════════
        # Precio toca o sale por debajo de banda inferior, o está cerca
        if dist_banda_inf <= Config.BB_CERCA_BANDA or precio <= bb_lower:
            direccion = "CALL"
            
            # Puntos por tocar banda
            if precio <= bb_lower:
                puntos += Config.PUNTOS_TOCA_BANDA
                razones.append(f"✅ Precio TOCA/SALE de banda inferior")
            elif dist_banda_inf <= Config.BB_CERCA_BANDA:
                puntos += int(Config.PUNTOS_TOCA_BANDA * 0.7)  # 70% si está cerca
                razones.append(f"✅ Precio cerca de banda inferior ({dist_banda_inf:.1f}%)")
            
            # RSI
            if rsi <= Config.RSI_SOBREVENTA_A:
                puntos += Config.PUNTOS_RSI_EXTREMO
                razones.append(f"✅ RSI extremo: {rsi:.1f} (≤{Config.RSI_SOBREVENTA_A})")
            elif rsi <= Config.RSI_SOBREVENTA_B:
                puntos += int(Config.PUNTOS_RSI_EXTREMO * 0.7)
                razones.append(f"✅ RSI bajo: {rsi:.1f} (≤{Config.RSI_SOBREVENTA_B})")
            
            # Rechazo
            hay_rechazo, tipo_rechazo = self.detectar_rechazo(velas, "CALL")
            if hay_rechazo:
                puntos += Config.PUNTOS_RECHAZO
                razones.append(f"✅ Rechazo: {tipo_rechazo}")
            
            # Confirmación
            hay_confirm, tipo_confirm = self.detectar_confirmacion(velas, "CALL")
            if hay_confirm:
                puntos += Config.PUNTOS_CONFIRMACION
                razones.append(f"✅ {tipo_confirm}")
        
        # ═══════════════ PUT (VENTA) ═══════════════
        # Precio toca o sale por encima de banda superior, o está cerca
        elif dist_banda_sup <= Config.BB_CERCA_BANDA or precio >= bb_upper:
            direccion = "PUT"
            
            # Puntos por tocar banda
            if precio >= bb_upper:
                puntos += Config.PUNTOS_TOCA_BANDA
                razones.append(f"✅ Precio TOCA/SALE de banda superior")
            elif dist_banda_sup <= Config.BB_CERCA_BANDA:
                puntos += int(Config.PUNTOS_TOCA_BANDA * 0.7)
                razones.append(f"✅ Precio cerca de banda superior ({dist_banda_sup:.1f}%)")
            
            # RSI
            if rsi >= Config.RSI_SOBRECOMPRA_A:
                puntos += Config.PUNTOS_RSI_EXTREMO
                razones.append(f"✅ RSI extremo: {rsi:.1f} (≥{Config.RSI_SOBRECOMPRA_A})")
            elif rsi >= Config.RSI_SOBRECOMPRA_B:
                puntos += int(Config.PUNTOS_RSI_EXTREMO * 0.7)
                razones.append(f"✅ RSI alto: {rsi:.1f} (≥{Config.RSI_SOBRECOMPRA_B})")
            
            # Rechazo
            hay_rechazo, tipo_rechazo = self.detectar_rechazo(velas, "PUT")
            if hay_rechazo:
                puntos += Config.PUNTOS_RECHAZO
                razones.append(f"✅ Rechazo: {tipo_rechazo}")
            
            # Confirmación
            hay_confirm, tipo_confirm = self.detectar_confirmacion(velas, "PUT")
            if hay_confirm:
                puntos += Config.PUNTOS_CONFIRMACION
                razones.append(f"✅ {tipo_confirm}")
        
        # Sin dirección clara
        if direccion is None:
            return None
        
        # Aplicar penalizaciones
        puntos += puntos_penalizacion
        razones.extend(penalizaciones)
        
        # Clasificar señal
        puntos = max(0, min(100, puntos))
        
        if puntos >= Config.UMBRAL_SENAL_A:
            clasificacion = "A"
        elif puntos >= Config.UMBRAL_SENAL_B:
            clasificacion = "B"
        else:
            clasificacion = "C"
        
        return {
            'direccion': direccion,
            'puntuacion': puntos,
            'clasificacion': clasificacion,
            'rsi': rsi,
            'bb_pos': bb_pos,
            'precio': precio,
            'ema': ema,
            'lado_ema': "encima" if precio > ema else "debajo",
            'razones': razones,
            'operar': clasificacion in ['A', 'B']
        }
    
    def buscar_mejor_oportunidad(self, activos: dict, pares_bloqueados: set = None) -> Optional[Tuple[int, dict]]:
        """Busca la mejor oportunidad A o B entre todos los activos"""
        if pares_bloqueados is None:
            pares_bloqueados = set()
        
        mejor_aid = None
        mejor_analisis = None
        mejor_puntos = 0
        
        for aid in activos.keys():
            if aid in pares_bloqueados:
                continue
            
            analisis = self.analizar_activo(aid)
            if analisis and analisis['operar'] and analisis['puntuacion'] > mejor_puntos:
                mejor_aid = aid
                mejor_analisis = analisis
                mejor_puntos = analisis['puntuacion']
        
        if mejor_aid:
            return mejor_aid, mejor_analisis
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#                              HISTORIAL Y GESTIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class Historial:
    def __init__(self, archivo):
        self.archivo = archivo
        self.senales = []
        self.entradas_por_par = defaultdict(int)
        self.perdidas_consecutivas = defaultdict(int)
        self.pausas = {}  # aid -> timestamp hasta cuando pausar
        self.cargar()
    
    def cargar(self):
        try:
            if os.path.exists(self.archivo):
                with open(self.archivo, 'r') as f:
                    data = json.load(f)
                    self.senales = data.get('senales', [])
        except:
            self.senales = []
    
    def guardar(self):
        try:
            with open(self.archivo, 'w') as f:
                json.dump({'senales': self.senales}, f, indent=2)
        except:
            pass
    
    def par_bloqueado(self, aid: int) -> Tuple[bool, str]:
        """Verifica si un par está bloqueado por gestión de riesgo"""
        ahora = time.time()
        
        # Verificar pausa por pérdidas
        if aid in self.pausas:
            if ahora < self.pausas[aid]:
                restante = int((self.pausas[aid] - ahora) / 60)
                return True, f"Pausado {restante} min por pérdidas"
            else:
                del self.pausas[aid]
                self.perdidas_consecutivas[aid] = 0
        
        # Verificar máximo de entradas seguidas
        if self.entradas_por_par[aid] >= Config.MAX_ENTRADAS_PAR:
            return True, f"Máximo {Config.MAX_ENTRADAS_PAR} entradas alcanzado"
        
        return False, ""
    
    def get_pares_bloqueados(self) -> set:
        bloqueados = set()
        for aid in list(self.entradas_por_par.keys()) + list(self.pausas.keys()):
            bloqueado, _ = self.par_bloqueado(aid)
            if bloqueado:
                bloqueados.add(aid)
        return bloqueados
    
    def agregar(self, senal):
        self.senales.append(senal)
        self.entradas_por_par[senal['activo_id']] += 1
        self.guardar()
        return len(self.senales)
    
    def marcar(self, num, resultado):
        for s in self.senales:
            if s.get('numero') == num:
                s['resultado'] = resultado
                s['verificado'] = True
                
                aid = s['activo_id']
                
                if resultado == 'GANADA':
                    # Reset contador de pérdidas y entradas
                    self.perdidas_consecutivas[aid] = 0
                    self.entradas_por_par[aid] = 0
                else:
                    # Incrementar pérdidas consecutivas
                    self.perdidas_consecutivas[aid] += 1
                    
                    # Si alcanza límite, pausar el par
                    if self.perdidas_consecutivas[aid] >= Config.PAUSA_TRAS_PERDIDAS:
                        self.pausas[aid] = time.time() + Config.TIEMPO_PAUSA
                        self.entradas_por_par[aid] = 0
                
                self.guardar()
                return True
        return False
    
    def estadisticas(self):
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        perdidas = [s for s in verificadas if s.get('resultado') == 'PERDIDA']
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        # Por clasificación
        senales_a = [s for s in verificadas if s.get('clasificacion') == 'A']
        ganadas_a = [s for s in senales_a if s.get('resultado') == 'GANADA']
        senales_b = [s for s in verificadas if s.get('clasificacion') == 'B']
        ganadas_b = [s for s in senales_b if s.get('resultado') == 'GANADA']
        
        precision_a = (len(ganadas_a) / len(senales_a) * 100) if senales_a else 0
        precision_b = (len(ganadas_b) / len(senales_b) * 100) if senales_b else 0
        
        racha = 0
        for s in reversed(verificadas):
            if s.get('resultado') == 'GANADA':
                racha += 1
            else:
                break
        
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(perdidas),
            'pendientes': total - len(verificadas),
            'precision': precision,
            'racha': racha,
            'senales_a': len(senales_a),
            'precision_a': precision_a,
            'senales_b': len(senales_b),
            'precision_b': precision_b
        }
    
    def pendientes(self):
        return [s for s in self.senales if not s.get('verificado')]
    
    def ultimas(self, n=10):
        return self.senales[-n:]


# ═══════════════════════════════════════════════════════════════════════════════
#                         🏆 BOT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class Bot:
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.conectado = False
        self.ejecutando = True
        
        self.historial = Historial(HISTORIAL_FILE)
        self.analizador = AnalizadorMeanReversion()
        self.activos = get_activos_habilitados()
        
        self.precios = {}
        self.senal_actual = None
        self.numero = len(self.historial.senales)
        self.ultima_senal_tiempo = {}
        
        print(f"\n  📊 Activos configurados: {len(self.activos)}")
    
    async def conectar(self):
        print(f"\n  🔌 Conectando a Bullex...")
        try:
            self.ws = await websockets.connect(
                WS_URL, origin='https://trade.bull-ex.com',
                ping_interval=30, ping_timeout=10
            )
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            self.conectado = True
            print(f"  ✅ Conectado!")
            return True
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def buscar_senal(self):
        """Busca la mejor oportunidad A o B"""
        pares_bloqueados = self.historial.get_pares_bloqueados()
        resultado = self.analizador.buscar_mejor_oportunidad(self.activos, pares_bloqueados)
        
        if resultado is None:
            return None
        
        aid, analisis = resultado
        
        # Verificar cooldown
        if aid in self.ultima_senal_tiempo:
            if time.time() - self.ultima_senal_tiempo[aid] < Config.COOLDOWN_ACTIVO:
                return None
        
        activo = self.activos[aid]
        self.numero += 1
        ahora = hora_rd()
        
        senal = {
            'numero': self.numero,
            'activo_id': aid,
            'nombre': activo['nombre'],
            'simbolo': activo['simbolo'],
            'mercado': activo['mercado'],
            'direccion': analisis['direccion'],
            'puntuacion': analisis['puntuacion'],
            'clasificacion': analisis['clasificacion'],
            'rsi': analisis['rsi'],
            'bb_pos': analisis['bb_pos'],
            'lado_ema': analisis['lado_ema'],
            'razones': analisis['razones'],
            'precio': analisis['precio'],
            'hora': fmt_hora(ahora),
            'timestamp': ahora.isoformat(),
            'verificado': False,
            'resultado': None
        }
        
        self.ultima_senal_tiempo[aid] = time.time()
        return senal
    
    def mostrar_senal(self, s):
        dir_emoji = "🟢🟢🟢" if s['direccion'] == "CALL" else "🔴🔴🔴"
        dir_texto = "COMPRAR (CALL) ↑" if s['direccion'] == "CALL" else "VENDER (PUT) ↓"
        
        # Clasificación
        if s['clasificacion'] == 'A':
            nivel = "🅰️ SEÑAL A - MEJOR CALIDAD"
            nivel_color = "🔥"
        else:
            nivel = "🅱️ SEÑAL B - BUENA"
            nivel_color = "✅"
        
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print(f"║  🎯 SEÑAL #{s['numero']} - {nivel:<40}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  📍 Activo:      {s['nombre']:<47}║")
        print(f"║  🏷️  Símbolo:     {s['simbolo']:<47}║")
        print(f"║  📊 Mercado:     {s['mercado']:<47}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║     {dir_emoji}  {dir_texto:<50}║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  📈 Puntuación:     {s['puntuacion']}/100{' ' * 41}║")
        print(f"║  📉 RSI:            {s['rsi']:.1f}{' ' * 45}║")
        print(f"║  📐 Bollinger:      {s['bb_pos']:.0f}%{' ' * 44}║")
        print(f"║  📏 Lado EMA20:     {s['lado_ema']:<44}║")
        print("╠" + "═" * 66 + "╣")
        print("║  📋 ¿POR QUÉ ESTA SEÑAL?" + " " * 40 + "║")
        print("║  " + "─" * 62 + "  ║")
        
        for r in s['razones'][:7]:
            texto = r[:62]
            print(f"║  {texto:<64}║")
        
        print("╠" + "═" * 66 + "╣")
        print(f"║  ⏱️  Expiración:     {Config.DURACION_OP} minuto(s){' ' * 38}║")
        print(f"║  🕐 Hora:           {s['hora']:<45}║")
        print("╚" + "═" * 66 + "╝")
        print("\n  💡 Escribe 'g' si GANASTE o 'p' si PERDISTE")
        
        # Telegram
        if TELEGRAM_ACTIVO:
            clase = "🅰️" if s['clasificacion'] == 'A' else "🅱️"
            msg = f"""🎯 <b>SEÑAL #{s['numero']}</b> {clase}

📍 {s['simbolo']}
{'🟢 CALL ↑' if s['direccion'] == 'CALL' else '🔴 PUT ↓'}

📊 Puntuación: {s['puntuacion']}/100
📉 RSI: {s['rsi']:.1f}
⏱️ Exp: {Config.DURACION_OP}m

📋 Razones:
""" + "\n".join(s['razones'][:4])
            enviar_telegram(msg)
        
        return s
    
    def mostrar_stats(self):
        st = self.historial.estadisticas()
        print("\n")
        print("╔" + "═" * 50 + "╗")
        print("║  📊 ESTADÍSTICAS" + " " * 32 + "║")
        print("╠" + "═" * 50 + "╣")
        print(f"║  Total señales:    {st['total']:<29}║")
        print(f"║  ✅ Ganadas:       {st['ganadas']:<29}║")
        print(f"║  ❌ Perdidas:      {st['perdidas']:<29}║")
        print(f"║  ⏳ Pendientes:    {st['pendientes']:<29}║")
        print("╠" + "═" * 50 + "╣")
        print(f"║  🎯 PRECISIÓN:     {st['precision']:.1f}%{' ' * 26}║")
        print(f"║  🔥 Racha:         {st['racha']} ganadas{' ' * 21}║")
        print("╠" + "═" * 50 + "╣")
        print(f"║  🅰️ Señales A:     {st['senales_a']} ({st['precision_a']:.0f}% win){' ' * 17}║")
        print(f"║  🅱️ Señales B:     {st['senales_b']} ({st['precision_b']:.0f}% win){' ' * 17}║")
        print("╚" + "═" * 50 + "╝")
    
    def mostrar_pendientes(self):
        pend = self.historial.pendientes()
        if not pend:
            print("\n  ✅ No hay señales pendientes")
            return
        
        print("\n  ⏳ PENDIENTES:")
        for s in pend[-10:]:
            emoji = "🟢" if s['direccion'] == "CALL" else "🔴"
            clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
            print(f"  #{s['numero']} {clase} {s['simbolo'][:15]:<15} {emoji} {s['direccion']}")
        print("\n  💡 Usa 'g #' o 'p #' para marcar")
    
    def mostrar_historial(self):
        ult = self.historial.ultimas(10)
        if not ult:
            print("\n  📭 Sin historial")
            return
        
        print("\n  📋 ÚLTIMAS SEÑALES:")
        for s in ult:
            dir_e = "🟢" if s['direccion'] == "CALL" else "🔴"
            clase = "🅰️" if s.get('clasificacion') == 'A' else "🅱️"
            res = s.get('resultado', 'PEND')
            res_e = "✅" if res == "GANADA" else "❌" if res == "PERDIDA" else "⏳"
            print(f"  #{s['numero']} {clase} {s['simbolo'][:15]:<15} {dir_e} {res_e} {res}")
    
    def mostrar_mercado(self):
        """Muestra estado actual del mercado"""
        print("\n  📊 ESTADO DEL MERCADO:")
        print("  " + "─" * 55)
        
        count = 0
        oportunidades = []
        
        for aid, info in self.activos.items():
            if self.analizador.tiene_datos(aid):
                analisis = self.analizador.analizar_activo(aid)
                velas = self.analizador.velas[aid]
                precios = [v['close'] for v in velas]
                rsi = self.analizador.calcular_rsi(precios)
                bb_u, bb_m, bb_l = self.analizador.calcular_bollinger(precios)
                
                if bb_u:
                    bb_pos = ((precios[-1] - bb_l) / (bb_u - bb_l)) * 100
                    
                    # Emoji según posición
                    if rsi <= 30:
                        emoji = "🟢"
                        nota = "SOBREVENTA"
                    elif rsi >= 70:
                        emoji = "🔴"
                        nota = "SOBRECOMPRA"
                    elif bb_pos <= 15:
                        emoji = "🔵"
                        nota = "cerca banda inf"
                    elif bb_pos >= 85:
                        emoji = "🟠"
                        nota = "cerca banda sup"
                    else:
                        emoji = "⚪"
                        nota = ""
                    
                    if analisis and analisis['operar']:
                        oportunidades.append((aid, info, analisis))
                    
                    if nota:
                        print(f"  {emoji} {info['simbolo'][:18]:<18} RSI:{rsi:5.1f}  BB:{bb_pos:5.1f}% {nota}")
                        count += 1
        
        if count == 0:
            print("  ⚪ Mercado en rango neutral - sin extremos")
        
        if oportunidades:
            print("\n  🎯 OPORTUNIDADES DETECTADAS:")
            for aid, info, an in oportunidades:
                clase = "🅰️" if an['clasificacion'] == 'A' else "🅱️"
                dir_e = "🟢CALL" if an['direccion'] == 'CALL' else "🔴PUT"
                print(f"  {clase} {info['simbolo'][:18]:<18} {dir_e} ({an['puntuacion']}pts)")
    
    def mostrar_menu(self):
        print("\n")
        print("┌" + "─" * 50 + "┐")
        print("│  📌 COMANDOS" + " " * 36 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [1] [s] → BUSCAR SEÑAL (A o B)" + " " * 16 + "│")
        print("│  [2] [e] → Estadísticas" + " " * 24 + "│")
        print("│  [3]     → Pendientes" + " " * 26 + "│")
        print("│  [4] [h] → Historial" + " " * 27 + "│")
        print("│  [5]     → Ver mercado" + " " * 25 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [g]     → Marcar última GANADA" + " " * 16 + "│")
        print("│  [p]     → Marcar última PERDIDA" + " " * 15 + "│")
        print("│  [g #]   → Marcar # GANADA" + " " * 21 + "│")
        print("│  [p #]   → Marcar # PERDIDA" + " " * 20 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [q]     → Salir" + " " * 31 + "│")
        print("└" + "─" * 50 + "┘")
        
        # Mostrar pares bloqueados
        bloqueados = self.historial.get_pares_bloqueados()
        if bloqueados:
            print(f"\n  ⚠️ Pares pausados: {len(bloqueados)}")
        
        datos = len([a for a in self.activos if self.analizador.tiene_datos(a)])
        print(f"\n  🕐 {fmt_hora()} | Datos de {datos}/{len(self.activos)} activos")
    
    def comando(self, cmd):
        cmd = cmd.strip().lower()
        
        if cmd in ['q', 'salir']:
            return False
        
        elif cmd in ['1', 's', 'senal']:
            senal = self.buscar_senal()
            if senal:
                self.mostrar_senal(senal)
                self.historial.agregar(senal)
                self.senal_actual = senal
            else:
                self.mostrar_mercado()
                print("\n  💡 No hay señales A o B ahora.")
                print("  💡 Espera que RSI llegue a extremos (≤30 o ≥70)")
        
        elif cmd in ['2', 'e', 'stats']:
            self.mostrar_stats()
        
        elif cmd in ['3', 'pendientes']:
            self.mostrar_pendientes()
        
        elif cmd in ['4', 'h', 'historial']:
            self.mostrar_historial()
        
        elif cmd == '5':
            self.mostrar_mercado()
        
        elif cmd.startswith('g'):
            try:
                if cmd == 'g' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                if self.historial.marcar(num, 'GANADA'):
                    print(f"\n  ✅ #{num} marcada como GANADA!")
                    enviar_telegram(f"✅ Señal #{num} GANADA")
                else:
                    print(f"\n  ❌ No encontré señal #{num}")
            except:
                print("\n  ❌ Uso: g o g [número]")
        
        elif cmd.startswith('p') and (cmd == 'p' or ' ' in cmd):
            try:
                if cmd == 'p' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                if self.historial.marcar(num, 'PERDIDA'):
                    print(f"\n  ❌ #{num} marcada como PERDIDA")
                    enviar_telegram(f"❌ Señal #{num} PERDIDA")
                else:
                    print(f"\n  ❌ No encontré señal #{num}")
            except:
                print("\n  ❌ Uso: p o p [número]")
        
        elif cmd in ['m', 'menu']:
            self.mostrar_menu()
        
        elif cmd in ['c', 'clear', 'cls']:
            limpiar()
            self.mostrar_encabezado()
        
        elif cmd:
            print(f"\n  ❓ '{cmd}' no reconocido. Escribe 'm' para menú")
        
        return True
    
    async def procesar_ws(self, msg):
        try:
            data = json.loads(msg)
            if data.get('name') == 'candle-generated':
                m = data.get('msg', {})
                aid = m.get('active_id', 0)
                if m.get('close'):
                    self.precios[aid] = m['close']
                    self.analizador.agregar_vela(aid, m)
        except:
            pass
    
    def mostrar_encabezado(self):
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print("║  🎯 BOT MEAN REVERSION - ESTRATEGIA BULLEX OPTIMIZADA           ║")
        print("╠" + "═" * 66 + "╣")
        print(f"║  🕐 {fmt_hora()} | 📅 {fmt_fecha():<44}║")
        print("╠" + "═" * 66 + "╣")
        print("║  📊 SISTEMA DE CLASIFICACIÓN:                                   ║")
        print("║     🅰️ Señal A (≥70 pts) → OPERAR - Mejor calidad              ║")
        print("║     🅱️ Señal B (60-69 pts) → OPERAR - Más riesgo               ║")
        print("║     🅲️ Señal C (<60 pts) → NO OPERAR                           ║")
        print("╠" + "═" * 66 + "╣")
        print("║  🛡️ FILTROS ACTIVOS:                                            ║")
        print("║     • Anti-volatilidad (velas monstruo)                         ║")
        print("║     • Anti-bandwalk (precio pegado a banda)                     ║")
        print("║     • Máx 2 entradas/par + pausa tras 2 pérdidas                ║")
        print("╠" + "═" * 66 + "╣")
        print("║  💡 Escribe '1' para buscar señal, 'm' para menú                ║")
        print("╚" + "═" * 66 + "╝")
    
    async def loop_input(self):
        loop = asyncio.get_event_loop()
        while self.ejecutando:
            try:
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 "))
                if not self.comando(cmd):
                    self.ejecutando = False
            except:
                pass
    
    async def loop_ws(self):
        while self.ejecutando and self.conectado:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                await self.procesar_ws(msg)
            except asyncio.TimeoutError:
                pass
            except:
                if self.ejecutando:
                    print("\n  ⚠️ Reconectando...")
                    await self.conectar()
    
    async def ejecutar(self):
        if not await self.conectar():
            return
        
        limpiar()
        self.mostrar_encabezado()
        self.mostrar_stats()
        self.mostrar_menu()
        
        print("\n  ⏳ Recolectando datos de mercado...")
        print("  💡 Espera ~30 seg antes de pedir la primera señal\n")
        
        try:
            await asyncio.gather(self.loop_ws(), self.loop_input())
        except:
            pass
        
        print("\n" + "═" * 60)
        self.mostrar_stats()
        if self.ws:
            await self.ws.close()
        print(f"\n  👋 ¡Hasta pronto! - {fmt_hora()}\n")


# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  🎯 BOT MEAN REVERSION - BULLEX OPTIMIZADO                        ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  📊 PUNTUACIÓN:                                                    ║
║     • Toca banda:        +35 pts                                   ║
║     • RSI extremo:       +25 pts (≤28 / ≥72)                       ║
║     • Rechazo:           +20 pts                                   ║
║     • Confirmación:      +20 pts                                   ║
║     • Volatilidad alta:  -40 pts                                   ║
║     • Band-walk:         -30 pts                                   ║
║                                                                    ║
║  🎯 CLASIFICACIÓN:                                                 ║
║     🅰️ ≥70 pts → OPERAR (mejor calidad)                           ║
║     🅱️ 60-69 pts → OPERAR (más riesgo)                            ║
║     🅲️ <60 pts → NO OPERAR                                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    ssid = MI_SSID.strip() or input("  🔑 SSID: ").strip()
    if not ssid:
        print("\n  ❌ SSID requerido")
        return
    
    await Bot(ssid).ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Cerrado\n")
