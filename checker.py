from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import os
import time
import re
from datetime import datetime

DATEI_NAME = "meine_datenbank.csv"

def get_stealth_result(match_info, driver):
    """
    Sucht intelligent und filtert alte Ergebnisse (H2H) raus.
    """
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].replace("Utd", "").strip()
            team_b_raw = parts[1]
            team_b = team_b_raw.split("England")[0].split("Germany")[0].strip().split()[0]
            # Wir suchen spezifisch nach dem "Final Score"
            query = f"{team_a} {team_b} final score result"
        else:
            query = f"{match_info} final score"
    except:
        query = match_info

    print(f"   -> Stealth-Suche: '{query}'")
    
    url = f"https://html.duckduckgo.com/html/?q={query}"
    driver.get(url)
    
    snippets = driver.eles('.result__snippet')
    
    for snippet in snippets:
        text = snippet.text
        text_lower = text.lower()
        
        # --- DER NEUE ANTI-HISTORIEN FILTER ---
        # Wenn diese Wörter auftauchen, ist es wahrscheinlich eine alte Statistik oder ein Tipp
        bad_words = ["h2h", "head to head", "head-to-head", "previous", "last meeting", "history", "prediction", "predict", "odds", "tip"]
        
        if any(bad in text_lower for bad in bad_words):
            print(f"   -> Ignoriere Snippet (Verdacht auf Historie/Tipp): {text[:40]}...")
            continue # Überspringe dieses Suchergebnis

        matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
        
        for m in matches:
            t1 = int(m[0])
            t2 = int(m[1])
            
            # Filter: Unmögliche Ergebnisse
            if t1 > 15 or t2 > 15: continue
            
            found_score = f"{t1}-{t2}"
            
            keywords = ["ft", "full time", "final", "finished", "ended", "full-time", "result"]
            is_finished = any(k in text_lower for k in keywords)
            
            # Bei 0-0 brauchen wir zwingend ein Keyword
            if t1 == 0 and t2 == 0:
                if is_finished:
                    return found_score
                else:
                    continue
            
            # Bei anderen Ergebnissen sind wir jetzt sicherer, da wir die "bad_words" gefiltert haben
            return found_score

    return None

def check_results():
    print("--- START STEALTH CHECKER (ANTI-HISTORY) ---")
    
    if not os.path.isfile(DATEI_NAME): return

    co = ChromiumOptions()
    co.set_argument('--headless=new')
    co.set_argument('--no-sandbox')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    page = ChromiumPage(co)

    zeilen = []
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
            
            # Wir prüfen alles, was "Offen" ist
            # UND wir prüfen Dinge, die wir vielleicht korrigieren müssen (manuell)
            
            if "Beendet" not in status:
                print(f"Prüfe: {match_info}")
                
                ergebnis = get_stealth_result(match_info, page)
                
                if ergebnis:
                    print(f"   -> TREFFER: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Nichts gefunden.")
                    # Nur updaten wenn nicht schon geprüft
                    if "Geprüft" not in status:
                        row[5] = f"Offen (Geprüft {jetzt})"
                        updates = True
                
                time.sleep(2)

    except Exception as e:
        print(f"FEHLER: {e}")
    finally:
        page.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Datenbank aktualisiert.")
    else:
        print("Keine Updates.")

if __name__ == "__main__":
    check_results()
