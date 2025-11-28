from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
import re # Modul für Mustererkennung
from datetime import datetime
import os

# --- KONFIGURATION ---
URL = "https://www.footballsuper.tips/football-accumulators-tips/football-tips-prediction-of-the-day/"
DATEI_NAME = "meine_datenbank.csv"

def parse_text(text):
    """
    Versucht, den Text in Einzelteile zu zerlegen.
    Format: "20:00 TippName in TeamA v TeamB LigaName Total Odd: 1.80"
    """
    daten = {
        "Uhrzeit": "N/A",
        "Tipp": "N/A",
        "Match": "N/A",
        "Quote": "N/A"
    }
    
    # 1. Uhrzeit finden (Startet meist damit)
    zeit_match = re.search(r'(\d{2}:\d{2})', text)
    if zeit_match:
        daten["Uhrzeit"] = zeit_match.group(1)
        
    # 2. Quote finden (Am Ende "Total Odd: 1.80")
    quote_match = re.search(r'Total Odd:\s*([\d\.]+)', text)
    if quote_match:
        daten["Quote"] = quote_match.group(1)

    # 3. Match finden (Alles zwischen " in " und der Liga ist schwer, 
    # daher nehmen wir alles zwischen " in " und "Total Odd", und versuchen " v " zu finden)
    if " in " in text and " v " in text:
        parts = text.split(" in ", 1) # Teile am ersten " in "
        rest = parts[1] # "Oxford Utd v Ipswich England Championship Total Odd: 1.80"
        
        # Schneide alles ab "Total Odd" weg
        match_part = rest.split("Total Odd")[0].strip()
        
        # Jetzt wird es knifflig: Die Liga steht hinter dem Match.
        # Wir machen es uns einfach: Wir speichern den Teil "Team v Team ... Liga" als Match-Info.
        daten["Match"] = match_part
        
        # Den Tipp isolieren (Alles vor dem " in ")
        # Aber die Uhrzeit muss weg (ersten 6 Zeichen ca)
        raw_tipp = parts[0]
        if len(raw_tipp) > 6:
            daten["Tipp"] = raw_tipp[6:].strip() # Schneidet "20:00 " ab
        else:
            daten["Tipp"] = raw_tipp

    return daten

def hol_daten():
    print("--- START STRUKTURIERTER SCRAPER ---")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(URL)
        time.sleep(8) 
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        datum = datetime.now().strftime("%Y-%m-%d")
        kandidaten = []

        # 1. Sammeln
        all_elements = soup.find_all(['div', 'p', 'li', 'span'])
        for element in all_elements:
            text = element.get_text(" ", strip=True)
            if "Odd:" in text and "Discover more" not in text and "Accumulator" not in text:
                if " v " in text or " vs " in text:
                    if len(text) < 200:
                        kandidaten.append(text)

        # 2. Auswählen & Zerlegen
        if kandidaten:
            kandidaten.sort(key=len)
            bester_treffer = kandidaten[0]
            print(f"Rohdaten: {bester_treffer}")
            
            # Hier passiert die Magie: Wir zerlegen den Text
            infos = parse_text(bester_treffer)
            
            # Speichern in separaten Spalten
            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Neue Kopfzeile!
                if not datei_existiert:
                    writer.writerow(["Datum", "Uhrzeit", "Tipp", "Match_Info", "Quote", "Status", "Rohdaten"])
                
                writer.writerow([
                    datum, 
                    infos["Uhrzeit"], 
                    infos["Tipp"], 
                    infos["Match"], 
                    infos["Quote"], 
                    "Offen", # <--- Das brauchen wir für den Ergebnis-Checker!
                    bester_treffer
                ])
                print("Strukturierter Eintrag gespeichert.")
        else:
            print("Nichts gefunden.")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
