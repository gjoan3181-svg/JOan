#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎯 BOT DE TRADING PROFESIONAL v5.0                                        ║
║                                                                              ║
║   ESTRUCTURA MODULAR:                                                        ║
║   ├── 1. Filtro de Mercado (volatilidad, sesión, tipo)                      ║
║   ├── 2. Detección de Zonas (soporte/resistencia)                           ║
║   ├── 3. Confirmación por Velas (mechas, patrones)                          ║
║   ├── 4. Confirmación por Indicadores (RSI, EMA, BB, ATR)                   ║
║   ├── 5. Gestión de Riesgo (SL/TP, límites)                                 ║
║   └── 6. Journal Automático (registro y evaluación)                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple
from enum import Enum
import os

# ══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════════════

MI_SSID = "115Pruebaf7510a7bbc0b1c583v"
OPENAI_API_KEY = "sk-proj-tgpdgSY2XRbEjxUZjEetAb4bcjqw2FTDpFrMZsEyefxQfRK5ALpFxvSnPruebibU4a0VYy85qTOs0AXIQeX-evaFj6pyG27_pj90MycypRN2Sv8tkL29-6C4A"
TELEGRAM_TOKEN = "8406117917:pruebs3ecN7Ww8r_xrtMRVlDk1z8E2VHdtU"
TELEGRAM_CHAT_ID = "54958p6471"
TELEGRAM_ACTIVO = True

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
JOURNAL_FILE = "trading_journal.json"
RD_TZ = timezone(timedelta(hours=-4))

VELAS_ANALISIS = 200


# ══════════════════════════════════════════════════════════════════════════════
#                         ENUMS Y DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

class TipoMercado(Enum):
    TENDENCIA_ALCISTA = "TENDENCIA_ALCISTA"
    TENDENCIA_BAJISTA = "TENDENCIA_BAJISTA"
    LATERAL = "LATERAL"
    INDEFINIDO = "INDEFINIDO"

class TipoSenal(Enum):
    LONG = "CALL"
    SHORT = "PUT"

class PatronVela(Enum):
    MARTILLO = "MARTILLO"
    MARTILLO_INVERTIDO = "MARTILLO_INVERTIDO"
    ENVOLVENTE_ALCISTA = "ENVOLVENTE_ALCISTA"
    ENVOLVENTE_BAJISTA = "ENVOLVENTE_BAJISTA"
    DOJI = "DOJI"
    SHOOTING_STAR = "SHOOTING_STAR"
    RECHAZO_ALCISTA = "RECHAZO_ALCISTA"
    RECHAZO_BAJISTA = "RECHAZO_BAJISTA"
    NINGUNO = "NINGUNO"

