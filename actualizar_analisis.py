#!/usr/bin/env python3
"""
Script para actualizar y analizar nuevos sorteos del Loto Leidsa
Uso: python3 actualizar_analisis.py
"""

import json
import sys
from datetime import datetime

def agregar_sorteo():
    """Permite agregar un nuevo sorteo manualmente"""
    print("=" * 60)
    print("🔄 ACTUALIZAR DATOS DEL LOTO LEIDSA")
    print("=" * 60)
    
    # Cargar datos existentes
    try:
        with open('/workspace/lottery_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No se encontró lottery_data.json")
        print("   Ejecuta primero: python3 leidsa_lottery_scraper.py")
        sys.exit(1)
    
    print(f"\n📊 Sorteos actuales en la base de datos: {len(data['historical_draws'])}")
    print("\n¿Deseas agregar un nuevo sorteo? (s/n)")
    
    respuesta = input("> ").strip().lower()
    
    if respuesta != 's':
        print("\nOperación cancelada.")
        return
    
    print("\n" + "-" * 60)
    print("Ingresa los 6 números del nuevo sorteo")
    print("(Números del 1 al 38, separados por espacios o comas)")
    print("-" * 60)
    
    while True:
        try:
            entrada = input("\nNúmeros: ").strip()
            # Permitir separación por espacios o comas
            numeros_str = entrada.replace(',', ' ').split()
            numeros = [int(n) for n in numeros_str]
            
            # Validar
            if len(numeros) != 6:
                print(f"❌ Error: Debes ingresar exactamente 6 números (ingresaste {len(numeros)})")
                continue
            
            if not all(1 <= n <= 38 for n in numeros):
                print("❌ Error: Los números deben estar entre 1 y 38")
                continue
            
            if len(numeros) != len(set(numeros)):
                print("❌ Error: No puedes repetir números")
                continue
            
            # Todo correcto
            break
            
        except ValueError:
            print("❌ Error: Ingresa solo números válidos")
            continue
    
    # Agregar el nuevo sorteo
    data['historical_draws'].append(sorted(numeros))
    data['date_updated'] = datetime.now().isoformat()
    
    # Guardar
    with open('/workspace/lottery_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Sorteo agregado exitosamente: {sorted(numeros)}")
    print(f"📊 Total de sorteos: {len(data['historical_draws'])}")
    
    print("\n" + "=" * 60)
    print("🔄 Regenerando análisis con los nuevos datos...")
    print("=" * 60)
    
    # Ejecutar análisis
    import subprocess
    try:
        subprocess.run(['python3', '/workspace/analyze_lottery.py'], check=True)
        print("\n✅ Análisis actualizado exitosamente!")
        print("\n📁 Archivos actualizados:")
        print("   • JUGADAS_HOY.txt")
        print("   • RESUMEN_NUMEROS_LOTO.txt")
        print("   • ANALISIS_LOTO_LEIDSA.md")
        print("   • analisis_loto_leidsa.json")
    except subprocess.CalledProcessError:
        print("\n⚠️  Hubo un error al regenerar el análisis")
        print("   Ejecuta manualmente: python3 analyze_lottery.py")

def mostrar_ultimo_sorteo():
    """Muestra el último sorteo registrado"""
    try:
        with open('/workspace/lottery_data.json', 'r') as f:
            data = json.load(f)
        
        ultimo = data['historical_draws'][-1]
        print("\n" + "=" * 60)
        print("📊 ÚLTIMO SORTEO REGISTRADO")
        print("=" * 60)
        print(f"\nNúmeros: {' - '.join(str(n).zfill(2) for n in ultimo)}")
        print(f"Total de sorteos en base de datos: {len(data['historical_draws'])}")
        
    except FileNotFoundError:
        print("❌ No se encontró la base de datos")
    except Exception as e:
        print(f"❌ Error: {e}")

def menu():
    """Menú principal"""
    print("\n" + "=" * 60)
    print("🎰 GESTOR DE DATOS - LOTO LEIDSA")
    print("=" * 60)
    print("\n1. Agregar nuevo sorteo")
    print("2. Ver último sorteo registrado")
    print("3. Regenerar análisis")
    print("4. Salir")
    print("\nElige una opción:")
    
    opcion = input("> ").strip()
    
    if opcion == '1':
        agregar_sorteo()
    elif opcion == '2':
        mostrar_ultimo_sorteo()
    elif opcion == '3':
        import subprocess
        print("\n🔄 Regenerando análisis...")
        subprocess.run(['python3', '/workspace/analyze_lottery.py'])
    elif opcion == '4':
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)
    else:
        print("\n❌ Opción inválida")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--ultimo':
        mostrar_ultimo_sorteo()
    else:
        while True:
            menu()
            input("\nPresiona Enter para continuar...")
