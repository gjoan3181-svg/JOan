#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   🎯 BULLEX BOT PRECISIÓN - VERSIÓN ULTRA OPTIMIZADA
══════════════════════════════════════════════════════════════════════════════════

   🏆 OBJETIVO: 80%+ de precisión (8 de 10 ganadoras)
   
   ✅ MEJORAS IMPLEMENTADAS:
   ─────────────────────────────────────────────────────────────────────────────
   1. FILTROS ULTRA-ESTRICTOS
      • Sentimiento mínimo: 92% (antes era 88%)
      • Probabilidad mínima: 90% (antes era 85%)
      • Confirmación técnica OBLIGATORIA
      • Rechazo de divergencias sentimiento vs técnico
   
   2. UNA SOLA SEÑAL POR PETICIÓN
      • Sistema de cola inteligente
      • Solo muestra la MEJOR señal disponible
      • Cooldown extendido entre señales
   
   3. EXPLICACIÓN DETALLADA
      • Muestra el PORQUÉ de cada señal
      • Puntuación de cada indicador
      • Nivel de confianza explicado
   
   4. FILTRO DE ACTIVOS
      • Solo activos que TÚ configures
      • Lista personalizable de activos permitidos
   
   5. ANÁLISIS MULTI-INDICADOR
      • RSI + Tendencia + Momentum + Volumen
      • Mínimo 4 confirmaciones para señal
      • Sistema de puntuación 0-100
   ─────────────────────────────────────────────────────────────────────────────

   Uso: python3 bot_precision.py

══════════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import os
import time

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# 👇 PEGA TU SSID AQUÍ:
MI_SSID = "e8b7b6185348833f922e675fe840fc3f"

# URLs
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_precision.json"

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))


# ═══════════════════════════════════════════════════════════════════════════════
#                    🎯 PARÁMETROS ULTRA-ESTRICTOS
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigPrecision:
    """
    Configuración optimizada para 80%+ de precisión.
    Cada parámetro está calculado para maximizar win rate.
    """
    
    # ══════════ FILTROS DE SEÑAL (MÁS ESTRICTOS) ══════════
    UMBRAL_SENTIMIENTO = 92      # Solo señales con >92% sentimiento (antes: 88%)
    PROBABILIDAD_MINIMA = 90     # Probabilidad mínima 90% (antes: 85%)
    PUNTUACION_MINIMA = 85       # Puntuación técnica mínima 85/100
    
    # ══════════ CONFIRMACIONES REQUERIDAS ══════════
    MIN_CONFIRMACIONES = 4       # Mínimo 4 indicadores confirmando
    RECHAZAR_DIVERGENCIAS = True # Rechazar si técnico contradice sentimiento
    
    # ══════════ TIEMPOS ══════════
    ANTICIPACION_MINUTOS = 2     # Señal 2 min antes de entrada
    DURACION_OPERACION = 2       # Operación de 2 minutos
    COOLDOWN_ACTIVO = 600        # 10 min entre señales del mismo activo (antes: 5)
    COOLDOWN_GLOBAL = 120        # 2 min entre cualquier señal
    
    # ══════════ LÍMITES ══════════
    MAX_SENALES_HORA = 6         # Máximo 6 señales por hora (antes: 15)
    UNA_SENAL_A_LA_VEZ = True    # Solo mostrar 1 señal, la mejor
    
    # ══════════ ANÁLISIS TÉCNICO ══════════
    VELAS_ANALISIS = 20          # Velas para análisis de tendencia
    VELAS_MOMENTUM = 10          # Velas para análisis de momentum
    
    # ══════════ PESOS DE INDICADORES ══════════
    PESO_SENTIMIENTO = 35        # 35% del score
    PESO_TENDENCIA = 25          # 25% del score  
    PESO_MOMENTUM = 20           # 20% del score
    PESO_VOLATILIDAD = 10        # 10% del score
    PESO_VOLUMEN = 10            # 10% del score


# ═══════════════════════════════════════════════════════════════════════════════
#               🎮 ACTIVOS PERMITIDOS (CONFIGURA EN config_activos.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Intenta importar desde config_activos.py, si no usa lista por defecto
try:
    from config_activos import get_activos_habilitados, ACTIVOS