@dataclass
class Vela:
    open: float
    high: float
    low: float
    close: float
    time: int = 0
    
    @property
    def rango(self) -> float:
        return self.high - self.low if self.high > self.low else 0.0001
    
    @property
    def cuerpo(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def mecha_superior(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def mecha_inferior(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def es_alcista(self) -> bool:
        return self.close > self.open
    
    @property
    def ratio_mecha_inferior(self) -> float:
        return self.mecha_inferior / self.rango if self.rango > 0 else 0
    
    @property
    def ratio_mecha_superior(self) -> float:
        return self.mecha_superior / self.rango if self.rango > 0 else 0
    
    @property
    def ratio_cuerpo(self) -> float:
        return self.cuerpo / self.rango if self.rango > 0 else 0

@dataclass
class Zona:
    tipo: str  # "SOPORTE" o "RESISTENCIA"
    precio: float
    buffer: float
    fuerza: int  # Número de toques
    
    @property
    def limite_superior(self) -> float:
        return self.precio + self.buffer
    
    @property
    def limite_inferior(self) -> float:
        return self.precio - self.buffer

@dataclass
class Senal:
    numero: int
    activo: str
    categoria: str
    tipo: TipoSenal
    precio_entrada: float
    stop_loss: float
    take_profit: float
    
    # Análisis
    tipo_mercado: TipoMercado
    zona: Optional[Zona]
    patron: PatronVela
    
    # Indicadores
    rsi: float
    bb_pos: float
    atr: float
    ema_rapida: float
    ema_lenta: float
    
    # Confirmaciones
    confirmaciones: List[str]
    puntuacion: int
    ratio_riesgo: float  # R:R
    
    # Metadata
    hora: str
    fecha: str
    resultado: Optional[str] = None
    pnl_r: Optional[float] = None  # Resultado en R


# ══════════════════════════════════════════════════════════════════════════════
#                         CONFIGURACIÓN DE ESTRATEGIA
# ══════════════════════════════════════════════════════════════════════════════

class ConfigEstrategia:
    """Parámetros configurables de la estrategia"""
    
    # ═══════════════ FILTRO DE MERCADO ═══════════════
    ATR_PERIODO = 14
    ATR_MULTIPLICADOR_VOLATILIDAD = 2.5  # Vela > 2.5*ATR = muy volátil
    ADX_PERIODO = 14
    ADX_UMBRAL_TENDENCIA = 25  # ADX > 25 = tendencia, < 25 = lateral
    
    # ═══════════════ ZONAS S/R ═══════════════
    SWING_PERIODO = 20  # Velas para detectar swing high/low
    ZONA_BUFFER_ATR = 0.3  # Zona = precio ± 0.3*ATR
    MIN_TOQUES_ZONA = 2  # Mínimo toques para zona válida
    
    # ═══════════════ PATRONES DE VELAS ═══════════════
    MECHA_RECHAZO_MIN = 0.50  # Mecha > 50% del rango
    CUERPO_DOJI_MAX = 0.10  # Cuerpo < 10% del rango = doji
    CUERPO_ENVOLVENTE_MIN = 1.5  # Cuerpo actual > 1.5x cuerpo anterior
    
    # ═══════════════ INDICADORES ═══════════════
    RSI_PERIODO = 14
    RSI_SOBREVENTA = 30
    RSI_SOBRECOMPRA = 70
    
    EMA_RAPIDA = 9
    EMA_MEDIA = 21
    EMA_LENTA = 50
    EMA_TENDENCIA = 200
    
    BB_PERIODO = 20
    BB_DESVIACION = 2.0
    BB_EXTREMO_INFERIOR = 10  # < 10% = muy cerca de banda inferior
    BB_EXTREMO_SUPERIOR = 90  # > 90% = muy cerca de banda superior
    
    # ═══════════════ GESTIÓN DE RIESGO ═══════════════
    RIESGO_POR_TRADE = 1.0  # % del balance por trade
    SL_BUFFER_ATR = 0.5  # SL = zona ± 0.5*ATR
    TP_MINIMO_R = 1.5  # TP mínimo 1.5R
    TP_MAXIMO_R = 3.0  # TP máximo 3R
    
    MAX_TRADES_DIA = 10
    MAX_PERDIDAS_CONSECUTIVAS = 3
    COOLDOWN_MINUTOS = 30  # Pausa después de pérdidas consecutivas
    
    # ═══════════════ CONFIRMACIONES ═══════════════
    MIN_CONFIRMACIONES = 3  # Mínimo confirmaciones para operar
    
    # Puntos por confirmación
    PUNTOS_ZONA = 25
    PUNTOS_PATRON_FUERTE = 20  # Martillo, Envolvente
    PUNTOS_PATRON_DEBIL = 10   # Doji, Rechazo
    PUNTOS_RSI = 15
    PUNTOS_BB = 15
    PUNTOS_TENDENCIA = 20
    PUNTOS_MECHA = 15
    
    MIN_PUNTUACION = 60


# ══════════════════════════════════════════════════════════════════════════════
#                    ACTIVOS BULLEX OTC
# ══════════════════════════════════════════════════════════════════════════════

ACTIVOS = {
    # FOREX
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
    33: {"nombre": "EUR/CAD (OTC)", "categoria": "FOREX"},
    84: {"nombre": "USD/CHF (OTC)", "categoria": "FOREX"},
    
    # CRYPTO
    212: {"nombre": "BTC/USD (OTC)", "categoria": "CRYPTO"},
    220: {"nombre": "ETH/USD (OTC)", "categoria": "CRYPTO"},
    1876: {"nombre": "SOL/USD (OTC)", "categoria": "CRYPTO"},
    2004: {"nombre": "Ripple (OTC)", "categoria": "CRYPTO"},
    
    # COMMODITIES
    959: {"nombre": "XAUUSD (OTC)", "categoria": "COMMODITIES"},
    960: {"nombre": "XAGUSD (OTC)", "categoria": "COMMODITIES"},
    
    # INDICES
    949: {"nombre": "US 30 (OTC)", "categoria": "INDICES"},
    947: {"nombre": "US 100 (OTC)", "categoria": "INDICES"},
    
    # ACCIONES
    1384: {"nombre": "Apple (OTC)", "categoria": "ACCIONES"},
    1385: {"nombre": "Tesla (OTC)", "categoria": "ACCIONES"},
    1388: {"nombre": "Meta (OTC)", "categoria": "ACCIONES"},
}


# ══════════════════════════════════════════════════════════════════════════════
#                              UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def hora_rd():
    return datetime.now(RD_TZ).strftime("%H:%M:%S")

def fecha_rd():
    return datetime.now(RD_TZ).strftime("%d/%m/%Y")

def limpiar():
    os.system('cls' if os.name == 'nt' else 'clear')


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 1: FILTRO DE MERCADO
# ══════════════════════════════════════════════════════════════════════════════

class FiltroMercado:
    """
    Evalúa si las condiciones del mercado son aptas para operar.
    Filtra volatilidad extrema y detecta tipo de mercado.
    """
    
    @staticmethod
    def calcular_atr(velas: List[Vela], periodo: int = 14) -> float:
        """Average True Range - mide volatilidad"""
        if len(velas) < periodo + 1:
            return 0
        
        trs = []
        for i in range(1, len(velas)):
            v = velas[i]
            v_prev = velas[i-1]
            tr = max(
                v.high - v.low,
                abs(v.high - v_prev.close),
                abs(v.low - v_prev.close)
            )
            trs.append(tr)
        
        return sum(trs[-periodo:]) / periodo
    
    @staticmethod
    def calcular_adx(velas: List[Vela], periodo: int = 14) -> float:
        """Average Directional Index - mide fuerza de tendencia"""
        if len(velas) < periodo * 2:
            return 25  # Valor neutral por defecto
        
        plus_dm = []
        minus_dm = []
        tr_list = []
        
        for i in range(1, len(velas)):
            v = velas[i]
            v_prev = velas[i-1]
            
            # True Range
            tr = max(v.high - v.low, abs(v.high - v_prev.close), abs(v.low - v_prev.close))
            tr_list.append(tr)
            
            # Directional Movement
            up_move = v.high - v_prev.high
            down_move = v_prev.low - v.low
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)
        
        if len(tr_list) < periodo:
            return 25
        
        # Suavizado
        atr = sum(tr_list[-periodo:]) / periodo
        plus_di = (sum(plus_dm[-periodo:]) / periodo) / atr * 100 if atr > 0 else 0
        minus_di = (sum(minus_dm[-periodo:]) / periodo) / atr * 100 if atr > 0 else 0
        
        # ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        
        return dx
    
    @staticmethod
    def detectar_tipo_mercado(velas: List[Vela], ema_rapida: float, ema_lenta: float, adx: float) -> TipoMercado:
        """Determina si el mercado está en tendencia o lateral"""
        
        if adx < ConfigEstrategia.ADX_UMBRAL_TENDENCIA:
            return TipoMercado.LATERAL
        
        precio = velas[-1].close
        
        if ema_rapida > ema_lenta and precio > ema_rapida:
            return TipoMercado.TENDENCIA_ALCISTA
        elif ema_rapida < ema_lenta and precio < ema_rapida:
            return TipoMercado.TENDENCIA_BAJISTA
        
        return TipoMercado.INDEFINIDO
    
    @staticmethod
    def es_vela_anomala(vela: Vela, atr: float) -> bool:
        """Detecta velas con volatilidad extrema"""
        if atr <= 0:
            return False
        return vela.rango > (ConfigEstrategia.ATR_MULTIPLICADOR_VOLATILIDAD * atr)
    
    @staticmethod
    def evaluar(velas: List[Vela], atr: float, adx: float) -> Tuple[bool, str, TipoMercado]:
        """
        Evalúa si el mercado es apto para operar.
        Returns: (apto, razon, tipo_mercado)
        """
        if len(velas) < 20:
            return False, "Datos insuficientes", TipoMercado.INDEFINIDO
        
        vela_actual = velas[-1]
        
        # Verificar vela anómala
        if FiltroMercado.es_vela_anomala(vela_actual, atr):
            return False, f"Vela anómala (rango > {ConfigEstrategia.ATR_MULTIPLICADOR_VOLATILIDAD}x ATR)", TipoMercado.INDEFINIDO
        
        # Verificar últimas 3 velas por spikes
        for v in velas[-3:]:
            if FiltroMercado.es_vela_anomala(v, atr):
                return False, "Spike reciente detectado", TipoMercado.INDEFINIDO
        
        # Determinar tipo de mercado (necesitamos EMAs, se calculan afuera)
        return True, "OK", TipoMercado.INDEFINIDO  # Tipo se actualiza después


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 2: DETECCIÓN DE ZONAS S/R
# ══════════════════════════════════════════════════════════════════════════════

class DetectorZonas:
    """
    Detecta zonas de soporte y resistencia basadas en swing highs/lows.
    """
    
    @staticmethod
    def encontrar_swing_highs(velas: List[Vela], periodo: int = 20) -> List[float]:
        """Encuentra máximos locales (swing highs)"""
        swings = []
        for i in range(periodo, len(velas) - periodo):
            es_swing = True
            high = velas[i].high
            
            for j in range(i - periodo, i + periodo + 1):
                if j != i and velas[j].high >= high:
                    es_swing = False
                    break
            
            if es_swing:
                swings.append(high)
        
        return swings
    
    @staticmethod
    def encontrar_swing_lows(velas: List[Vela], periodo: int = 20) -> List[float]:
        """Encuentra mínimos locales (swing lows)"""
        swings = []
        for i in range(periodo, len(velas) - periodo):
            es_swing = True
            low = velas[i].low
            
            for j in range(i - periodo, i + periodo + 1):
                if j != i and velas[j].low <= low:
                    es_swing = False
                    break
            
            if es_swing:
                swings.append(low)
        
        return swings
    
    @staticmethod
    def agrupar_niveles(niveles: List[float], tolerancia: float) -> List[Tuple[float, int]]:
        """Agrupa niveles cercanos y cuenta toques"""
        if not niveles:
            return []
        
        grupos = []
        niveles_sorted = sorted(niveles)
        
        grupo_actual = [niveles_sorted[0]]
        
        for nivel in niveles_sorted[1:]:
            if nivel - grupo_actual[-1] <= tolerancia:
                grupo_actual.append(nivel)
            else:
                promedio = sum(grupo_actual) / len(grupo_actual)
                grupos.append((promedio, len(grupo_actual)))
                grupo_actual = [nivel]
        
        # Último grupo
        if grupo_actual:
            promedio = sum(grupo_actual) / len(grupo_actual)
            grupos.append((promedio, len(grupo_actual)))
        
        return grupos
    
    @staticmethod
    def detectar_zonas(velas: List[Vela], atr: float) -> List[Zona]:
        """Detecta zonas de soporte y resistencia"""
        buffer = ConfigEstrategia.ZONA_BUFFER_ATR * atr
        tolerancia = buffer * 2
        
        # Encontrar swings
        swing_highs = DetectorZonas.encontrar_swing_highs(velas, ConfigEstrategia.SWING_PERIODO)
        swing_lows = DetectorZonas.encontrar_swing_lows(velas, ConfigEstrategia.SWING_PERIODO)
        
        zonas = []
        
        # Agrupar resistencias
        resistencias = DetectorZonas.agrupar_niveles(swing_highs, tolerancia)
        for precio, toques in resistencias:
            if toques >= ConfigEstrategia.MIN_TOQUES_ZONA:
                zonas.append(Zona("RESISTENCIA", precio, buffer, toques))
        
        # Agrupar soportes
        soportes = DetectorZonas.agrupar_niveles(swing_lows, tolerancia)
        for precio, toques in soportes:
            if toques >= ConfigEstrategia.MIN_TOQUES_ZONA:
                zonas.append(Zona("SOPORTE", precio, buffer, toques))
        
        return zonas
    
    @staticmethod
    def precio_en_zona(precio: float, zonas: List[Zona]) -> Optional[Zona]:
        """Verifica si el precio está dentro de alguna zona"""
        for zona in zonas:
            if zona.limite_inferior <= precio <= zona.limite_superior:
                return zona
        return None
    
    @staticmethod
    def zona_mas_cercana(precio: float, zonas: List[Zona], tipo: str = None) -> Optional[Zona]:
        """Encuentra la zona más cercana al precio"""
        zonas_filtradas = [z for z in zonas if tipo is None or z.tipo == tipo]
        
        if not zonas_filtradas:
            return None
        
        return min(zonas_filtradas, key=lambda z: abs(z.precio - precio))


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 3: PATRONES DE VELAS
# ══════════════════════════════════════════════════════════════════════════════

class DetectorPatrones:
    """
    Detecta patrones de velas japonesas relevantes para trading.
    """
    
    @staticmethod
    def es_martillo(vela: Vela, velas_previas: List[Vela]) -> bool:
        """
        Martillo (bullish): cuerpo pequeño arriba, mecha inferior larga.
        Debe aparecer después de movimiento bajista.
        """
        # Mecha inferior >= 2x cuerpo
        if vela.cuerpo == 0:
            return False
        
        if vela.mecha_inferior < 2 * vela.cuerpo:
            return False
        
        # Mecha superior pequeña
        if vela.mecha_superior > vela.cuerpo * 0.5:
            return False
        
        # Verificar tendencia bajista previa
        if len(velas_previas) >= 3:
            precios_previos = [v.close for v in velas_previas[-3:]]
            if precios_previos[-1] > precios_previos[0]:  # Subiendo, no es martillo
                return False
        
        return True
    
    @staticmethod
    def es_shooting_star(vela: Vela, velas_previas: List[Vela]) -> bool:
        """
        Shooting Star (bearish): cuerpo pequeño abajo, mecha superior larga.
        Debe aparecer después de movimiento alcista.
        """
        if vela.cuerpo == 0:
            return False
        
        if vela.mecha_superior < 2 * vela.cuerpo:
            return False
        
        if vela.mecha_inferior > vela.cuerpo * 0.5:
            return False
        
        # Verificar tendencia alcista previa
        if len(velas_previas) >= 3:
            precios_previos = [v.close for v in velas_previas[-3:]]
            if precios_previos[-1] < precios_previos[0]:  # Bajando, no es shooting star
                return False
        
        return True
    
    @staticmethod
    def es_envolvente_alcista(vela_actual: Vela, vela_previa: Vela) -> bool:
        """Envolvente alcista: cuerpo verde envuelve cuerpo rojo previo"""
        if not vela_actual.es_alcista or vela_previa.es_alcista:
            return False
        
        # Cuerpo actual envuelve el anterior
        return (vela_actual.open <= vela_previa.close and 
                vela_actual.close >= vela_previa.open and
                vela_actual.cuerpo > vela_previa.cuerpo * ConfigEstrategia.CUERPO_ENVOLVENTE_MIN)
    
    @staticmethod
    def es_envolvente_bajista(vela_actual: Vela, vela_previa: Vela) -> bool:
        """Envolvente bajista: cuerpo rojo envuelve cuerpo verde previo"""
        if vela_actual.es_alcista or not vela_previa.es_alcista:
            return False
        
        return (vela_actual.open >= vela_previa.close and 
                vela_actual.close <= vela_previa.open and
                vela_actual.cuerpo > vela_previa.cuerpo * ConfigEstrategia.CUERPO_ENVOLVENTE_MIN)
    
    @staticmethod
    def es_doji(vela: Vela) -> bool:
        """Doji: cuerpo muy pequeño respecto al rango"""
        return vela.ratio_cuerpo < ConfigEstrategia.CUERPO_DOJI_MAX
    
    @staticmethod
    def tiene_rechazo_alcista(vela: Vela) -> bool:
        """Mecha inferior > 50% indica rechazo de precios bajos"""
        return vela.ratio_mecha_inferior >= ConfigEstrategia.MECHA_RECHAZO_MIN
    
    @staticmethod
    def tiene_rechazo_bajista(vela: Vela) -> bool:
        """Mecha superior > 50% indica rechazo de precios altos"""
        return vela.ratio_mecha_superior >= ConfigEstrategia.MECHA_RECHAZO_MIN
    
    @staticmethod
    def detectar_patron(velas: List[Vela]) -> PatronVela:
        """Detecta el patrón de vela más relevante"""
        if len(velas) < 2:
            return PatronVela.NINGUNO
        
        actual = velas[-1]
        previa = velas[-2]
        previas = velas[:-1]
        
        # Patrones fuertes (prioridad)
        if DetectorPatrones.es_martillo(actual, previas):
            return PatronVela.MARTILLO
        
        if DetectorPatrones.es_shooting_star(actual, previas):
            return PatronVela.SHOOTING_STAR
        
        if DetectorPatrones.es_envolvente_alcista(actual, previa):
            return PatronVela.ENVOLVENTE_ALCISTA
        
        if DetectorPatrones.es_envolvente_bajista(actual, previa):
            return PatronVela.ENVOLVENTE_BAJISTA
        
        # Patrones débiles
        if DetectorPatrones.es_doji(actual):
            return PatronVela.DOJI
        
        if DetectorPatrones.tiene_rechazo_alcista(actual):
            return PatronVela.RECHAZO_ALCISTA
        
        if DetectorPatrones.tiene_rechazo_bajista(actual):
            return PatronVela.RECHAZO_BAJISTA
        
        return PatronVela.NINGUNO


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 4: INDICADORES TÉCNICOS
# ══════════════════════════════════════════════════════════════════════════════

class Indicadores:
    """Cálculo de indicadores técnicos"""
    
    @staticmethod
    def calcular_ema(precios: List[float], periodo: int) -> float:
        if len(precios) < periodo:
            return sum(precios) / len(precios) if precios else 0
        
        mult = 2 / (periodo + 1)
        ema = sum(precios[:periodo]) / periodo
        
        for precio in precios[periodo:]:
            ema = (precio * mult) + (ema * (1 - mult))
        
        return ema
    
    @staticmethod
    def calcular_rsi(precios: List[float], periodo: int = 14) -> float:
        if len(precios) < periodo + 1:
            return 50
        
        cambios = [precios[i] - precios[i-1] for i in range(1, len(precios))]
        
        ganancias = []
        perdidas = []
        
        for c in cambios[:periodo]:
            ganancias.append(max(c, 0))
            perdidas.append(abs(min(c, 0)))
        
        avg_gain = sum(ganancias) / periodo
        avg_loss = sum(perdidas) / periodo
        
        # Suavizado Wilder
        for c in cambios[periodo:]:
            ganancia = max(c, 0)
            perdida = abs(min(c, 0))
            avg_gain = (avg_gain * (periodo - 1) + ganancia) / periodo
            avg_loss = (avg_loss * (periodo - 1) + perdida) / periodo
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calcular_bollinger(precios: List[float], periodo: int = 20, desviacion: float = 2.0) -> Tuple[float, float, float]:
        if len(precios) < periodo:
            return 0, 0, 0
        
        ultimos = precios[-periodo:]
        media = sum(ultimos) / periodo
        varianza = sum((p - media) ** 2 for p in ultimos) / periodo
        std = varianza ** 0.5
        
        banda_superior = media + std * desviacion
        banda_inferior = media - std * desviacion
        
        return banda_superior, media, banda_inferior
    
    @staticmethod
    def posicion_bollinger(precio: float, bb_sup: float, bb_inf: float) -> float:
        """Retorna posición del precio en las bandas (0-100)"""
        if bb_sup == bb_inf:
            return 50
        return ((precio - bb_inf) / (bb_sup - bb_inf)) * 100
    
    @staticmethod
    def rsi_cruzando_sobreventa(rsi_actual: float, rsi_previo: float) -> bool:
        """RSI cruzando arriba del nivel de sobreventa"""
        return rsi_previo < ConfigEstrategia.RSI_SOBREVENTA and rsi_actual >= ConfigEstrategia.RSI_SOBREVENTA
    
    @staticmethod
    def rsi_cruzando_sobrecompra(rsi_actual: float, rsi_previo: float) -> bool:
        """RSI cruzando abajo del nivel de sobrecompra"""
        return rsi_previo > ConfigEstrategia.RSI_SOBRECOMPRA and rsi_actual <= ConfigEstrategia.RSI_SOBRECOMPRA


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 5: GESTIÓN DE RIESGO
# ══════════════════════════════════════════════════════════════════════════════

class GestionRiesgo:
    """Cálculo de SL/TP y gestión de límites"""
    
    def __init__(self):
        self.trades_hoy = 0
        self.perdidas_consecutivas = 0
        self.ultimo_trade_time = None
        self.en_cooldown = False
        self.cooldown_hasta = None
    
    def calcular_sl(self, precio_entrada: float, zona: Optional[Zona], atr: float, tipo: TipoSenal) -> float:
        """Calcula Stop Loss basado en zona y ATR"""
        buffer = ConfigEstrategia.SL_BUFFER_ATR * atr
        
        if tipo == TipoSenal.LONG:
            if zona and zona.tipo == "SOPORTE":
                return zona.limite_inferior - buffer
            return precio_entrada - (1.5 * atr)
        else:  # SHORT
            if zona and zona.tipo == "RESISTENCIA":
                return zona.limite_superior + buffer
            return precio_entrada + (1.5 * atr)
    
    def calcular_tp(self, precio_entrada: float, sl: float, ratio_minimo: float = 1.5) -> float:
        """Calcula Take Profit con ratio R:R mínimo"""
        riesgo = abs(precio_entrada - sl)
        
        if precio_entrada > sl:  # LONG
            return precio_entrada + (riesgo * ratio_minimo)
        else:  # SHORT
            return precio_entrada - (riesgo * ratio_minimo)
    
    def puede_operar(self) -> Tuple[bool, str]:
        """Verifica si se puede abrir un nuevo trade"""
        
        # Límite diario
        if self.trades_hoy >= ConfigEstrategia.MAX_TRADES_DIA:
            return False, f"Límite diario alcanzado ({ConfigEstrategia.MAX_TRADES_DIA} trades)"
        
        # Cooldown por pérdidas
        if self.en_cooldown:
            if datetime.now(RD_TZ) < self.cooldown_hasta:
                restante = (self.cooldown_hasta - datetime.now(RD_TZ)).seconds // 60
                return False, f"En cooldown ({restante} min restantes)"
            else:
                self.en_cooldown = False
                self.perdidas_consecutivas = 0
        
        return True, "OK"
    
    def registrar_trade(self, ganado: bool):
        """Registra resultado de trade"""
        self.trades_hoy += 1
        
        if ganado:
            self.perdidas_consecutivas = 0
        else:
            self.perdidas_consecutivas += 1
            
            if self.perdidas_consecutivas >= ConfigEstrategia.MAX_PERDIDAS_CONSECUTIVAS:
                self.en_cooldown = True
                self.cooldown_hasta = datetime.now(RD_TZ) + timedelta(minutes=ConfigEstrategia.COOLDOWN_MINUTOS)
    
    def reset_diario(self):
        """Reset al inicio de cada día"""
        self.trades_hoy = 0
        self.perdidas_consecutivas = 0
        self.en_cooldown = False


# ══════════════════════════════════════════════════════════════════════════════
#                    MÓDULO 6: JOURNAL AUTOMÁTICO
# ══════════════════════════════════════════════════════════════════════════════

class Journal:
    """Registro y análisis de trades"""
    
    def __init__(self):
        self.datos = self.cargar()
    
    def cargar(self) -> Dict:
        try:
            if os.path.exists(JOURNAL_FILE):
                with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            'trades': [],
            'estadisticas': {
                'total': 0,
                'ganados': 0,
                'perdidos': 0,
                'total_r': 0.0,
                'mejor_racha': 0,
                'peor_racha': 0,
                'por_patron': {},
                'por_activo': {},
                'por_tipo_mercado': {},
                'por_hora': {}
            }
        }
    
    def guardar(self):
        try:
            with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"  ⚠️ Error guardando journal: {e}")
    
    def registrar_senal(self, senal: Senal):
        """Registra una nueva señal"""
        entrada = {
            'numero': senal.numero,
            'activo': senal.activo,
            'categoria': senal.categoria,
            'tipo': senal.tipo.value,
            'precio_entrada': senal.precio_entrada,
            'sl': senal.stop_loss,
            'tp': senal.take_profit,
            'tipo_mercado': senal.tipo_mercado.value,
            'zona': asdict(senal.zona) if senal.zona else None,
            'patron': senal.patron.value,
            'rsi': senal.rsi,
            'bb_pos': senal.bb_pos,
            'atr': senal.atr,
            'confirmaciones': senal.confirmaciones,
            'puntuacion': senal.puntuacion,
            'ratio_rr': senal.ratio_riesgo,
            'hora': senal.hora,
            'fecha': senal.fecha,
            'resultado': None,
            'pnl_r': None
        }
        
        self.datos['trades'].append(entrada)
        self.datos['estadisticas']['total'] += 1
        self.guardar()
    
    def registrar_resultado(self, numero: int, resultado: str, pnl_r: float = None):
        """Registra el resultado de un trade"""
        for trade in self.datos['trades']:
            if trade['numero'] == numero and trade['resultado'] is None:
                trade['resultado'] = resultado
                trade['pnl_r'] = pnl_r
                
                # Actualizar estadísticas
                stats = self.datos['estadisticas']
                
                if resultado == 'GANADA':
                    stats['ganados'] += 1
                else:
                    stats['perdidos'] += 1
                
                if pnl_r:
                    stats['total_r'] += pnl_r
                
                # Por patrón
                patron = trade['patron']
                if patron not in stats['por_patron']:
                    stats['por_patron'][patron] = {'g': 0, 'p': 0}
                stats['por_patron'][patron]['g' if resultado == 'GANADA' else 'p'] += 1
                
                # Por activo
                activo = trade['activo']
                if activo not in stats['por_activo']:
                    stats['por_activo'][activo] = {'g': 0, 'p': 0, 'r': 0}
                stats['por_activo'][activo]['g' if resultado == 'GANADA' else 'p'] += 1
                if pnl_r:
                    stats['por_activo'][activo]['r'] += pnl_r
                
                # Por tipo de mercado
                tipo_m = trade['tipo_mercado']
                if tipo_m not in stats['por_tipo_mercado']:
                    stats['por_tipo_mercado'][tipo_m] = {'g': 0, 'p': 0}
                stats['por_tipo_mercado'][tipo_m]['g' if resultado == 'GANADA' else 'p'] += 1
                
                self.guardar()
                return True
        
        return False
    
    def get_estadisticas(self) -> Dict:
        """Retorna estadísticas completas"""
        stats = self.datos['estadisticas']
        total = stats['ganados'] + stats['perdidos']
        
        return {
            'total_senales': stats['total'],
            'verificadas': total,
            'ganadas': stats['ganados'],
            'perdidas': stats['perdidos'],
            'precision': (stats['ganados'] / total * 100) if total > 0 else 0,
            'total_r': stats['total_r'],
            'promedio_r': stats['total_r'] / total if total > 0 else 0,
            'por_patron': stats['por_patron'],
            'por_activo': stats['por_activo'],
            'por_tipo_mercado': stats['por_tipo_mercado'],
            'pendientes': stats['total'] - total
        }
    
    def get_pendientes(self) -> List[Dict]:
        """Retorna trades sin resultado"""
        return [t for t in self.datos['trades'] if t['resultado'] is None]
    
    def get_historial(self, n: int = 15) -> List[Dict]:
        """Retorna últimos n trades"""
        return self.datos['trades'][-n:]


