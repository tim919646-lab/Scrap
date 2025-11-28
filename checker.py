import csv
import re
import os
import time
from datetime import datetime
from duckduckgo_search import DDGS

# Datei-Pfad
DATEI_NAME = "meine_datenbank.csv"

def finde_ergebnis_online(match_info):
    """
    Sucht via DuckDuckGo nach dem Ergebnis.
    Match_Info z.B.: "Oxford Utd v Ipswich England Championship"
    """
    query = f"{match_info} result score"
    print(f"   -> Suche nach: {query}")
    
    try:
        # Wir nutzen DuckDuckGo, um keine Google-Sperre zu kassieren
        results = DDGS().text(query, max_results=3)
        
        for r in results:
            text = r['body']
            # Wir suchen nach einem Muster wie "1-1", "2:0", "1 - 2"
            # Dies ist ein grober Filter
            score_match = re.search(r'(\d+)\s*-\s*(\d+)', text)
            if score_match:
                return f"{score_match.group(1)}-{score_match.group(2)}"
                
        return None
    except Exception as e:
        print(f"   -> Fehler bei der Suche: {e}")
        return None

def check_results():
    print("--- START ERGEBNIS-CHECKER ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Keine Datenbank gefunden.")
        return

    # 1. Datenbank lesen
    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    header = zeilen[0]
    daten = zeilen[1:]
    
    updates_gemacht = False

    # 2. Durchlaufen und prüfen
    for i, row in enumerate(daten):
        # Wir prüfen nur Zeilen, die "Offen" sind
        # Die Spalte Status ist Index 5 (0=Datum, 1=Uhrzeit, 2=Tipp, 3=Match, 4=Quote, 5=Status)
        status = row[5]
        match_info = row[3]
        
        if status == "Offen":
            print(f"Prüfe Spiel: {match_info}")
            
            ergebnis = finde_ergebnis_online(match_info)
            
            if ergebnis:
                print(f"   -> GEFUNDEN: {ergebnis}")
                # Wir schreiben das Ergebnis in die Status-Spalte (erstmal nur das Ergebnis, z.B. "1-1")
                row[5] = f"Beendet ({ergebnis})"
                updates_gemacht = True
                time.sleep(2) # Kurz warten, um nicht geblockt zu werden
            else:
                print("   -> Kein eindeutiges Ergebnis gefunden.")
    
    # 3. Speichern (nur wenn Updates da waren)
    if updates_gemacht:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen) # Alles wieder reinschreiben
        print("Datenbank aktualisiert.")
    else:
        print("Keine Änderungen vorgenommen.")

if __name__ == "__main__":
    check_results()
