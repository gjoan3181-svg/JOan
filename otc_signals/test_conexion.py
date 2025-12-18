#!/usr/bin/env python3
"""Test de conexión a Bullex"""

import asyncio
import json
import websockets

SSID = "e8b7b6185348833f922e675fe840fc3f"
WS_URL = "wss://ws.trade.bull-ex.com/echo/websocket"

async def test():
    print("\n🔌 Conectando a Bullex...")
    
    try:
        ws = await websockets.connect(
            WS_URL, 
            origin='https://trade.bull-ex.com',
            ping_interval=30
        )
        print("✅ WebSocket conectado")
        
        # Enviar SSID
        await ws.send(json.dumps({'name': 'ssid', 'msg': SSID}))
        print(f"📤 SSID enviado: {SSID[:20]}...")
        
        # Esperar respuesta
        await asyncio.sleep(1)
        
        # Suscribirse a velas
        await ws.send(json.dumps({
            'name': 'subscribeMessage', 
            'msg': {'name': 'candle-generated'}
        }))
        print("📤 Suscrito a candle-generated")
        
        # Escuchar mensajes por 15 segundos
        print("\n⏳ Esperando datos (15 seg)...\n")
        
        count = 0
        activos_vistos = set()
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 15:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(msg)
                
                name = data.get('name', '')
                
                if name == 'candle-generated':
                    m = data.get('msg', {})
                    aid = m.get('active_id')
                    close = m.get('close')
                    if aid and close:
                        activos_vistos.add(aid)
                        count += 1
                        if count <= 5:
                            print(f"  📊 Vela recibida: activo={aid}, precio={close}")
                        elif count == 6:
                            print(f"  ... (recibiendo más datos)")
                
                elif name == 'timeSync':
                    pass  # Ignorar
                
                elif name:
                    print(f"  📨 Mensaje: {name}")
                    
            except asyncio.TimeoutError:
                pass
        
        await ws.close()
        
        print(f"\n{'═' * 50}")
        print(f"📊 RESULTADO:")
        print(f"   Velas recibidas: {count}")
        print(f"   Activos únicos: {len(activos_vistos)}")
        
        if count > 0:
            print(f"\n✅ CONEXIÓN FUNCIONANDO!")
            print(f"   IDs de activos: {sorted(list(activos_vistos))[:10]}...")
        else:
            print(f"\n❌ NO SE RECIBEN DATOS")
            print(f"   Posibles causas:")
            print(f"   1. SSID expirado - Necesitas uno nuevo")
            print(f"   2. Mercado cerrado")
            print(f"   3. Problema de conexión")
        
        print(f"{'═' * 50}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test())
