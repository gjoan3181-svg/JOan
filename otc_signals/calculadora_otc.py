#!/usr/bin/env python3
"""
🎯 CALCULADORA DE SEÑALES PARA BINARIAS OTC
============================================

Tú ingresas los valores de los indicadores de tu plataforma (Bullex)
y el script te dice si entrar CALL o PUT.

Uso:
    python3 calculadora_otc.py
"""

from datetime import datetime


def obtener_float(pregunta: str, minimo: float = None, maximo: float = None) -> float:
    """Obtiene un número del usuario."""
    while True:
        try:
            valor = input(pregunta).strip()
            if valor == '':
                return None
            valor = float(valor.replace(',', '.'))
            if minimo is not None and valor < minimo:
                print(f"  ⚠️ Valor debe ser mayor a {minimo}")
                continue
            if maximo is not None and valor > maximo:
                print(f"  ⚠️ Valor debe ser menor a {maximo}")
                continue
            return valor
        except ValueError:
            print("  ⚠️ Ingresa un número válido")


def obtener_opcion(pregunta: str, opciones: list) -> str:
    """Obtiene una opción del usuario."""
    opciones_str = "/".join(opciones)
    while True:
        valor = input(f"{pregunta} ({opciones_str}): ").strip().upper()
        if valor in [o.upper() for o in opciones]:
            return valor
        print(f"  ⚠️ Opciones válidas: {opciones_str}")


