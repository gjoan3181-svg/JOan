#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import websockets

EMAIL = 'gjoan3181@gmail.com'
PASSWORD = 'Frederik1499@'

ACTIVOS = {
    1: 'EUR/USD', 77: 'USD/RUB', 78: 'EUR/NZD', 85: 'AUD/CAD',
    1861: 'LINK/USD', 1867: 'UNI/USD', 1873: 'DOGE/USD', 1935: 'KAVA/USD',
    1941: 'XTZ/USD', 2044: 'ARB/USD', 2049: 'RNDR/USD', 2062: 'RUNE/USD',
    2063: 'BONK/USD', 2099: 'FLOKI/USD', 2117: 'SAFE/USD', 2122: 'PNUT/USD',
    2132: 'HYPE/USD', 2144: 'GRIFFAIN/USD', 2150: 'ELIZA/USD', 2151: 'TRUMP/USD',
    2182: 'NIL/USD', 2183: 'PARTI/USD', 2291: 'KEKIUS/USD', 2320: 'FUEL/USD',
}

async def main():
    print('🤖 BULLEX BOT')
    print('=' * 50)
    
    # Login
    print('🔐 Login...')
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.trade.bull-ex.com/v2/login',
            json={'identifier': EMAIL, 'password': PASSWORD},
            headers={'Content-Type': 'application/json', 'Origin': 'https://trade.bull-ex.com'}) as resp:
            data = await resp.json()
            ssid = data.get('ssid', '')
            cookies = {c.key: c.value for c in resp.cookies.values()}
    print('   ✅ OK')
    
    # WebSocket
    print('🔌 WebSocket...')
    cookie_str = '; '.join([f'{k}={v}' for k,v in cookies.items()])
    
    ws = await websockets.connect(
        'wss://ws.trade.bull-ex.com/echo/websocket',
        origin='https://trade.bull-ex.com',
        additional_headers={'Cookie': cookie_str}
    )
    print('   ✅ Conectado')
    
    # Auth y suscripción
    await ws.send(json.dumps({'name': 'ssid', 'msg': ssid}))
    await ws.send(json.dumps({'name': 'subscribeMessage', 'msg': {'name': 'traders-mood-changed'}}))
    
    print()
    print('🎯 SEÑALES (20 segundos):')
    print('-' * 50)
    
    vistas = set()
    start = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start < 20:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1)
            data = json.loads(msg)
            
            if data.get('name') == 'traders-mood-changed':
                m = data['msg']
                aid = m.get('asset_id', 0)
                inst = m.get('instrument', '')
                value = m.get('value', 0.5)
                
                call_pct = value * 100
                put_pct = 100 - call_pct
                
                if call_pct >= 60 or put_pct >= 60:
                    clave = f'{aid}_{inst}'
                    if clave not in vistas:
                        vistas.add(clave)
                        nombre = ACTIVOS.get(aid, f'#{aid}')
                        tipo = ' [B]' if 'blitz' in inst else ' [T]' if 'turbo' in inst else ''
                        
                        if call_pct >= 90:
                            print(f'🟢🟢🟢🟢🟢 {nombre}{tipo} CALL {call_pct:.0f}% !!!EXTREMO')
                        elif call_pct >= 80:
                            print(f'🟢🟢🟢🟢 {nombre}{tipo} CALL {call_pct:.0f}% !!FUERTE')
                        elif call_pct >= 70:
                            print(f'🟢🟢🟢 {nombre}{tipo} CALL {call_pct:.0f}% !BUENA')
                        elif call_pct >= 60:
                            print(f'🟢🟢 {nombre}{tipo} CALL {call_pct:.0f}%')
                        elif put_pct >= 90:
                            print(f'🔴🔴🔴🔴🔴 {nombre}{tipo} PUT {put_pct:.0f}% !!!EXTREMO')
                        elif put_pct >= 80:
                            print(f'🔴🔴🔴🔴 {nombre}{tipo} PUT {put_pct:.0f}% !!FUERTE')
                        elif put_pct >= 70:
                            print(f'🔴🔴🔴 {nombre}{tipo} PUT {put_pct:.0f}% !BUENA')
                        elif put_pct >= 60:
                            print(f'🔴🔴 {nombre}{tipo} PUT {put_pct:.0f}%')
            
            elif data.get('name') == 'profile':
                bal = data.get('msg', {}).get('balance', 0)
                print(f'💰 Balance: ${bal:.2f}')
                
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f'Error: {e}')
            break
    
    print('-' * 50)
    print(f'✅ {len(vistas)} señales detectadas')
    await ws.close()

if __name__ == '__main__':
    asyncio.run(main())
