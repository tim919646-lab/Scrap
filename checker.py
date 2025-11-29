from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import os
import time
import re
from datetime import datetime

DATEI_NAME = "meine_datenbank.csv"

def get_stealth_result(match_info, driver):
    """
    Sucht intelligent und prüft auf 'Full Time' Status.
    """
    # 1. Suchbegriff
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].replace("Utd", "").strip()
            team_b_raw = parts[1]
            team_b = team_b_raw.split("England")[0].split("Germany")[0].strip().split()[0]
            # Wir fügen "Result" hinzu, um Vorschauen zu vermeiden
            query = f"{team_a} {team_b} final score result"
        else:
            query = f"{match_info} final score"
    except:
        query = match_info

    print(f"   -> Stealth-Suche: '{query}'")
    
    # DuckDuckGo HTML
    url = f"https://html.duckduckgo.com/html/?q={query}"
    driver.get(url)
    
    # Wir holen alle Suchergebnis-Schnipsel einzeln
    # DuckDuckGo HTML nutzt die Klasse 'result__snippet' für den Text
    snippets = driver.eles('.result__snippet')
    
    for snippet in snippets:
        text = snippet.text
        
        # 2. Suche nach Ergebnis (Zahl-Zahl)
        matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
        
        for m in matches:
            t1 = int(m[0])
            t2 = int(m[1])
            
            # Filter: Unmögliche Ergebnisse raus
            if t1 > 15 or t2 > 15: continue
            
            found_score = f"{t1}-{t2}"
            
            # --- DER NEUE FILTER ---
            
            # Wir suchen nach Beweisen, dass das Spiel VORBEI ist
            # Wir wandeln den Text in Kleinbuchstaben um für den Vergleich
            text_lower = text.lower()
            
            keywords = ["ft", "full time", "final", "finished", "ended", "full-time"]
            
            is_finished = any(k in text_lower for k in keywords)
            
            # REGEL 1: Wenn das Ergebnis "0-0" ist, MUSS "FT" oder "Final" dabei stehen.
            if t1 == 0 and t2 == 0:
                if is_finished:
                    print(f"   -> Valides 0-0 gefunden (mit '{keywords}'): {text[:50]}...")
                    return found_score
                else:
                    # Ignorieren, wahrscheinlich Vorschau
                    continue
            
            # REGEL 2: Bei anderen Ergebnissen sind wir toleranter, aber bevorzugen "FT"
            # Wenn wir ein klares Ergebnis wie 2-1 finden, ist die Chance hoch, dass es stimmt.
            # Aber wir prüfen sicherheitshalber, ob es nicht "Previous results: 2-1" heißt.
            if "previous" not in text_lower and "last match" not in text_lower:
                return found_score

    return None

def check_results():
    print("--- START STEALTH CHECKER (SMART FILTER) ---")
    
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
            
            # Wir prüfen alles, was NICHT "Beendet" ist
            # WICHTIG: Wenn da schon "Beendet (0-0)" steht (falsch), müssen wir es manuell korrigieren oder ignorieren.
            # Mein Code prüft nur Zeilen, wo NICHT "Beendet" steht, ODER wo "0-0" steht (um Fehler zu korrigieren)
            
            needs_check = False
            if "Beendet" not in status:
                needs_check = True
            elif "0-0" in status:
                # Wir prüfen 0-0 Ergebnisse nochmal nach, falls sie falsch waren
                print(f"Prüfe verdächtiges 0-0: {match_info}")
                needs_check = True
            
            if needs_check:
                print(f"Prüfe: {match_info}")
                
                ergebnis = get_stealth_result(match_info, page)
                
                if ergebnis:
                    # Wenn wir ein neues Ergebnis haben
                    if str(ergebnis) not in status: 
                        print(f"   -> TREFFER: {ergebnis}")
                        row[5] = f"Beendet ({ergebnis})"
                        updates = True
                else:
                    print("   -> Kein finales Ergebnis gefunden (Spiel läuft noch oder Vorschau).")
                    # Wenn wir vorher fälschlicherweise "Beendet 0-0" hatten und jetzt nichts finden,
                    # setzen wir es zurück auf Offen!
                    if "0-0" in status:
                        row[5] = "Offen (Korrektur: War Vorschau)"
                        updates = True
                    elif "Beendet" not in status:
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
