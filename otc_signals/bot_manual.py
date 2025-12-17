#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════
   🎯 BULLEX BOT - MODO MANUAL + ANÁLISIS MEJORADO
══════════════════════════════════════════════════════════════════════

   COMANDOS:
   [S] = Solicitar señal ahora
   [A] = Activar modo automático
   [P] = Pausar señales
   [E] = Ver estadísticas
   [Q] = Salir

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
import threading

# ═══════════════════════════════════════════════════════════════════════════════
# 👇 PEGA TU SSID AQUÍ:
MI_SSID = ""
# ═══════════════════════════════════════════════════════════════════════════════

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
HISTORIAL_FILE = "historial_manual.json"
RD_TZ = timezone(timedelta(hours=-4))

# ═══════════════════════════════════════════════════════════════════════════════
#                    SOLO ACTIVOS QUE TIENES EN BULLEX
# ═══════════════════════════════════════════════════════════════════════════════

# Basado en tus screenshots - SOLO estos activos
ACTIVOS_PERMITIDOS = {
    # FOREX OTC (de tus screenshots)
    1:   {"s": "EUR/USD (OTC)",    "m": "FOREX"},
    3:   {"s": "GBP/USD (OTC)",    "m": "FOREX"},
    4:   {"s": "EUR/JPY (OTC)",    "m": "FOREX"},
    5:   {"s": "USD/JPY (OTC)",    "m": "FOREX"},
    6:   {"s": "AUD/USD (OTC)",    "m": "FOREX"},
    7:   {"s": "USD/CAD (OTC)",    "m": "FOREX"},
    31:  {"s": "AUD/JPY (OTC)",    "m": "FOREX"},
    32:  {"s": "EUR/AUD (OTC)",    "m": "FOREX"},
    33:  {"s": "EUR/CAD (OTC)",    "m": "FOREX"},
    34:  {"s": "GBP/JPY (OTC)",    "m": "FOREX"},
    36:  {"s": "GBP/AUD (OTC)",    "m": "FOREX"},
    37:  {"s": "CAD/JPY (OTC)",    "m": "FOREX"},
    38:  {"s": "NZD/USD (OTC)",    "m": "FOREX"},
    51:  {"s": "EUR/CHF (OTC)",    "m": "FOREX"},
    78:  {"s": "EUR/NZD (OTC)",    "m": "FOREX"},
    84:  {"s": "USD/CHF (OTC)",    "m": "FOREX"},
    85:  {"s": "AUD/CAD (OTC)",    "m": "FOREX"},
    86:  {"s": "AUD/CAD (OTC)",    "m": "FOREX"},
    
    # CRYPTO OTC (de tus screenshots)
    212:  {"s": "BTC/USD (OTC)",     "m": "CRYPTO"},
    220:  {"s": "ETH/USD (OTC)",     "m": "CRYPTO"},
    1876: {"s": "SOL/USD (OTC)",     "m": "CRYPTO"},
    2151: {"s": "TRUMP (OTC)",       "m": "CRYPTO"},
    2152: {"s": "MELANIA (OTC)",     "m": "CRYPTO"},
    2157: {"s": "ONDO (OTC)",        "m": "CRYPTO"},
    2048: {"s": "SUI (OTC)",         "m": "CRYPTO"},
    2049: {"s": "RENDER (OTC)",      "m": "CRYPTO"},
    
    # COMMODITIES (de tus screenshots)
    959:  {"s": "XAU/USD (OTC)",     "m": "ORO"},
    960:  {"s": "XAG/USD (OTC)",     "m": "PLATA"},
    
    # INDICES (de tus screenshots)
    947:  {"s": "US 100 (OTC)",      "m": "ÍNDICE"},
    948:  {"s": "US 500 (OTC)",      "m": "ÍNDICE"},
    949:  {"s": "US 30 (OTC)",       "m": "ÍNDICE"},
    950:  {"s": "UK 100 (OTC)",      "m": "ÍNDICE"},
    951:  {"s": "GER 30 (OTC)",      "m": "ÍNDICE"},
    953:  {"s": "JP 225 (OTC)",      "m": "ÍNDICE"},
    954:  {"s": "HK 33 (OTC)",       "m": "ÍNDICE"},
    955:  {"s": "AUS 200 (OTC)",     "m": "ÍNDICE"},
    
    # ACCIONES (de tus screenshots)
    1380: {"s": "INTC (OTC)",        "m": "ACCIÓN"},
    1383: {"s": "NVDA (OTC)",        "m": "ACCIÓN"},
}

