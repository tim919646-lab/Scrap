import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os

# Konfiguration
URL = "https://www.footballsuper.tips/football-accumulators-tips/football-tips-prediction-of-the-day/"
DATEI_NAME = "meine_datenbank.csv"

def hol_daten():
    # 1. Seite laden - Wir tarnen uns als normaler Browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(URL, headers=headers)
    
    if response.status_code != 200:
        print("Fehler beim Laden der Seite")
        return

    # 2. HTML analysieren
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Wir suchen nach der Tabelle oder den Listen. 
    # Hinweis: Da ich die Seite nicht live sehe, nehmen wir alles was nach "Prediction" aussieht.
    # Wir speichern einfach den rohen Text der Vorhersagen, um sicherzugehen.
    
    daten_heute = []
    datum = datetime.now().strftime("%Y-%m-%d")

    # Suche nach Zeilen in Tabellen (üblich bei solchen Seiten)
    rows = soup.find_all('tr')
    
    for row in rows:
        text = row.get_text(" | ", strip=True)
        # Filter: Wir nehmen nur Zeilen, die nach Spiel aussehen (mindestens 10 Zeichen)
        if len(text) > 10:
            daten_heute.append([datum, text])

    # 3. Speichern
    datei_existiert = os.path.isfile(DATEI_NAME)
    
    with open(DATEI_NAME, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not datei_existiert:
            writer.writerow(["Datum", "Inhalt"]) # Kopfzeile
        
        for eintrag in daten_heute:
            writer.writerow(eintrag)
            
    print(f"{len(daten_heute)} Einträge gespeichert.")

if __name__ == "__main__":
    hol_daten()
