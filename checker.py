from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import re
import os
import time

DATEI_NAME = "meine_datenbank.csv"

def simplify_name(team_name):
    """
    Macht Teamnamen vergleichbar.
    Aus "Oxford Utd" wird "Oxford".
    Aus "Ipswich Town" wird "Ipswich".
    """
    # Entferne typische Füllwörter
    ignore = ["FC", "Utd", "United", "City", "Town", "Real", "AC", "Inter", "Sporting", "Club", "v", "CF"]
    
    parts = team_name.replace("Utd", "").split()
    
    # Wir nehmen das erste kräftige Wort
    for p in parts:
        clean = p.strip()
        if clean not in ignore and len(clean) > 2:
            return clean
            
    return parts[0] if parts else team_name

def check_skysports_archive(driver, datum, team_a, team_b):
    """
    Geht direkt ins Archiv von SkySports für das Datum.
    URL-Schema: https://www.skysports.com/football-results/2025-11-28
    """
    url = f"https://www.skysports.com/football-results/{datum}"
    print(f"   [SkySports] Prüfe Archiv: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        # Wir holen den ganzen Text der Seite
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text()
        
        # Vereinfache Namen für die Suche (z.B. "Oxford" und "Ipswich")
        simple_a = simplify_name(team_a)
        simple_b = simplify_name(team_b)
        
        print(f"   -> Suche nach '{simple_a}' und '{simple_b}'...")
        
        # Wir zerlegen die Seite in Zeilen und suchen die Zeile, wo beide Teams stehen
        lines = page_text.split('\n')
        for line in lines:
            if simple_a in line and simple_b in line:
                # Zeile gefunden! Jetzt Ergebnis extrahieren (z.B. "1-1" oder "1 1")
                # Suche nach zwei Zahlen
                match = re.search(r'(\d+)\s*[-:]\s*(\d+)', line)
                if match:
                    score = f"{match.group(1)}-{match.group(2)}"
                    return score
                
                # Manchmal stehen die Zahlen ohne Bindestrich: "Oxford 1 1 Ipswich"
                match_b = re.search(r'(\d+)\s+(\d+)', line)
                if match_b:
                    score = f"{match_b.group(1)}-{match_b.group(2)}"
                    return score
                    
    except Exception as e:
        print(f"   [Fehler] {e}")
        
    return None

def check_results():
    print("--- START ARCHIV CHECKER ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Keine Datenbank.")
        return

    # Chrome Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Daten lesen
    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2: return
    
    daten = zeilen[1:]
    updates = False

    try:
        for row in daten:
            if len(row) < 6: continue
            
            status = row[5]
            match_info = row[3] # "Oxford Utd v Ipswich..."
            datum = row[0]      # "2025-11-28"
            
            # WICHTIG: Wir prüfen nur, wenn Status "Offen" ist
            if "Offen" in status:
                print(f"------------------------------------------------")
                print(f"ANALYSING: {match_info} (Datum: {datum})")
                
                # Teams trennen
                if " v " in match_info:
                    parts = match_info.split(" v ")
                    team_a = parts[0]
                    # Den zweiten Teil säubern (Liga-Namen entfernen)
                    team_b_raw = parts[1]
                    # Wir schneiden alles ab, was nach England/Liga aussieht
                    team_b = team_b_raw.split("England")[0].strip()
                else:
                    print("   -> Formatfehler in Match-Info.")
                    continue

                # 1. VERSUCH: SkySports Archiv
                ergebnis = check_skysports_archive(driver, datum, team_a, team_b)

                if ergebnis:
                    print(f"   -> !!! TREFFER !!!: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Kein Ergebnis im Archiv gefunden.")
                    # Wir markieren es als geprüft, damit wir sehen, dass der Bot lief
                    row[5] = "Offen (Geprüft - Nichts gefunden)"
                    updates = True

                time.sleep(2)

    except Exception as e:
        print(f"KRITISCHER FEHLER: {e}")
    finally:
        driver.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Update gespeichert.")
    else:
        print("Keine Updates nötig.")

if __name__ == "__main__":
    check_results()
