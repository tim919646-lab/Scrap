from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import re
import os
import time
from datetime import datetime, timedelta

DATEI_NAME = "meine_datenbank.csv"

def get_bulk_results_for_date(driver, datum_str):
    """
    Lädt ALLE Ergebnisse eines Tages von SkySports.
    Gibt den kompletten Text der Seite zurück.
    """
    # URL Format: https://www.skysports.com/football-results/2025-11-28
    url = f"https://www.skysports.com/football-results/{datum_str}"
    print(f"   [BULK-LOAD] Lade alle Ergebnisse vom {datum_str}...")
    
    driver.get(url)
    time.sleep(3)
    
    # Wir holen den ganzen Text, aber bereinigt
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # SkySports packt Ergebnisse in Container. Wir holen alles Textartige.
    text_content = soup.get_text(" ", strip=True)
    return text_content

def find_score_in_bulk(bulk_text, team_a, team_b):
    """
    Sucht im riesigen Textblock nach den beiden Teams und dem Ergebnis.
    """
    # Vereinfachung der Namen für die Suche
    # Wir nehmen nur den Kern-Namen (z.B. "Oxford" statt "Oxford Utd")
    core_a = team_a.replace("Utd", "").replace("United", "").replace("FC", "").strip().split()[0]
    core_b = team_b.replace("Utd", "").replace("United", "").replace("FC", "").strip().split()[0]
    
    # Wir suchen nach einem Muster: TeamA ... Zahl ... Zahl ... TeamB (oder umgekehrt)
    # Da im Bulk-Text viel Müll steht, suchen wir nach den Namen in der Nähe zueinander.
    
    # Wir splitten den Text in grobe Happen (z.B. an "Match Report" oder Uhrzeiten)
    parts = bulk_text.split("Match Report")
    
    for part in parts:
        if core_a in part and core_b in part:
            # Beide Teams sind in diesem Abschnitt! Das ist unser Match.
            # Jetzt suchen wir nach dem Ergebnis in diesem Abschnitt.
            
            # Suche nach Muster "1-1" oder "2 1" oder "0:0"
            matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', part)
            for m in matches:
                t1 = int(m[0])
                t2 = int(m[1])
                if t1 < 15 and t2 < 15: # Plausibilität
                    return f"{t1}-{t2}"
            
            # Manchmal stehen die Tore direkt bei den Namen: "Oxford 1 Ipswich 1"
            # Das ist komplexer, aber der Regex oben fängt das meiste ab.
            
    return None

def is_recent(datum_str):
    """
    Prüft, ob das Datum heute, gestern oder vorgestern war.
    Ältere Spiele prüfen wir nicht mehr (Effizienz!).
    """
    try:
        match_date = datetime.strptime(datum_str, "%Y-%m-%d")
        heute = datetime.now()
        delta = heute - match_date
        # Wir prüfen alles, was jünger als 3 Tage ist oder in der Zukunft liegt
        return delta.days <= 3
    except:
        return True # Im Zweifel prüfen

def check_results():
    print("--- START BULK CHECKER (EFFIZIENT) ---")
    
    if not os.path.isfile(DATEI_NAME): return

    # Chrome Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2: return
    
    daten = zeilen[1:]
    updates = False
    
    # Cache für die Webseiten (damit wir SkySports nicht 10x für denselben Tag laden)
    daily_cache = {} 

    try:
        for row in daten:
            if len(row) < 6: continue
            
            status = row[5]
            datum = row[0]
            match_info = row[3]
            
            # EFFIZIENZ-CHECK 1: Ist das Spiel schon beendet?
            if "Beendet" in status:
                continue
                
            # EFFIZIENZ-CHECK 2: Ist das Datum relevant? (Heute/Gestern)
            if not is_recent(datum):
                print(f"Überspringe altes Spiel: {match_info} ({datum})")
                continue

            print(f"Prüfe: {match_info} ({datum})")
            
            # 1. Haben wir die Ergebnisse für diesen Tag schon geladen?
            if datum not in daily_cache:
                daily_cache[datum] = get_bulk_results_for_date(driver, datum)
            
            # 2. Teams extrahieren
            if " v " in match_info:
                parts = match_info.split(" v ")
                team_a = parts[0]
                team_b = parts[1].split("England")[0].strip() # Liga abschneiden
            else:
                continue

            # 3. Im Speicher suchen
            ergebnis = find_score_in_bulk(daily_cache[datum], team_a, team_b)
            
            if ergebnis:
                print(f"   -> TREFFER: {ergebnis}")
                row[5] = f"Beendet ({ergebnis})"
                updates = True
            else:
                print("   -> Noch kein Ergebnis im Tages-Bericht.")
                # Wir updaten den Status nur, wenn er noch ganz frisch ist
                if status == "Offen":
                    row[5] = "Offen (Geprüft)"
                    updates = True

    finally:
        driver.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Gespeichert.")
    else:
        print("Keine Updates.")

if __name__ == "__main__":
    check_results()
