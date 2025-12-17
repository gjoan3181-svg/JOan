#!/usr/bin/env python3
"""
🎯 BULLEX OTC - SEÑALES EN TIEMPO REAL
======================================

Conexión directa al WebSocket de Bullex con autenticación.
Recibe datos en tiempo real y genera señales.

⚠️ IMPORTANTE: Actualiza las cookies cuando expire tu sesión.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, field

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run(['pip3', 'install', 'websockets'], capture_output=True)
    import websockets


# ============= TUS COOKIES DE BULLEX =============
# ⚠️ Actualiza estos valores si expiran
BULLEX_COOKIES = {
    "ssid": "8fdcce6b8186c946a35d96f93122363n",
    "identity": "901b317a53bee6be26e4437608f80e9fc2855",  # Puede estar incompleto
    "device_id": "0d82d9b5-bcd6-4829-8687-25e61f62429a",
    "platform": "187",
    "lang": "es_ES"
}

BULLEX_WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# IDs de activos (iremos descubriendo más)
ACTIVOS = {
    86: "AUD/CAD",
    # Agregaremos más según los descubramos
}


@dataclass
class Sentimiento:
    """Sentimiento de traders."""
    asset_id: int
    call_pct: float  # Porcentaje que va CALL
    timestamp: float = 0


@dataclass
class Vela:
    """Datos de vela."""
    asset_id: int
    open: float
    high: float
    low: float
    close: float
    timestamp: int


@dataclass
class DatosOTC:
    """Almacén de datos."""
    sentimiento: Dict[int, Sentimiento] = field(default_factory=dict)
    velas: Dict[int, List[Vela]] = field(default_factory=dict)
    precios: Dict[int, float] = field(default_factory=dict)
    activos_descubiertos: Dict[int, str] = field(default_factory=dict)


class BullexLive:
    """Cliente de Bullex en tiempo real."""
    
    def __init__(self):
        self.ws = None
        self.datos = DatosOTC()
        self.conectado = False
        self.msg_count = 0
    
    def _crear_cookie_header(self) -> str:
        """Crea el header de cookies."""
        return "; ".join([f"{k}={v}" for k, v in BULLEX_COOKIES.items()])
    
    async def conectar(self):
        """Conecta a Bullex."""
        print("\n" + "🔌"*20)
        print("  CONECTANDO A BULLEX OTC")
        print("🔌"*20)
        
        headers = {
            "Cookie": self._crear_cookie_header(),
            "Origin": "https://trade.bull-ex.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        }
        
        try:
            print(f"\n  📡 Conectando con autenticación...")
            
            self.ws = await websockets.connect(
                BULLEX_WS_URL,
                extra_headers=headers,
                ping_interval=25,
                ping_timeout=10
            )
            
            self.conectado = True
            print("  ✅ ¡CONECTADO!")
            
            # Enviar mensaje de autenticación si es necesario
            await self._autenticar()
            
            return True
            
        except TypeError:
            # Versión antigua de websockets
            try:
                self.ws = await websockets.connect(
                    BULLEX_WS_URL,
                    origin="https://trade.bull-ex.com",
                    ping_interval=25
                )
                self.conectado = True
                print("  ✅ ¡CONECTADO (modo compatible)!")
                return True
            except Exception as e:
                print(f"  ❌ Error: {e}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    async def _autenticar(self):
        """Envía mensaje de autenticación."""
        # Mensaje de autenticación basado en el protocolo de Bullex
        auth_msg = {
            "name": "ssid",
            "msg": BULLEX_COOKIES["ssid"]
        }
        
        try:
            await self.ws.send(json.dumps(auth_msg))
            print("  🔐 Mensaje de autenticación enviado")
        except:
            pass
    
    async def suscribir(self, asset_id: int):
        """Suscribe a un activo."""
        msgs = [
            {
                "name": "subscribeMessage",
                "msg": {
                    "name": "candle-generated",
                    "params": {"routingFilters": {"active_id": str(asset_id)}}
                }
            },
            {
                "name": "subscribeMessage", 
                "msg": {
                    "name": "traders-mood-changed",
                    "params": {"routingFilters": {"asset_id": str(asset_id)}}
                }
            }
        ]
        
        for msg in msgs:
            try:
                await self.ws.send(json.dumps(msg))
            except:
                pass
    
    def _procesar(self, mensaje: str):
        """Procesa mensaje recibido."""
        try:
            data = json.loads(mensaje)
            self.msg_count += 1
            
            nombre = data.get("name", "")
            msg = data.get("msg", {})
            
            if nombre == "candle-generated":
                self._procesar_vela(msg)
                
            elif nombre == "traders-mood-changed":
                self._procesar_sentimiento(msg)
                
            elif nombre == "timeSync":
                pass
                
            elif nombre == "profile":
                print(f"  👤 Perfil recibido")
                
            elif nombre == "balance":
                bal = msg.get("current_balance", {})
                amount = bal.get("amount", 0)
                print(f"  💰 Balance: ${amount}")
                
            elif nombre and nombre not in ["heartbeat"]:
                # Descubrir nuevos tipos de mensajes
                print(f"  📨 {nombre}")
                
                # Descubrir activos
                if "active_id" in str(msg) or "asset_id" in str(msg):
                    aid = msg.get("active_id") or msg.get("asset_id")
                    if aid and aid not in self.datos.activos_descubiertos:
                        self.datos.activos_descubiertos[aid] = f"Activo {aid}"
                        print(f"     📋 Nuevo activo descubierto: {aid}")
                        
        except json.JSONDecodeError:
            pass
        except Exception as e:
            pass
    
    def _procesar_vela(self, msg: dict):
        """Procesa datos de vela."""
        aid = msg.get("active_id", 0)
        
        if aid not in self.datos.activos_descubiertos:
            self.datos.activos_descubiertos[aid] = ACTIVOS.get(aid, f"Activo {aid}")
        
        # Mostrar precio
        close = msg.get("close", 0)
        if close:
            self.datos.precios[aid] = close
            nombre = self.datos.activos_descubiertos.get(aid, f"#{aid}")
            print(f"  💹 {nombre}: {close:.6f}")
    
    def _procesar_sentimiento(self, msg: dict):
        """Procesa sentimiento de traders."""
        aid = msg.get("asset_id", 0)
        valor = msg.get("value", 0.5)
        
        call_pct = valor * 100
        put_pct = 100 - call_pct
        
        self.datos.sentimiento[aid] = Sentimiento(
            asset_id=aid,
            call_pct=call_pct,
            timestamp=time.time()
        )
        
        nombre = self.datos.activos_descubiertos.get(aid, ACTIVOS.get(aid, f"#{aid}"))
        
        # Generar señal basada en sentimiento
        if call_pct >= 70:
            print(f"  🟢🟢 {nombre}: {call_pct:.0f}% CALL - ¡MAYORÍA COMPRA!")
        elif call_pct >= 60:
            print(f"  🟢 {nombre}: {call_pct:.0f}% CALL")
        elif put_pct >= 70:
            print(f"  🔴🔴 {nombre}: {put_pct:.0f}% PUT - ¡MAYORÍA VENDE!")
        elif put_pct >= 60:
            print(f"  🔴 {nombre}: {put_pct:.0f}% PUT")
        else:
            print(f"  ⚪ {nombre}: CALL {call_pct:.0f}% | PUT {put_pct:.0f}%")
    
    async def escuchar(self, segundos: int = 60):
        """Escucha mensajes."""
        if not self.ws:
            return
        
        print(f"\n  👂 Escuchando datos en tiempo real ({segundos}s)...")
        print("  " + "─"*50)
        
        inicio = time.time()
        
        try:
            while time.time() - inicio < segundos:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    self._procesar(msg)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"  ⚠️ Conexión cerrada: {e}")
                    break
                    
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print("  " + "─"*50)
    
    def mostrar_resumen(self):
        """Muestra resumen."""
        print("\n" + "="*60)
        print("  📊 RESUMEN DE DATOS BULLEX")
        print("="*60)
        
        print(f"\n  📨 Mensajes recibidos: {self.msg_count}")
        
        if self.datos.activos_descubiertos:
            print(f"\n  📋 ACTIVOS DESCUBIERTOS:")
            for aid, nombre in self.datos.activos_descubiertos.items():
                precio = self.datos.precios.get(aid, "N/A")
                sent = self.datos.sentimiento.get(aid)
                sent_str = f"CALL {sent.call_pct:.0f}%" if sent else "N/A"
                print(f"     ID {aid}: {nombre} | Precio: {precio} | Sent: {sent_str}")
        
        if self.datos.sentimiento:
            print(f"\n  👥 SENTIMIENTO ACTUAL:")
            for aid, sent in self.datos.sentimiento.items():
                nombre = self.datos.activos_descubiertos.get(aid, f"#{aid}")
                emoji = "🟢" if sent.call_pct > 55 else "🔴" if sent.call_pct < 45 else "⚪"
                print(f"     {emoji} {nombre}: {sent.call_pct:.0f}% CALL | {100-sent.call_pct:.0f}% PUT")
        
        print("\n" + "="*60)
    
    async def cerrar(self):
        """Cierra conexión."""
        if self.ws:
            await self.ws.close()
            print("  👋 Desconectado")


async def main():
    """Función principal."""
    print("\n" + "🎯"*25)
    print("  BULLEX OTC - DATOS EN TIEMPO REAL")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🎯"*25)
    
    cliente = BullexLive()
    
    if await cliente.conectar():
        # Suscribir a activo conocido
        await cliente.suscribir(86)  # AUD/CAD
        
        # Escuchar datos
        await cliente.escuchar(segundos=60)
        
        # Mostrar resumen
        cliente.mostrar_resumen()
        
        await cliente.cerrar()
    else:
        print("\n  ❌ No se pudo conectar")
        print("\n  💡 Posibles causas:")
        print("     1. Las cookies expiraron - actualízalas")
        print("     2. Sesión cerrada en Bullex")
        print("     3. Problemas de red")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  👋 Cancelado")
