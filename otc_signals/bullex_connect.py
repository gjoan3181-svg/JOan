#!/usr/bin/env python3
"""
🎯 CONEXIÓN DIRECTA A BULLEX OTC
================================

Se conecta al WebSocket de Bullex para recibir datos en tiempo real.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.run(['pip3', 'install', 'websockets'], capture_output=True)
    import websockets


# ============= CONFIGURACIÓN DE BULLEX =============
BULLEX_WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

# IDs de activos conocidos
ACTIVOS_BULLEX = {
    86: "AUD/CAD (OTC)",
}


@dataclass 
class SentimientoTraders:
    """Sentimiento de los traders."""
    asset_id: int
    valor: float
    instrumento: str = ""


@dataclass
class DatosBullex:
    """Almacena los datos recibidos."""
    sentimiento: Dict[int, SentimientoTraders] = field(default_factory=dict)
    ultimo_precio: Dict[int, float] = field(default_factory=dict)
    mensajes: List[dict] = field(default_factory=list)


class BullexConnector:
    """Conector WebSocket para Bullex."""
    
    def __init__(self):
        self.ws = None
        self.datos = DatosBullex()
        self.conectado = False
        self.mensajes_recibidos = 0
        
    async def conectar(self):
        """Establece conexión con Bullex."""
        print("\n" + "🔌"*20)
        print("  CONECTANDO A BULLEX OTC")
        print("🔌"*20)
        
        try:
            print(f"\n  📡 Conectando a {BULLEX_WS_URL}...")
            
            self.ws = await websockets.connect(
                BULLEX_WS_URL,
                origin="https://trade.bull-ex.com",
                ping_interval=30,
                ping_timeout=10
            )
            
            self.conectado = True
            print("  ✅ ¡CONECTADO A BULLEX!")
            return True
            
        except Exception as e:
            print(f"  ❌ Error de conexión: {e}")
            return False
    
    def procesar_mensaje(self, mensaje: str):
        """Procesa un mensaje recibido."""
        try:
            data = json.loads(mensaje)
            self.mensajes_recibidos += 1
            
            nombre = data.get("name", "")
            msg = data.get("msg", {})
            
            # Guardar mensaje
            self.datos.mensajes.append(data)
            
            if nombre == "candle-generated":
                active_id = msg.get("active_id", 0)
                nombre_activo = ACTIVOS_BULLEX.get(active_id, f"Activo {active_id}")
                print(f"  📊 Vela: {nombre_activo}")
                
            elif nombre == "traders-mood-changed":
                asset_id = msg.get("asset_id", 0)
                valor = msg.get("value", 0.5)
                nombre_activo = ACTIVOS_BULLEX.get(asset_id, f"Activo {asset_id}")
                call_pct = valor * 100
                put_pct = (1 - valor) * 100
                
                emoji = "🟢" if call_pct > 60 else "🔴" if put_pct > 60 else "⚪"
                print(f"  {emoji} Sentimiento {nombre_activo}: CALL {call_pct:.1f}% | PUT {put_pct:.1f}%")
                
                self.datos.sentimiento[asset_id] = SentimientoTraders(
                    asset_id=asset_id,
                    valor=valor,
                    instrumento=msg.get("instrument", "")
                )
                
            elif nombre == "timeSync":
                pass  # Ignorar
                
            else:
                if nombre:
                    print(f"  📨 {nombre}")
                    
        except Exception as e:
            pass
    
    async def escuchar(self, duracion_segundos: int = 30):
        """Escucha mensajes."""
        if not self.ws:
            return
        
        print(f"\n  👂 Escuchando {duracion_segundos} segundos...")
        print("  " + "─"*50)
        
        inicio = time.time()
        
        try:
            while time.time() - inicio < duracion_segundos:
                try:
                    mensaje = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                    self.procesar_mensaje(mensaje)
                except asyncio.TimeoutError:
                    continue
                    
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
        
        print("  " + "─"*50)
        print(f"  📊 Mensajes recibidos: {self.mensajes_recibidos}")
    
    async def desconectar(self):
        """Cierra la conexión."""
        if self.ws:
            await self.ws.close()
            print("  👋 Desconectado")
    
    def mostrar_resumen(self):
        """Muestra resumen."""
        print("\n" + "="*60)
        print("  📊 RESUMEN")
        print("="*60)
        print(f"  Total mensajes: {self.mensajes_recibidos}")
        
        if self.datos.sentimiento:
            print("\n  👥 SENTIMIENTO DE TRADERS:")
            for asset_id, sent in self.datos.sentimiento.items():
                nombre = ACTIVOS_BULLEX.get(asset_id, f"Activo {asset_id}")
                print(f"     {nombre}: {sent.valor*100:.1f}% CALL")


async def main():
    """Función principal."""
    print("\n" + "🎯"*20)
    print("  BULLEX OTC - CONEXIÓN DIRECTA")
    print("🎯"*20)
    
    connector = BullexConnector()
    
    if await connector.conectar():
        await connector.escuchar(duracion_segundos=20)
        connector.mostrar_resumen()
        await connector.desconectar()
    else:
        print("\n  📋 Necesitamos autenticación.")
        print("  Por favor, proporciona las cookies de sesión.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  👋 Cancelado")