# ══════════════════════════════════════════════════════════════════════════════
#                    ANALIZADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class Analizador:
    """Coordina todos los módulos para generar señales"""
    
    def __init__(self, journal: Journal, gestion: GestionRiesgo):
        self.velas: Dict[int, List[Vela]] = {}
        self.journal = journal
        self.gestion = gestion
        self.numero_senal = len(journal.datos['trades'])
    
    def agregar_velas(self, aid: int, candles: List[Dict]) -> bool:
        if not candles:
            return False
        
        self.velas[aid] = [
            Vela(
                open=float(c.get('open', 0)),
                high=float(c.get('max', c.get('high', 0))),
                low=float(c.get('min', c.get('low', 0))),
                close=float(c.get('close', 0)),
                time=c.get('time', 0)
            )
            for c in candles
        ]
        return len(self.velas[aid]) >= 50
    
    def analizar_activo(self, aid: int, nombre: str, categoria: str) -> Optional[Senal]:
        """Análisis completo de un activo"""
        
        if aid not in self.velas or len(self.velas[aid]) < 50:
            return None
        
        velas = self.velas[aid]
        precios = [v.close for v in velas]
        precio_actual = precios[-1]
        
        # ═══════════════ INDICADORES ═══════════════
        atr = FiltroMercado.calcular_atr(velas, ConfigEstrategia.ATR_PERIODO)
        adx = FiltroMercado.calcular_adx(velas, ConfigEstrategia.ADX_PERIODO)
        
        rsi = Indicadores.calcular_rsi(precios, ConfigEstrategia.RSI_PERIODO)
        rsi_previo = Indicadores.calcular_rsi(precios[:-1], ConfigEstrategia.RSI_PERIODO)
        
        ema_rapida = Indicadores.calcular_ema(precios, ConfigEstrategia.EMA_RAPIDA)
        ema_media = Indicadores.calcular_ema(precios, ConfigEstrategia.EMA_MEDIA)
        ema_lenta = Indicadores.calcular_ema(precios, ConfigEstrategia.EMA_LENTA)
        
        bb_sup, bb_mid, bb_inf = Indicadores.calcular_bollinger(precios)
        bb_pos = Indicadores.posicion_bollinger(precio_actual, bb_sup, bb_inf)
        
        # ═══════════════ FILTRO DE MERCADO ═══════════════
        mercado_ok, razon_mercado, _ = FiltroMercado.evaluar(velas, atr, adx)
        if not mercado_ok:
            return None
        
        tipo_mercado = FiltroMercado.detectar_tipo_mercado(velas, ema_rapida, ema_lenta, adx)
        
        # ═══════════════ ZONAS S/R ═══════════════
        zonas = DetectorZonas.detectar_zonas(velas, atr)
        zona_actual = DetectorZonas.precio_en_zona(precio_actual, zonas)
        
        # ═══════════════ PATRONES ═══════════════
        patron = DetectorPatrones.detectar_patron(velas)
        vela_actual = velas[-1]
        
        # ═══════════════ EVALUAR SEÑALES ═══════════════
        confirmaciones = []
        puntos = 0
        tipo_senal = None
        
        # --- SEÑAL LONG (CALL) ---
        if self._evaluar_long(zona_actual, patron, vela_actual, rsi, rsi_previo, 
                              bb_pos, tipo_mercado, ema_rapida, ema_lenta, precio_actual):
            tipo_senal = TipoSenal.LONG
            confirmaciones, puntos = self._calcular_confirmaciones_long(
                zona_actual, patron, vela_actual, rsi, rsi_previo, bb_pos, 
                tipo_mercado, precio_actual, ema_lenta
            )
        
        # --- SEÑAL SHORT (PUT) ---
        elif self._evaluar_short(zona_actual, patron, vela_actual, rsi, rsi_previo,
                                  bb_pos, tipo_mercado, ema_rapida, ema_lenta, precio_actual):
            tipo_senal = TipoSenal.SHORT
            confirmaciones, puntos = self._calcular_confirmaciones_short(
                zona_actual, patron, vela_actual, rsi, rsi_previo, bb_pos,
                tipo_mercado, precio_actual, ema_lenta
            )
        
        if not tipo_senal:
            return None
        
        # Verificar mínimo de confirmaciones y puntuación
        if len(confirmaciones) < ConfigEstrategia.MIN_CONFIRMACIONES:
            return None
        
        if puntos < ConfigEstrategia.MIN_PUNTUACION:
            return None
        
        # ═══════════════ GESTIÓN DE RIESGO ═══════════════
        sl = self.gestion.calcular_sl(precio_actual, zona_actual, atr, tipo_senal)
        tp = self.gestion.calcular_tp(precio_actual, sl, ConfigEstrategia.TP_MINIMO_R)
        
        riesgo = abs(precio_actual - sl)
        beneficio = abs(tp - precio_actual)
        ratio_rr = beneficio / riesgo if riesgo > 0 else 0
        
        # ═══════════════ CREAR SEÑAL ═══════════════
        self.numero_senal += 1
        
        return Senal(
            numero=self.numero_senal,
            activo=nombre,
            categoria=categoria,
            tipo=tipo_senal,
            precio_entrada=precio_actual,
            stop_loss=sl,
            take_profit=tp,
            tipo_mercado=tipo_mercado,
            zona=zona_actual,
            patron=patron,
            rsi=rsi,
            bb_pos=bb_pos,
            atr=atr,
            ema_rapida=ema_rapida,
            ema_lenta=ema_lenta,
            confirmaciones=confirmaciones,
            puntuacion=puntos,
            ratio_riesgo=ratio_rr,
            hora=hora_rd(),
            fecha=fecha_rd()
        )
    
    def _evaluar_long(self, zona, patron, vela, rsi, rsi_previo, bb_pos, tipo_mercado, ema_r, ema_l, precio):
        """Evalúa si hay condiciones para LONG"""
        condiciones = 0
        
        # Zona de soporte
        if zona and zona.tipo == "SOPORTE":
            condiciones += 1
        
        # Patrón alcista
        if patron in [PatronVela.MARTILLO, PatronVela.ENVOLVENTE_ALCISTA, PatronVela.RECHAZO_ALCISTA]:
            condiciones += 1
        
        # Mecha de rechazo
        if vela.ratio_mecha_inferior >= ConfigEstrategia.MECHA_RECHAZO_MIN:
            condiciones += 1
        
        # RSI saliendo de sobreventa
        if rsi <= ConfigEstrategia.RSI_SOBREVENTA + 5:
            condiciones += 1
        
        # Bollinger cerca de banda inferior
        if bb_pos <= ConfigEstrategia.BB_EXTREMO_INFERIOR + 10:
            condiciones += 1
        
        return condiciones >= 2
    
    def _evaluar_short(self, zona, patron, vela, rsi, rsi_previo, bb_pos, tipo_mercado, ema_r, ema_l, precio):
        """Evalúa si hay condiciones para SHORT"""
        condiciones = 0
        
        # Zona de resistencia
        if zona and zona.tipo == "RESISTENCIA":
            condiciones += 1
        
        # Patrón bajista
        if patron in [PatronVela.SHOOTING_STAR, PatronVela.ENVOLVENTE_BAJISTA, PatronVela.RECHAZO_BAJISTA]:
            condiciones += 1
        
        # Mecha de rechazo
        if vela.ratio_mecha_superior >= ConfigEstrategia.MECHA_RECHAZO_MIN:
            condiciones += 1
        
        # RSI saliendo de sobrecompra
        if rsi >= ConfigEstrategia.RSI_SOBRECOMPRA - 5:
            condiciones += 1
        
        # Bollinger cerca de banda superior
        if bb_pos >= ConfigEstrategia.BB_EXTREMO_SUPERIOR - 10:
            condiciones += 1
        
        return condiciones >= 2
    
    def _calcular_confirmaciones_long(self, zona, patron, vela, rsi, rsi_previo, bb_pos, tipo_mercado, precio, ema_lenta):
        confirmaciones = []
        puntos = 0
        
        if zona and zona.tipo == "SOPORTE":
            confirmaciones.append(f"📍 En soporte (fuerza: {zona.fuerza})")
            puntos += ConfigEstrategia.PUNTOS_ZONA
        
        if patron == PatronVela.MARTILLO:
            confirmaciones.append("🔨 Martillo")
            puntos += ConfigEstrategia.PUNTOS_PATRON_FUERTE
        elif patron == PatronVela.ENVOLVENTE_ALCISTA:
            confirmaciones.append("🟢 Envolvente alcista")
            puntos += ConfigEstrategia.PUNTOS_PATRON_FUERTE
        elif patron == PatronVela.RECHAZO_ALCISTA:
            confirmaciones.append("↑ Rechazo alcista")
            puntos += ConfigEstrategia.PUNTOS_PATRON_DEBIL
        elif patron == PatronVela.DOJI:
            confirmaciones.append("⚖️ Doji (indecisión)")
            puntos += ConfigEstrategia.PUNTOS_PATRON_DEBIL
        
        if vela.ratio_mecha_inferior >= ConfigEstrategia.MECHA_RECHAZO_MIN:
            confirmaciones.append(f"📊 Mecha inferior: {vela.ratio_mecha_inferior*100:.0f}%")
            puntos += ConfigEstrategia.PUNTOS_MECHA
        
        if rsi <= ConfigEstrategia.RSI_SOBREVENTA:
            confirmaciones.append(f"📉 RSI sobreventa: {rsi:.1f}")
            puntos += ConfigEstrategia.PUNTOS_RSI
        elif Indicadores.rsi_cruzando_sobreventa(rsi, rsi_previo):
            confirmaciones.append(f"📈 RSI cruzando: {rsi:.1f}")
            puntos += ConfigEstrategia.PUNTOS_RSI
        
        if bb_pos <= ConfigEstrategia.BB_EXTREMO_INFERIOR:
            confirmaciones.append(f"📐 BB inferior: {bb_pos:.0f}%")
            puntos += ConfigEstrategia.PUNTOS_BB
        
        if tipo_mercado == TipoMercado.TENDENCIA_ALCISTA:
            confirmaciones.append("📈 A favor de tendencia")
            puntos += ConfigEstrategia.PUNTOS_TENDENCIA
        elif tipo_mercado == TipoMercado.LATERAL:
            confirmaciones.append("↔️ Mercado lateral")
            puntos += ConfigEstrategia.PUNTOS_TENDENCIA // 2
        
        return confirmaciones, puntos
    
    def _calcular_confirmaciones_short(self, zona, patron, vela, rsi, rsi_previo, bb_pos, tipo_mercado, precio, ema_lenta):
        confirmaciones = []
        puntos = 0
        
        if zona and zona.tipo == "RESISTENCIA":
            confirmaciones.append(f"📍 En resistencia (fuerza: {zona.fuerza})")
            puntos += ConfigEstrategia.PUNTOS_ZONA
        
        if patron == PatronVela.SHOOTING_STAR:
            confirmaciones.append("⭐ Shooting Star")
            puntos += ConfigEstrategia.PUNTOS_PATRON_FUERTE
        elif patron == PatronVela.ENVOLVENTE_BAJISTA:
            confirmaciones.append("🔴 Envolvente bajista")
            puntos += ConfigEstrategia.PUNTOS_PATRON_FUERTE
        elif patron == PatronVela.RECHAZO_BAJISTA:
            confirmaciones.append("↓ Rechazo bajista")
            puntos += ConfigEstrategia.PUNTOS_PATRON_DEBIL
        elif patron == PatronVela.DOJI:
            confirmaciones.append("⚖️ Doji (indecisión)")
            puntos += ConfigEstrategia.PUNTOS_PATRON_DEBIL
        
        if vela.ratio_mecha_superior >= ConfigEstrategia.MECHA_RECHAZO_MIN:
            confirmaciones.append(f"📊 Mecha superior: {vela.ratio_mecha_superior*100:.0f}%")
            puntos += ConfigEstrategia.PUNTOS_MECHA
        
        if rsi >= ConfigEstrategia.RSI_SOBRECOMPRA:
            confirmaciones.append(f"📈 RSI sobrecompra: {rsi:.1f}")
            puntos += ConfigEstrategia.PUNTOS_RSI
        elif Indicadores.rsi_cruzando_sobrecompra(rsi, rsi_previo):
            confirmaciones.append(f"📉 RSI cruzando: {rsi:.1f}")
            puntos += ConfigEstrategia.PUNTOS_RSI
        
        if bb_pos >= ConfigEstrategia.BB_EXTREMO_SUPERIOR:
            confirmaciones.append(f"📐 BB superior: {bb_pos:.0f}%")
            puntos += ConfigEstrategia.PUNTOS_BB
        
        if tipo_mercado == TipoMercado.TENDENCIA_BAJISTA:
            confirmaciones.append("📉 A favor de tendencia")
            puntos += ConfigEstrategia.PUNTOS_TENDENCIA
        elif tipo_mercado == TipoMercado.LATERAL:
            confirmaciones.append("↔️ Mercado lateral")
            puntos += ConfigEstrategia.PUNTOS_TENDENCIA // 2
        
        return confirmaciones, puntos
    
    def buscar_oportunidades(self) -> List[Senal]:
        """Busca señales en todos los activos"""
        senales = []
        
        for aid, info in ACTIVOS.items():
            senal = self.analizar_activo(aid, info['nombre'], info['categoria'])
            if senal:
                senales.append(senal)
        
        # Ordenar por puntuación
        return sorted(senales, key=lambda s: s.puntuacion, reverse=True)


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
    def enviar_senal(s: Senal):
        tipo_emoji = "🟢 CALL ↑" if s.tipo == TipoSenal.LONG else "🔴 PUT ↓"
        mercado_emoji = "📈" if s.tipo_mercado == TipoMercado.TENDENCIA_ALCISTA else "📉" if s.tipo_mercado == TipoMercado.TENDENCIA_BAJISTA else "↔️"
        
        confirmaciones_txt = "\n".join([f"  • {c}" for c in s.confirmaciones])
        
        msg = f"""<b>🎯 SEÑAL #{s.numero}</b>

<b>📍 {s.activo}</b>
<b>{tipo_emoji}</b>

<b>💰 Precio:</b> {s.precio_entrada:.5f}
<b>🛑 SL:</b> {s.stop_loss:.5f}
<b>🎯 TP:</b> {s.take_profit:.5f}
<b>📊 R:R:</b> 1:{s.ratio_riesgo:.1f}

<b>📈 Análisis:</b>
• Puntuación: {s.puntuacion}/100
• RSI: {s.rsi:.1f}
• BB: {s.bb_pos:.0f}%
• Patrón: {s.patron.value}
{mercado_emoji} Mercado: {s.tipo_mercado.value}

<b>✅ Confirmaciones ({len(s.confirmaciones)}):</b>
{confirmaciones_txt}

🕐 {s.hora} | 📅 {s.fecha}"""
        
        return Telegram.enviar(msg)


