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
URL = "https://betmines.com/de/empfohlene-wetten-fussball"
DATEI_NAME = "betmines.csv"

def hol_daten():
    print("--- START BETMINES SNIPER ---")

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(URL)
        print("Warte auf Seite (15s)...")
        time.sleep(15)
        
        # Einmal scrollen
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        datum = datetime.now().strftime("%Y-%m-%d")
        
        # Wir suchen alle Container
        all_elements = soup.find_all(['div', 'li', 'section'])
        
        gefunden = False
        target_text = ""
        gesamtquote = "N/A"

        print("Suche nach 'Verdoppelung'...")

        for element in all_elements:
            text = element.get_text(" ", strip=True)
            
            # --- DER FILTER ---
            # Wir suchen exakt den Block, der "Verdoppelung" (oder Doubling) enthält
            # UND lang genug ist, um Spiele zu enthalten.
            if ("Verdoppelung" in text or "Doubling" in text) and "Gesamtquote" in text:
                
                # Wir wollen nicht den ganz großen Container (der die ganze Seite enthält),
                # sondern den kompaktesten Block, der diese Infos hat.
                if len(text) < 1000: 
                    target_text = text
                    gefunden = True
                    
                    # Versuch, die Gesamtquote zu isolieren
                    quote_match = re.search(r'Gesamtquote:?\s*([\d\.]+)', text)
                    if quote_match:
                        gesamtquote = quote_match.group(1)
                    
                    # Wenn wir einen guten Treffer haben, brechen wir ab (wir wollen ja nur den einen)
                    break
        
        # Speichern
        if gefunden:
            # Bereinigung: Doppelte Leerzeichen entfernen
            clean_text = " ".join(target_text.split())
            
            print(f"TREFFER: {clean_text[:50]}... Quote: {gesamtquote}")
            
            datei_existiert = os.path.isfile(DATEI_NAME)
            with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not datei_existiert:
                    writer.writerow(["Datum", "Kategorie", "Details", "Gesamtquote"])
                
                writer.writerow([datum, "Verdoppelung des Tages", clean_text, gesamtquote])
                print("Erfolgreich gespeichert.")
        else:
            print("Nichts gefunden. Eventuell Layout geändert oder Seite lädt nicht.")

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    hol_daten()
