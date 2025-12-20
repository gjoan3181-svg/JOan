import requests
from bs4 import BeautifulSoup
import sys

def get_latest_results():
    url = "https://www.conectate.com.do/loterias/leidsa/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching latest results: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find Loto section
    # Based on previous exploration: game-block containing "Loto - Loto Más"
    game_blocks = soup.find_all('div', class_='game-block')
    
    for block in game_blocks:
        text = block.get_text(strip=True)
        if "Loto - Loto Más" in text:
            # Extract numbers. 
            # The structure inside game-block usually has spans with class 'score' or similar, 
            # but my previous grep didn't show the structure clearly, just the text concatenation.
            # Let's try to find all 'span' with class 'ball' or similar if they exist.
            # In the stats page they were 'ball', here they might be different.
            # Let's rely on the text content if structured parsing fails, 
            # but usually they are in some container.
            
            # Re-inspecting the output from grep previously...
            # The grep output was cut off.
            # Let's try to be smart.
            
            # Let's assume the text contains the date and numbers.
            # "17-12Loto - Loto Más0102152934401212"
            # We can try to format this string if we can't parse HTML perfectly.
            
            return text
            
    return None

def get_hot_numbers():
    url = "https://www.conectate.com.do/loterias/leidsa/loto-mas/estadisticas"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    company_titles = soup.find_all('div', class_='company-title')
    target_block = None
    
    for title in company_titles:
        if "TOP 10 Loto - Loto Más" in title.get_text():
            company_block = title.parent
            game_block = company_block.find_next_sibling('div', class_='game-block')
            if game_block:
                target_block = game_block
                break
    
    if not target_block:
        return []

    stats = []
    rows = target_block.find_all('div', class_='d-flex align-items-center gap-3')
    
    for row in rows:
        ball = row.find('span', class_='ball')
        if ball:
            number = ball.get_text(strip=True)
            freq = row.get_text(strip=True).replace(number, '', 1).strip()
            stats.append((number, freq))
            
    return stats

def main():
    print("Fetching Leidsa Loto Data...\n")
    
    # Latest Results
    latest = get_latest_results()
    if latest:
        print("--- ÚLTIMOS RESULTADOS ---")
        # Format the text a bit if possible
        # Expected: "17-12Loto - Loto Más0102152934401212"
        # We can try to split by known name
        name = "Loto - Loto Más"
        if name in latest:
            parts = latest.split(name)
            date = parts[0]
            numbers_str = parts[1]
            
            # Assuming numbers are 2 digits each
            # Loto has 6 numbers + 2 extra?
            # 01 02 15 29 34 40 12 12
            # Length 16 characters -> 8 numbers
            
            nums = [numbers_str[i:i+2] for i in range(0, len(numbers_str), 2)]
            
            print(f"Fecha: {date}")
            print(f"Sorteo: {name}")
            if len(nums) >= 6:
                print(f"Números: {' - '.join(nums[:6])}")
            if len(nums) > 6:
                print(f"Más: {nums[6]}")
            if len(nums) > 7:
                print(f"Super Más: {nums[7]}")
        else:
            print(latest)
    else:
        print("No se pudieron obtener los últimos resultados.")
        
    print("\n")
    
    # Hot Numbers
    stats = get_hot_numbers()
    if stats:
        print("--- NÚMEROS CALIENTES (Últimos 60 días) ---")
        print(f"{'Número':<10} | {'Frecuencia'}")
        print("-" * 25)
        for num, freq in stats:
            print(f"{num:<10} | {freq}")
    else:
        print("No se pudieron obtener las estadísticas.")

if __name__ == "__main__":
    main()
