from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import csv
import re
import os
import time
import urllib.parse

DATEI_NAME = "meine_datenbank.csv"

def check_bing_titles(match_info, driver):
    """
    Sucht bei Bing und scannt NUR die Überschriften der Suchergebnisse.
    Das ist oft genauer, weil dort z.B. steht 'Oxford 1-1 Ipswich'.
    """
    # Wir bereinigen den Suchbegriff und fügen das Jahr hinzu
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].strip().replace("Utd", "").replace("FC", "").strip()
            # Vom zweiten Team nur das erste Wort
            team_b = parts[1].split("England")[0].strip().split()[0]
            # Suchanfrage: "Oxford Ipswich result November 2025"
            query = f"{team_a} vs {team_b} result November 2025"
        else:
            query = f"{match_info} result 2025"
    except:
        query = f"{match_info} result 2025"

    print(f"   -> Bing Suche: '{query}'")
    
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&setlang=en-US"
    driver.get(url)
    time.sleep(4)
    
    # JETZT DER TRICK: Wir holen uns alle Überschriften (h2 tags)
    try:
        titles = driver.find_elements(By.TAG_NAME, "h2")
        
        for title in titles:
            text = title.text
            # Wir prüfen, ob im Titel Zahlen im Format "1-1", "1:2", "2 - 1" vorkommen
            matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
            
            for m in matches:
                t1 = int(m[0])
                t2 = int(m[1])
                
                # Plausibilitäts-Check:
                # Fußballergebnisse sind selten zweistellig (außer Elfmeterschießen, das ignorieren wir erstmal)
                # Wir ignorieren Datum (28-11) oder Uhrzeit (19:00)
                if t1 < 10 and t2 < 10:
                    found = f"{t1}-{t2}"
                    print(f"   -> TREFFER im Titel ('{text}'): {found}")
                    return found
    except Exception as e:
        print(f"   -> Fehler beim Lesen der Titel: {e}")
        
    return None

def check_results():
    print("--- START TITLE SCANNER ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Keine Datenbank.")
        return

    # Tarnkappe an
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en-US")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2: return
    
    updates = False
    daten = zeilen[1:]

    try:
        for row in daten:
            if len(row) < 6: continue
            
            status = row[5]
            match_info = row[3]
            
            # Wir prüfen alles was "Offen" ist
            if "Offen" in status:
                print(f"-------------------")
                print(f"Prüfe: {match_info}")
                
                ergebnis = check_bing_titles(match_info, driver)
                
                if ergebnis:
                    print(f"   -> !!! ERGEBNIS GEFUNDEN !!!: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Kein Ergebnis in den Überschriften gefunden.")
                    # Wir markieren es als geprüft, aber lassen es offen
                    if "Geprüft" not in status:
                        row[5] = "Offen (Geprüft - Warten auf Ergebnis)"
                        updates = True
                
                time.sleep(2)

    finally:
        driver.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Datenbank erfolgreich aktualisiert.")
    else:
        print("Keine neuen Ergebnisse.")

if __name__ == "__main__":
    check_results()
