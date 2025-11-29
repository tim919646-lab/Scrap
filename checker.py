from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import csv
import re
import os
import time
import urllib.parse

DATEI_NAME = "meine_datenbank.csv"

# --- HILFSFUNKTIONEN ---

def simplify_name(team_name):
    """
    Reduziert 'Oxford Utd' zu 'Oxford', 'Borussia Dortmund' zu 'Dortmund'.
    Hilft beim Vergleichen.
    """
    ignore_words = ["FC", "Utd", "United", "City", "Town", "Real", "AC", "Inter", "Sporting", "Club", "v"]
    parts = team_name.split()
    
    # Nimm das längste Wort, das nicht auf der Ignore-Liste steht
    best_word = ""
    for p in parts:
        clean_p = p.strip()
        if clean_p not in ignore_words and len(clean_p) > len(best_word):
            best_word = clean_p
            
    if not best_word and parts:
        return parts[0] # Fallback
    return best_word

def extract_score_from_line(line):
    """
    Sucht nach Musters wie '1-1', '2 - 0', '1:0' in einer Textzeile.
    """
    # Regex: Zahl, evtl Leerzeichen, Bindestrich/Doppelpunkt, evtl Leerzeichen, Zahl
    match = re.search(r'(\d+)\s*[-:]\s*(\d+)', line)
    if match:
        t1 = int(match.group(1))
        t2 = int(match.group(2))
        # Plausibilitätscheck: Kein Fußballspiel geht 20-25 aus (das ist ein Datum)
        if t1 < 15 and t2 < 15:
            return f"{t1}-{t2}"
    return None

# --- DIE QUELLEN (SOURCES) ---

def check_skysports(driver, datum, team_a, team_b):
    try:
        url = f"https://www.skysports.com/football-scores-fixtures/{datum}"
        print(f"   [SkySports] Prüfe: {url}")
        driver.get(url)
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')
        
        simple_a = simplify_name(team_a)
        simple_b = simplify_name(team_b)
        
        for line in lines:
            if simple_a in line and simple_b in line:
                score = extract_score_from_line(line)
                if score: return score
    except Exception as e:
        print(f"   [SkySports] Fehler: {e}")
    return None

def check_tipsomatic(driver, datum, team_a, team_b):
    try:
        # Tipsomatic Format: games/date-YYYY-MM-DD
        url = f"https://tipsomatic.com/games/date-{datum}"
        print(f"   [Tipsomatic] Prüfe: {url}")
        driver.get(url)
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')
        
        simple_a = simplify_name(team_a)
        simple_b = simplify_name(team_b)

        for line in lines:
            # Tipsomatic schreibt Teams oft weit auseinander, wir suchen im Block
            if simple_a in line and simple_b in line:
                score = extract_score_from_line(line)
                if score: return score
    except:
        pass
    return None

def check_bbc(driver, datum, team_a, team_b):
    try:
        url = f"https://www.bbc.com/sport/football/scores-fixtures/{datum}"
        print(f"   [BBC] Prüfe: {url}")
        driver.get(url)
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # BBC ist komplex, wir suchen einfach im Textdump
        simple_a = simplify_name(team_a)
        simple_b = simplify_name(team_b)
        
        if simple_a in body_text and simple_b in body_text:
            # Wenn beide Teams auf der Seite sind, versuchen wir die Zeile zu finden
            lines = body_text.split('\n')
            for line in lines:
                if simple_a in line and simple_b in line:
                    score = extract_score_from_line(line)
                    if score: return score
    except:
        pass
    return None

def check_bing_fallback(driver, match_info):
    try:
        query = f"{match_info} final score"
        print(f"   [Bing] Fallback Suche: {query}")
        driver.get(f"https://www.bing.com/search?q={urllib.parse.quote(query)}")
        time.sleep(4)
        
        body = driver.find_element(By.TAG_NAME, "body").text
        # Wir nehmen das allererste Ergebnis, das wie ein Score aussieht
        score = extract_score_from_line(body[:500]) # Nur oben suchen
        return score
    except:
        pass
    return None

# --- HAUPTPROGRAMM ---

def check_results():
    print("--- START MULTI-SOURCE CHECKER ---")
    
    if not os.path.isfile(DATEI_NAME):
        print("Datenbank nicht gefunden.")
        return

    # Chrome Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Daten laden
    zeilen = []
    with open(DATEI_NAME, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        zeilen = reader

    if len(zeilen) < 2: return
    
    daten = zeilen[1:]
    updates = False

    try:
        for row in daten:
            if len(row) < 6: continue
            
            status = row[5]
            match_info = row[3] # "Oxford Utd v Ipswich..."
            datum = row[0]      # "2025-11-28"
            
            if status == "Offen":
                print(f"------------------------------------------------")
                print(f"ANALYSING: {match_info} ({datum})")
                
                # Teams extrahieren
                if " v " in match_info:
                    parts = match_info.split(" v ")
                    team_a = parts[0]
                    team_b = parts[1].split("England")[0] # Versuch Liga abzuschneiden
                else:
                    team_a = match_info
                    team_b = ""

                ergebnis = None
                
                # 1. VERSUCH: SkySports
                if not ergebnis:
                    ergebnis = check_skysports(driver, datum, team_a, team_b)
                
                # 2. VERSUCH: Tipsomatic
                if not ergebnis:
                    ergebnis = check_tipsomatic(driver, datum, team_a, team_b)
                    
                # 3. VERSUCH: BBC
                if not ergebnis:
                    ergebnis = check_bbc(driver, datum, team_a, team_b)
                    
                # 4. VERSUCH: Bing (Notnagel)
                if not ergebnis:
                    ergebnis = check_bing_fallback(driver, match_info)

                # FAZIT
                if ergebnis:
                    print(f"   -> !!! TREFFER !!!: {ergebnis}")
                    row[5] = f"Beendet ({ergebnis})"
                    updates = True
                else:
                    print("   -> Alle Quellen geprüft. Kein Ergebnis gefunden.")

    except Exception as e:
        print(f"KRITISCHER FEHLER: {e}")
    finally:
        driver.quit()

    if updates:
        with open(DATEI_NAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(zeilen)
        print("Update gespeichert.")
    else:
        print("Keine Updates.")

if __name__ == "__main__":
    check_results()
