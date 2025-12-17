#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import websockets

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.trade.bull-ex.com/v2/login',
            json={'identifier': 'gjoan3181@gmail.com', 'password': 'Frederik1499@'},
            headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
            data = await resp.json()
            ssid = data.get('ssid', '')
            cookies = {c.key: c.value for c in resp.cookies.values()}
    
    print(f'SSID: OK')
    
    cookie_str = '; '.join([f'{k}={v}' for k,v in cookies.items()])
    ws = await websockets.connect(
        'wss://ws.trade.bull-ex.com/echo/websocket',
        origin='https://trade.bull-ex.com',
        extra_headers={'Cookie': cookie_str}
    )
    print('WS: OK')
    
    # Auth
    await ws.send(json.dumps({'name': 'ssid', 'msg': ssid}))
    print('Auth enviada')
    
    # Esperar profile
    await asyncio.sleep(1)
    
    # Probar múltiples formatos de suscripción
    subs = [
        # Formato 1: usado antes (funcionó)
        {'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}},
        
        # Formato 2: con request_id
        {'name': 'subscribeMessage', 'request_id': '1', 'msg': {'name': 'traders-mood-changed'}},
        
        # Formato 3: sendMessage
        {'name': 'sendMessage', 'msg': {'name': 'subscribeMessage', 'body': {'name': 'traders-mood-changed'}}},
        
        # Formato 4: version
        {'name': 'sendMessage', 'msg': {'name': 'subscribeMessage', 'version': '1.0', 'body': {'name': 'traders-mood-changed'}}},
        
        # Formato 5: subscribe
        {'name': 'subscribe', 'msg': 'traders-mood-changed'},
    ]
    
    for i, sub in enumerate(subs):
        await ws.send(json.dumps(sub))
        print(f'Sub {i+1}: {sub["name"]}')
    
    print()
    print('Escuchando respuestas (15s)...')
    
    tipos = {}
    mood_count = 0
    
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < 15:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
            data = json.loads(msg)
            name = data.get('name', '')
            tipos[name] = tipos.get(name, 0) + 1
            
            # Mostrar mensajes que no sean timeSync
            if name != 'timeSync':
                if name == 'traders-mood-changed':
                    mood_count += 1
                    if mood_count <= 5:
                        m = data.get('msg', {})
                        v = m.get('value', 0.5) * 100
                        print(f'  MOOD #{m.get("asset_id")}: {v:.0f}% CALL')
                else:
                    print(f'  {name}: {str(data)[:100]}')
                
        except asyncio.TimeoutError:
            continue
    
    await ws.close()
    
    print()
    print('Resumen:')
    for n, c in sorted(tipos.items(), key=lambda x: -x[1]):
        print(f'  {n}: {c}')
    
    print(f'\nMood recibidos: {mood_count}')

if __name__ == '__main__':
    asyncio.run(main())
