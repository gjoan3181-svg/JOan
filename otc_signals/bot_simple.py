#!/usr/bin/env python3
"""
🎯 BOT SIMPLE - SEÑALES OTC BULLEX
==================================
python3 bot_simple.py
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta, timezone
import time
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

MI_SSID = ""  # Pega tu SSID aquí o ingresalo al ejecutar

WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"
RD_TZ = timezone(timedelta(hours=-4))  # República Dominicana

# Filtros
UMBRAL_MINIMO = 90       # Solo señales >90%
COOLDOWN = 300           # 5 min entre señales del mismo activo
ANTICIPACION = 3         # Minutos antes de entrada
DURACION = 2             # Duración operación

# ═══════════════════════════════════════════════════════════════
# ACTIVOS OTC PERMITIDOS
# ═══════════════════════════════════════════════════════════════

ACTIVOS = {
    # FOREX OTC
    1: "EUR/USD (OTC)", 2: "EUR/GBP (OTC)", 3: "GBP/USD (OTC)",
    4: "EUR/JPY (OTC)", 5: "USD/JPY (OTC)", 6: "AUD/USD (OTC)",
    7: "USD/CAD (OTC)", 31: "AUD/JPY (OTC)", 32: "EUR/AUD (OTC)",
    33: "EUR/CAD (OTC)", 34: "GBP/JPY (OTC)", 35: "GBP/CAD (OTC)",
    36: "GBP/AUD (OTC)", 37: "CAD/JPY (OTC)", 38: "NZD/USD (OTC)",
    51: "EUR/CHF (OTC)", 78: "EUR/NZD (OTC)", 84: "USD/CHF (OTC)",
    85: "AUD/CAD (OTC)", 86: "AUD/CAD (OTC)",
    
    # CRYPTO OTC
    212: "Bitcoin (OTC)", 220: "Ethereum (OTC)", 1470: "Ripple (OTC)",
    1876: "Solana (OTC)", 2151: "TRUMP (OTC)", 2152: "MELANIA (OTC)",
    2157: "Ondo (OTC)", 2048: "Sui (OTC)", 2049: "Render (OTC)",
    
    # INDICES OTC
    947: "Nasdaq 100 (OTC)", 948: "S&P 500 (OTC)", 949: "Dow Jones (OTC)",
    
    # COMMODITIES
    959: "Oro XAU (OTC)", 960: "Plata XAG (OTC)",
}

# ═══════════════════════════════════════════════════════════════

def hora():
    return datetime.now(RD_TZ).strftime("%H:%M:%S")

def hora_entrada():
    ahora = datetime.now(RD_TZ)
    entrada = ahora.replace(second=0, microsecond=0) + timedelta(minutes=ANTICIPACION + 1)
    expira = entrada + timedelta(minutes=DURACION)
    return entrada.strftime("%H:%M:%S"), expira.strftime("%H:%M:%S")


class Bot:
    def __init__(self, ssid):
        self.ssid = ssid
        self.ws = None
        self.ultima = {}
        self.total = 0
        self.precios = {}
    
    async def conectar(self):
        print(f"\n🔌 [{hora()}] Conectando...")
        try:
            self.ws = await websockets.connect(WS_URL, origin='https://trade.bull-ex.com')
            await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
            await asyncio.sleep(1)
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
            await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
            print(f"✅ Conectado!\n")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def mostrar(self, activo, direccion, prob, entrada, expira):
        self.total += 1
        
        if direccion == "CALL":
            emoji = "🟢"
            texto = "SUBE ↑"
        else:
            emoji = "🔴"
            texto = "BAJA ↓"
        
        print("")
        print("═" * 50)
        print(f"  🎯 SEÑAL #{self.total}")
        print("═" * 50)
        print(f"  📍 {activo}")
        print(f"  {emoji} {texto} ({direccion})")
        print(f"  📊 Probabilidad: {prob:.0f}%")
        print("─" * 50)
        print(f"  ⏰ ENTRAR A LAS:  {entrada}")
        print(f"  ⏱️  EXPIRA A LAS:  {expira}")
        print(f"  ⌛ Duración:      {DURACION} minutos")
        print("─" * 50)
        print(f"  🕐 Hora RD: {hora()}")
        print("═" * 50)
    
    async def procesar(self, msg):
        try:
            data = json.loads(msg)
            nombre = data.get('name', '')
            m = data.get('msg', {})
            
            if nombre == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                valor = m.get('value', 0.5)
                
                # Filtrar blitz
                if 'blitz' in inst.lower():
                    return
                
                # Solo activos OTC permitidos
                if aid not in ACTIVOS:
                    return
                
                # Calcular porcentajes
                call = valor * 100
                put = 100 - call
                
                # Solo señales fuertes
                if call >= UMBRAL_MINIMO:
                    direccion = "CALL"
                    prob = call
                elif put >= UMBRAL_MINIMO:
                    direccion = "PUT"
                    prob = put
                else:
                    return
                
                # Cooldown
                ahora = time.time()
                clave = f"{aid}_{inst}"
                if clave in self.ultima:
                    if ahora - self.ultima[clave] < COOLDOWN:
                        return
                self.ultima[clave] = ahora
                
                # Mostrar señal
                entrada, expira = hora_entrada()
                self.mostrar(ACTIVOS[aid], direccion, prob, entrada, expira)
                
            elif nombre == 'candle-generated':
                aid = m.get('active_id', 0)
                close = m.get('close', 0)
                if close:
                    self.precios[aid] = close
                    
        except:
            pass
    
    async def ejecutar(self):
        if not await self.conectar():
            return
        
        print("═" * 50)
        print("  🎯 BOT SEÑALES OTC - BULLEX")
        print("═" * 50)
        print(f"  🕐 Hora RD: {hora()}")
        print(f"  📊 Umbral: >{UMBRAL_MINIMO}%")
        print(f"  ⏰ Anticipación: {ANTICIPACION} min")
        print(f"  🔄 Cooldown: {COOLDOWN//60} min")
        print("═" * 50)
        print("  Esperando señales...")
        print("  Presiona Ctrl+C para salir")
        print("═" * 50)
        
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                    await self.procesar(msg)
                except asyncio.TimeoutError:
                    print(f"  [{hora()}] ⏳ Esperando señales...")
                except websockets.exceptions.ConnectionClosed:
                    print(f"\n⚠️ Reconectando...")
                    if await self.conectar():
                        continue
                    break
        except KeyboardInterrupt:
            pass
        
        print(f"\n\n📊 Total señales: {self.total}")
        if self.ws:
            await self.ws.close()
        print("👋 Bot cerrado")


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🎯 BOT SEÑALES OTC - BULLEX                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PASOS PARA OBTENER TU SSID:                                 ║
║                                                              ║
║  1. Abre Chrome → https://trade.bull-ex.com                  ║
║  2. Haz login con tu cuenta                                  ║
║  3. Presiona F12                                             ║
║  4. Click en "Application" (arriba)                          ║
║  5. Click en "Cookies" → "trade.bull-ex.com"                 ║
║  6. Busca "ssid" y copia el valor                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    ssid = MI_SSID.strip()
    if not ssid:
        ssid = input("🔑 Pega tu SSID aquí: ").strip()
    
    if not ssid:
        print("\n❌ Necesitas un SSID válido")
        return
    
    bot = Bot(ssid)
    await bot.ejecutar()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Cerrado")