def analizar_senal(datos: dict) -> dict:
    """
    Analiza los indicadores y genera una señal.
    
    Args:
        datos: Diccionario con los valores de indicadores
    
    Returns:
        Diccionario con la señal y razones
    """
    call_pts = 0
    put_pts = 0
    razones = []
    advertencias = []
    
    # ==================== TENDENCIA (MUY IMPORTANTE) ====================
    tendencia = datos.get('tendencia')
    if tendencia == 'SUBE':
        call_pts += 25
        razones.append("📈 Tendencia ALCISTA")
    elif tendencia == 'BAJA':
        put_pts += 25
        razones.append("📉 Tendencia BAJISTA")
    else:
        razones.append("↔️ Tendencia LATERAL")
    
    # ==================== RSI ====================
    rsi = datos.get('rsi')
    if rsi is not None:
        if rsi < 20:
            call_pts += 20
            razones.append(f"🟢 RSI MUY bajo ({rsi}) - Sobreventa fuerte")
        elif rsi < 30:
            call_pts += 15
            razones.append(f"🟢 RSI bajo ({rsi}) - Sobreventa")
        elif rsi < 40:
            call_pts += 8
        elif rsi > 80:
            put_pts += 20
            razones.append(f"🔴 RSI MUY alto ({rsi}) - Sobrecompra fuerte")
        elif rsi > 70:
            put_pts += 15
            razones.append(f"🔴 RSI alto ({rsi}) - Sobrecompra")
        elif rsi > 60:
            put_pts += 8
        
        # ADVERTENCIA: RSI contra tendencia
        if tendencia == 'BAJA' and rsi < 30:
            advertencias.append("⚠️ RSI bajo en tendencia bajista - puede seguir bajando")
        if tendencia == 'SUBE' and rsi > 70:
            advertencias.append("⚠️ RSI alto en tendencia alcista - puede seguir subiendo")
    
    # ==================== STOCHASTIC ====================
    stoch = datos.get('stochastic')
    stoch_cruce = datos.get('stoch_cruce')
    
    if stoch is not None:
        if stoch < 20:
            if stoch_cruce == 'ARRIBA':
                call_pts += 20
                razones.append(f"🟢 Stoch cruce ALCISTA en sobreventa ({stoch})")
            else:
                call_pts += 10
                razones.append(f"🟢 Stoch en sobreventa ({stoch})")
        elif stoch > 80:
            if stoch_cruce == 'ABAJO':
                put_pts += 20
                razones.append(f"🔴 Stoch cruce BAJISTA en sobrecompra ({stoch})")
            else:
                put_pts += 10
                razones.append(f"🔴 Stoch en sobrecompra ({stoch})")
        elif stoch_cruce == 'ARRIBA':
            call_pts += 10
            razones.append("🟢 Stoch cruce alcista")
        elif stoch_cruce == 'ABAJO':
            put_pts += 10
            razones.append("🔴 Stoch cruce bajista")
    
    # ==================== MACD ====================
    macd_senal = datos.get('macd')
    if macd_senal == 'ARRIBA':
        call_pts += 15
        razones.append("🟢 MACD cruce ALCISTA")
    elif macd_senal == 'ABAJO':
        put_pts += 15
        razones.append("🔴 MACD cruce BAJISTA")
    elif macd_senal == 'POSITIVO':
        call_pts += 8
    elif macd_senal == 'NEGATIVO':
        put_pts += 8
    
    # ==================== BOLLINGER BANDS ====================
    bollinger = datos.get('bollinger')
    if bollinger == 'INFERIOR':
        call_pts += 15
        razones.append("🟢 Precio en BANDA INFERIOR Bollinger")
    elif bollinger == 'SUPERIOR':
        put_pts += 15
        razones.append("🔴 Precio en BANDA SUPERIOR Bollinger")
    elif bollinger == 'CERCA_INF':
        call_pts += 8
    elif bollinger == 'CERCA_SUP':
        put_pts += 8
    
    # ==================== VELAS ====================
    vela = datos.get('vela')
    if vela == 'MARTILLO':
        call_pts += 18
        razones.append("🟢 Patrón MARTILLO (reversión alcista)")
    elif vela == 'ENVOLVENTE_ALC':
        call_pts += 18
        razones.append("🟢 ENVOLVENTE ALCISTA")
    elif vela == 'ESTRELLA_MANANA':
        call_pts += 15
        razones.append("🟢 Estrella de la mañana")
    elif vela == 'ESTRELLA_FUGAZ':
        put_pts += 18
        razones.append("🔴 Patrón ESTRELLA FUGAZ (reversión bajista)")
    elif vela == 'ENVOLVENTE_BAJ':
        put_pts += 18
        razones.append("🔴 ENVOLVENTE BAJISTA")
    elif vela == 'ESTRELLA_TARDE':
        put_pts += 15
        razones.append("🔴 Estrella de la tarde")
    elif vela == 'DOJI':
        razones.append("⚪ DOJI - Indecisión")
        advertencias.append("⚠️ Doji = mercado indeciso, esperar confirmación")
    
    # ==================== MEDIAS MÓVILES ====================
    ma_pos = datos.get('precio_vs_ma')
    if ma_pos == 'ARRIBA':
        call_pts += 10
        razones.append("📈 Precio sobre Media Móvil")
    elif ma_pos == 'ABAJO':
        put_pts += 10
        razones.append("📉 Precio bajo Media Móvil")
    
    # ==================== FILTRO DE TENDENCIA ====================
    # Si hay tendencia fuerte, penalizar señales contra-tendencia
    if tendencia == 'BAJA' and call_pts > put_pts:
        diferencia_original = call_pts - put_pts
        call_pts = int(call_pts * 0.5)  # Reducir señales CALL en tendencia bajista
        advertencias.append("⚠️ Señal CALL contra tendencia bajista - RIESGOSO")
    elif tendencia == 'SUBE' and put_pts > call_pts:
        put_pts = int(put_pts * 0.5)  # Reducir señales PUT en tendencia alcista
        advertencias.append("⚠️ Señal PUT contra tendencia alcista - RIESGOSO")
    
    # ==================== CALCULAR RESULTADO ====================
    diferencia = abs(call_pts - put_pts)
    total = call_pts + put_pts
    
    if call_pts > put_pts and diferencia >= 15:
        direccion = "CALL"
        probabilidad = min(55 + diferencia * 0.8, 92)
    elif put_pts > call_pts and diferencia >= 15:
        direccion = "PUT"
        probabilidad = min(55 + diferencia * 0.8, 92)
    else:
        direccion = "ESPERAR"
        probabilidad = 50
    
    # Fuerza
    if diferencia >= 50:
        fuerza = 5
    elif diferencia >= 40:
        fuerza = 4
    elif diferencia >= 30:
        fuerza = 3
    elif diferencia >= 20:
        fuerza = 2
    else:
        fuerza = 1
    
    # Momento
    if fuerza >= 4 and len(razones) >= 3:
        momento = "🔥 ENTRAR AHORA"
    elif fuerza >= 3:
        momento = "✅ BUENA ENTRADA"
    elif fuerza >= 2:
        momento = "⏳ ESPERAR CONFIRM."
    else:
        momento = "❌ NO OPERAR"
        direccion = "ESPERAR"
    
    return {
        'direccion': direccion,
        'probabilidad': probabilidad,
        'fuerza': fuerza,
        'momento': momento,
        'razones': razones,
        'advertencias': advertencias,
        'call_pts': call_pts,
        'put_pts': put_pts
    }


