#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════════
   🎯 BULLEX BOT INTERACTIVO - CON MENÚ Y CONTROL MANUAL
══════════════════════════════════════════════════════════════════════════════════

   ✅ CARACTERÍSTICAS:
   ─────────────────────────────────────────────────────────────────────────────
   1. MODO AUTOMÁTICO: Recibe señales automáticamente
   2. PEDIR SEÑAL: Solicita la mejor señal disponible en el momento
   3. MARCAR RESULTADO: Registra si ganaste o perdiste
   4. VER ESTADÍSTICAS: Win rate, racha, historial
   5. EXPLICACIÓN DETALLADA: Muestra el PORQUÉ de cada señal
   ─────────────────────────────────────────────────────────────────────────────

   Uso: python3 bot_interactivo.py

══════════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional, List, Dict
import os
import time
import sys
import threading

# ═══════════════════════════════════════════════════════════════════════════════
#                              CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# 👇 PEGA TU SSID AQUÍ:
MI_SSID = "e8b7b6185348833f922e675fe840fc3f"

# URLs
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_interactivo.json"

# Zona horaria República Dominicana (UTC-4)
RD_TZ = timezone(timedelta(hours=-4))


# ═══════════════════════════════════════════════════════════════════════════════
#                    🎯 PARÁMETROS DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    # ══════════ FILTROS DE SEÑAL ══════════
    UMBRAL_SENTIMIENTO = 85      # Solo señales con >85% sentimiento
    PROBABILIDAD_MINIMA = 80     # Probabilidad mínima 80%
    PUNTUACION_MINIMA = 75       # Puntuación técnica mínima 75/100
    
    # ══════════ CONFIRMACIONES REQUERIDAS ══════════
    MIN_CONFIRMACIONES = 3       # Mínimo 3 indicadores confirmando
    RECHAZAR_DIVERGENCIAS = True # Rechazar si técnico contradice sentimiento
    
    # ══════════ TIEMPOS ══════════
    DURACION_OPERACION = 2       # Operación de 2 minutos
    COOLDOWN_ACTIVO = 180        # 3 min entre señales del mismo activo
    
    # ══════════ ANÁLISIS TÉCNICO ══════════
    VELAS_ANALISIS = 20
    VELAS_MOMENTUM = 10