# ═══════════════════════════════════════════════════════════════════════════════

def hora():
    return datetime.now(RD_TZ).strftime("%H:%M:%S")

def fecha():
    return datetime.now(RD_TZ).strftime("%d/%m/%Y")


class Analizador:
    """Análisis técnico mejorado"""
    
    def __init__(self):
        self.velas = defaultdict(list)
        self.sentimiento = {}
        self.historial_sent = defaultdict(list)  # Historial de sentimiento
    
    def agregar_vela(self, aid, vela):
        self.velas[aid].append({
            'o': vela.get('open', 0),
            'h': vela.get('max', vela.get('high', 0)),
            'l': vela.get('min', vela.get('low', 0)),
            'c': vela.get('close', 0),
            't': time.time()
        })
        if len(self.velas[aid]) > 30:
            self.velas[aid].pop(0)
    
    def agregar_sentimiento(self, aid, valor):
        """Guarda historial de sentimiento para ver estabilidad"""
        self.sentimiento[aid] = valor
        self.historial_sent[aid].append({'v': valor, 't': time.time()})
        if len(self.historial_sent[aid]) > 10:
            self.historial_sent[aid].pop(0)
    
    def sentimiento_estable(self, aid):
        """Verifica si el sentimiento ha sido estable (no cambia mucho)"""
        hist = self.historial_sent.get(aid, [])
        if len(hist) < 3:
            return False
        
        # Verificar que todos apuntan en la misma dirección
        direcciones = [1 if h['v'] > 0.5 else -1 for h in hist[-5:]]
        return len(set(direcciones)) == 1  # Todos iguales
    
    def tendencia(self, aid):
        """Calcula tendencia: 1=alcista, -1=bajista, 0=lateral"""
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return 0
        
        ultimas = velas[-10:]
        if ultimas[0]['c'] == 0:
            return 0
        
        cambio = (ultimas[-1]['c'] - ultimas[0]['c']) / ultimas[0]['c'] * 100
        alcistas = sum(1 for v in ultimas if v['c'] > v['o'])
        
        if cambio > 0.03 and alcistas >= 6:
            return 1
        elif cambio < -0.03 and alcistas <= 4:
            return -1
        return 0
    
    def volatilidad(self, aid):
        """Mide volatilidad - alta volatilidad = más riesgo"""
        velas = self.velas.get(aid, [])
        if len(velas) < 5:
            return "NORMAL"
        
        rangos = [(v['h'] - v['l']) / v['c'] * 100 if v['c'] else 0 for v in velas[-10:]]
        promedio = sum(rangos) / len(rangos) if rangos else 0
        
        if promedio > 0.5:
            return "ALTA"
        elif promedio < 0.1:
            return "BAJA"
        return "NORMAL"
    
    def analizar(self, aid):
        """Análisis completo del activo"""
        sent = self.sentimiento.get(aid, 0.5)
        tend = self.tendencia(aid)
        estable = self.sentimiento_estable(aid)
        volat = self.volatilidad(aid)
        
        # Dirección por sentimiento
        if sent > 0.5:
            dir = "CALL"
            pct = sent * 100
        else:
            dir = "PUT"
            pct = (1 - sent) * 100
        
        # Calcular confianza
        confianza = pct
        razones = []
        
        # Bonus si tendencia confirma
        if (dir == "CALL" and tend == 1) or (dir == "PUT" and tend == -1):
            confianza = min(99, confianza + 5)
            razones.append("✅ Tendencia confirma")
        elif (dir == "CALL" and tend == -1) or (dir == "PUT" and tend == 1):
            confianza = max(50, confianza - 15)
            razones.append("⚠️ Tendencia opuesta")
        
        # Bonus si sentimiento estable
        if estable:
            confianza = min(99, confianza + 3)
            razones.append("✅ Sentimiento estable")
        else:
            razones.append("⚠️ Sentimiento inestable")
        
        # Penalizar alta volatilidad
        if volat == "ALTA":
            confianza = max(50, confianza - 5)
            razones.append("⚠️ Alta volatilidad")
        
        return {
            'direccion': dir,
            'sentimiento': pct,
            'confianza': confianza,
            'tendencia': "ALCISTA" if tend == 1 else "BAJISTA" if tend == -1 else "LATERAL",
            'volatilidad': volat,
            'estable': estable,
            'razones': razones,
            'recomendado': confianza >= 85 and estable
        }


