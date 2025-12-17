#!/usr/bin/env python3
"""
🎯 BULLEX BOT - SEÑALES EN TIEMPO REAL CON AUTO-LOGIN
=====================================================

Este bot:
1. Inicia sesión automáticamente en Bullex
2. Se conecta al WebSocket
3. Recibe datos en tiempo real
4. Genera señales de trading

⚠️ SEGURIDAD: Crea un archivo .env con tus credenciales
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field

try:
    import aiohttp
except ImportError:
    import subprocess
    subprocess.run(['pip3', 'install', 'aiohttp'], capture_output=True)
    import aiohttp

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run(['pip3', 'install', 'websockets'], capture_output=True)
    import websockets


# ============= CONFIGURACIÓN =============
# Opción 1: Variables de entorno (más seguro)
# Opción 2: Archivo .env
# Opción 3: Directamente aquí (menos seguro)

BULLEX_EMAIL = os.environ.get('BULLEX_EMAIL', 'gjoan3181@gmail.com')
BULLEX_PASSWORD = os.environ.get('BULLEX_PASSWORD', 'Frederik1499@')

# URLs de Bullex
LOGIN_URL = "https://api.trade.bull-ex.com/v2/login"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# Activos conocidos
ACTIVOS = {
    86: "AUD/CAD (OTC)",
    # Se irán agregando más automáticamente
}


@dataclass
class Sesion:
    """Datos de sesión de Bullex."""
    ssid: str = ""
    identity: str = ""
    cookies: Dict[str, str] = field(default_factory=dict)
    logged_in: bool = False


@dataclass
class Senal:
    """Señal de trading."""
    activo: str
    direccion: str  # "CALL" o "PUT"
    fuerza: int  # 1-5
    razon: str
    timestamp: datetime


class BullexBot:
    """Bot de trading para Bullex."""
    
    def __init__(self):
        self.sesion = Sesion()
        self.ws = None
        self.conectado = False
        self.datos = {
            'sentimiento': {},
            'precios': {},
            'activos': {}
        }
        self.senales: list = []
    
    async def login(self) -> bool:
        """Inicia sesión en Bullex."""
        print("\n" + "🔐"*20)
        print("  INICIANDO SESIÓN EN BULLEX")
        print("🔐"*20)
        
        payload = {
            "identifier": BULLEX_EMAIL,
            "password": BULLEX_PASSWORD
        }
        
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://trade.bull-ex.com",
            "Referer": "https://trade.bull-ex.com/"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(LOGIN_URL, json=payload, headers=headers) as resp:
                    
                    print(f"  📡 Respuesta: {resp.status}")
                    
                    if resp.status == 200:
                        # Extraer cookies
                        for cookie in resp.cookies.values():
                            self.sesion.cookies[cookie.key] = cookie.value
                            if cookie.key == 'ssid':
                                self.sesion.ssid = cookie.value
                                print(f"  ✅ SSID obtenido: {cookie.value[:20]}...")
                        
                        # También revisar Set-Cookie en headers
                        if 'Set-Cookie' in resp.headers:
                            set_cookie = resp.headers['Set-Cookie']
                            if 'ssid=' in set_cookie:
                                ssid = set_cookie.split('ssid=')[1].split(';')[0]
                                self.sesion.ssid = ssid
                                self.sesion.cookies['ssid'] = ssid
                                print(f"  ✅ SSID desde header: {ssid[:20]}...")
                        
                        # Intentar leer body
                        try:
                            data = await resp.json()
                            print(f"  📦 Respuesta: {list(data.keys()) if isinstance(data, dict) else 'OK'}")
                        except:
                            pass
                        
                        self.sesion.logged_in = True
                        print("  ✅ ¡LOGIN EXITOSO!")
                        return True
                    else:
                        text = await resp.text()
                        print(f"  ❌ Error: {resp.status}")
                        print(f"  📄 {text[:200]}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ Error de conexión: {e}")
            return False
    
    async def conectar_ws(self) -> bool:
        """Conecta al WebSocket de Bullex."""
        print("\n" + "🔌"*20)
        print("  CONECTANDO AL WEBSOCKET")
        print("🔌"*20)
        
        if not self.sesion.ssid:
            print("  ❌ No hay sesión activa. Haz login primero.")
            return False
        
        # Construir cookies para el WebSocket
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.sesion.cookies.items()])
        
        headers = {
            "Cookie": cookie_str,
            "Origin": "https://trade.bull-ex.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        }
        
        try:
            print(f"  📡 Conectando a {WS_URL}...")
            
            # Intentar con headers
            try:
                self.ws = await websockets.connect(
                    WS_URL,
                    extra_headers=headers,
                    ping_interval=25,
                    ping_timeout=10
                )
            except TypeError:
                # Versión antigua de websockets
                self.ws = await websockets.connect(
                    WS_URL,
                    origin="https://trade.bull-ex.com",
                    ping_interval=25
                )
            
            self.conectado = True
            print("  ✅ ¡CONECTADO AL WEBSOCKET!")
            
            # Enviar autenticación
            await self._enviar_auth()
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    async def _enviar_auth(self):
        """Envía mensaje de autenticación al WebSocket."""
        # Enviar SSID
        auth_msg = {
            "name": "ssid",
            "msg": self.sesion.ssid
        }
        
        try:
            await self.ws.send(json.dumps(auth_msg))
            print("  🔐 Autenticación enviada")
        except Exception as e:
            print(f"  ⚠️ Error enviando auth: {e}")
    
    async def suscribir_canales(self):
        """Suscribe a los canales de datos."""
        canales = [
            {"name": "candle-generated"},
            {"name": "traders-mood-changed"},
            {"name": "price-generated"},
        ]
        
        for canal in canales:
            msg = {
                "name": "subscribeMessage",
                "msg": canal
            }
            try:
                await self.ws.send(json.dumps(msg))
                print(f"  📢 Suscrito a: {canal['name']}")
            except:
                pass
    
    def _procesar_mensaje(self, mensaje: str):
        """Procesa mensaje del WebSocket."""
        try:
            data = json.loads(mensaje)
            nombre = data.get("name", "")
            msg = data.get("msg", {})
            
            if nombre == "traders-mood-changed":
                self._procesar_sentimiento(msg)
                
            elif nombre == "candle-generated":
                self._procesar_vela(msg)
                
            elif nombre == "profile":
                print(f"  👤 Perfil cargado")
                
            elif nombre == "balance":
                balance = msg.get("amount", msg.get("current_balance", {}).get("amount", 0))
                print(f"  💰 Balance: ${balance}")
                
            elif nombre == "timeSync":
                pass
                
            elif nombre:
                # Descubrir activos
                aid = msg.get("active_id") or msg.get("asset_id")
                if aid and aid not in self.datos['activos']:
                    self.datos['activos'][aid] = f"Activo {aid}"
                    
        except:
            pass
    
    def _procesar_sentimiento(self, msg: dict):
        """Procesa sentimiento de traders y genera señales."""
        aid = msg.get("asset_id", 0)
        valor = msg.get("value", 0.5)
        
        call_pct = valor * 100
        put_pct = 100 - call_pct
        
        nombre = ACTIVOS.get(aid, self.datos['activos'].get(aid, f"#{aid}"))
        
        # Guardar datos
        self.datos['sentimiento'][aid] = {
            'call': call_pct,
            'put': put_pct,
            'timestamp': time.time()
        }
        
        # Generar señal basada en sentimiento extremo
        if call_pct >= 75:
            self._nueva_senal(nombre, "CALL", 5, f"Sentimiento extremo: {call_pct:.0f}% CALL")
            print(f"  🟢🟢🟢 {nombre}: {call_pct:.0f}% CALL - ¡SEÑAL FUERTE!")
        elif call_pct >= 65:
            self._nueva_senal(nombre, "CALL", 3, f"Sentimiento alto: {call_pct:.0f}% CALL")
            print(f"  🟢 {nombre}: {call_pct:.0f}% CALL")
        elif put_pct >= 75:
            self._nueva_senal(nombre, "PUT", 5, f"Sentimiento extremo: {put_pct:.0f}% PUT")
            print(f"  🔴🔴🔴 {nombre}: {put_pct:.0f}% PUT - ¡SEÑAL FUERTE!")
        elif put_pct >= 65:
            self._nueva_senal(nombre, "PUT", 3, f"Sentimiento alto: {put_pct:.0f}% PUT")
            print(f"  🔴 {nombre}: {put_pct:.0f}% PUT")
        else:
            print(f"  ⚪ {nombre}: CALL {call_pct:.0f}% | PUT {put_pct:.0f}%")
    
    def _procesar_vela(self, msg: dict):
        """Procesa datos de vela."""
        aid = msg.get("active_id", 0)
        close = msg.get("close", 0)
        
        if close:
            self.datos['precios'][aid] = close
            nombre = ACTIVOS.get(aid, self.datos['activos'].get(aid, f"#{aid}"))
            print(f"  💹 {nombre}: {close:.6f}")
    
    def _nueva_senal(self, activo: str, direccion: str, fuerza: int, razon: str):
        """Registra una nueva señal."""
        senal = Senal(
            activo=activo,
            direccion=direccion,
            fuerza=fuerza,
            razon=razon,
            timestamp=datetime.now()
        )
        self.senales.append(senal)
        
        # Mantener solo las últimas 50 señales
        if len(self.senales) > 50:
            self.senales = self.senales[-50:]
    
    async def escuchar(self, segundos: int = 300):
        """Escucha datos en tiempo real."""
        if not self.ws:
            print("  ❌ WebSocket no conectado")
            return
        
        print(f"\n  👂 Escuchando datos en tiempo real...")
        print(f"  ⏱️  Duración: {segundos} segundos")
        print("  " + "─"*50)
        print("  Presiona Ctrl+C para detener")
        print("  " + "─"*50 + "\n")
        
        inicio = time.time()
        
        try:
            while time.time() - inicio < segundos:
                try:
                    mensaje = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    self._procesar_mensaje(mensaje)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"\n  ⚠️ Conexión cerrada: {e}")
                    print("  🔄 Intentando reconectar...")
                    if await self.reconectar():
                        continue
                    else:
                        break
                        
        except KeyboardInterrupt:
            print("\n  👋 Detenido por el usuario")
        except Exception as e:
            print(f"\n  ❌ Error: {e}")
    
    async def reconectar(self) -> bool:
        """Intenta reconectar."""
        print("  🔄 Reconectando...")
        
        # Primero hacer login de nuevo
        if await self.login():
            # Luego conectar WebSocket
            if await self.conectar_ws():
                await self.suscribir_canales()
                return True
        return False
    
    def mostrar_resumen(self):
        """Muestra resumen de la sesión."""
        print("\n" + "="*60)
        print("  📊 RESUMEN DE SESIÓN")
        print("="*60)
        
        print(f"\n  🔐 Sesión activa: {'Sí' if self.sesion.logged_in else 'No'}")
        print(f"  🔌 WebSocket: {'Conectado' if self.conectado else 'Desconectado'}")
        
        if self.datos['sentimiento']:
            print(f"\n  👥 SENTIMIENTO ACTUAL:")
            for aid, sent in self.datos['sentimiento'].items():
                nombre = ACTIVOS.get(aid, self.datos['activos'].get(aid, f"#{aid}"))
                emoji = "🟢" if sent['call'] > 55 else "🔴" if sent['put'] > 55 else "⚪"
                print(f"     {emoji} {nombre}: CALL {sent['call']:.0f}% | PUT {sent['put']:.0f}%")
        
        if self.senales:
            print(f"\n  🎯 ÚLTIMAS SEÑALES:")
            for senal in self.senales[-5:]:
                emoji = "🟢" if senal.direccion == "CALL" else "🔴"
                estrellas = "⭐" * senal.fuerza
                print(f"     {emoji} {senal.activo}: {senal.direccion} {estrellas}")
                print(f"        {senal.razon}")
        
        print("\n" + "="*60)
    
    async def cerrar(self):
        """Cierra conexiones."""
        if self.ws:
            await self.ws.close()
        print("  👋 Conexiones cerradas")


async def main():
    """Función principal."""
    print("\n" + "🤖"*25)
    print("  BULLEX BOT - SEÑALES EN TIEMPO REAL")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🤖"*25)
    
    bot = BullexBot()
    
    # 1. Login
    if not await bot.login():
        print("\n  ❌ No se pudo iniciar sesión")
        return
    
    # 2. Conectar WebSocket
    if not await bot.conectar_ws():
        print("\n  ❌ No se pudo conectar al WebSocket")
        return
    
    # 3. Suscribir a canales
    await bot.suscribir_canales()
    
    # 4. Escuchar datos (5 minutos por defecto)
    await bot.escuchar(segundos=300)
    
    # 5. Mostrar resumen
    bot.mostrar_resumen()
    
    # 6. Cerrar
    await bot.cerrar()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Bot detenido")