def mostrar_resultado(resultado: dict):
    """Muestra el resultado del análisis."""
    
    estrellas = "⭐" * resultado['fuerza'] + "☆" * (5 - resultado['fuerza'])
    
    print(f"\n{'═'*60}")
    print(f"  🎯 RESULTADO DEL ANÁLISIS")
    print(f"{'═'*60}")
    
    # Mostrar advertencias primero
    if resultado['advertencias']:
        print(f"\n  {'─'*55}")
        for adv in resultado['advertencias']:
            print(f"  {adv}")
        print(f"  {'─'*55}")
    
    # Señal principal
    if resultado['direccion'] == 'CALL':
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'🟢🟢🟢 CALL ↑ (SUBE) 🟢🟢🟢':^56}║")
        print(f"  ╚{'═'*56}╝")
    elif resultado['direccion'] == 'PUT':
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'🔴🔴🔴 PUT ↓ (BAJA) 🔴🔴🔴':^56}║")
        print(f"  ╚{'═'*56}╝")
    else:
        print(f"\n  ╔{'═'*56}╗")
        print(f"  ║{'⚪ ESPERAR - NO OPERAR ⚪':^56}║")
        print(f"  ╚{'═'*56}╝")
    
    print(f"\n  📊 Probabilidad: {resultado['probabilidad']:.0f}%")
    print(f"  💪 Fuerza:       {estrellas}")
    print(f"  🚦 Momento:      {resultado['momento']}")
    print(f"  📈 Puntos CALL:  {resultado['call_pts']}")
    print(f"  📉 Puntos PUT:   {resultado['put_pts']}")
    
    print(f"\n  {'─'*55}")
    print(f"  📋 RAZONES:")
    for r in resultado['razones']:
        print(f"     • {r}")
    
    # Recomendación de expiración
    print(f"\n  {'─'*55}")
    if resultado['fuerza'] >= 4:
        print(f"  ⏱️  EXPIRACIÓN RECOMENDADA: 1-3 minutos")
    elif resultado['fuerza'] >= 3:
        print(f"  ⏱️  EXPIRACIÓN RECOMENDADA: 3-5 minutos")
    else:
        print(f"  ⏱️  EXPIRACIÓN RECOMENDADA: 5+ minutos (o no operar)")
    
    print(f"{'═'*60}\n")


def modo_rapido():
    """Modo rápido con menos preguntas."""
    print("\n" + "🚀"*20)
    print("  MODO RÁPIDO")
    print("🚀"*20)
    
    print("\n  Solo los indicadores más importantes:")
    
    datos = {}
    
    # Tendencia
    print("\n  1️⃣  TENDENCIA (mira las últimas 5-10 velas)")
    datos['tendencia'] = obtener_opcion("     ¿El precio está subiendo, bajando o lateral?", 
                                        ['SUBE', 'BAJA', 'LATERAL'])
    
    # RSI
    print("\n  2️⃣  RSI")
    datos['rsi'] = obtener_float("     Valor del RSI (0-100, o Enter si no tienes): ", 0, 100)
    
    # Stochastic
    print("\n  3️⃣  STOCHASTIC")
    datos['stochastic'] = obtener_float("     Valor del Stochastic %K (0-100, o Enter si no tienes): ", 0, 100)
    if datos['stochastic'] is not None:
        datos['stoch_cruce'] = obtener_opcion("     ¿La línea %K cruzó a %D?", 
                                              ['ARRIBA', 'ABAJO', 'NO'])
    
    # Bollinger
    print("\n  4️⃣  BOLLINGER BANDS")
    print("     ¿Dónde está el precio respecto a las bandas?")
    datos['bollinger'] = obtener_opcion("     ", 
                                        ['SUPERIOR', 'CERCA_SUP', 'MEDIO', 'CERCA_INF', 'INFERIOR'])
    
    return datos