class BotManual:
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.analizador = Analizador()
        self.precios = {}
        self.modo_auto = False
        self.pausado = True  # Empieza pausado
        self.corriendo = True
        self.ultima_senal = {}
        self.senales = []
        self.ganadas = 0
        self.perdidas = 0
        self.comando = None
    
    async def conectar(self):
        print(f"\n  🔌 [{hora()}] Conectando...")
        try:
            self.ws = await websockets.connect(WS_URL, origin='https://trade.bull-ex.com')
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            print(f"  ✅ Conectado!\n")
            return True
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def mostrar_menu(self):
        print("\n" + "═" * 50)
        print("  🎮 COMANDOS DISPONIBLES:")
        print("═" * 50)
        print("  [S] = Solicitar MEJOR señal ahora")
        print("  [A] = Activar modo automático")
        print("  [P] = Pausar/Detener señales")
        print("  [E] = Ver estadísticas")
        print("  [L] = Listar activos disponibles")
        print("  [Q] = Salir")
        print("═" * 50)
        estado = "🟢 AUTO" if self.modo_auto else "🔴 MANUAL" if self.pausado else "🟡 ACTIVO"
        print(f"  Estado: {estado}")
        print("═" * 50 + "\n")
    
    def obtener_mejor_senal(self):
        """Obtiene la mejor señal disponible ahora"""
        mejores = []
        
        for aid, info in ACTIVOS_PERMITIDOS.items():
            if aid not in self.analizador.sentimiento:
                continue
            
            analisis = self.analizador.analizar(aid)
            
            # Solo señales recomendadas
            if analisis['confianza'] >= 85:
                mejores.append({
                    'aid': aid,
                    'simbolo': info['s'],
                    'mercado': info['m'],
                    'analisis': analisis
                })
        
        # Ordenar por confianza
        mejores.sort(key=lambda x: x['analisis']['confianza'], reverse=True)
        
        return mejores[:3]  # Top 3
    
    def mostrar_senal(self, senal):
        a = senal['analisis']
        ahora = datetime.now(RD_TZ)
        entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=4)
        expira = entrada + timedelta(minutes=2)
        
        if a['direccion'] == 'CALL':
            emoji = "🟢"
            texto = "COMPRAR (CALL) ↑"
        else:
            emoji = "🔴"
            texto = "VENDER (PUT) ↓"
        
        if a['confianza'] >= 95:
            nivel = "🔥 EXTREMA"
        elif a['confianza'] >= 90:
            nivel = "✅ MUY ALTA"
        elif a['confianza'] >= 85:
            nivel = "📊 ALTA"
        else:
            nivel = "⚠️ MEDIA"
        
        print("\n" + "╔" + "═" * 54 + "╗")
        print(f"║  🎯 SEÑAL - {nivel:<40}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║  📍 {senal['simbolo']:<48}║")
        print(f"║  📊 {senal['mercado']:<48}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║     {emoji}{emoji}{emoji}  {texto:<38}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║  📈 Confianza:    {a['confianza']:.0f}%{' ' * 32}║")
        print(f"║  👥 Sentimiento:  {a['sentimiento']:.0f}%{' ' * 32}║")
        print(f"║  📉 Tendencia:    {a['tendencia']:<34}║")
        print(f"║  📊 Volatilidad:  {a['volatilidad']:<34}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║  🎯 ENTRAR A LAS: {entrada.strftime('%H:%M:%S'):<34}║")
        print(f"║  ⏱️  EXPIRA A LAS: {expira.strftime('%H:%M:%S'):<34}║")
        print(f"║  ⌛ DURACIÓN:     2 minutos{' ' * 25}║")
        print("╠" + "═" * 54 + "╣")
        for r in a['razones'][:3]:
            print(f"║  {r:<52}║")
        print("╠" + "═" * 54 + "╣")
        print(f"║  🕐 Hora RD:      {hora():<34}║")
        print("╚" + "═" * 54 + "╝")
        
        # Guardar señal
        self.senales.append({
            'simbolo': senal['simbolo'],
            'direccion': a['direccion'],
            'confianza': a['confianza'],
            'hora': hora()
        })
    
    def mostrar_estadisticas(self):
        total = len(self.senales)
        print("\n" + "┌" + "─" * 40 + "┐")
        print(f"│  📊 ESTADÍSTICAS{' ' * 23}│")
        print("├" + "─" * 40 + "┤")
        print(f"│  Señales generadas: {total:<18}│")
        print(f"│  ✅ Ganadas:        {self.ganadas:<18}│")
        print(f"│  ❌ Perdidas:       {self.perdidas:<18}│")
        if self.ganadas + self.perdidas > 0:
            pct = self.ganadas / (self.ganadas + self.perdidas) * 100
            print(f"│  📈 Precisión:      {pct:.1f}%{' ' * 15}│")
        print("└" + "─" * 40 + "┘")
    
    def listar_activos(self):
        print("\n" + "┌" + "─" * 45 + "┐")
        print(f"│  📋 ACTIVOS DISPONIBLES ({len(ACTIVOS_PERMITIDOS)}){' ' * 14}│")
        print("├" + "─" * 45 + "┤")
        
        # Agrupar por mercado
        por_mercado = defaultdict(list)
        for aid, info in ACTIVOS_PERMITIDOS.items():
            por_mercado[info['m']].append(info['s'])
        
        for mercado, activos in por_mercado.items():
            print(f"│  {mercado}:{' ' * (40 - len(mercado))}│")
            for activo in activos[:5]:
                print(f"│    • {activo:<37}│")
            if len(activos) > 5:
                print(f"│    ... y {len(activos) - 5} más{' ' * 27}│")
        
        print("└" + "─" * 45 + "┘")
    
    def leer_input(self):
        """Lee input del usuario en un hilo separado"""
        while self.corriendo:
            try:
                cmd = input().strip().upper()
                self.comando = cmd
            except:
                pass
    
    async def procesar_comando(self):
        """Procesa comandos del usuario"""
        if not self.comando:
            return
        
        cmd = self.comando
        self.comando = None
        
        if cmd == 'S':
            print("\n  🔍 Buscando mejor señal...")
            mejores = self.obtener_mejor_senal()
            if mejores:
                print(f"\n  📊 Encontradas {len(mejores)} señales de calidad:")
                for s in mejores:
                    self.mostrar_senal(s)
            else:
                print("\n  ⚠️ No hay señales de alta calidad ahora.")
                print("  💡 Espera unos minutos e intenta de nuevo.")
        
        elif cmd == 'A':
            self.modo_auto = True
            self.pausado = False
            print("\n  🟢 Modo AUTOMÁTICO activado")
            print("  📢 Las señales aparecerán automáticamente")
        
        elif cmd == 'P':
            self.modo_auto = False
            self.pausado = True
            print("\n  🔴 Señales PAUSADAS")
            print("  💡 Presiona [S] para solicitar una señal")
        
        elif cmd == 'E':
            self.mostrar_estadisticas()
        
        elif cmd == 'L':
            self.listar_activos()
        
        elif cmd == 'Q':
            self.corriendo = False
            print("\n  👋 Cerrando bot...")
        
        elif cmd == 'G':
            self.ganadas += 1
            print("  ✅ Registrada como GANADA")
        
        elif cmd == 'X':
            self.perdidas += 1
            print("  ❌ Registrada como PERDIDA")
        
        else:
            print(f"\n  ❓ Comando '{cmd}' no reconocido")
            self.mostrar_menu()
    
    async def procesar_mensaje(self, msg):
        try:
            data = json.loads(msg)
            nombre = data.get('name', '')
            m = data.get('msg', {})
            
            if nombre == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close and aid in ACTIVOS_PERMITIDOS:
                    self.precios[aid] = close
                    self.analizador.agregar_vela(aid, m)
            
            elif nombre == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                valor = m.get('value', 0.5)
                
                if 'blitz' in inst.lower():
                    return
                
                if aid not in ACTIVOS_PERMITIDOS:
                    return
                
                self.analizador.agregar_sentimiento(aid, valor)
                
                # Modo automático
                if self.modo_auto and not self.pausado:
                    call_pct = valor * 100
                    if call_pct >= 92 or call_pct <= 8:
                        analisis = self.analizador.analizar(aid)
                        if analisis['recomendado']:
                            # Cooldown
                            ahora = time.time()
                            if aid in self.ultima_senal:
                                if ahora - self.ultima_senal[aid] < 300:
                                    return
                            self.ultima_senal[aid] = ahora
                            
                            info = ACTIVOS_PERMITIDOS[aid]
                            self.mostrar_senal({
                                'aid': aid,
                                'simbolo': info['s'],
                                'mercado': info['m'],
                                'analisis': analisis
                            })
                            
        except:
            pass
    
    async def ejecutar(self):
        if not await self.conectar():
            return
        
        # Iniciar hilo para leer input
        input_thread = threading.Thread(target=self.leer_input, daemon=True)
        input_thread.start()
        
        print("\n" + "═" * 55)
        print("  🎯 BULLEX BOT - MODO MANUAL")
        print("═" * 55)
        print(f"  🕐 Hora RD: {hora()}")
        print(f"  📅 Fecha:   {fecha()}")
        print("═" * 55)
        
        self.mostrar_menu()
        
        print("  ⏳ Recopilando datos del mercado...")
        print("  💡 Espera 30 segundos y presiona [S] para señal\n")
        
        try:
            while self.corriendo:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    await self.procesar_mensaje(msg)
                except asyncio.TimeoutError:
                    pass
                
                await self.procesar_comando()
                
        except websockets.exceptions.ConnectionClosed:
            print("\n  ⚠️ Conexión perdida. Reconectando...")
            if await self.conectar():
                await self.ejecutar()
        except:
            pass
        
        # Resumen final
        print("\n" + "═" * 55)
        print("  📊 RESUMEN DE SESIÓN")
        print("═" * 55)
        self.mostrar_estadisticas()
        
        if self.senales:
            print("\n  📋 SEÑALES GENERADAS:")
            for s in self.senales[-5:]:
                emoji = "🟢" if s['direccion'] == 'CALL' else "🔴"
                print(f"  {emoji} {s['simbolo']} | {s['direccion']} | {s['confianza']:.0f}% | {s['hora']}")
        
        if self.ws:
            await self.ws.close()
        print(f"\n  👋 [{hora()}] Bot cerrado\n")


def mostrar_bienvenida():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║            🎯 BULLEX BOT - MODO MANUAL MEJORADO                  ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   ✅ Solo activos de TU cuenta Bullex                             ║
║   ✅ Análisis mejorado (tendencia + estabilidad)                  ║
║   ✅ Modo manual - TÚ controlas cuándo ver señales               ║
║   ✅ Filtros estrictos para mejor precisión                       ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   📋 PARA OBTENER TU SSID:                                        ║
║   1. Chrome → trade.bull-ex.com → Login                           ║
║   2. F12 → Application → Cookies → ssid → Copiar                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


async def main():
    mostrar_bienvenida()
    
    ssid = MI_SSID.strip()
    if not ssid:
        ssid = input("  🔑 Pega tu SSID: ").strip()
    
    if not ssid:
        print("\n  ❌ Necesitas un SSID válido\n")
        return
    
    bot = BotManual(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot cerrado\n")
