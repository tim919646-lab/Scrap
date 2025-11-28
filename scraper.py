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
    print("--- START INTELLIGENT SCRAPER ---")

    # Chrome Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Lade Seite: {URL}")
        driver.get(URL)
        time.sleep(8) # Kurze Wartezeit für Page-Load

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        datum = datetime.now().strftime("%Y-%m-%d")
        kandidaten = []

        # 1. Alles sammeln
        all_elements = soup.find_all(['div', 'p', 'li', 'span', 'h2', 'h3'])
        
        for element in all_elements:
            text = element.get_text(" ", strip=True)
            
            # Muss "Odd:" enthalten
            if "Odd:" in text:
                # 2. Müll-Filter: Wenn diese Wörter vorkommen, ist es wahrscheinlich ein Container mit Werbung
                if "Discover more" in text or "Football kits" in text or "Accumulator Today" in text:
                    continue
                
                # Wir wollen nur Texte, die auch das Match (" v " oder " vs ") enthalten
                # Damit filtern wir reine Quoten ohne Spielpaarung raus
                if " v " in text or " vs " in text:
                    if len(text) < 200: # Zu lange Texte sind meist Müll
                        kandidaten.append(text)

        # 3. Der Auswahl-Algorithmus
        if kandidaten:
            # Wir sortieren nach Länge. Der kürzeste Text ist meist der sauberste (ohne Menüs drumherum).
            kandidaten.sort(key=len)
            bester_treffer = kandidaten[0]
            
            print(f"Gewinner-Text: {bester_treffer}")

            # Speichern
            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not datei_existiert:
                    writer.writerow(["Datum", "Tipp"])
                
                # Wir schreiben nur diesen EINEN besten Treffer
                writer.writerow([datum, bester_treffer])
                print("Eintrag gespeichert.")
        else:
            print("Kein sauberer Tipp gefunden (Filter zu streng oder Seite leer).")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