# ══════════════════════════════════════════════════════════════════════════════
#                              BOT PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class BotProfesional:
    def __init__(self):
        self.ws = None
        self.journal = Journal()
        self.gestion = GestionRiesgo()
        self.analizador = Analizador(self.journal, self.gestion)
        self.senal_actual = None
    
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
    
    async def obtener_datos(self):
        """Obtiene datos de activos uno por uno (corregido)"""
        print(f"\n  📊 Cargando {len(ACTIVOS)} activos...")
        
        cargados = 0
        for aid in ACTIVOS:
            try:
                msg = json.dumps({
                    "name": "sendMessage",
                    "msg": {
                        "name": "get-candles",
                        "version": "2.0",
                        "body": {"active_id": aid, "size": 60, "count": VELAS_ANALISIS}
                    }
                })
                await self.ws.send(msg)
                
                for _ in range(20):
                    try:
                        resp = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
                        data = json.loads(resp)
                        
                        if data.get('name') == 'candles':
                            candles = data.get('msg', {}).get('candles', [])
                            if candles and self.analizador.agregar_velas(aid, candles):
                                cargados += 1
                            break
                    except asyncio.TimeoutError:
                        continue
                    except:
                        continue
            except:
                continue
        
        print(f"  ✅ {cargados}/{len(ACTIVOS)} activos cargados")
        return cargados > 0
    
    def mostrar_senal(self, s: Senal):
        tipo = "🟢 CALL ↑" if s.tipo == TipoSenal.LONG else "🔴 PUT ↓"
        mercado = "📈" if s.tipo_mercado == TipoMercado.TENDENCIA_ALCISTA else "📉" if s.tipo_mercado == TipoMercado.TENDENCIA_BAJISTA else "↔️"
        
        print("\n")
        print("  ╔" + "═" * 60 + "╗")
        print(f"  ║  🎯 SEÑAL #{s.numero}" + " " * 45 + "║")
        print("  ╠" + "═" * 60 + "╣")
        print(f"  ║  📍 {s.activo:<54}║")
        print(f"  ║     {tipo:<54}║")
        print("  ╠" + "═" * 60 + "╣")
        print(f"  ║  💰 Entrada:  {s.precio_entrada:<44}║")
        print(f"  ║  🛑 SL:       {s.stop_loss:<44}║")
        print(f"  ║  🎯 TP:       {s.take_profit:<44}║")
        print(f"  ║  📊 R:R:      1:{s.ratio_riesgo:.1f}" + " " * 42 + "║")
        print("  ╠" + "═" * 60 + "╣")
        print(f"  ║  📈 Puntuación: {s.puntuacion}/100" + " " * 37 + "║")
        print(f"  ║  📉 RSI: {s.rsi:.1f}  📐 BB: {s.bb_pos:.0f}%" + " " * 32 + "║")
        print(f"  ║  🕯️  Patrón: {s.patron.value:<45}║")
        print(f"  ║  {mercado} Mercado: {s.tipo_mercado.value:<44}║")
        print("  ╠" + "═" * 60 + "╣")
        print(f"  ║  ✅ CONFIRMACIONES ({len(s.confirmaciones)}):" + " " * 33 + "║")
        for c in s.confirmaciones[:6]:
            print(f"  ║     {c[:54]:<55}║")
        print("  ╚" + "═" * 60 + "╝")
        print("\n  💡 'g' = GANADA | 'p' = PERDIDA | 'g +1.5' = con R")
        
        self.senal_actual = s
        self.journal.registrar_senal(s)
        Telegram.enviar_senal(s)
    
    def mostrar_estadisticas(self):
        stats = self.journal.get_estadisticas()
        precision = stats['precision']
        estado = "🔥" if precision >= 65 else "✅" if precision >= 55 else "⚠️"
        
        print("\n  ╔" + "═" * 55 + "╗")
        print("  ║  📊 ESTADÍSTICAS COMPLETAS" + " " * 28 + "║")
        print("  ╠" + "═" * 55 + "╣")
        print(f"  ║  Total señales: {stats['total_senales']:<37}║")
        print(f"  ║  Verificadas: {stats['verificadas']:<39}║")
        print(f"  ║  ✅ Ganadas: {stats['ganadas']:<40}║")
        print(f"  ║  ❌ Perdidas: {stats['perdidas']:<39}║")
        print("  ╠" + "═" * 55 + "╣")
        print(f"  ║  🎯 Precisión: {precision:.1f}% {estado:<35}║")
        print(f"  ║  💰 Total R: {stats['total_r']:+.2f}R" + " " * 35 + "║")
        print(f"  ║  📊 Promedio: {stats['promedio_r']:+.2f}R por trade" + " " * 25 + "║")
        print("  ╠" + "═" * 55 + "╣")
        
        # Por patrón
        print("  ║  📋 POR PATRÓN:" + " " * 39 + "║")
        for patron, data in list(stats['por_patron'].items())[:4]:
            total = data['g'] + data['p']
            prec = data['g'] / total * 100 if total > 0 else 0
            print(f"  ║     {patron[:20]:<22} {prec:.0f}% ({total})" + " " * 15 + "║")
        
        print("  ╚" + "═" * 55 + "╝")
    
    def mostrar_menu(self):
        print("\n  ┌" + "─" * 50 + "┐")
        print("  │  🎯 BOT PROFESIONAL v5.0" + " " * 24 + "│")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [1] 🎯 Buscar señal                            │")
        print("  │  [2] 📊 Estadísticas completas                  │")
        print("  │  [3] ⏳ Pendientes                              │")
        print("  │  [4] 📋 Historial                               │")
        print("  │  [5] 📱 Enviar stats a Telegram                 │")
        print("  ├" + "─" * 50 + "┤")
        print("  │  [g] GANADA  [p] PERDIDA  [g +1.5] con R        │")
        print("  │  [m] Menú   [c] Limpiar   [q] Salir             │")
        print("  └" + "─" * 50 + "┘")
    
    async def ejecutar(self):
        limpiar()
        print("\n  🎯 BOT PROFESIONAL v5.0 - ESTRUCTURA MODULAR")
        print(f"  🕐 {hora_rd()} | 📅 {fecha_rd()}")
        
        if not await self.conectar():
            return
        
        await self.obtener_datos()
        self.mostrar_menu()
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 ").strip().lower())
                
                if cmd == '1':
                    # Verificar si puede operar
                    puede, razon = self.gestion.puede_operar()
                    if not puede:
                        print(f"\n  ⚠️ {razon}")
                        continue
                    
                    await self.obtener_datos()
                    senales = self.analizador.buscar_oportunidades()
                    
                    if senales:
                        mejor = senales[0]
                        print(f"\n  📍 Mejor: {mejor.activo} ({mejor.puntuacion}pts, {len(mejor.confirmaciones)} conf.)")
                        self.mostrar_senal(mejor)
                    else:
                        print("\n  💡 No hay señales con suficientes confirmaciones")
                
                elif cmd == '2':
                    self.mostrar_estadisticas()
                
                elif cmd == '3':
                    pend = self.journal.get_pendientes()
                    print("\n  ⏳ PENDIENTES:")
                    if pend:
                        for p in pend[-10:]:
                            tipo = "🟢" if p['tipo'] == 'CALL' else "🔴"
                            print(f"  #{p['numero']} {p['activo'][:20]} {tipo}")
                    else:
                        print("  ✅ No hay pendientes")
                
                elif cmd == '4':
                    hist = self.journal.get_historial()
                    print("\n  📋 HISTORIAL:")
                    for t in hist:
                        tipo = "🟢" if t['tipo'] == 'CALL' else "🔴"
                        res = "✅" if t['resultado'] == 'GANADA' else "❌" if t['resultado'] == 'PERDIDA' else "⏳"
                        r_txt = f" ({t['pnl_r']:+.1f}R)" if t.get('pnl_r') else ""
                        print(f"  #{t['numero']} {t['activo'][:18]:<20} {tipo} {res}{r_txt}")
                
                elif cmd == '5':
                    stats = self.journal.get_estadisticas()
                    msg = f"📊 Precisión: {stats['precision']:.1f}%\n✅ {stats['ganadas']} | ❌ {stats['perdidas']}\n💰 Total: {stats['total_r']:+.2f}R"
                    Telegram.enviar(msg)
                    print("  ✅ Stats enviadas")
                
                elif cmd.startswith('g'):
                    try:
                        parts = cmd.split()
                        
                        if len(parts) == 1 and self.senal_actual:
                            num = self.senal_actual.numero
                            pnl = ConfigEstrategia.TP_MINIMO_R
                        elif len(parts) >= 2:
                            if parts[1].replace('+', '').replace('-', '').replace('.', '').isdigit():
                                num = self.senal_actual.numero if self.senal_actual else 0
                                pnl = float(parts[1])
                            else:
                                num = int(parts[1])
                                pnl = float(parts[2]) if len(parts) > 2 else ConfigEstrategia.TP_MINIMO_R
                        else:
                            raise ValueError()
                        
                        if self.journal.registrar_resultado(num, 'GANADA', pnl):
                            self.gestion.registrar_trade(True)
                            print(f"\n  ✅ #{num} GANADA (+{pnl}R)")
                            Telegram.enviar(f"✅ #{num} GANADA (+{pnl}R)")
                        else:
                            print("  ❌ No encontrada")
                    except:
                        print("  Uso: 'g', 'g +1.5', 'g 5 +2.0'")
                
                elif cmd.startswith('p'):
                    try:
                        parts = cmd.split()
                        
                        if len(parts) == 1 and self.senal_actual:
                            num = self.senal_actual.numero
                            pnl = -1.0
                        elif len(parts) >= 2:
                            if parts[1].replace('+', '').replace('-', '').replace('.', '').isdigit():
                                num = self.senal_actual.numero if self.senal_actual else 0
                                pnl = float(parts[1])
                            else:
                                num = int(parts[1])
                                pnl = float(parts[2]) if len(parts) > 2 else -1.0
                        else:
                            raise ValueError()
                        
                        if self.journal.registrar_resultado(num, 'PERDIDA', pnl):
                            self.gestion.registrar_trade(False)
                            print(f"\n  ❌ #{num} PERDIDA ({pnl}R)")
                            Telegram.enviar(f"❌ #{num} PERDIDA ({pnl}R)")
                        else:
                            print("  ❌ No encontrada")
                    except:
                        print("  Uso: 'p', 'p -1', 'p 5 -0.5'")
                
                elif cmd == 'm':
                    self.mostrar_menu()
                
                elif cmd == 'c':
                    limpiar()
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
╔═══════════════════════════════════════════════════════════════════════╗
║  🎯 BOT DE TRADING PROFESIONAL v5.0                                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ESTRUCTURA MODULAR:                                                  ║
║  ├── 1. Filtro de Mercado (ATR, ADX, velas anómalas)                 ║
║  ├── 2. Detección de Zonas S/R (swing highs/lows)                    ║
║  ├── 3. Patrones de Velas (Martillo, Envolvente, Doji...)            ║
║  ├── 4. Indicadores (RSI, EMA, Bollinger)                            ║
║  ├── 5. Gestión de Riesgo (SL/TP dinámico, límites)                  ║
║  └── 6. Journal Automático (estadísticas por patrón/activo)          ║
║                                                                       ║
║  REGLAS:                                                              ║
║  • Mínimo 3 confirmaciones para operar                               ║
║  • Mínimo 60 puntos de puntuación                                    ║
║  • SL/TP basado en ATR y zonas                                       ║
║  • Cooldown después de 3 pérdidas consecutivas                       ║
║  • Máximo 10 trades por día                                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")
    asyncio.run(BotProfesional().ejecutar())
