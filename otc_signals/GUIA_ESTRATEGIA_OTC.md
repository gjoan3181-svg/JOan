# 🎯 GUÍA DE ESTRATEGIA PARA BINARIAS OTC

## ⚠️ REGLA #1: SIEMPRE SIGUE LA TENDENCIA

```
📈 Tendencia SUBE  → Solo buscar CALL
📉 Tendencia BAJA  → Solo buscar PUT
↔️  Tendencia LATERAL → Buscar rebotes en extremos
```

---

## 🟢 CUÁNDO ENTRAR CALL (SUBE)

### ✅ Condiciones IDEALES para CALL:

| # | Indicador | Valor | ✓ |
|---|-----------|-------|---|
| 1 | **Tendencia** | Subiendo o Lateral | ☐ |
| 2 | **RSI** | Menor a 30 (sobreventa) | ☐ |
| 3 | **Stochastic** | Menor a 20 + cruce hacia arriba | ☐ |
| 4 | **Bollinger** | Precio tocando banda INFERIOR | ☐ |
| 5 | **MACD** | Cruzando hacia arriba | ☐ |
| 6 | **Vela** | Martillo o Envolvente alcista | ☐ |

### 🎯 Entrada CALL:
- **Mínimo 3 condiciones** deben cumplirse
- **NUNCA** entres CALL si la tendencia es BAJISTA FUERTE
- **Mejor señal**: RSI < 25 + Stoch cruce + Bollinger inferior

---

## 🔴 CUÁNDO ENTRAR PUT (BAJA)

### ✅ Condiciones IDEALES para PUT:

| # | Indicador | Valor | ✓ |
|---|-----------|-------|---|
| 1 | **Tendencia** | Bajando o Lateral | ☐ |
| 2 | **RSI** | Mayor a 70 (sobrecompra) | ☐ |
| 3 | **Stochastic** | Mayor a 80 + cruce hacia abajo | ☐ |
| 4 | **Bollinger** | Precio tocando banda SUPERIOR | ☐ |
| 5 | **MACD** | Cruzando hacia abajo | ☐ |
| 6 | **Vela** | Estrella fugaz o Envolvente bajista | ☐ |

### 🎯 Entrada PUT:
- **Mínimo 3 condiciones** deben cumplirse
- **NUNCA** entres PUT si la tendencia es ALCISTA FUERTE
- **Mejor señal**: RSI > 75 + Stoch cruce + Bollinger superior

---

## ❌ CUÁNDO NO OPERAR

1. **RSI entre 40-60** → Zona neutral, sin fuerza
2. **Stochastic entre 30-70** → Sin señal de extremo
3. **Precio en medio de Bollinger** → Sin rebote claro
4. **Vela Doji** → Mercado indeciso
5. **Tendencia no clara** → Esperar

---

## 📊 PATRONES DE VELAS IMPORTANTES

### 🟢 ALCISTAS (CALL):

```
MARTILLO                    ENVOLVENTE ALCISTA
    |                            ┃
   ┃|┃                          █┃█
    |                           █ ▀
    |                           █
 Mecha larga abajo          Verde cubre roja
```

### 🔴 BAJISTAS (PUT):

```
ESTRELLA FUGAZ              ENVOLVENTE BAJISTA
    |                            
    |                           █
   ┃|┃                          █ ▄
    |                           █┃█
                                 ┃
 Mecha larga arriba          Roja cubre verde
```

---

## ⏱️ TIEMPO DE EXPIRACIÓN

| Fuerza de Señal | Expiración |
|-----------------|------------|
| ⭐⭐⭐⭐⭐ (5 indicadores alineados) | 1-2 min |
| ⭐⭐⭐⭐ (4 indicadores) | 2-3 min |
| ⭐⭐⭐ (3 indicadores) | 3-5 min |
| ⭐⭐ (2 indicadores) | NO OPERAR |

---

## 📋 CHECKLIST RÁPIDO ANTES DE OPERAR

### Para CALL:
```
☐ ¿Tendencia NO es bajista fuerte?
☐ ¿RSI < 35?
☐ ¿Stochastic < 30 o cruzando arriba?
☐ ¿Precio cerca de Bollinger inferior?
☐ ¿Hay patrón de vela alcista?
→ Si tienes 3+ ✓ = CALL
```

### Para PUT:
```
☐ ¿Tendencia NO es alcista fuerte?
☐ ¿RSI > 65?
☐ ¿Stochastic > 70 o cruzando abajo?
☐ ¿Precio cerca de Bollinger superior?
☐ ¿Hay patrón de vela bajista?
→ Si tienes 3+ ✓ = PUT
```

---

## 💡 TIPS IMPORTANTES

1. **Espera el cierre de vela** antes de entrar
2. **No operes contra la tendencia** aunque los indicadores digan lo contrario
3. **Si dudas, NO OPERES** - Siempre habrá otra oportunidad
4. **Gestión de dinero**: Máximo 2-5% de tu cuenta por operación
5. **Después de 2 pérdidas seguidas**: Para y analiza qué salió mal

---

## 🔢 TABLA DE VALORES RSI

| RSI | Significado | Acción |
|-----|-------------|--------|
| 0-20 | MUY sobrevendido | CALL fuerte |
| 20-30 | Sobrevendido | CALL |
| 30-40 | Bajo | CALL débil |
| 40-60 | NEUTRAL | NO OPERAR |
| 60-70 | Alto | PUT débil |
| 70-80 | Sobrecomprado | PUT |
| 80-100 | MUY sobrecomprado | PUT fuerte |

---

## 🔢 TABLA DE VALORES STOCHASTIC

| %K | Significado | Acción |
|----|-------------|--------|
| 0-20 | Sobreventa + cruce arriba | CALL |
| 20-30 | Sobreventa | CALL si cruza |
| 30-70 | NEUTRAL | NO OPERAR |
| 70-80 | Sobrecompra | PUT si cruza |
| 80-100 | Sobrecompra + cruce abajo | PUT |

---

## 📱 USO DE LA CALCULADORA

```bash
cd /workspace/otc_signals
python3 calculadora_otc.py
```

1. Mira los indicadores en Bullex
2. Ingresa los valores en la calculadora
3. El script te dice CALL, PUT o ESPERAR
4. Solo opera si la fuerza es ⭐⭐⭐ o más

---

*Recuerda: La disciplina es más importante que la estrategia*