def modo_completo():
    """Modo completo con todos los indicadores."""
    print("\n" + "📊"*20)
    print("  MODO COMPLETO")
    print("📊"*20)
    
    datos = {}
    
    # ===== TENDENCIA =====
    print("\n  ═══ 1. TENDENCIA GENERAL ═══")
    print("  Mira las últimas 5-10 velas. ¿El precio general está...?")
    datos['tendencia'] = obtener_opcion("  ", ['SUBE', 'BAJA', 'LATERAL'])
    
    # ===== RSI =====
    print("\n  ═══ 2. RSI ═══")
    datos['rsi'] = obtener_float("  Valor del RSI (0-100): ", 0, 100)
    
    # ===== STOCHASTIC =====
    print("\n  ═══ 3. STOCHASTIC ═══")
    datos['stochastic'] = obtener_float("  Valor del %K (0-100): ", 0, 100)
    if datos['stochastic'] is not None:
        print("  ¿La línea rápida (%K) cruzó a la lenta (%D)?")
        datos['stoch_cruce'] = obtener_opcion("  ", ['ARRIBA', 'ABAJO', 'NO'])
    
    # ===== MACD =====
    print("\n  ═══ 4. MACD ═══")
    print("  ¿Qué muestra el MACD?")
    print("  - ARRIBA: La línea MACD acaba de cruzar hacia arriba la señal")
    print("  - ABAJO: La línea MACD acaba de cruzar hacia abajo la señal")
    print("  - POSITIVO: MACD está sobre la línea de señal")
    print("  - NEGATIVO: MACD está bajo la línea de señal")
    datos['macd'] = obtener_opcion("  ", ['ARRIBA', 'ABAJO', 'POSITIVO', 'NEGATIVO', 'NO_SE'])
    
    # ===== BOLLINGER =====
    print("\n  ═══ 5. BOLLINGER BANDS ═══")
    print("  ¿Dónde está el precio respecto a las bandas?")
    print("  - SUPERIOR: Tocando banda superior")
    print("  - CERCA_SUP: Cerca de banda superior")
    print("  - MEDIO: En el medio")
    print("  - CERCA_INF: Cerca de banda inferior")
    print("  - INFERIOR: Tocando banda inferior")
    datos['bollinger'] = obtener_opcion("  ", 
                                        ['SUPERIOR', 'CERCA_SUP', 'MEDIO', 'CERCA_INF', 'INFERIOR'])
    
    # ===== VELAS =====
    print("\n  ═══ 6. PATRÓN DE VELAS ═══")
    print("  ¿Ves alguno de estos patrones en las últimas velas?")
    print("  - MARTILLO: Cuerpo pequeño arriba, mecha larga abajo")
    print("  - ESTRELLA_FUGAZ: Cuerpo pequeño abajo, mecha larga arriba")
    print("  - ENVOLVENTE_ALC: Vela verde grande que cubre la roja anterior")
    print("  - ENVOLVENTE_BAJ: Vela roja grande que cubre la verde anterior")
    print("  - DOJI: Vela con cuerpo muy pequeño")
    print("  - NINGUNO: No veo patrón claro")
    datos['vela'] = obtener_opcion("  ", 
                                   ['MARTILLO', 'ESTRELLA_FUGAZ', 'ENVOLVENTE_ALC', 
                                    'ENVOLVENTE_BAJ', 'DOJI', 'NINGUNO'])
    
    # ===== MEDIA MÓVIL =====
    print("\n  ═══ 7. MEDIA MÓVIL ═══")
    print("  ¿El precio está arriba o abajo de la media móvil?")
    datos['precio_vs_ma'] = obtener_opcion("  ", ['ARRIBA', 'ABAJO', 'CRUZANDO'])
    
    return datos


def main():
    """Función principal."""
    
    print("\n" + "🎯"*25)
    print("  CALCULADORA DE SEÑALES BINARIAS OTC")
    print("  Ingresa los valores de Bullex")
    print("🎯"*25)
    
    while True:
        print("\n" + "─"*50)
        print("  ¿Qué modo quieres usar?")
        print("  1. RÁPIDO (4 indicadores principales)")
        print("  2. COMPLETO (todos los indicadores)")
        print("  3. SALIR")
        
        opcion = input("\n  Opción (1/2/3): ").strip()
        
        if opcion == '1':
            datos = modo_rapido()
            resultado = analizar_senal(datos)
            mostrar_resultado(resultado)
            
        elif opcion == '2':
            datos = modo_completo()
            resultado = analizar_senal(datos)
            mostrar_resultado(resultado)
            
        elif opcion == '3':
            print("\n  👋 ¡Éxito en tus trades!")
            break
        else:
            print("  ⚠️ Opción no válida")


if __name__ == '__main__':
    main()
