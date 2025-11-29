from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import csv
import re
import os
import time
from datetime import datetime
import urllib.parse

DATEI_NAME = "meine_datenbank.csv"

def clean_team_name(name):
    """
    Entfernt alles, was die Suche verwirren könnte.
    """
    # Liste von Wörtern, die wir löschen
    blacklist = ["Utd", "United", "FC", "F.C.", "City", "Town", "Rovers", "County", "Athletic", "Real", "Sporting"]
    
    parts = name.split()
    clean_parts = [p for p in parts if p not in blacklist]
    
    # Wenn nach dem Löschen nichts übrig bleibt, nehmen wir das Original
    if not clean_parts:
        return name
        
    # Wir nehmen nur das erste Wort, das ist meistens der Hauptname (z.B. "Oxford", "Ipswich")
    return clean_parts[0]

def google_search_score(match_info, driver):
    """
    Googelt aggressiv nach dem Ergebnis.
    """
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = clean_team_name(parts[0])
            # Beim zweiten Team schneiden wir Liganamen ab
            raw_b = parts[1].split("England")[0].split("Germany")[0].split("Italy")[0]
            team_b = clean_team_name(raw_b)
            
            # Suchanfrage: "Oxford Ipswich score"
            query = f"{team_a} {team_b} score"
        else:
            query = f"{match_info} score"
    except:
        query = match_info

    print(f"   -> Google Suche: '{query}'")
    
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en"
    driver.get(url)
    time.sleep(4)
    
    # Wir suchen im gesamten Text der Google-Seite nach einem Ergebnis-Muster
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        
        # Muster: Eine kleine Zahl, Trennzeichen, eine kleine Zahl
        # Wir filtern Jahreszahlen und Uhrzeiten raus
        matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', body)
        
        for m in matches:
            t1 = int(m[0])
            t2 = int(m[1])
            
            # Plausibilität: Fußballergebnisse sind < 10 (meistens)
            # Datum (2025) oder Uhrzeit (19:00) sind > 10
            if t1 < 10 and t2 < 10:
                found = f"{t1}-{t2}"
                print(f"   -> TREFFER im Text: {found}")
                return found
    except Exception as e:
        print(f"   -> Lesefehler: {e}")

    return None

def check_results():
    print("--- START AGGRESSIVE CHECKER ---")
    
    if not os.path.isfile(DATEI_NAME): return

    # Maximale Tarnung
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    zeilen = []
    # Datei lesen
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
            
            # Wir fassen alles an, was nicht "Beendet" ist
            if "Beendet" not in status:
                print(f"Prüfe: {match_info}")
                
                ergebnis = google_search_score(match_info, driver)
                
                if ergebnis:
                    print(f"   -> GEWONNEN: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Nichts gefunden.")
                    # WICHTIG: Wir ändern den Status trotzdem, um zu beweisen, dass wir schreiben können!
                    row[5] = f"Offen (Geprüft um {jetzt}: Nichts)"
                    updates = True
                
                time.sleep(3) # Wartezeit für Google
    finally:
        driver.quit()

    if updates:
        # Schreiben erzwingen
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Update in CSV geschrieben.")
    else:
        print("Keine Updates nötig.")

if __name__ == "__main__":
    check_results()
