from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import os
import random

# --- KONFIGURATION ---
# Wir nehmen die Basis-URL, damit der Token nicht abläuft
URL = "https://betmines.com/de/empfohlene-wetten-fussball"
DATEI_NAME = "betmines.csv"

def hol_daten():
    print("--- START BETMINES SCRAPER ---")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Ein sehr gängiger User-Agent (Windows 10, Chrome)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Lade Seite: {URL}")
        driver.get(URL)
        
        # WICHTIG: BetMines hat Cloudflare. Wir müssen "Menschlichkeit" simulieren.
        # Wir warten länger (15 Sekunden).
        print("Warte auf Cloudflare-Check (15s)...")
        time.sleep(15)

        # Wir scrollen ein bisschen runter, um Inhalte zu laden
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        datum = datetime.now().strftime("%Y-%m-%d")
        funde = []

        # Analyse der BetMines Struktur
        # BetMines nutzt oft "Cards" für die Spiele. Wir suchen Textblöcke.
        print("Analysiere HTML...")
        
        # Wir suchen nach Elementen, die nach Spiel aussehen.
        # BetMines hat oft Teams und Quoten in DIVs.
        all_elements = soup.find_all(['div', 'li'])
        
        seen_texts = set()

        for element in all_elements:
            text = element.get_text(" ", strip=True)
            
            # Wir filtern: Text muss eine Quote enthalten (Dezimalzahl) 
            # und lang genug sein für Teams.
            # BetMines zeigt oft das Datum an, z.B. "29.11" oder Uhrzeiten
            if len(text) > 20 and len(text) < 300:
                # Suche nach typischen Merkmalen
                # Enthält es eine Uhrzeit? (XX:XX)
                if ":" in text and ("Quote" in text or "." in text):
                    
                    # Grober Filter gegen Menü-Texte
                    if "Anmelden" in text or "Registrieren" in text or "Cookie" in text:
                        continue

                    # Wir nehmen an, dass es ein Spiel ist, wenn zwei Teams (vs, -) da sind
                    # BetMines nutzt oft Zeilenumbrüche. Wir speichern erstmal interessante Blöcke.
                    if text not in seen_texts:
                        # Wir speichern nur Blöcke, die "fett" genug sind (Teams + Quote)
                        funde.append(text)
                        seen_texts.add(text)

        # Sortieren und Speichern
        # Da BetMines viele Spiele anzeigt, nehmen wir die Top 5 der längsten/detailliertesten Funde,
        # um sicherzugehen, dass wir die "Wettscheine" erwischen.
        
        if funde:
            # Wir sortieren so, dass wir nicht die winzigen Schnipsel haben
            # BetMines Karten enthalten meist viele Infos -> Längerer Text ist oft besser
            funde.sort(key=len, reverse=True)
            
            # Wir nehmen die Top 10 Kandidaten, um sicher zu sein
            top_funde = funde[:10]

            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not datei_existiert:
                    writer.writerow(["Datum", "Rohdaten_BetMines"])
                
                print(f"{len(top_funde)} potenzielle Wetten gefunden.")
                for item in top_funde:
                    # Bereinigung: Doppelte Leerzeichen weg
                    clean_item = " ".join(item.split())
                    writer.writerow([datum, clean_item])
                    print(f"Gespeichert: {clean_item[:50]}...")
        else:
            print("Keine Daten gefunden. Cloudflare hat uns vielleicht blockiert oder Struktur geändert.")
            # Debugging
            print("Seitentitel:", driver.title)

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
