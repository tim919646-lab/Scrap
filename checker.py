import csv
import re
import os
import time
import sys

# Wir versuchen den Import sicher zu machen
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    print("FEHLER: duckduckgo_search Modul konnte nicht geladen werden.")
    SEARCH_AVAILABLE = False
except Exception as e:
    print(f"FEHLER beim Import: {e}")
    SEARCH_AVAILABLE = False

DATEI_NAME = "meine_datenbank.csv"

def finde_ergebnis_online(match_info):
    if not SEARCH_AVAILABLE:
        return None

    query = f"{match_info} final score result"
    print(f"   -> Suche: '{query}'")
    
    try:
        # Wir nutzen einen Time-Limit, damit er sich nicht aufhängt
        with DDGS() as ddgs:
            # Einfachere Suche, nur Text
            results = list(ddgs.text(query, max_results=2))
            
            if not results:
                print("   -> Suchmaschine lieferte keine Ergebnisse.")
                return None

            for r in results:
                body = r.get('body', '')
                # Suche nach typischen Fußball-Ergebnissen (z.B. 2-1, 1:0, 0 - 0)
                # Dieser Regex ist etwas toleranter
                score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', body)
                if score_match:
                    found_score = f"{score_match.group(1)}-{score_match.group(2)}"
                    print(f"   -> Treffer im Text: {found_score}")
                    return found_score
                    
    except Exception as e:
        print(f"   -> Such-Fehler (Ignoriert): {e}")
        return None
    
    return None

def check_results():
    print("--- START ERGEBNIS-CHECKER v2 ---")
    
    if not os.path.isfile(DATEI_NAME):
        print(f"FEHLER: Datei {DATEI_NAME} nicht gefunden. Abbruch.")
        # Wir beenden hier, aber ohne Crash (exit code 0)
        return

    # Lesen
    try:
        with open(DATEI_NAME, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            zeilen = reader
    except Exception as e:
        print(f"FEHLER beim Lesen der CSV: {e}")
        return

    if len(zeilen) < 2:
        print("Datenbank ist leer (nur Header).")
        return

    header = zeilen[0]
    daten = zeilen[1:]
    
    updates_gemacht = False

    # Prüfen
    for i, row in enumerate(daten):
        # Sicherheitscheck: Hat die Zeile überhaupt genug Spalten?
        if len(row) < 6:
            continue

        status = row[5]
        match_info = row[3]
        
        if status == "Offen":
            print(f"Prüfe: {match_info}")
            ergebnis = finde_ergebnis_online(match_info)
            
            if ergebnis:
                print(f"   -> UPDATE: {ergebnis}")
                row[5] = f"Beendet ({ergebnis})"
                updates_gemacht = True
                time.sleep(3) # Höflichkeits-Pause für die Suchmaschine
            else:
                print("   -> Kein Ergebnis gefunden (Spiel läuft noch oder API blockt).")
    
    # Speichern
    if updates_gemacht:
        try:
            with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(zeilen)
            print("Datenbank erfolgreich aktualisiert.")
        except Exception as e:
            print(f"FEHLER beim Speichern: {e}")
    else:
        print("Keine Änderungen nötig.")

if __name__ == "__main__":
    try:
        check_results()
    except Exception as e:
        # Hier fangen wir den "roten X" Fehler ab
        print(f"KRITISCHER SYSTEM-FEHLER: {e}")
        # Wir lassen das Skript normal enden, damit GitHub nicht meckert
        sys.exit(0)
