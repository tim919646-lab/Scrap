from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime
import os

# --- KONFIGURATION ---
URL = "https://www.footballsuper.tips/football-accumulators-tips/football-tips-prediction-of-the-day/"
DATEI_NAME = "meine_datenbank.csv"

def parse_text(text):
    """
    Intelligente Zerlegung.
    Funktioniert mit: "20:00 Tipp in Match..." UND "Tipp in Match..."
    """
    daten = {
        "Uhrzeit": "N/A",
        "Tipp": "N/A",
        "Match": "N/A",
        "Quote": "N/A"
    }
    
    # 1. Quote finden (Am Ende "Total Odd: 1.80")
    quote_match = re.search(r'Odd:?\s*([\d\.]+)', text, re.IGNORECASE)
    if quote_match:
        daten["Quote"] = quote_match.group(1)

    # 2. Aufsplitten am Wort " in "
    if " in " in text:
        parts = text.split(" in ", 1)
        linker_teil = parts[0].strip() # Hier steht Tipp (und evtl Uhrzeit)
        rechter_teil = parts[1].strip() # Hier steht Match und Quote
        
        # A) Match isolieren (alles vor "Total Odd" oder "Odd")
        match_raw = re.split(r'Total Odd|Odd:', rechter_teil, flags=re.IGNORECASE)[0]
        daten["Match"] = match_raw.strip()
        
        # B) Uhrzeit und Tipp trennen
        # Prüfen, ob der linke Teil mit einer Uhrzeit beginnt (z.B. "20:00 ")
        zeit_match = re.match(r'^(\d{2}:\d{2})', linker_teil)
        
        if zeit_match:
            daten["Uhrzeit"] = zeit_match.group(1)
            # Uhrzeit aus dem Tipp entfernen
            daten["Tipp"] = linker_teil.replace(zeit_match.group(1), "").strip()
        else:
            # Keine Uhrzeit gefunden -> Der ganze linke Teil ist der Tipp
            daten["Tipp"] = linker_teil

    return daten

def hol_daten():
    print("--- START FIX SCRAPER ---")

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

        all_elements = soup.find_all(['div', 'p', 'li', 'span'])
        for element in all_elements:
            text = element.get_text(" ", strip=True)
            if "Odd:" in text and "Discover more" not in text:
                if " v " in text or " vs " in text:
                    if len(text) < 200:
                        kandidaten.append(text)

        if kandidaten:
            kandidaten.sort(key=len)
            bester_treffer = kandidaten[0]
            print(f"Rohdaten: {bester_treffer}")
            
            infos = parse_text(bester_treffer)
            
            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not datei_existiert:
                    writer.writerow(["Datum", "Uhrzeit", "Tipp", "Match_Info", "Quote", "Status", "Rohdaten"])
                
                writer.writerow([
                    datum, 
                    infos["Uhrzeit"], 
                    infos["Tipp"], 
                    infos["Match"], 
                    infos["Quote"], 
                    "Offen", 
                    bester_treffer
                ])
                print("Gespeichert.")
        else:
            print("Nichts gefunden.")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
