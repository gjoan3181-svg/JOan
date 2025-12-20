#!/usr/bin/env python3
"""
Análisis estadístico del Loto de Leidsa
"""

import json
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime

def load_data():
    """Carga los datos de lotería"""
    with open('/workspace/lottery_data.json', 'r') as f:
        return json.load(f)

def analyze_frequency(draws):
    """Analiza la frecuencia de aparición de cada número"""
    all_numbers = []
    for draw in draws:
        all_numbers.extend(draw)
    
    frequency = Counter(all_numbers)
    return frequency

def calculate_statistics(draws):
    """Calcula estadísticas detalladas"""
    all_numbers = []
    for draw in draws:
        all_numbers.extend(draw)
    
    frequency = Counter(all_numbers)
    
    # Números más frecuentes
    most_common = frequency.most_common(15)
    
    # Números menos frecuentes
    least_common = frequency.most_common()[:-16:-1]
    
    # Números "calientes" (más frecuentes en últimos 10 sorteos)
    recent_numbers = []
    for draw in draws[-10:]:
        recent_numbers.extend(draw)
    hot_numbers = Counter(recent_numbers).most_common(10)
    
    # Números "fríos" (menos frecuentes)
    cold_numbers = [num for num, count in frequency.most_common()[::-1][:10]]
    
    # Pares e impares
    pairs = [num for num in all_numbers if num % 2 == 0]
    odds = [num for num in all_numbers if num % 2 != 0]
    
    return {
        'most_common': most_common,
        'least_common': least_common,
        'hot_numbers': hot_numbers,
        'cold_numbers': cold_numbers,
        'pair_percentage': (len(pairs) / len(all_numbers)) * 100,
        'odd_percentage': (len(odds) / len(all_numbers)) * 100,
        'total_draws': len(draws),
        'total_numbers': len(all_numbers)
    }

def generate_recommendations(stats):
    """Genera recomendaciones de números basadas en estadísticas"""
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS ESTADÍSTICO DEL LOTO LEIDSA")
    print("=" * 60)
    
    print(f"\n📈 Total de sorteos analizados: {stats['total_draws']}")
    print(f"📈 Total de números extraídos: {stats['total_numbers']}")
    
    print("\n🔥 NÚMEROS MÁS FRECUENTES (Histórico):")
    print("-" * 60)
    for i, (num, count) in enumerate(stats['most_common'][:15], 1):
        percentage = (count / stats['total_draws']) * 100
        bar = "█" * int(percentage * 2)
        print(f"{i:2}. Número {num:2} | Apariciones: {count:3} | {percentage:5.1f}% {bar}")
    
    print("\n🌟 NÚMEROS 'CALIENTES' (Últimos sorteos):")
    print("-" * 60)
    for i, (num, count) in enumerate(stats['hot_numbers'][:10], 1):
        print(f"{i:2}. Número {num:2} | Apariciones recientes: {count}")
    
    print("\n❄️  NÚMEROS 'FRÍOS' (Menos frecuentes):")
    print("-" * 60)
    cold_display = ", ".join(map(str, stats['cold_numbers'][:10]))
    print(f"   {cold_display}")
    
    print("\n⚖️  DISTRIBUCIÓN PAR/IMPAR:")
    print("-" * 60)
    print(f"   Números PARES:   {stats['pair_percentage']:.1f}% {'█' * int(stats['pair_percentage']/2)}")
    print(f"   Números IMPARES: {stats['odd_percentage']:.1f}% {'█' * int(stats['odd_percentage']/2)}")
    
    print("\n🎯 COMBINACIONES RECOMENDADAS:")
    print("=" * 60)
    
    # Generar combinaciones balanceadas
    top_numbers = [num for num, _ in stats['most_common'][:20]]
    hot_nums = [num for num, _ in stats['hot_numbers'][:10]]
    
    # Combinación 1: Basada en frecuencia histórica
    combo1 = sorted([num for num, _ in stats['most_common'][:6]])
    
    # Combinación 2: Mix de calientes y frecuentes
    combo2_nums = list(set(hot_nums[:3] + top_numbers[:8]))[:6]
    combo2 = sorted(combo2_nums)
    
    # Combinación 3: Balanceada (pares e impares)
    pairs = [num for num, _ in stats['most_common'] if num % 2 == 0][:3]
    odds = [num for num, _ in stats['most_common'] if num % 2 != 0][:3]
    combo3 = sorted(pairs + odds)
    
    # Combinación 4: Números dispersos
    combo4 = sorted([num for num, _ in stats['most_common'][::3]][:6])
    
    # Combinación 5: Mix estratégico
    combo5_nums = (
        [stats['hot_numbers'][0][0]] +  # 1 número caliente
        [num for num, _ in stats['most_common'][1:4]] +  # 3 muy frecuentes
        [num for num, _ in stats['most_common'][10:12]]  # 2 moderadamente frecuentes
    )
    combo5 = sorted(combo5_nums)
    
    combinations = [
        ("Máxima Frecuencia", combo1, "Basada en los números que más han salido históricamente"),
        ("Números Calientes", combo2, "Combinación de números recientes y frecuentes"),
        ("Balanceada Par/Impar", combo3, "Equilibrio entre números pares e impares"),
        ("Dispersión Alta", combo4, "Números distribuidos en todo el rango"),
        ("Estrategia Mixta", combo5, "Combina tendencias calientes y frecuencia")
    ]
    
    for i, (name, combo, description) in enumerate(combinations, 1):
        print(f"\n🎲 Combinación {i}: {name}")
        print(f"   {description}")
        print(f"   Números: {' - '.join(str(n).zfill(2) for n in combo)}")
        print(f"   Formato: [{', '.join(str(n) for n in combo)}]")
    
    print("\n" + "=" * 60)
    print("💡 CONSEJOS ADICIONALES:")
    print("=" * 60)
    print("""
1. 🎯 El Loto Leidsa sortea 6 números del 1 al 38
2. 📊 Las estadísticas muestran tendencias, no garantizan resultados
3. 🔄 Los números calientes tienen alta actividad reciente
4. ⚖️  Una buena combinación suele tener 3 pares y 3 impares
5. 📈 Considera mezclar números frecuentes con menos frecuentes
6. 🎲 La lotería es aleatoria - juega responsablemente
7. 💰 No gastes más de lo que puedes permitirte perder
8. 🔍 Revisa los resultados oficiales en www.leidsa.com
    """)
    
    print("=" * 60)
    print("🍀 ¡BUENA SUERTE! 🍀")
    print("=" * 60)
    
    return combinations