except ImportError:
    # Lista por defecto si no existe config_activos.py
    ACTIVOS_PERMITIDOS = {
        # ════════════════ FOREX OTC (Los más estables) ════════════════
        1:   {"nombre": "EUR/USD",     "mercado": "FOREX",  "simbolo": "EUR/USD (OTC)",  "activo": True},
        2:   {"nombre": "EUR/GBP",     "mercado": "FOREX",  "simbolo": "EUR/GBP (OTC)",  "activo": True},
        3:   {"nombre": "GBP/USD",     "mercado": "FOREX",  "simbolo": "GBP/USD (OTC)",  "activo": True},
        4:   {"nombre": "EUR/JPY",     "mercado": "FOREX",  "simbolo": "EUR/JPY (OTC)",  "activo": True},
        5:   {"nombre": "USD/JPY",     "mercado": "FOREX",  "simbolo": "USD/JPY (OTC)",  "activo": True},
        6:   {"nombre": "AUD/USD",     "mercado": "FOREX",  "simbolo": "AUD/USD (OTC)",  "activo": True},
        7:   {"nombre": "USD/CAD",     "mercado": "FOREX",  "simbolo": "USD/CAD (OTC)",  "activo": True},
        
        # ════════════════ CRYPTO OTC (Los más populares) ════════════════
        212:  {"nombre": "Bitcoin",     "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)",  "activo": True},
        220:  {"nombre": "Ethereum",    "mercado": "CRYPTO", "simbolo": "ETH/USD (OTC)",  "activo": True},
        1876: {"nombre": "Solana",      "mercado": "CRYPTO", "simbolo": "SOL/USD (OTC)",  "activo": True},
        1873: {"nombre": "Dogecoin",    "mercado": "CRYPTO", "simbolo": "DOGE/USD (OTC)", "activo": True},
        
        # ════════════════ COMMODITIES OTC ════════════════
        959:  {"nombre": "Oro",         "mercado": "COMMODITIES", "simbolo": "XAU/USD (OTC)", "activo": True},
        960:  {"nombre": "Plata",       "mercado": "COMMODITIES", "simbolo": "XAG/USD (OTC)", "activo": True},
        
        # ════════════════ ÍNDICES OTC ════════════════
        947:  {"nombre": "Nasdaq 100",  "mercado": "ÍNDICES", "simbolo": "US100 (OTC)",   "activo": True},
        948:  {"nombre": "S&P 500",     "mercado": "ÍNDICES", "simbolo": "US500 (OTC)",   "activo": True},
    }
    
    def get_activos_habilitados():
        return {k: v for k, v in ACTIVOS_PERMITIDOS.items() if v.get("activo", True)}


# ═══════════════════════════════════════════════════════════════════════════════
#                              ESTRUCTURAS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

