from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import os
import time
import re
from datetime import datetime

DATEI_NAME = "meine_datenbank.csv"

def get_stealth_result(match_info, driver):
    """
    Sucht intelligent und filtert Uhrzeiten (15:00) raus.
    """
    try:
        if " v " in match_info:
            parts = match_info.split(" v ")
            team_a = parts[0].replace("Utd", "").strip()
            team_b_raw = parts[1]
            team_b = team_b_raw.split("England")[0].split("Germany")[0].strip().split()[0]
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
        
        matches = re.findall(r'(\d+)\s*[-:]\s*(\d+)', text)
        
        for m in matches:
            t1 = int(m[0])
            t2 = int(m[1])
            
            # --- DER NEUE STRENGE FILTER ---
            # Kein Team schießt mehr als 9 Tore (filtert 10:00, 15:00, 19:30 etc.)
            if t1 > 9 or t2 > 9: 
                continue
            
            found_score = f"{t1}-{t2}"
            text_lower = text.lower()
            keywords = ["ft", "full time", "final", "finished", "ended", "full-time"]
            is_finished = any(k in text_lower for k in keywords)
            
            # Regel: 0-0 braucht Beweis (FT)
            if t1 == 0 and t2 == 0:
                if is_finished:
                    return found_score
                else:
                    continue
            
            # Alle anderen Ergebnisse (z.B. 2-1) nehmen wir an
            return found_score

    return None

def check_results():
    print("--- START STEALTH CHECKER (ANTI-TIME BUG) ---")
    
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
            
            needs_check = False
            
            # 1. Normale offene Spiele prüfen
            if "Beendet" not in status:
                needs_check = True
            
            # 2. FEHLER-KORREKTUR: "15-0" finden und neu prüfen!
            # Wir prüfen einfach, ob eine Zahl > 9 im Status steht
            elif "Beendet" in status:
                # Suche nach Zahlen im Status
                nums = re.findall(r'\d+', status)
                for n in nums:
                    if int(n) > 9: # Aha! 15-0 entdeckt!
                        print(f"Ungültiges Ergebnis entdeckt ({status}). Korrigiere...")
                        needs_check = True
                        break

            if needs_check:
                print(f"Prüfe: {match_info}")
                ergebnis = get_stealth_result(match_info, page)
                
                if ergebnis:
                    # Wenn neu gefunden
                    if str(ergebnis) not in status: 
                        print(f"   -> TREFFER: {ergebnis}")
                        row[5] = f"Beendet ({ergebnis})"
                        updates = True
                else:
                    print("   -> Kein Ergebnis.")
                    # Wenn wir vorher "15-0" hatten und jetzt nichts finden -> Zurücksetzen!
                    if "15-0" in status or "15-" in status or "-15" in status:
                        row[5] = "Offen (Korrektur: War Uhrzeit)"
                        updates = True
                    elif "Beendet" not in status:
                        row[5] = f"Offen (Geprüft {jetzt}: Nichts)"
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