def save_report(stats, combinations):
    """Guarda un reporte detallado"""
    report = {
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'estadisticas': stats,
        'combinaciones_recomendadas': [
            {
                'nombre': name,
                'numeros': combo,
                'descripcion': desc
            }
            for name, combo, desc in combinations
        ]
    }
    
    with open('/workspace/analisis_loto_leidsa.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte guardado en: analisis_loto_leidsa.json")

def create_markdown_report(stats, combinations):
    """Crea un reporte en formato Markdown"""
    report = f"""# 🎰 Análisis Estadístico del Loto Leidsa
## República Dominicana

**Fecha de análisis:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

---

## 📊 Resumen Estadístico

- **Total de sorteos analizados:** {stats['total_draws']}
- **Total de números extraídos:** {stats['total_numbers']}
- **Distribución Par/Impar:** {stats['pair_percentage']:.1f}% pares / {stats['odd_percentage']:.1f}% impares

---

## 🔥 Top 15 Números Más Frecuentes

| Posición | Número | Apariciones | Porcentaje |
|----------|--------|-------------|------------|
"""
    
    for i, (num, count) in enumerate(stats['most_common'][:15], 1):
        percentage = (count / stats['total_draws']) * 100
        report += f"| {i} | **{num}** | {count} | {percentage:.1f}% |\n"
    
    report += "\n---\n\n## 🌟 Números Calientes (Últimos sorteos)\n\n"
    hot_list = ", ".join([f"**{num}** ({count}x)" for num, count in stats['hot_numbers'][:10]])
    report += f"{hot_list}\n"
    
    report += "\n---\n\n## ❄️ Números Fríos (Menos frecuentes)\n\n"
    cold_list = ", ".join([f"{num}" for num in stats['cold_numbers'][:10]])
    report += f"{cold_list}\n"
    
    report += "\n---\n\n## 🎯 Combinaciones Recomendadas\n\n"
    
    for i, (name, combo, description) in enumerate(combinations, 1):
        report += f"### 🎲 Combinación {i}: {name}\n\n"
        report += f"**Descripción:** {description}\n\n"
        report += f"**Números:** {' - '.join(str(n).zfill(2) for n in combo)}\n\n"
        report += f"```\n[{', '.join(str(n) for n in combo)}]\n```\n\n"
    
    report += """---

## 💡 Consejos para Jugar

1. 🎯 **Formato del juego:** El Loto Leidsa sortea 6 números del 1 al 38
2. 📊 **Sobre las estadísticas:** Muestran tendencias históricas, no garantizan resultados futuros
3. 🔥 **Números calientes:** Han aparecido frecuentemente en sorteos recientes
4. ❄️ **Números fríos:** Han aparecido menos, pero podrían "despertar"
5. ⚖️ **Balance:** Una buena combinación suele tener 3 números pares y 3 impares
6. 📈 **Diversificación:** Mezcla números muy frecuentes con moderadamente frecuentes
7. 🎲 **Aleatoriedad:** La lotería es un juego de azar - juega responsablemente
8. 💰 **Presupuesto:** No gastes más de lo que puedes permitirte perder
9. 🔍 **Verificación:** Siempre revisa los resultados oficiales en [www.leidsa.com](https://www.leidsa.com)

---

## 📝 Nota Importante

Este análisis se basa en datos históricos y patrones estadísticos. Los sorteos de lotería son eventos aleatorios e independientes. Cada número tiene la misma probabilidad de salir en cada sorteo, independientemente de su historial.

**¡Juega con responsabilidad y buena suerte! 🍀**

---

*Generado automáticamente - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open('/workspace/ANALISIS_LOTO_LEIDSA.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Reporte en Markdown guardado en: ANALISIS_LOTO_LEIDSA.md")

if __name__ == "__main__":
    # Cargar datos
    data = load_data()
    draws = data['historical_draws']
    
    # Analizar
    stats = calculate_statistics(draws)
    
    # Generar recomendaciones
    combinations = generate_recommendations(stats)
    
    # Guardar reportes
    save_report(stats, combinations)
    create_markdown_report(stats, combinations)