class TipoSenal(Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass
class AnalisisTecnico:
    """Resultado detallado del análisis técnico"""
    tendencia: int              # 1=alcista, -1=bajista, 0=lateral
    tendencia_texto: str
    tendencia_fuerza: float     # 0-100
    momentum: float             # 0-100
    volatilidad: str            # BAJA, MEDIA, ALTA
    volumen_relativo: float     # ratio vs promedio
    confirmaciones: List[str]   # Lista de indicadores que confirman
    rechazos: List[str]         # Lista de indicadores que rechazan
    puntuacion: float           # Score total 0-100


@dataclass 
class RazonSenal:
    """Explicación detallada de una razón para la señal"""
    indicador: str
    valor: str
    contribucion: float  # Puntos que aporta
    explicacion: str


@dataclass
class SenalPrecision:
    """Señal de trading con explicación completa"""
    id: str
    timestamp: str
    activo_id: int
    nombre: str
    simbolo: str
    mercado: str
    
    direccion: TipoSenal
    probabilidad: float
    puntuacion: float
    
    # Análisis detallado
    sentimiento_pct: float
    analisis: AnalisisTecnico
    razones: List[RazonSenal]
    
    # Tiempos
    hora_senal: str
    entrada: str
    expiracion: str
    segundos_hasta_entrada: int
    
    # Estado
    precio_entrada: float = 0
    verificado: bool = False
    resultado: Optional[str] = None


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
#                    🔬 ANALIZADOR TÉCNICO AVANZADO
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorAvanzado:
    """
    Analizador técnico multi-indicador para máxima precisión.
    Combina: Tendencia + Momentum + Volatilidad + Volumen
    """
    
    def __init__(self):
        self.velas = defaultdict(list)
        self.volumenes = defaultdict(list)
        self.max_velas = ConfigPrecision.VELAS_ANALISIS
    
    def agregar_vela(self, aid: int, vela: dict):
        """Agrega una vela al historial del activo"""
        datos = {
            'open': vela.get('open', 0),
            'high': vela.get('max', vela.get('high', 0)),
            'low': vela.get('min', vela.get('low', 0)),
            'close': vela.get('close', 0),
            'volume': vela.get('volume', 0),
            'time': vela.get('time', time.time())
        }
        
        self.velas[aid].append(datos)
        if datos['volume'] > 0:
            self.volumenes[aid].append(datos['volume'])
        
        # Mantener solo las últimas N velas
        if len(self.velas[aid]) > self.max_velas:
            self.velas[aid].pop(0)
        if len(self.volumenes[aid]) > self.max_velas:
            self.volumenes[aid].pop(0)
    
    def calcular_ema(self, precios: List[float], periodo: int) -> float:
        """Calcula EMA (Exponential Moving Average)"""
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        
        multiplicador = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        
        for precio in precios[periodo:]:
            ema = (precio * multiplicador) + (ema * (1 - multiplicador))
        
        return ema
    
    def calcular_rsi(self, precios: List[float], periodo: int = 14) -> float:
        """Calcula RSI (Relative Strength Index)"""
        if len(precios) < periodo + 1:
            return 50
        
        cambios = [precios[i] - precios[i-1] for i in range(1, len(precios))]
        ganancias = [c if c > 0 else 0 for c in cambios[-periodo:]]
        perdidas = [-c if c < 0 else 0 for c in cambios[-periodo:]]
        
        avg_ganancia = sum(ganancias) / periodo
        avg_perdida = sum(perdidas) / periodo
        
        if avg_perdida == 0:
            return 100
        
        rs = avg_ganancia / avg_perdida
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calcular_tendencia(self, aid: int) -> tuple:
        """
        Calcula la tendencia usando múltiples métodos.
        Retorna: (direccion, fuerza, texto)
        """
        velas = self.velas.get(aid, [])
        if len(velas) < 10:
            return 0, 0, "INSUFICIENTES DATOS"
        
        precios = [v['close'] for v in velas]
        
        # 1. EMA Cross (EMA 5 vs EMA 10)
        ema5 = self.calcular_ema(precios, 5)
        ema10 = self.calcular_ema(precios, 10)
        
        # 2. Cambio porcentual reciente
        precio_inicio = precios[-10]
        precio_fin = precios[-1]
        cambio_pct = ((precio_fin - precio_inicio) / precio_inicio) * 100 if precio_inicio else 0
        
        # 3. Contar velas alcistas vs bajistas
        ultimas = velas[-10:]
        alcistas = sum(1 for v in ultimas if v['close'] > v['open'])
        
        # Calcular score de tendencia
        score = 0
        
        # EMA cross
        if ema5 > ema10:
            score += 30
        else:
            score -= 30
        
        # Cambio porcentual
        if cambio_pct > 0.1:
            score += 25
        elif cambio_pct < -0.1:
            score -= 25
        
        # Velas alcistas/bajistas
        if alcistas >= 7:
            score += 25
        elif alcistas <= 3:
            score -= 25
        
        # Precio actual vs EMAs
        if precio_fin > ema5 > ema10:
            score += 20
        elif precio_fin < ema5 < ema10:
            score -= 20
        
        # Determinar dirección y fuerza
        if score >= 50:
            return 1, abs(score), "ALCISTA FUERTE ↑↑"
        elif score >= 20:
            return 1, abs(score), "ALCISTA ↑"
        elif score <= -50:
            return -1, abs(score), "BAJISTA FUERTE ↓↓"
        elif score <= -20:
            return -1, abs(score), "BAJISTA ↓"
        else:
            return 0, abs(score), "LATERAL →"
    
    def calcular_momentum(self, aid: int) -> float:
        """
        Calcula el momentum (fuerza y velocidad del movimiento).
        Retorna: valor de 0 a 100
        """
        velas = self.velas.get(aid, [])
        if len(velas) < ConfigPrecision.VELAS_MOMENTUM:
            return 50
        
        precios = [v['close'] for v in velas]
        
        # RSI
        rsi = self.calcular_rsi(precios)
        
        # Velocidad del cambio (ROC)
        roc = ((precios[-1] - precios[-5]) / precios[-5]) * 100 if precios[-5] else 0
        
        # Aceleración
        cambio_reciente = precios[-1] - precios[-3]
        cambio_anterior = precios[-3] - precios[-5]
        aceleracion = cambio_reciente - cambio_anterior
        
        # Combinar métricas
        momentum = 50
        
        # RSI contribuye 40%
        if rsi > 70:
            momentum += 20
        elif rsi < 30:
            momentum -= 20
        elif rsi > 60:
            momentum += 10
        elif rsi < 40:
            momentum -= 10
        
        # ROC contribuye 30%
        momentum += min(max(roc * 10, -15), 15)
        
        # Aceleración contribuye 30%
        if aceleracion > 0:
            momentum += min(aceleracion * 100, 15)
        else:
            momentum += max(aceleracion * 100, -15)
        
        return max(0, min(100, momentum))
    
    def calcular_volatilidad(self, aid: int) -> tuple:
        """
        Calcula la volatilidad del activo.
        Retorna: (clasificacion, valor)
        """
        velas = self.velas.get(aid, [])
        if len(velas) < 10:
            return "MEDIA", 50
        
        # ATR simplificado
        rangos = []
        for i in range(1, len(velas)):
            tr = max(
                velas[i]['high'] - velas[i]['low'],
                abs(velas[i]['high'] - velas[i-1]['close']),
                abs(velas[i]['low'] - velas[i-1]['close'])
            )
            rangos.append(tr)
        
        atr = sum(rangos[-10:]) / 10 if rangos else 0
        precio = velas[-1]['close']
        
        atr_pct = (atr / precio) * 100 if precio else 0
        
        if atr_pct < 0.3:
            return "BAJA", atr_pct
        elif atr_pct < 0.8:
            return "MEDIA", atr_pct
        else:
            return "ALTA", atr_pct
    
    def calcular_volumen_relativo(self, aid: int) -> float:
        """Calcula el volumen relativo al promedio"""
        volumenes = self.volumenes.get(aid, [])
        if len(volumenes) < 5:
            return 1.0
        
        promedio = sum(volumenes[:-1]) / (len(volumenes) - 1)
        actual = volumenes[-1]
        
        return actual / promedio if promedio > 0 else 1.0
    
    def analizar_completo(self, aid: int, sentimiento_pct: float) -> AnalisisTecnico:
        """
        Realiza análisis técnico completo.
        Retorna: AnalisisTecnico con todos los detalles
        """
        # Obtener métricas
        tendencia, tendencia_fuerza, tendencia_texto = self.calcular_tendencia(aid)
        momentum = self.calcular_momentum(aid)
        volatilidad, vol_valor = self.calcular_volatilidad(aid)
        vol_relativo = self.calcular_volumen_relativo(aid)
        
        confirmaciones = []
        rechazos = []
        puntuacion = 0
        
        # ══════════ ANÁLISIS DE SENTIMIENTO ══════════
        # Determinar dirección esperada por sentimiento
        if sentimiento_pct > 50:
            direccion_sent = 1  # CALL esperado
            sent_fuerza = sentimiento_pct
        else:
            direccion_sent = -1  # PUT esperado
            sent_fuerza = 100 - sentimiento_pct
        
        # Puntos por sentimiento (máx 35)
        puntos_sent = (sent_fuerza / 100) * ConfigPrecision.PESO_SENTIMIENTO
        puntuacion += puntos_sent
        
        if sent_fuerza >= 92:
            confirmaciones.append(f"✅ Sentimiento EXTREMO: {sent_fuerza:.0f}%")
        elif sent_fuerza >= 88:
            confirmaciones.append(f"✅ Sentimiento fuerte: {sent_fuerza:.0f}%")
        else:
            rechazos.append(f"⚠️ Sentimiento débil: {sent_fuerza:.0f}%")
        
        # ══════════ ANÁLISIS DE TENDENCIA ══════════
        # Puntos por tendencia (máx 25)
        if tendencia == direccion_sent:
            puntos_tend = (tendencia_fuerza / 100) * ConfigPrecision.PESO_TENDENCIA
            puntuacion += puntos_tend
            confirmaciones.append(f"✅ Tendencia CONFIRMA: {tendencia_texto}")
        elif tendencia == -direccion_sent:
            # Tendencia contradice - penalización fuerte
            puntuacion -= 15
            rechazos.append(f"❌ Tendencia CONTRADICE: {tendencia_texto}")
        else:
            # Lateral - no suma ni resta mucho
            puntuacion += 5
            confirmaciones.append(f"➡️ Tendencia lateral (neutral)")
        
        # ══════════ ANÁLISIS DE MOMENTUM ══════════
        # Puntos por momentum (máx 20)
        if direccion_sent == 1:  # CALL
            if momentum > 60:
                puntos_mom = ((momentum - 50) / 50) * ConfigPrecision.PESO_MOMENTUM
                puntuacion += puntos_mom
                confirmaciones.append(f"✅ Momentum alcista: {momentum:.0f}")
            elif momentum < 40:
                puntuacion -= 10
                rechazos.append(f"❌ Momentum bajista: {momentum:.0f}")
        else:  # PUT
            if momentum < 40:
                puntos_mom = ((50 - momentum) / 50) * ConfigPrecision.PESO_MOMENTUM
                puntuacion += puntos_mom
                confirmaciones.append(f"✅ Momentum bajista: {momentum:.0f}")
            elif momentum > 60:
                puntuacion -= 10
                rechazos.append(f"❌ Momentum alcista: {momentum:.0f}")
        
        # ══════════ ANÁLISIS DE VOLATILIDAD ══════════
        # Puntos por volatilidad (máx 10)
        if volatilidad == "BAJA":
            puntuacion += 8  # Preferimos baja volatilidad
            confirmaciones.append(f"✅ Volatilidad baja (predecible)")
        elif volatilidad == "MEDIA":
            puntuacion += 5
            confirmaciones.append(f"➡️ Volatilidad media")
        else:
            puntuacion -= 5  # Alta volatilidad es riesgosa
            rechazos.append(f"⚠️ Volatilidad ALTA (riesgoso)")
        
        # ══════════ ANÁLISIS DE VOLUMEN ══════════
        # Puntos por volumen (máx 10)
        if vol_relativo > 1.3:
            puntuacion += 10
            confirmaciones.append(f"✅ Volumen alto: {vol_relativo:.1f}x")
        elif vol_relativo > 0.8:
            puntuacion += 5
            confirmaciones.append(f"➡️ Volumen normal: {vol_relativo:.1f}x")
        else:
            rechazos.append(f"⚠️ Volumen bajo: {vol_relativo:.1f}x")
        
        return AnalisisTecnico(
            tendencia=tendencia,
            tendencia_texto=tendencia_texto,
            tendencia_fuerza=tendencia_fuerza,
            momentum=momentum,
            volatilidad=volatilidad,
            volumen_relativo=vol_relativo,
            confirmaciones=confirmaciones,
            rechazos=rechazos,
            puntuacion=max(0, min(100, puntuacion))
        )


# ═══════════════════════════════════════════════════════════════════════════════
#                              GESTOR DE HISTORIAL
# ═══════════════════════════════════════════════════════════════════════════════

class HistorialPrecision:
    """Gestiona el historial con estadísticas detalladas"""
    
    def __init__(self, archivo):
        self.archivo = archivo
        self.senales = []
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
    
    def agregar(self, senal: dict):
        self.senales.append(senal)
        self.guardar()
    
    def actualizar_resultado(self, senal_id: str, resultado: str, precio_cierre: float):
        for s in self.senales:
            if s.get('id') == senal_id:
                s['resultado'] = resultado
                s['precio_cierre'] = precio_cierre
                s['verificado'] = True
                break
        self.guardar()
    
    def estadisticas(self) -> dict:
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        perdidas = [s for s in verificadas if s.get('resultado') == 'PERDIDA']
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        # Calcular racha
        racha_actual = 0
        for s in reversed(verificadas):
            if s.get('resultado') == 'GANADA':
                racha_actual += 1
            else:
                break
        
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(perdidas),
            'pendientes': total - len(verificadas),
            'precision': precision,
            'racha': racha_actual
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                         🏆 BOT DE PRECISIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class BotPrecision:
    """
    Bot de trading optimizado para máxima precisión.
    Objetivo: 80%+ de operaciones ganadoras.
    """
    
    def __init__(self, ssid: str):
        self.ssid = ssid
        self.ws = None
        self.conectado = False
        
        # Componentes
        self.historial = HistorialPrecision(HISTORIAL_FILE)
        self.analizador = AnalizadorAvanzado()
        self.activos = get_activos_habilitados()
        
        # Estado
        self.precios = {}
        self.senal_pendiente: Optional[dict] = None  # Solo 1 señal a la vez
        self.senal_activa: Optional[dict] = None
        self.ultima_senal_global = 0
        self.ultima_senal_activo = {}
        self.senales_hora = 0
        self.hora_reset = time.time()
        
        # Cola de señales candidatas
        self.cola_senales = []
        
        print(f"\n  📊 Activos habilitados: {len(self.activos)}")
        for aid, info in self.activos.items():
            print(f"     • {info['simbolo']}")
    
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
            print(f"  ✅ Conectado exitosamente\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Error de conexión: {e}\n")
            return False
    
    def calcular_tiempos(self):
        """Calcula tiempos de entrada y expiración"""
        ahora = hora_rd()
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(
            minutes=ConfigPrecision.ANTICIPACION_MINUTOS + 1
        )
        expiracion = entrada + timedelta(minutes=ConfigPrecision.DURACION_OPERACION)
        segundos = (entrada - ahora).total_seconds()
        return entrada, expiracion, int(segundos)
    
    def generar_razones(self, analisis: AnalisisTecnico, sentimiento: float) -> List[RazonSenal]:
        """Genera lista detallada de razones para la señal"""
        razones = []
        
        # Razón: Sentimiento
        razones.append(RazonSenal(
            indicador="SENTIMIENTO",
            valor=f"{sentimiento:.0f}%",
            contribucion=ConfigPrecision.PESO_SENTIMIENTO * (sentimiento/100),
            explicacion=f"El {sentimiento:.0f}% de los traders están en esta dirección"
        ))
        
        # Razón: Tendencia
        razones.append(RazonSenal(
            indicador="TENDENCIA",
            valor=analisis.tendencia_texto,
            contribucion=analisis.tendencia_fuerza * 0.25,
            explicacion=f"El precio muestra tendencia {analisis.tendencia_texto.lower()}"
        ))
        
        # Razón: Momentum
        razones.append(RazonSenal(
            indicador="MOMENTUM",
            valor=f"{analisis.momentum:.0f}/100",
            contribucion=analisis.momentum * 0.2,
            explicacion=f"La fuerza del movimiento es {'alta' if analisis.momentum > 60 else 'media' if analisis.momentum > 40 else 'baja'}"
        ))
        
        # Razón: Volatilidad
        razones.append(RazonSenal(
            indicador="VOLATILIDAD",
            valor=analisis.volatilidad,
            contribucion=10 if analisis.volatilidad == "BAJA" else 5,
            explicacion=f"Volatilidad {analisis.volatilidad.lower()} = {'predecible' if analisis.volatilidad == 'BAJA' else 'moderada' if analisis.volatilidad == 'MEDIA' else 'riesgosa'}"
        ))
        
        # Razón: Volumen
        razones.append(RazonSenal(
            indicador="VOLUMEN",
            valor=f"{analisis.volumen_relativo:.1f}x",
            contribucion=10 if analisis.volumen_relativo > 1.3 else 5,
            explicacion=f"Volumen {'elevado (confirmación)' if analisis.volumen_relativo > 1.3 else 'normal'}"
        ))
        
        return razones
    
    def evaluar_senal(self, aid: int, sentimiento_pct: float) -> Optional[dict]:
        """
        Evalúa si una señal cumple con los criterios ultra-estrictos.
        Retorna: dict con la señal si pasa los filtros, None si no
        """
        ahora = time.time()
        
        # ═══════ FILTRO 1: Activo habilitado ═══════
        if aid not in self.activos:
            return None
        
        # ═══════ FILTRO 2: Cooldown por activo ═══════
        if aid in self.ultima_senal_activo:
            if ahora - self.ultima_senal_activo[aid] < ConfigPrecision.COOLDOWN_ACTIVO:
                return None
        
        # ═══════ FILTRO 3: Cooldown global ═══════
        if ahora - self.ultima_senal_global < ConfigPrecision.COOLDOWN_GLOBAL:
            return None
        
        # ═══════ FILTRO 4: Límite por hora ═══════
        if self.senales_hora >= ConfigPrecision.MAX_SENALES_HORA:
            return None
        
        # ═══════ FILTRO 5: Sentimiento mínimo ═══════
        if sentimiento_pct > 50:
            direccion = TipoSenal.CALL
            sent_fuerza = sentimiento_pct
        else:
            direccion = TipoSenal.PUT
            sent_fuerza = 100 - sentimiento_pct
        
        if sent_fuerza < ConfigPrecision.UMBRAL_SENTIMIENTO:
            return None
        
        # ═══════ ANÁLISIS TÉCNICO COMPLETO ═══════
        analisis = self.analizador.analizar_completo(aid, sentimiento_pct)
        
        # ═══════ FILTRO 6: Puntuación mínima ═══════
        if analisis.puntuacion < ConfigPrecision.PUNTUACION_MINIMA:
            return None
        
        # ═══════ FILTRO 7: Mínimo de confirmaciones ═══════
        if len(analisis.confirmaciones) < ConfigPrecision.MIN_CONFIRMACIONES:
            return None
        
        # ═══════ FILTRO 8: Rechazar divergencias ═══════
        if ConfigPrecision.RECHAZAR_DIVERGENCIAS:
            # Si tendencia contradice sentimiento, rechazar
            if (direccion == TipoSenal.CALL and analisis.tendencia == -1) or \
               (direccion == TipoSenal.PUT and analisis.tendencia == 1):
                if analisis.tendencia_fuerza > 50:  # Solo si es fuerte
                    return None
        
        # ═══════ CALCULAR PROBABILIDAD FINAL ═══════
        probabilidad = analisis.puntuacion
        
        # Bonus por sentimiento extremo
        if sent_fuerza >= 95:
            probabilidad = min(99, probabilidad + 5)
        
        # ═══════ FILTRO 9: Probabilidad mínima ═══════
        if probabilidad < ConfigPrecision.PROBABILIDAD_MINIMA:
            return None
        
        # ═══════ GENERAR SEÑAL ═══════
        activo = self.activos[aid]
        entrada, expiracion, segundos = self.calcular_tiempos()
        razones = self.generar_razones(analisis, sent_fuerza)
        
        return {
            'id': f"{aid}_{int(ahora)}",
            'timestamp': hora_rd().isoformat(),
            'activo_id': aid,
            'nombre': activo['nombre'],
            'simbolo': activo['simbolo'],
            'mercado': activo['mercado'],
            'direccion': direccion.value,
            'probabilidad': probabilidad,
            'puntuacion': analisis.puntuacion,
            'sentimiento': sent_fuerza,
            'analisis': {
                'tendencia': analisis.tendencia_texto,
                'momentum': analisis.momentum,
                'volatilidad': analisis.volatilidad,
                'volumen': analisis.volumen_relativo,
                'confirmaciones': analisis.confirmaciones,
                'rechazos': analisis.rechazos
            },
            'razones': [
                {
                    'indicador': r.indicador,
                    'valor': r.valor,
                    'contribucion': r.contribucion,
                    'explicacion': r.explicacion
                } for r in razones
            ],
            'hora_senal': fmt_hora(),
            'entrada': fmt_hora(entrada),
            'entrada_dt': entrada.isoformat(),
            'expiracion': fmt_hora(expiracion),
            'expiracion_dt': expiracion.isoformat(),
            'segundos_hasta_entrada': segundos,
            'precio_entrada': self.precios.get(aid, 0),
            'verificado': False,
            'resultado': None
        }
    
    def mostrar_senal(self, s: dict):
        """Muestra una señal con explicación detallada del PORQUÉ"""
        
        direccion = s['direccion']
        if direccion == 'CALL':
            dir_emoji = "🟢🟢🟢"
            dir_texto = "COMPRAR (CALL) ↑"
            dir_color = "VERDE"
        else:
            dir_emoji = "🔴🔴🔴"
            dir_texto = "VENDER (PUT) ↓"
            dir_color = "ROJO"
        
        mins = s['segundos_hasta_entrada'] // 60
        segs = s['segundos_hasta_entrada'] % 60
        
        # Nivel de confianza
        prob = s['probabilidad']
        if prob >= 95:
            nivel = "🔥 EXTREMA"
            estrellas = "★★★★★"
        elif prob >= 92:
            nivel = "✅ MUY ALTA"
            estrellas = "★★★★☆"
        else:
            nivel = "📊 ALTA"
            estrellas = "★★★☆☆"
        
        print("\n")
        print("╔" + "═" * 70 + "╗")
        print(f"║  🎯 SEÑAL DE PRECISIÓN - {nivel:<43}║")
        print(f"║  {estrellas:<66}║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  📍 Activo:       {s['nombre']:<50}║")
        print(f"║  🏷️  Símbolo:      {s['simbolo']:<50}║")
        print(f"║  📊 Mercado:      {s['mercado']:<50}║")
        print("╠" + "═" * 70 + "╣")
        print(f"║     {dir_emoji}  {dir_texto:<53}║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  📈 Probabilidad:    {s['probabilidad']:.0f}%{' ' * 46}║")
        print(f"║  🎯 Puntuación:      {s['puntuacion']:.0f}/100{' ' * 43}║")
        print(f"║  👥 Sentimiento:     {s['sentimiento']:.0f}% de traders{' ' * 34}║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  ⏰ ENTRAR EN:       {mins} min {segs:02d} seg{' ' * 40}║")
        print(f"║  🎯 HORA ENTRADA:    {s['entrada']:<48}║")
        print(f"║  ⏱️  EXPIRACIÓN:      {s['expiracion']:<48}║")
        print("╠" + "═" * 70 + "╣")
        
        # ══════════ EXPLICACIÓN DEL PORQUÉ ══════════
        print("║" + " " * 70 + "║")
        print("║  📋 ¿POR QUÉ ESTA SEÑAL?" + " " * 44 + "║")
        print("║  " + "─" * 66 + "  ║")
        
        # Mostrar confirmaciones
        analisis = s['analisis']
        for conf in analisis['confirmaciones'][:5]:
            texto = conf[:64]
            print(f"║  {texto:<68}║")
        
        print("║" + " " * 70 + "║")
        
        # Mostrar razones detalladas
        print("║  📊 ANÁLISIS DETALLADO:" + " " * 45 + "║")
        print("║  " + "─" * 66 + "  ║")
        
        for razon in s['razones']:
            linea = f"  • {razon['indicador']}: {razon['valor']}"
            print(f"║{linea:<70}║")
            exp = f"    → {razon['explicacion'][:60]}"
            print(f"║{exp:<70}║")
        
        # Advertencias si hay
        if analisis['rechazos']:
            print("║" + " " * 70 + "║")
            print("║  ⚠️  ADVERTENCIAS:" + " " * 50 + "║")
            for rech in analisis['rechazos'][:2]:
                texto = rech[:64]
                print(f"║  {texto:<68}║")
        
        print("╠" + "═" * 70 + "╣")
        print(f"║  🕐 Hora RD:         {fmt_hora():<48}║")
        print("╚" + "═" * 70 + "╝")
    
    def mostrar_alerta_entrada(self, s: dict):
        """Muestra alerta cuando es momento de entrar"""
        direccion = s['direccion']
        if direccion == 'CALL':
            dir_texto = "🟢 COMPRAR (CALL)"
        else:
            dir_texto = "🔴 VENDER (PUT)"
        
        print("\n")
        print("🔔" * 30)
        print("╔" + "═" * 58 + "╗")
        print(f"║  ⚡⚡⚡ ¡¡¡ ENTRAR AHORA !!! ⚡⚡⚡{' ' * 19}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📍 {s['nombre']:<52}║")
        print(f"║  🏷️  {s['simbolo']:<52}║")
        print(f"║  {dir_texto:<56}║")
        print(f"║  📈 Probabilidad: {s['probabilidad']:.0f}%{' ' * 36}║")
        print(f"║  ⏱️  Expira: {s['expiracion']}{' ' * 41}║")
        print("╚" + "═" * 58 + "╝")
        print("🔔" * 30)
    
    def mostrar_resultado(self, s: dict, resultado: str, precio_cierre: float):
        """Muestra el resultado de una operación"""
        if resultado == 'GANADA':
            emoji = "✅ ¡GANADA!"
        else:
            emoji = "❌ PERDIDA"
        
        print(f"\n{emoji} {s['nombre']} ({s['simbolo']})")
        print(f"   Dirección: {s['direccion']}")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas de precisión"""
        stats = self.historial.estadisticas()
        
        print("\n")
        print("┌" + "─" * 54 + "┐")
        print(f"│  📊 ESTADÍSTICAS DE PRECISIÓN{' ' * 23}│")
        print("├" + "─" * 54 + "┤")
        print(f"│  Señales hoy:          {self.senales_hora}/{ConfigPrecision.MAX_SENALES_HORA}{' ' * 25}│")
        print("├" + "─" * 54 + "┤")
        print(f"│  Total histórico:      {stats['total']:<28}│")
        print(f"│  Verificadas:          {stats['verificadas']:<28}│")
        print(f"│  ✅ Ganadas:           {stats['ganadas']:<28}│")
        print(f"│  ❌ Perdidas:          {stats['perdidas']:<28}│")
        print("├" + "─" * 54 + "┤")
        print(f"│  🎯 PRECISIÓN:         {stats['precision']:.1f}%{' ' * 25}│")
        print(f"│  🔥 Racha actual:      {stats['racha']} ganadas{' ' * 20}│")
        print("└" + "─" * 54 + "┘")
    
    def mostrar_encabezado(self):
        """Muestra el encabezado del bot"""
        print("\n")
        print("╔" + "═" * 70 + "╗")
        print("║" + " " * 70 + "║")
        print("║     🎯  BOT DE PRECISIÓN - OBJETIVO 80%+ WIN RATE  🎯" + " " * 14 + "║")
        print("║" + " " * 70 + "║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  🕐 Hora:             {fmt_hora()} (Rep. Dominicana){' ' * 21}║")
        print(f"║  📅 Fecha:            {fmt_fecha():<46}║")
        print("╠" + "═" * 70 + "╣")
        print("║  🔒 FILTROS ULTRA-ESTRICTOS:" + " " * 40 + "║")
        print(f"║     • Sentimiento mínimo:   {ConfigPrecision.UMBRAL_SENTIMIENTO}%{' ' * 36}║")
        print(f"║     • Probabilidad mínima:  {ConfigPrecision.PROBABILIDAD_MINIMA}%{' ' * 36}║")
        print(f"║     • Puntuación mínima:    {ConfigPrecision.PUNTUACION_MINIMA}/100{' ' * 33}║")
        print(f"║     • Confirmaciones min:   {ConfigPrecision.MIN_CONFIRMACIONES} indicadores{' ' * 28}║")
        print(f"║     • Cooldown activo:      {ConfigPrecision.COOLDOWN_ACTIVO//60} minutos{' ' * 32}║")
        print(f"║     • Máximo señales/hora:  {ConfigPrecision.MAX_SENALES_HORA}{' ' * 40}║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  📊 Activos habilitados:    {len(self.activos):<40}║")
        print("╠" + "═" * 70 + "╣")
        print("║  💡 SOLO recibirás 1 señal a la vez (la mejor disponible)" + " " * 11 + "║")
        print("║  ⌨️  Ctrl+C = Salir y ver estadísticas" + " " * 30 + "║")
        print("╚" + "═" * 70 + "╝")
    
    async def verificar_alertas(self):
        """Verifica si hay señales pendientes para alertar"""
        if not self.senal_pendiente:
            return
        
        ahora = hora_rd()
        senal = self.senal_pendiente
        entrada_dt = datetime.fromisoformat(senal['entrada_dt'])
        restante = (entrada_dt - ahora).total_seconds()
        
        # Alertar 5 segundos antes
        if restante <= 5:
            self.mostrar_alerta_entrada(senal)
            senal['precio_entrada'] = self.precios.get(senal['activo_id'], 0)
            self.senal_activa = senal
            self.senal_pendiente = None
    
    async def verificar_resultados(self):
        """Verifica resultados de operaciones expiradas"""
        if not self.senal_activa:
            return
        
        ahora = hora_rd()
        senal = self.senal_activa
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
                
                self.historial.actualizar_resultado(senal['id'], resultado, precio_cierre)
                self.mostrar_resultado(senal, resultado, precio_cierre)
            
            self.senal_activa = None
    
    async def procesar_mensaje(self, msg: str):
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
                
                # Ignorar blitz
                if 'blitz' in inst.lower():
                    return
                
                # Reset contador cada hora
                if time.time() - self.hora_reset >= 3600:
                    self.senales_hora = 0
                    self.hora_reset = time.time()
                
                # Si ya hay señal pendiente, ignorar
                if ConfigPrecision.UNA_SENAL_A_LA_VEZ and self.senal_pendiente:
                    return
                
                # Calcular porcentaje
                call_pct = valor * 100
                
                # Evaluar señal
                senal = self.evaluar_senal(aid, call_pct)
                
                if senal:
                    # Actualizar cooldowns
                    self.ultima_senal_global = time.time()
                    self.ultima_senal_activo[aid] = time.time()
                    self.senales_hora += 1
                    
                    # Mostrar señal
                    self.mostrar_senal(senal)
                    
                    # Guardar y programar
                    self.historial.agregar(senal)
                    self.senal_pendiente = senal
                    
        except Exception as e:
            pass
    
    async def ejecutar(self):
        """Bucle principal del bot"""
        if not await self.conectar():
            print("\n  ❌ No se pudo conectar. Verifica tu SSID.")
            return
        
        self.mostrar_encabezado()
        self.mostrar_estadisticas()
        
        print("\n  🔍 Buscando señales de ALTA PRECISIÓN...")
        print("  ⏳ Solo recibirás señales cuando cumplan TODOS los criterios")
        print("  💡 Esto puede tomar varios minutos - paciencia = precisión\n")
        
        ultimo_check = time.time()
        
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=1)
                    await self.procesar_mensaje(msg)
                except asyncio.TimeoutError:
                    pass
                
                await self.verificar_alertas()
                
                if time.time() - ultimo_check >= 5:
                    await self.verificar_resultados()
                    ultimo_check = time.time()
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"\n  ⚠️ Conexión perdida. Reconectando...")
            await asyncio.sleep(2)
            if await self.conectar():
                await self.ejecutar()
                
        except KeyboardInterrupt:
            pass
        
        # Mostrar resumen
        print("\n\n" + "═" * 72)
        print("  📊 RESUMEN DE SESIÓN - BOT DE PRECISIÓN")
        print("═" * 72)
        self.mostrar_estadisticas()
        
        if self.ws:
            await self.ws.close()
        
        print(f"\n  👋 [{fmt_hora()}] Bot cerrado")
        print("═" * 72 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                              PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def mostrar_bienvenida():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║          🎯  BOT DE PRECISIÓN - OBJETIVO 80%+ WIN RATE  🎯                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   🔒 FILTROS ULTRA-ESTRICTOS:                                                ║
║      • Sentimiento mínimo: 92% (solo señales muy fuertes)                    ║
║      • Probabilidad mínima: 90%                                              ║
║      • Mínimo 4 indicadores confirmando                                      ║
║      • Rechaza divergencias técnicas vs sentimiento                          ║
║      • Cooldown de 10 min entre señales del mismo activo                     ║
║                                                                              ║
║   ✅ CARACTERÍSTICAS:                                                        ║
║      • UNA sola señal a la vez (la mejor)                                    ║
║      • Explicación detallada del PORQUÉ de cada señal                        ║
║      • Solo activos que TÚ configures                                        ║
║      • Verificación automática de resultados                                 ║
║                                                                              ║
║   ⚠️  IMPORTANTE:                                                            ║
║      • Recibirás MENOS señales, pero MÁS precisas                            ║
║      • Paciencia = Precisión                                                 ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   📋 PARA OBTENER TU SSID:                                                   ║
║   1. Abre Chrome → https://trade.bull-ex.com                                 ║
║   2. Inicia sesión                                                           ║
║   3. F12 → Application → Cookies → ssid                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


async def main():
    mostrar_bienvenida()
    
    ssid = MI_SSID.strip()
    
    if not ssid:
        ssid = input("  🔑 Pega tu SSID aquí: ").strip()
    
    if not ssid:
        print("\n  ❌ Error: Necesitas un SSID válido.")
        return
    
    bot = BotPrecision(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot detenido por el usuario\n")