# ═══════════════════════════════════════════════════════════════════════════════
#               🎮 ACTIVOS PERMITIDOS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from config_activos import get_activos_habilitados, ACTIVOS
except ImportError:
    ACTIVOS = {
        1:   {"nombre": "EUR/USD",     "mercado": "FOREX",  "simbolo": "EUR/USD (OTC)",   "activo": True},
        212: {"nombre": "Bitcoin",     "mercado": "CRYPTO", "simbolo": "BTC/USD (OTC)",   "activo": True},
        220: {"nombre": "Ethereum",    "mercado": "CRYPTO", "simbolo": "ETH/USD (OTC)",   "activo": True},
        959: {"nombre": "Oro",         "mercado": "COMMODITIES", "simbolo": "XAU/USD (OTC)", "activo": True},
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
#                    🔬 ANALIZADOR TÉCNICO
# ═══════════════════════════════════════════════════════════════════════════════

class Analizador:
    def __init__(self):
        self.velas = defaultdict(list)
        self.max_velas = Config.VELAS_ANALISIS
    
    def agregar_vela(self, aid: int, vela: dict):
        datos = {
            'open': vela.get('open', 0),
            'high': vela.get('max', vela.get('high', 0)),
            'low': vela.get('min', vela.get('low', 0)),
            'close': vela.get('close', 0),
            'time': vela.get('time', time.time())
        }
        self.velas[aid].append(datos)
        if len(self.velas[aid]) > self.max_velas:
            self.velas[aid].pop(0)
    
    def calcular_tendencia(self, aid: int) -> tuple:
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 0, 0, "SIN DATOS"
        
        precios = [v['close'] for v in velas]
        ultimas = velas[-10:] if len(velas) >= 10 else velas
        
        # Calcular EMA
        ema5 = sum(precios[-5:]) / 5 if len(precios) >= 5 else precios[-1]
        ema10 = sum(precios[-10:]) / 10 if len(precios) >= 10 else precios[-1]
        
        # Cambio porcentual
        cambio = ((precios[-1] - precios[0]) / precios[0]) * 100 if precios[0] else 0
        
        # Velas alcistas
        alcistas = sum(1 for v in ultimas if v['close'] > v['open'])
        
        score = 0
        if ema5 > ema10: score += 30
        else: score -= 30
        
        if cambio > 0.05: score += 25
        elif cambio < -0.05: score -= 25
        
        if alcistas >= 6: score += 25
        elif alcistas <= 3: score -= 25
        
        if score >= 40:
            return 1, abs(score), "ALCISTA FUERTE ↑↑"
        elif score >= 15:
            return 1, abs(score), "ALCISTA ↑"
        elif score <= -40:
            return -1, abs(score), "BAJISTA FUERTE ↓↓"
        elif score <= -15:
            return -1, abs(score), "BAJISTA ↓"
        else:
            return 0, abs(score), "LATERAL →"
    
    def calcular_momentum(self, aid: int) -> float:
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 50
        
        precios = [v['close'] for v in velas]
        cambios = [(precios[i] - precios[i-1]) / precios[i-1] * 100 
                   for i in range(1, len(precios)) if precios[i-1] != 0]
        
        if not cambios:
            return 50
        
        momentum = 50 + sum(cambios[-5:]) * 10
        return max(0, min(100, momentum))


# ═══════════════════════════════════════════════════════════════════════════════
#                              GESTOR DE HISTORIAL
# ═══════════════════════════════════════════════════════════════════════════════

class Historial:
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
        return len(self.senales)
    
    def marcar_resultado(self, numero: int, resultado: str) -> bool:
        """Marca el resultado de una señal por su número"""
        for s in self.senales:
            if s.get('numero') == numero:
                s['resultado'] = resultado
                s['verificado'] = True
                s['fecha_verificacion'] = hora_rd().isoformat()
                self.guardar()
                return True
        return False
    
    def obtener_pendientes(self) -> List[dict]:
        """Retorna señales sin verificar"""
        return [s for s in self.senales if not s.get('verificado')]
    
    def estadisticas(self) -> dict:
        total = len(self.senales)
        verificadas = [s for s in self.senales if s.get('verificado')]
        ganadas = [s for s in verificadas if s.get('resultado') == 'GANADA']
        perdidas = [s for s in verificadas if s.get('resultado') == 'PERDIDA']
        
        precision = (len(ganadas) / len(verificadas) * 100) if verificadas else 0
        
        # Calcular racha actual
        racha = 0
        for s in reversed(verificadas):
            if s.get('resultado') == 'GANADA':
                racha += 1
            else:
                break
        
        # Estadísticas de hoy
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
            'hoy_verificadas': len(hoy_verificadas)
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
        self.analizador = Analizador()
        self.activos = get_activos_habilitados()
        
        # Estado
        self.precios = {}
        self.sentimientos = {}  # {aid: valor}
        self.ultima_senal = None
        self.senal_actual = None
        self.modo_auto = False
        self.ejecutando = True
        self.numero_senal = len(self.historial.senales)
        
        # Cola de señales candidatas
        self.candidatas = {}  # {aid: senal_data}
    
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
            print(f"  ✅ Conectado exitosamente\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            return False
    
    def evaluar_senal(self, aid: int, sentimiento_pct: float) -> Optional[dict]:
        """Evalúa si una señal es válida"""
        if aid not in self.activos:
            return None
        
        # Determinar dirección
        if sentimiento_pct > 50:
            direccion = "CALL"
            fuerza = sentimiento_pct
        else:
            direccion = "PUT"
            fuerza = 100 - sentimiento_pct
        
        # Filtro de sentimiento
        if fuerza < Config.UMBRAL_SENTIMIENTO:
            return None
        
        # Análisis técnico
        tendencia, tend_fuerza, tend_texto = self.analizador.calcular_tendencia(aid)
        momentum = self.analizador.calcular_momentum(aid)
        
        # Calcular puntuación
        puntuacion = 0
        confirmaciones = []
        rechazos = []
        
        # Sentimiento (35 pts)
        puntuacion += (fuerza / 100) * 35
        confirmaciones.append(f"✅ Sentimiento: {fuerza:.0f}%")
        
        # Tendencia (25 pts)
        dir_num = 1 if direccion == "CALL" else -1
        if tendencia == dir_num:
            puntuacion += (tend_fuerza / 100) * 25
            confirmaciones.append(f"✅ Tendencia: {tend_texto}")
        elif tendencia == -dir_num:
            puntuacion -= 10
            rechazos.append(f"❌ Tendencia opuesta: {tend_texto}")
        else:
            puntuacion += 10
            confirmaciones.append(f"➡️ Tendencia neutral")
        
        # Momentum (20 pts)
        if (direccion == "CALL" and momentum > 55) or (direccion == "PUT" and momentum < 45):
            puntuacion += 20
            confirmaciones.append(f"✅ Momentum favorable: {momentum:.0f}")
        elif (direccion == "CALL" and momentum < 40) or (direccion == "PUT" and momentum > 60):
            puntuacion -= 10
            rechazos.append(f"⚠️ Momentum opuesto: {momentum:.0f}")
        else:
            puntuacion += 10
            confirmaciones.append(f"➡️ Momentum neutral: {momentum:.0f}")
        
        # Bonus por fuerza extrema
        if fuerza >= 90:
            puntuacion += 10
            confirmaciones.append(f"🔥 Sentimiento EXTREMO")
        
        # Verificar mínimos
        if puntuacion < Config.PUNTUACION_MINIMA:
            return None
        
        if len(confirmaciones) < Config.MIN_CONFIRMACIONES:
            return None
        
        # Rechazar divergencias fuertes
        if Config.RECHAZAR_DIVERGENCIAS and tendencia == -dir_num and tend_fuerza > 50:
            return None
        
        activo = self.activos[aid]
        ahora = hora_rd()
        
        return {
            'activo_id': aid,
            'nombre': activo['nombre'],
            'simbolo': activo['simbolo'],
            'mercado': activo['mercado'],
            'direccion': direccion,
            'sentimiento': fuerza,
            'puntuacion': puntuacion,
            'tendencia': tend_texto,
            'momentum': momentum,
            'confirmaciones': confirmaciones,
            'rechazos': rechazos,
            'precio': self.precios.get(aid, 0),
            'timestamp': ahora.isoformat(),
            'hora': fmt_hora(ahora)
        }
    
    def obtener_mejor_senal(self) -> Optional[dict]:
        """Obtiene la mejor señal disponible de las candidatas"""
        if not self.candidatas:
            return None
        
        # Ordenar por puntuación
        mejor = max(self.candidatas.values(), key=lambda x: x['puntuacion'])
        return mejor
    
    def mostrar_senal(self, s: dict, numero: int = None):
        """Muestra una señal con formato completo"""
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
        
        prob = s['puntuacion']
        if prob >= 85:
            nivel = "🔥 EXCELENTE"
            estrellas = "★★★★★"
        elif prob >= 75:
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
        print(f"║  👥 Sentimiento:     {s['sentimiento']:.0f}% de traders{' ' * 30}║")
        print(f"║  📉 Tendencia:       {s['tendencia']:<43}║")
        print(f"║  ⚡ Momentum:        {s['momentum']:.0f}/100{' ' * 40}║")
        print("╠" + "═" * 66 + "╣")
        print("║  📋 ¿POR QUÉ ESTA SEÑAL?" + " " * 40 + "║")
        print("║  " + "─" * 62 + "  ║")
        
        for conf in s['confirmaciones'][:5]:
            texto = conf[:60]
            print(f"║  {texto:<64}║")
        
        if s['rechazos']:
            print("║" + " " * 66 + "║")
            for rech in s['rechazos'][:2]:
                texto = rech[:60]
                print(f"║  {texto:<64}║")
        
        print("╠" + "═" * 66 + "╣")
        print(f"║  🕐 Hora:            {s['hora']:<44}║")
        print(f"║  ⏱️  Duración:        {Config.DURACION_OPERACION} minutos{' ' * 39}║")
        print("╚" + "═" * 66 + "╝")
        
        return s
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas completas"""
        stats = self.historial.estadisticas()
        
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║  📊 ESTADÍSTICAS" + " " * 40 + "║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📅 HOY:{' ' * 49}║")
        print(f"║     Señales:        {stats['hoy_total']:<36}║")
        print(f"║     Verificadas:    {stats['hoy_verificadas']:<36}║")
        print(f"║     Ganadas:        {stats['hoy_ganadas']:<36}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📈 HISTÓRICO:{' ' * 43}║")
        print(f"║     Total señales:  {stats['total']:<36}║")
        print(f"║     Verificadas:    {stats['verificadas']:<36}║")
        print(f"║     ✅ Ganadas:     {stats['ganadas']:<36}║")
        print(f"║     ❌ Perdidas:    {stats['perdidas']:<36}║")
        print(f"║     ⏳ Pendientes:  {stats['pendientes']:<36}║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  🎯 PRECISIÓN:      {stats['precision']:.1f}%{' ' * 33}║")
        print(f"║  🔥 Racha actual:   {stats['racha']} ganadas consecutivas{' ' * 14}║")
        print("╚" + "═" * 58 + "╝")
    
    def mostrar_pendientes(self):
        """Muestra señales pendientes de verificar"""
        pendientes = self.historial.obtener_pendientes()
        
        if not pendientes:
            print("\n  ✅ No hay señales pendientes de verificar\n")
            return
        
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║  ⏳ SEÑALES PENDIENTES DE VERIFICAR" + " " * 21 + "║")
        print("╠" + "═" * 58 + "╣")
        
        for s in pendientes[-10:]:  # Últimas 10
            num = s.get('numero', '?')
            simbolo = s.get('simbolo', 'N/A')[:20]
            direccion = s.get('direccion', 'N/A')
            hora = s.get('hora', 'N/A')
            emoji = "🟢" if direccion == "CALL" else "🔴"
            
            print(f"║  #{num:<4} {simbolo:<22} {emoji} {direccion:<6} {hora:<8}║")
        
        print("╚" + "═" * 58 + "╝")
        print("\n  💡 Usa 'g #' para marcar GANADA o 'p #' para PERDIDA")
    
    def mostrar_ultimas(self):
        """Muestra últimas señales con resultados"""
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
        """Muestra el menú principal"""
        print("\n")
        print("┌" + "─" * 50 + "┐")
        print("│  📌 MENÚ DE COMANDOS" + " " * 28 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [1] o [s] → Pedir SEÑAL ahora" + " " * 17 + "│")
        print("│  [2] o [e] → Ver ESTADÍSTICAS" + " " * 17 + "│")
        print("│  [3] o [p] → Ver señales PENDIENTES" + " " * 12 + "│")
        print("│  [4] o [h] → Ver HISTORIAL (últimas 10)" + " " * 8 + "│")
        print("│  [5] o [a] → Modo AUTOMÁTICO on/off" + " " * 12 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [g #] → Marcar señal # como GANADA" + " " * 12 + "│")
        print("│  [p #] → Marcar señal # como PERDIDA" + " " * 11 + "│")
        print("├" + "─" * 50 + "┤")
        print("│  [q] → SALIR" + " " * 35 + "│")
        print("└" + "─" * 50 + "┘")
        
        modo = "🟢 ACTIVADO" if self.modo_auto else "⚪ DESACTIVADO"
        print(f"\n  🤖 Modo automático: {modo}")
        print(f"  🕐 Hora RD: {fmt_hora()}")
    
    def procesar_comando(self, cmd: str) -> bool:
        """Procesa un comando del usuario. Retorna False para salir."""
        cmd = cmd.strip().lower()
        
        if cmd in ['q', 'salir', 'exit']:
            return False
        
        elif cmd in ['1', 's', 'senal', 'señal']:
            # Pedir señal
            mejor = self.obtener_mejor_senal()
            if mejor:
                senal = self.mostrar_senal(mejor)
                self.historial.agregar(senal)
                self.senal_actual = senal
                self.candidatas.clear()  # Limpiar candidatas
                print("\n  💡 Usa 'g' para GANADA o 'p' para PERDIDA cuando termine")
            else:
                print("\n  ⏳ No hay señales disponibles ahora.")
                print("  💡 Espera unos segundos y vuelve a intentar...")
        
        elif cmd in ['2', 'e', 'stats', 'estadisticas']:
            self.mostrar_estadisticas()
        
        elif cmd in ['3', 'pendientes']:
            self.mostrar_pendientes()
        
        elif cmd in ['4', 'h', 'historial']:
            self.mostrar_ultimas()
        
        elif cmd in ['5', 'a', 'auto', 'automatico']:
            self.modo_auto = not self.modo_auto
            estado = "ACTIVADO ✅" if self.modo_auto else "DESACTIVADO ⚪"
            print(f"\n  🤖 Modo automático: {estado}")
        
        elif cmd.startswith('g ') or cmd.startswith('g'):
            # Marcar como ganada
            try:
                if cmd == 'g' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                
                if self.historial.marcar_resultado(num, 'GANADA'):
                    print(f"\n  ✅ Señal #{num} marcada como GANADA!")
                else:
                    print(f"\n  ❌ No se encontró la señal #{num}")
            except:
                print("\n  ❌ Uso: g [número] - Ejemplo: g 5")
        
        elif cmd.startswith('p ') or (cmd == 'p' and self.senal_actual):
            # Marcar como perdida
            try:
                if cmd == 'p' and self.senal_actual:
                    num = self.senal_actual['numero']
                else:
                    num = int(cmd.split()[1])
                
                if self.historial.marcar_resultado(num, 'PERDIDA'):
                    print(f"\n  ❌ Señal #{num} marcada como PERDIDA")
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
            print(f"\n  ❓ Comando no reconocido: '{cmd}'")
            print("  💡 Escribe 'm' para ver el menú")
        
        return True
    
    async def procesar_mensaje(self, msg: str):
        """Procesa mensajes del WebSocket"""
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
                
                call_pct = valor * 100
                self.sentimientos[aid] = call_pct
                
                # Evaluar señal
                senal = self.evaluar_senal(aid, call_pct)
                if senal:
                    self.candidatas[aid] = senal
                    
                    # Si modo auto está activado, mostrar
                    if self.modo_auto and senal['puntuacion'] >= 80:
                        senal_mostrada = self.mostrar_senal(senal)
                        self.historial.agregar(senal_mostrada)
                        self.senal_actual = senal_mostrada
                        del self.candidatas[aid]
                        
        except:
            pass
    
    def mostrar_encabezado(self):
        """Muestra el encabezado del bot"""
        print("\n")
        print("╔" + "═" * 62 + "╗")
        print("║" + " " * 62 + "║")
        print("║     🎯  BOT INTERACTIVO - BULLEX  🎯" + " " * 22 + "║")
        print("║" + " " * 62 + "║")
        print("╠" + "═" * 62 + "╣")
        print(f"║  🕐 Hora:           {fmt_hora()} (Rep. Dominicana){' ' * 14}║")
        print(f"║  📅 Fecha:          {fmt_fecha():<40}║")
        print(f"║  📊 Activos:        {len(self.activos)} habilitados{' ' * 26}║")
        print("╠" + "═" * 62 + "╣")
        print("║  💡 Escribe 'm' para ver el menú de comandos" + " " * 16 + "║")
        print("╚" + "═" * 62 + "╝")
    
    async def loop_entrada(self):
        """Loop para procesar entrada del usuario"""
        loop = asyncio.get_event_loop()
        
        while self.ejecutando:
            try:
                # Leer entrada de forma no bloqueante
                cmd = await loop.run_in_executor(None, lambda: input("\n  👉 Comando: "))
                
                if not self.procesar_comando(cmd):
                    self.ejecutando = False
                    break
                    
            except EOFError:
                break
            except Exception as e:
                pass
    
    async def loop_websocket(self):
        """Loop para procesar mensajes del WebSocket"""
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
            except Exception as e:
                pass
    
    async def ejecutar(self):
        """Ejecuta el bot"""
        if not await self.conectar():
            print("\n  ❌ No se pudo conectar. Verifica tu SSID.")
            return
        
        limpiar()
        self.mostrar_encabezado()
        self.mostrar_estadisticas()
        self.mostrar_menu()
        
        # Ejecutar ambos loops en paralelo
        try:
            await asyncio.gather(
                self.loop_websocket(),
                self.loop_entrada()
            )
        except:
            pass
        
        # Mostrar resumen final
        print("\n\n" + "═" * 64)
        print("  📊 RESUMEN FINAL")
        print("═" * 64)
        self.mostrar_estadisticas()
        self.mostrar_ultimas()
        
        if self.ws:
            await self.ws.close()
        
        print(f"\n  👋 ¡Hasta pronto! - {fmt_hora()}")
        print("═" * 64 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                              PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

def mostrar_bienvenida():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║          🎯  BOT INTERACTIVO - BULLEX  🎯                            ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   ✅ CARACTERÍSTICAS:                                                ║
║      • Pedir señales cuando quieras                                  ║
║      • Marcar ganadas/perdidas                                       ║
║      • Ver estadísticas en tiempo real                               ║
║      • Modo automático opcional                                      ║
║      • Explicación del PORQUÉ de cada señal                          ║
║                                                                      ║
║   📋 COMANDOS PRINCIPALES:                                           ║
║      [1] Pedir señal    [2] Estadísticas    [3] Pendientes           ║
║      [g #] Ganada       [p #] Perdida       [q] Salir                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")


async def main():
    mostrar_bienvenida()
    
    ssid = MI_SSID.strip()
    
    if not ssid:
        ssid = input("  🔑 Pega tu SSID aquí: ").strip()
    
    if not ssid:
        print("\n  ❌ Error: Necesitas un SSID válido.")
        return
    
    bot = BotInteractivo(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot detenido\n")
