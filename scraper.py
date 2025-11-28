from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import os

# --- KONFIGURATION ---
URL = "https://www.footballsuper.tips/football-accumulators-tips/football-tips-prediction-of-the-day/"
DATEI_NAME = "meine_datenbank.csv"

def hol_daten():
    print("--- START SELENIUM SCRAPER ---")

    # 1. Chrome Setup (Headless = ohne Monitor)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Wir tarnen uns als normaler Windows-PC
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Öffne Seite: {URL}")
        driver.get(URL)
        
        # WICHTIG: Wir warten 10 Sekunden, damit die Seite komplett lädt
        print("Warte 10 Sekunden auf Ladevorgang...")
        time.sleep(10)

        # Holen des fertigen HTML-Codes
        page_source = driver.page_source
        
        # Jetzt übergeben wir das an BeautifulSoup zum Analysieren
        soup = BeautifulSoup(page_source, 'html.parser')
        
        daten_heute = []
        datum = datetime.now().strftime("%Y-%m-%d")

        # Suche nach allen Text-Elementen
        print("Analysiere Inhalte...")
        all_elements = soup.find_all(['p', 'li', 'div', 'span'])
        
        gefunden_count = 0
        
        for element in all_elements:
            text = element.get_text(" ", strip=True)
            
            # --- FILTER LOGIK ---
            # Wir suchen nach dem Wort "Odd" oder typischen Tipp-Strukturen
            if "Odd:" in text or "Total Odd" in text:
                # Duplikate vermeiden (manche Texte kommen doppelt vor im HTML)
                is_duplicate = any(text in entry for entry in daten_heute)
                
                # Wir nehmen nur Texte mit vernünftiger Länge
                if len(text) > 15 and len(text) < 400 and not is_duplicate:
                    print(f"TREFFER: {text[:60]}...")
                    daten_heute.append([datum, text])
                    gefunden_count += 1

        # Speichern
        if gefunden_count > 0:
            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not datei_existiert:
                    writer.writerow(["Datum", "Tipp_Inhalt"])
                
                for eintrag in daten_heute:
                    writer.writerow(eintrag)
            print(f"ERFOLG: {gefunden_count} Tipps gespeichert.")
        else:
            print("WARNUNG: Seite geladen, aber keine Tipps mit 'Odd:' gefunden. Prüfe Log.")
            # Debugging: Zeige uns einen Teil des HTMLs, falls es scheitert
            print("Seitenausschnitt:", soup.get_text()[:500])

    except Exception as e:
        print(f"KRITISCHER FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
