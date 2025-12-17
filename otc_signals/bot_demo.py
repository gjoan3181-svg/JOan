#!/usr/bin/env python3
"""
🎯 BULLEX BOT DEMO - Prueba de Operaciones Automáticas
======================================================

Este bot:
1. Espera señales de alta confianza (>90%)
2. Ejecuta 2-3 operaciones de prueba en demo
3. Verifica resultados

⚠️ SOLO PARA CUENTA DEMO
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime, timedelta
import time
import os

EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# Activos conocidos
ACTIVOS = {
    1: "EUR/USD", 3: "GBP/USD", 5: "USD/JPY", 6: "AUD/USD",
    85: "AUD/CAD", 86: "AUD/CAD OTC", 212: "Bitcoin",
    1857: "BNB", 1866: "Cardano", 1873: "Dogecoin", 1876: "Solana",
    1973: "Pepe", 2044: "Arbitrum", 2048: "Sui", 2108: "Dogs",
    2151: "Trump", 2152: "Melania",
}


class BotDemo:
    def __init__(self):
        self.ws = None
        self.ssid = ""
        self.cookies = {}
        self.balance = 0
        self.balance_id = 0
        self.operaciones = []
        self.max_operaciones = 3
        self.monto_operacion = 1.00  # $1 por operación
        self.precios = {}
        self.sentimiento = {}
    
    async def login(self):
        print("\n🔐 Conectando a Bullex...")
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URL,
                json={'identifier': EMAIL, 'password': PASSWORD},
                headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
                
                if resp.status != 200:
                    print(f"   ❌ Error: {resp.status}")
                    return False
                
                data = await resp.json()
                self.ssid = data.get('ssid', '')
                self.cookies = {c.key: c.value for c in resp.cookies.values()}
        
        print("   ✅ Login exitoso")
        return True
    
    async def conectar_ws(self):
        print("🔌 Conectando WebSocket...")
        cookie_str = '; '.join([f'{k}={v}' for k,v in self.cookies.items()])
        self.ws = await websockets.connect(
            WS_URL,
            origin='https://trade.bull-ex.com',
            extra_headers={'Cookie': cookie_str}
        )
        
        await self.ws.send(json.dumps({'name': 'ssid', 'msg': self.ssid}))
        await asyncio.sleep(1)
        await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
        await self.ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'candle-generated'}}))
        
        print("   ✅ Conectado")
        return True
    
    async def abrir_operacion(self, activo_id: int, direccion: str, monto: float, duracion: int = 60):
        """
        Intenta abrir una operación binaria.
        direccion: "call" o "put"
        duracion: segundos (60 = 1 minuto)
        """
        # Calcular tiempo de expiración
        ahora = datetime.now()
        expiracion = ahora + timedelta(seconds=duracion + 30)
        exp_timestamp = int(expiracion.timestamp())
        
        # Mensaje para abrir operación (formato IQ Option / Bullex)
        orden = {
            "name": "sendMessage",
            "msg": {
                "name": "binary-options.open-option",
                "version": "1.0",
                "body": {
                    "user_balance_id": self.balance_id,
                    "active_id": activo_id,
                    "option_type_id": 3,  # turbo
                    "direction": direccion,
                    "expired": exp_timestamp,
                    "refund_value": 0,
                    "price": monto,
                    "value": 0,
                    "profit_percent": 80
                }
            }
        }
        
        print(f"\n   📤 Enviando orden: {direccion.upper()} en activo #{activo_id}...")
        await self.ws.send(json.dumps(orden))
        
        # También probar formato alternativo
        orden_alt = {
            "name": "sendMessage",
            "msg": {
                "name": "buyV2",
                "body": {
                    "price": monto,
                    "active_id": activo_id,
                    "direction": direccion,
                    "option_type_id": 3,
                    "expired": exp_timestamp,
                    "user_balance_id": self.balance_id
                }
            }
        }
        await self.ws.send(json.dumps(orden_alt))
        
        return True
    
    async def procesar_mensaje(self, msg):
        try:
            data = json.loads(msg)
            name = data.get('name', '')
            m = data.get('msg', {})
            
            if name == 'profile':
                self.balance = m.get('balance', 0)
                self.balance_id = m.get('balance_id', 0)
                print(f"\n💰 Balance: ${self.balance:.2f}")
                print(f"   Balance ID: {self.balance_id}")
                
                # Verificar si es cuenta demo
                balance_type = m.get('balance_type', 0)
                if balance_type == 4:
                    print("   ✅ Cuenta DEMO detectada")
                else:
                    print(f"   ⚠️ Tipo de balance: {balance_type}")
            
            elif name == 'balance':
                nuevo = m.get('amount', m.get('current_balance', {}).get('amount', 0))
                if nuevo != self.balance:
                    diff = nuevo - self.balance
                    emoji = "📈" if diff > 0 else "📉"
                    print(f"\n{emoji} Balance: ${self.balance:.2f} → ${nuevo:.2f} ({diff:+.2f})")
                    self.balance = nuevo
            
            elif name == 'traders-mood-changed':
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                # Solo turbo/binary, no blitz
                if 'blitz' in inst.lower():
                    return
                
                call_pct = value * 100
                put_pct = 100 - call_pct
                
                # Guardar sentimiento
                self.sentimiento[aid] = {
                    'call': call_pct,
                    'put': put_pct,
                    'inst': inst
                }
                
                # Señal muy fuerte (>95%) y tenemos operaciones disponibles
                if len(self.operaciones) < self.max_operaciones:
                    if call_pct >= 95 and aid in ACTIVOS:
                        await self.ejecutar_senal(aid, "call", call_pct)
                    elif put_pct >= 95 and aid in ACTIVOS:
                        await self.ejecutar_senal(aid, "put", put_pct)
            
            elif name == 'candle-generated':
                aid = m.get('active_id', 0)
                self.precios[aid] = m.get('close', 0)
            
            # Respuestas de órdenes
            elif name in ['option', 'option-opened', 'buyComplete', 'result']:
                print(f"\n📩 Respuesta orden: {name}")
                print(f"   {str(m)[:200]}")
            
            elif 'error' in name.lower() or 'reject' in name.lower():
                print(f"\n❌ Error: {name}")
                print(f"   {str(m)[:200]}")
                
        except Exception as e:
            pass
    
    async def ejecutar_senal(self, aid: int, direccion: str, pct: float):
        """Ejecuta una señal de trading."""
        nombre = ACTIVOS.get(aid, f"#{aid}")
        
        print("\n" + "=" * 60)
        print(f"🎯 EJECUTANDO OPERACIÓN #{len(self.operaciones) + 1}")
        print("=" * 60)
        print(f"📍 Activo: {nombre} (ID: {aid})")
        print(f"📊 Dirección: {direccion.upper()}")
        print(f"👥 Sentimiento: {pct:.0f}%")
        print(f"💵 Monto: ${self.monto_operacion:.2f}")
        print(f"⏱️  Duración: 1 minuto")
        
        # Registrar operación
        op = {
            'id': len(self.operaciones) + 1,
            'activo': nombre,
            'activo_id': aid,
            'direccion': direccion,
            'sentimiento': pct,
            'precio_entrada': self.precios.get(aid, 0),
            'timestamp': datetime.now().isoformat(),
            'resultado': None
        }
        self.operaciones.append(op)
        
        # Intentar abrir operación
        await self.abrir_operacion(aid, direccion, self.monto_operacion)
        
        print("=" * 60)
        
        # Esperar un poco entre operaciones
        await asyncio.sleep(5)
    
    async def ejecutar(self):
        if not await self.login():
            return
        
        if not await self.conectar_ws():
            return
        
        print("\n" + "=" * 60)
        print("  🤖 BOT DEMO - PRUEBA DE OPERACIONES")
        print("=" * 60)
        print(f"  📊 Máximo operaciones: {self.max_operaciones}")
        print(f"  💵 Monto por operación: ${self.monto_operacion:.2f}")
        print(f"  🎯 Umbral: >95% sentimiento")
        print("=" * 60)
        print("  Esperando señales fuertes...")
        print("=" * 60)
        
        inicio = time.time()
        timeout = 120  # 2 minutos máximo de espera
        
        try:
            while len(self.operaciones) < self.max_operaciones:
                if time.time() - inicio > timeout:
                    print("\n⏱️ Timeout - no se encontraron suficientes señales fuertes")
                    break
                
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=2)
                    await self.procesar_mensaje(msg)
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print("\n⚠️ Conexión perdida")
                    break
        
        except KeyboardInterrupt:
            pass
        
        # Resumen
        print("\n\n" + "=" * 60)
        print("📊 RESUMEN DE OPERACIONES")
        print("=" * 60)
        
        if self.operaciones:
            for op in self.operaciones:
                emoji = "🟢" if op['direccion'] == "call" else "🔴"
                print(f"  {emoji} {op['activo']}: {op['direccion'].upper()} | {op['sentimiento']:.0f}%")
        else:
            print("  No se ejecutaron operaciones")
        
        print(f"\n💰 Balance final: ${self.balance:.2f}")
        print("=" * 60)
        
        await self.ws.close()


async def main():
    bot = BotDemo()
    await bot.ejecutar()


if __name__ == '__main__':
    asyncio.run(main())
