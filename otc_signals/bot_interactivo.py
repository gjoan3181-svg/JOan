#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   🎯 BOT MEAN REVERSION - ANÁLISIS TÉCNICO PURO
══════════════════════════════════════════════════════════════════════════════════

   ✅ SIN SENTIMIENTO - Solo análisis técnico
   
   ESTRATEGIA:
   • RSI en extremos (≤30 o ≥70)
   • Precio alejado de EMA20
   • Bollinger Bands (rebote desde bandas)
   • Vela de freno/confirmación
   • Filtro de volatilidad

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
HISTORIAL_FILE = "historial_tecnico.json"
RD_TZ = timezone(timedelta(hours=-4))


# ═══════════════════════════════════════════════════════════════════════════════
#                    🎯 CONFIGURACIÓN MEAN REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # RSI
    RSI_PERIODO = 14
    RSI_SOBREVENTA = 30        # RSI ≤ 30 para CALL
    RSI_SOBRECOMPRA = 70       # RSI ≥ 70 para PUT
    
    # EMA
    EMA_PERIODO = 20
    
    # Bollinger
    BB_PERIODO = 20
    BB_STD = 2
    
    # Filtros
    MIN_VELAS = 25
    PUNTUACION_MINIMA = 60
    
    # Gestión
    MAX_TRADES_POR_PAR = 5
    COOLDOWN_ACTIVO = 60
    DURACION_OP = 1


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
#                    🔬 ANALIZADOR TÉCNICO PURO
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizadorTecnico:
    """Análisis técnico puro - Sin sentimiento"""
    
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
        if datos['close'] > 0:
            self.velas[aid].append(datos)
            if len(self.velas[aid]) > self.max_velas:
                self.velas[aid].pop(0)
    
    def tiene_datos(self, aid: int) -> bool:
        return len(self.velas.get(aid, [])) >= Config.MIN_VELAS
    
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
    
    def detectar_vela_rechazo(self, velas: List[dict], direccion: str) -> Tuple[bool, str]:
        """Detecta vela de rechazo (pin bar, hammer, shooting star)"""
        if len(velas) < 2:
            return False, ""
        
        v = velas[-1]
        cuerpo = abs(v['close'] - v['open'])
        rango = v['high'] - v['low']
        
        if rango == 0:
            return False, ""
        
        mecha_sup = v['high'] - max(v['open'], v['close'])
        mecha_inf = min(v['open'], v['close']) - v['low']
        
        if direccion == "CALL":
            # Hammer: mecha inferior larga, cuerpo pequeño arriba
            if mecha_inf >= rango * 0.6 and cuerpo <= rango * 0.3:
                return True, "Hammer (martillo)"
            # Vela verde después de rojas
            if v['close'] > v['open'] and velas[-2]['close'] < velas[-2]['open']:
                return True, "Vela alcista de reversión"
        
        elif direccion == "PUT":
            # Shooting star: mecha superior larga, cuerpo pequeño abajo
            if mecha_sup >= rango * 0.6 and cuerpo <= rango * 0.3:
                return True, "Shooting Star"
            # Vela roja después de verdes
            if v['close'] < v['open'] and velas[-2]['close'] > velas[-2]['open']:
                return True, "Vela bajista de reversión"
        
        return False, ""
    
    def analizar_activo(self, aid: int) -> Optional[dict]:
        """
        Analiza un activo y retorna oportunidad si existe.
        
        CALL cuando:
        - RSI ≤ 30 (sobreventa)
        - Precio debajo de EMA20
        - Precio cerca/toca banda inferior
        - Vela de rechazo alcista
        
        PUT cuando:
        - RSI ≥ 70 (sobrecompra)
        - Precio encima de EMA20
        - Precio cerca/toca banda superior
        - Vela de rechazo bajista
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
        
        # Posición en Bollinger (0-100, donde 0 es banda inferior)
        bb_pos = ((precio - bb_lower) / (bb_upper - bb_lower)) * 100 if bb_upper != bb_lower else 50
        
        # Distancia a EMA
        dist_ema = ((precio - ema) / ema) * 100
        
        puntos = 0
        razones = []
        direccion = None
        
        # ════════════════ ANÁLISIS CALL ════════════════
        if rsi <= Config.RSI_SOBREVENTA:
            direccion = "CALL"
            puntos += 30
            razones.append(f"✅ RSI en SOBREVENTA: {rsi:.1f}")
            
            if precio < ema:
                puntos += 15
                razones.append(f"✅ Precio {abs(dist_ema):.2f}% debajo de EMA20")
            
            if bb_pos <= 20:
                puntos += 20
                razones.append(f"✅ Precio en zona INFERIOR de Bollinger ({bb_pos:.0f}%)")
            elif bb_pos <= 35:
                puntos += 10
                razones.append(f"✅ Precio cerca de banda inferior ({bb_pos:.0f}%)")
            
            tiene_rechazo, tipo_rechazo = self.detectar_vela_rechazo(velas, "CALL")
            if tiene_rechazo:
                puntos += 20
                razones.append(f"✅ {tipo_rechazo} detectado")
            
            # Confirmar que no sigue cayendo
            if velas[-1]['close'] > velas[-1]['open']:
                puntos += 10
                razones.append(f"✅ Última vela alcista (confirmación)")
        
        # ════════════════ ANÁLISIS PUT ════════════════
        elif rsi >= Config.RSI_SOBRECOMPRA:
            direccion = "PUT"
            puntos += 30
            razones.append(f"✅ RSI en SOBRECOMPRA: {rsi:.1f}")
            
            if precio > ema:
                puntos += 15
                razones.append(f"✅ Precio {abs(dist_ema):.2f}% encima de EMA20")
            
            if bb_pos >= 80:
                puntos += 20
                razones.append(f"✅ Precio en zona SUPERIOR de Bollinger ({bb_pos:.0f}%)")
            elif bb_pos >= 65:
                puntos += 10
                razones.append(f"✅ Precio cerca de banda superior ({bb_pos:.0f}%)")
            
            tiene_rechazo, tipo_rechazo = self.detectar_vela_rechazo(velas, "PUT")
            if tiene_rechazo:
                puntos += 20
                razones.append(f"✅ {tipo_rechazo} detectado")
            
            # Confirmar que no sigue subiendo
            if velas[-1]['close'] < velas[-1]['open']:
                puntos += 10
                razones.append(f"✅ Última vela bajista (confirmación)")
        
        # ════════════════ ANÁLISIS ALTERNATIVO (RSI moderado) ════════════════
        # Si no hay RSI extremo, buscar otras condiciones fuertes
        if direccion is None:
            # CALL: RSI bajo + precio muy debajo de banda
            if rsi <= 40 and bb_pos <= 10:
                direccion = "CALL"
                puntos = 50
                razones.append(f"✅ RSI bajo: {rsi:.1f}")
                razones.append(f"✅ Precio en EXTREMO inferior Bollinger ({bb_pos:.0f}%)")
                
                tiene_rechazo, tipo_rechazo = self.detectar_vela_rechazo(velas, "CALL")
                if tiene_rechazo:
                    puntos += 25
                    razones.append(f"✅ {tipo_rechazo}")
            
            # PUT: RSI alto + precio muy encima de banda
            elif rsi >= 60 and bb_pos >= 90:
                direccion = "PUT"
                puntos = 50
                razones.append(f"✅ RSI alto: {rsi:.1f}")
                razones.append(f"✅ Precio en EXTREMO superior Bollinger ({bb_pos:.0f}%)")
                
                tiene_rechazo, tipo_rechazo = self.detectar_vela_rechazo(velas, "PUT")
                if tiene_rechazo:
                    puntos += 25
                    razones.append(f"✅ {tipo_rechazo}")
        
        if direccion is None or puntos < Config.PUNTUACION_MINIMA:
            return None
        
        return {
            'direccion': direccion,
            'puntuacion': min(puntos, 100),
            'rsi': rsi,
            'bb_pos': bb_pos,
            'dist_ema': dist_ema,
            'precio': precio,
            'razones': razones
        }
    
    def buscar_mejor_oportunidad(self, activos: dict) -> Optional[Tuple[int, dict]]:
        """Busca la mejor oportunidad entre todos los activos"""
        mejor_aid = None
        mejor_analisis = None
        mejor_puntos = 0
        
        for aid in activos.keys():
            analisis = self.analizar_activo(aid)
            if analisis and analisis['puntuacion'] > mejor_puntos:
                mejor_aid = aid
                mejor_analisis = analisis
                mejor_puntos = analisis['puntuacion']
        
        if mejor_aid:
            return mejor_aid, mejor_analisis
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#                              HISTORIAL
# ═══════════════════════════════════════════════════════════════════════════════

class Historial:
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
        try:
            with open(self.archivo, 'w') as f:
                json.dump({'senales': self.senales}, f, indent=2)
        except:
            pass
    
    def agregar(self, senal):
        self.senales.append(senal)
        self.guardar()
        return len(self.senales)
    
    def marcar(self, num, resultado):
        for s in self.senales:
            if s.get('numero') == num:
                s['resultado'] = resultado
                s['verificado'] = True
                self.guardar()
                return True
        return False
    
    def estadisticas(self):
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
        
        return {
            'total': total,
            'verificadas': len(verificadas),
            'ganadas': len(ganadas),
            'perdidas': len(perdidas),
            'pendientes': total - len(verificadas),
            'precision': precision,
            'racha': racha
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
        self.analizador = AnalizadorTecnico()
        self.activos = get_activos_habilitados()
        
        self.precios = {}
        self.senal_actual = None
        self.numero = len(self.historial.senales)
        self.ultima_senal_tiempo = {}
        
        print(f"\n  📊 Activos: {len(self.activos)}")
    
    async def conectar(self):
        print(f"\n  🔌 Conectando...")
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
        """Busca la mejor oportunidad en todos los activos"""
        resultado = self.analizador.buscar_mejor_oportunidad(self.activos)
        
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
            'rsi': analisis['rsi'],
            'bb_pos': analisis['bb_pos'],
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
        
        punt = s['puntuacion']
        if punt >= 80:
            nivel = "🔥 EXCELENTE"
        elif punt >= 70:
            nivel = "✅ MUY BUENA"
        else:
            nivel = "📊 BUENA"
        
        print("\n")
        print("╔" + "═" * 66 + "╗")
        print(f"║  🎯 SEÑAL #{s['numero']} - {nivel:<44}║")
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
        print("╠" + "═" * 66 + "╣")
        print("║  📋 ¿POR QUÉ ESTA SEÑAL?" + " " * 40 + "║")
        print("║  " + "─" * 62 + "  ║")
        
        for r in s['razones'][:6]:
            print(f"║  {r[:62]:<64}║")
        
        print("╠" + "═" * 66 + "╣")
        print(f"║  ⏱️  Expiración:     {Config.DURACION_OP} minuto(s){' ' * 38}║")
        print(f"║  🕐 Hora:           {s['hora']:<45}║")
        print("╚" + "═" * 66 + "╝")
        print("\n  💡 Escribe 'g' si GANASTE o 'p' si PERDISTE")
        
        # Telegram
        if TELEGRAM_ACTIVO:
            msg = f"🎯 SEÑAL #{s['numero']}\n{s['simbolo']}\n{s['direccion']}\nRSI: {s['rsi']:.1f}"
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
        print("╚" + "═" * 50 + "╝")
    
    def mostrar_pendientes(self):
        pend = self.historial.pendientes()
        if not pend:
            print("\n  ✅ No hay señales pendientes")
            return
        
        print("\n  ⏳ PENDIENTES:")
        for s in pend[-10:]:
            emoji = "🟢" if s['direccion'] == "CALL" else "🔴"
            print(f"  #{s['numero']} {s['simbolo'][:15]:<15} {emoji} {s['direccion']}")
        print("\n  💡 Usa 'g #' o 'p #' para marcar")
    
    def mostrar_historial(self):
        ult = self.historial.ultimas(10)
        if not ult:
            print("\n  📭 Sin historial")
            return
        
        print("\n  📋 ÚLTIMAS SEÑALES:")
        for s in ult:
            dir_e = "🟢" if s['direccion'] == "CALL" else "🔴"
            res = s.get('resultado', 'PEND')
            res_e = "✅" if res == "GANADA" else "❌" if res == "PERDIDA" else "⏳"
            print(f"  #{s['numero']} {s['simbolo'][:15]:<15} {dir_e} {res_e} {res}")
    
    def mostrar_menu(self):
        print("\n")
        print("┌" + "─" * 45 + "┐")
        print("│  📌 COMANDOS" + " " * 31 + "│")
        print("├" + "─" * 45 + "┤")
        print("│  [1] [s] → BUSCAR SEÑAL" + " " * 19 + "│")
        print("│  [2] [e] → Estadísticas" + " " * 19 + "│")
        print("│  [3]     → Pendientes" + " " * 21 + "│")
        print("│  [4] [h] → Historial" + " " * 22 + "│")
        print("├" + "─" * 45 + "┤")
        print("│  [g]     → Marcar GANADA" + " " * 18 + "│")
        print("│  [p]     → Marcar PERDIDA" + " " * 17 + "│")
        print("│  [g #]   → Marcar # GANADA" + " " * 16 + "│")
        print("│  [p #]   → Marcar # PERDIDA" + " " * 15 + "│")
        print("├" + "─" * 45 + "┤")
        print("│  [q]     → Salir" + " " * 26 + "│")
        print("└" + "─" * 45 + "┘")
        print(f"\n  🕐 {fmt_hora()} | Datos de {len([a for a in self.activos if self.analizador.tiene_datos(a)])} activos")
    
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
                # Mostrar estado de los activos
                print("\n  ⏳ No hay oportunidades claras ahora.")
                print("\n  📊 Estado de indicadores:")
                
                count = 0
                for aid, info in self.activos.items():
                    if self.analizador.tiene_datos(aid):
                        velas = self.analizador.velas[aid]
                        precios = [v['close'] for v in velas]
                        rsi = self.analizador.calcular_rsi(precios)
                        bb_u, bb_m, bb_l = self.analizador.calcular_bollinger(precios)
                        if bb_u:
                            bb_pos = ((precios[-1] - bb_l) / (bb_u - bb_l)) * 100
                            emoji = "🟢" if rsi <= 35 else "🔴" if rsi >= 65 else "⚪"
                            print(f"  {emoji} {info['simbolo'][:18]:<18} RSI:{rsi:5.1f}  BB:{bb_pos:5.1f}%")
                            count += 1
                            if count >= 10:
                                break
                
                print("\n  💡 Busco RSI ≤30 (CALL) o ≥70 (PUT)")
                print("  💡 Espera unos minutos e intenta de nuevo")
        
        elif cmd in ['2', 'e', 'stats']:
            self.mostrar_stats()
        
        elif cmd in ['3', 'pendientes']:
            self.mostrar_pendientes()
        
        elif cmd in ['4', 'h', 'historial']:
            self.mostrar_historial()
        
        elif cmd.startswith('g'):
            try:
                if cmd == 'g' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                if self.historial.marcar(num, 'GANADA'):
                    print(f"\n  ✅ #{num} GANADA!")
                else:
                    print(f"\n  ❌ No encontré #{num}")
            except:
                print("\n  ❌ Uso: g o g [número]")
        
        elif cmd.startswith('p') and (cmd == 'p' or ' ' in cmd):
            try:
                if cmd == 'p' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                if self.historial.marcar(num, 'PERDIDA'):
                    print(f"\n  ❌ #{num} PERDIDA")
                else:
                    print(f"\n  ❌ No encontré #{num}")
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
        print("╔" + "═" * 60 + "╗")
        print("║  🎯 BOT MEAN REVERSION - ANÁLISIS TÉCNICO" + " " * 16 + "║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  🕐 {fmt_hora()} | 📅 {fmt_fecha():<38}║")
        print("╠" + "═" * 60 + "╣")
        print("║  📊 Estrategia: Reversión a la Media" + " " * 21 + "║")
        print("║     • RSI ≤30 → CALL (sobreventa)" + " " * 24 + "║")
        print("║     • RSI ≥70 → PUT (sobrecompra)" + " " * 24 + "║")
        print("║     • Bollinger + Velas de rechazo" + " " * 23 + "║")
        print("╠" + "═" * 60 + "╣")
        print("║  💡 Escribe '1' para buscar señal, 'm' para menú" + " " * 9 + "║")
        print("╚" + "═" * 60 + "╝")
    
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
╔════════════════════════════════════════════════════════════════╗
║  🎯 BOT MEAN REVERSION - ANÁLISIS TÉCNICO PURO                ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ✅ Sin sentimiento - Solo indicadores técnicos               ║
║  ✅ RSI + Bollinger + Velas de rechazo                        ║
║  ✅ Busca reversiones a la media                              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
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
