from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import csv
import re
import os
import time
import urllib.parse

DATEI_NAME = "meine_datenbank.csv"

def google_search_result(match_info, driver):
    """
    Sucht auf Google nach dem Ergebnis.
    """
    # Wir reinigen den Suchbegriff: Nur die Teams, ohne Liga-Namen (verwirrt Google oft)
    # Match Info ist z.B.: "Oxford Utd v Ipswich England Championship"
    # Wir schneiden alles nach " v " ab und nehmen die 2 Worte davor und danach
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].strip()
            team_b = parts[1].split("England")[0].strip() # Versuch Liga abzuschneiden
            query = f"{team_a} vs {team_b} score result"
        else:
            query = f"{match_info} score result"
    except:
        query = f"{match_info} score result"

    print(f"   -> Google Suche: '{query}'")
    
    # URL sicher kodieren
    encoded_query = urllib.parse.quote(query)
    driver.get(f"https://www.google.com/search?q={encoded_query}&hl=en")
    
    time.sleep(5) # Warten auf Ergebnisse
    
    try:
        # Wir suchen nach den typischen Google-Ergebnis-Boxen
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Regex Suche im ganzen Text nach "1-1" oder "2 : 0" oder "FT 1-1"
        # Wir suchen nach Zahlen, die nah beieinander stehen
        # Sucht nach Muster: Zahl Leerzeichen Bindestrich Leerzeichen Zahl
        match = re.search(r'\b(\d+)\s*[-:]\s*(\d+)\b', body_text)
        
        if match:
            # Sicherheitscheck: Ist das Ergebnis plausibel? (Nicht 2025-11)
            score = f"{match.group(1)}-{match.group(2)}"
            # Wenn die Zahlen zu groß sind (Jahreszahlen), ignorieren
            if int(match.group(1)) > 20 or int(match.group(2)) > 20:
                return None
            return score
            
    except Exception as e:
        print(f"   -> Fehler beim Lesen der Seite: {e}")
    
    return None

def check_results():
    print("--- START SELENIUM CHECKER ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Datenbank nicht gefunden.")
        return

    # Chrome starten
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Daten lesen
    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2:
        return

    daten = zeilen[1:]
    updates = False

    try:
        for row in daten:
            if len(row) < 6: continue
            
            # Spalte 5 ist Status, Spalte 3 ist Match Info
            status = row[5]
            match_info = row[3]
            
            if status == "Offen":
                print(f"Prüfe: {match_info}")
                ergebnis = google_search_result(match_info, driver)
                
                if ergebnis:
                    print(f"   -> GEFUNDEN: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Kein klares Ergebnis gefunden.")
                
                time.sleep(3) # Kurze Pause

    finally:
        driver.quit()

    # Speichern
    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Update gespeichert.")
    else:
        print("Keine neuen Ergebnisse.")

if __name__ == "__main__":
    check_results()
