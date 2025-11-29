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

def bing_search_result(match_info, driver):
    """
    Sucht auf Bing nach dem Ergebnis.
    Bing ist oft "bot-freundlicher" als Google auf GitHub-Servern.
    """
    # 1. Suchbegriff reinigen
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].strip()
            # Versuch, den Liga-Namen am Ende abzuschneiden (alles nach dem zweiten Team)
            raw_team_b = parts[1]
            # Wir nehmen an, dass das Team-B nur aus den ersten 2-3 Worten besteht
            team_b_words = raw_team_b.split()[:2] 
            team_b = " ".join(team_b_words)
            
            query = f"{team_a} vs {team_b} score result"
        else:
            query = f"{match_info} result"
    except:
        query = f"{match_info} result"

    print(f"   -> SUCHE BEI BING: '{query}'")
    
    encoded_query = urllib.parse.quote(query)
    driver.get(f"https://www.bing.com/search?q={encoded_query}&setmkt=en-US&setlang=en")
    
    time.sleep(5) # Warten
    
    # 2. DEBUG: Was sieht der Bot?
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Wir drucken die ersten 200 Zeichen, um zu sehen, ob wir geblockt werden
        print(f"   [DEBUG] Seiten-Anfang: {body_text[:200].replace(chr(10), ' ')}...")
        
        # 3. Ergebnis suchen (Mustererkennung)
        # Suche nach "Oxford Utd 1 - 1 Ipswich" oder ähnlichem
        # Regex sucht nach: Zahl [Bindestrich/Doppelpunkt] Zahl
        # Wir suchen etwas aggressiver nach Ergebnissen
        matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', body_text)
        
        # Filter: Wir nehmen nur Ergebnisse, die plausibel sind (keine Jahreszahlen 20-25)
        # und nicht 0-0 (das ist oft Platzhalter vor dem Spiel, aber manchmal auch das Ergebnis)
        
        potenzielle_ergebnisse = []
        for m in matches:
            t1 = int(m[0])
            t2 = int(m[1])
            if t1 < 15 and t2 < 15: # Ein Fußballspiel endet selten 20:20
                potenzielle_ergebnisse.append(f"{t1}-{t2}")
        
        if potenzielle_ergebnisse:
            # Das erste gefundene Ergebnis bei Bing ist meistens das richtige (in der Info-Box oben)
            print(f"   -> MÖGLICHE TREFFER: {potenzielle_ergebnisse}")
            return potenzielle_ergebnisse[0]
            
    except Exception as e:
        print(f"   -> Fehler beim Lesen der Seite: {e}")
    
    return None

def check_results():
    print("--- START BING CHECKER (DEBUG MODE) ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Datenbank nicht gefunden.")
        return

    # Chrome starten
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Englisch als Sprache erzwingen (besser für "Score")
    chrome_options.add_argument("--lang=en-US")
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
            
            status = row[5]
            match_info = row[3]
            datum = row[0]
            
            # Wir prüfen nur Zeilen, die "Offen" sind
            if status == "Offen":
                print(f"------------------------------------------------")
                print(f"PRÜFE: {match_info} (Vom {datum})")
                
                ergebnis = bing_search_result(match_info, driver)
                
                if ergebnis:
                    print(f"   -> !!! TREFFER !!!: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Nichts gefunden. Bot sieht keine Zahlen.")
                
                time.sleep(3)

    finally:
        driver.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Update gespeichert.")
    else:
        print("Keine neuen Ergebnisse gefunden.")

if __name__ == "__main__":
    check_results()
