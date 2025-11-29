from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import os
import time
import re
from datetime import datetime

DATEI_NAME = "meine_datenbank.csv"

def get_stealth_result(match_info, driver):
    """
    Nutzt DrissionPage (Stealth), um Google zu befragen.
    """
    # 1. Suchbegriff säubern
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].replace("Utd", "").strip()
            # Vom zweiten Team alles nach dem Namen abschneiden
            team_b_raw = parts[1]
            team_b = team_b_raw.split("England")[0].split("Germany")[0].strip().split()[0]
            
            # Suchanfrage: "Oxford Ipswich final score"
            query = f"{team_a} {team_b} final score"
        else:
            query = f"{match_info} score"
    except:
        query = match_info

    print(f"   -> Stealth-Suche: '{query}'")
    
    # Wir rufen DuckDuckGo auf (die HTML Version, die ist super schnell und blockt nicht)
    url = f"https://html.duckduckgo.com/html/?q={query}"
    
    driver.get(url)
    
    # Wir suchen im Ergebnis-Text
    # DuckDuckGo HTML liefert Ergebnisse in "result__snippet" Klassen
    
    # Wir holen den ganzen Text der Seite
    body_text = driver.ele('tag:body').text
    
    # Regex Suche nach Ergebnissen (1-1, 2:1, etc.)
    matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', body_text)
    
    best_match = None
    
    for m in matches:
        t1 = int(m[0])
        t2 = int(m[1])
        
        # Filter:
        # Datum (28-11, 20-25) rausfiltern
        if t1 > 15 or t2 > 15: continue
        
        # Uhrzeiten (19-30) rausfiltern
        if t1 > 10 and t2 > 10: continue
        
        # Das erste plausible Ergebnis ist meistens das richtige
        best_match = f"{t1}-{t2}"
        # Wir geben es sofort zurück
        return best_match
        
    return None

def check_results():
    print("--- START STEALTH CHECKER (DrissionPage) ---")
    
    if not os.path.isfile(DATEI_NAME): return

    # --- STEALTH SETUP ---
    # Das hier umgeht die Bot-Erkennung
    co = ChromiumOptions()
    co.set_argument('--headless=new') # Ohne Monitor
    co.set_argument('--no-sandbox')
    # Wir setzen einen echten User-Agent
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    # Browser starten
    page = ChromiumPage(co)

    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2: return
    
    updates = False
    daten = zeilen[1:]
    
    jetzt = datetime.now().strftime("%H:%M")

    try:
        for row in daten:
            if len(row) < 6: continue
            
            status = row[5]
            match_info = row[3]
            
            # Wir prüfen alles, was nicht "Beendet" ist
            if "Beendet" not in status:
                print(f"Prüfe: {match_info}")
                
                ergebnis = get_stealth_result(match_info, page)
                
                if ergebnis:
                    print(f"   -> TREFFER: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Nichts gefunden.")
                    # Wir aktualisieren den Status, damit wir sehen, dass es lief
                    row[5] = f"Offen (Stealth-Check {jetzt}: Nichts)"
                    updates = True
                
                time.sleep(2)

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        page.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Datenbank aktualisiert.")
    else:
        print("Keine Updates.")

if __name__ == "__main__":
    check_results()
