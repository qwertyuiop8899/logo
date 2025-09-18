from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    """Converte il contenuto HTML della programmazione in formato JSON."""
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}

    schedule_div = soup.find('div', id='schedule')
    if not schedule_div:
        print("AVVISO: Contenitore 'schedule' non trovato nel contenuto HTML!")
        return {}

    for day_div in schedule_div.find_all('div', class_='schedule__day'):
        day_title_tag = day_div.find('div', class_='schedule__dayTitle')
        if not day_title_tag:
            continue
        
        current_date = day_title_tag.text.strip()
        result[current_date] = {}

        for category_div in day_div.find_all('div', class_='schedule__category'):
            cat_header = category_div.find('div', class_='schedule__catHeader')
            if not cat_header:
                continue
            
            current_category = cat_header.text.strip()
            result[current_date][current_category] = []
            
            category_body = category_div.find('div', class_='schedule__categoryBody')
            if not category_body:
                continue

            for event_div in category_body.find_all('div', class_='schedule__event'):
                event_header = event_div.find('div', class_='schedule__eventHeader')
                if not event_header:
                    continue

                time_span = event_header.find('span', class_='schedule__time')
                event_title_span = event_header.find('span', class_='schedule__eventTitle')
                
                event_data = {
                    "time": time_span.text.strip() if time_span else "",
                    "event": event_title_span.text.strip() if event_title_span else "Evento Sconosciuto",
                    "channels": []
                }

                channels_div = event_div.find('div', class_='schedule__channels')
                if channels_div:
                    for link in channels_div.find_all('a', href=re.compile(r'/watch\.php\?id=\d+')):
                        href = link.get('href', '')
                        channel_id_match = re.search(r'id=(\d+)', href)
                        if channel_id_match:
                            channel_id = channel_id_match.group(1)
                            channel_name = link.text.strip()
                            channel_name = re.sub(r'\s*CH-\d+$', '', channel_name).strip()

                            event_data["channels"].append({
                                "channel_name": channel_name,
                                "channel_id": channel_id
                            })
                
                result[current_date][current_category].append(event_data)

    return result

def modify_json_file(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    current_month = datetime.now().strftime("%B")

    # Questa logica non è più necessaria con la nuova struttura HTML
    # che fornisce già la data completa.
    # for date in list(data.keys()):
    #     match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\d{4})", date)
    #     if match:
    #         day_part = match.group(1)
    #         suffix = match.group(2)
    #         year_part = match.group(3)
    #         new_date = f"{day_part}{suffix} {current_month} {year_part}"
    #         data[new_date] = data.pop(date)

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"File JSON modificato e salvato in {json_file_path}")

def extract_schedule_container():
    url = f"https://dlhd.dad/"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_output = os.path.join(script_dir, "daddyliveSchedule_new.json")

    print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Tentativo {attempt} di {max_attempts}...")
                page.goto(url)
                print("Attesa per il caricamento completo...")
                page.wait_for_timeout(10000)  # 10 secondi

                schedule_content = page.evaluate("""() => {
                    const container = document.querySelector('body');
                    return container ? container.outerHTML : '';
                }""")

                if not schedule_content:
                    print("AVVISO: Contenuto della pagina non trovato o vuoto!")
                    if attempt == max_attempts:
                        browser.close()
                        return False
                    else:
                        continue

                print("Conversione HTML della programmazione principale in formato JSON...")
                json_data = html_to_json(schedule_content)

                with open(json_output, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)

                print(f"Dati JSON salvati in {json_output}")

                modify_json_file(json_output)
                browser.close()
                return True

            except Exception as e:
                print(f"ERRORE nel tentativo {attempt}: {str(e)}")
                if attempt == max_attempts:
                    print("Tutti i tentativi falliti!")
                    browser.close()
                    return False
                else:
                    print(f"Riprovando... (tentativo {attempt + 1} di {max_attempts})")

        browser.close()
        return False

if __name__ == "__main__":
    success = extract_schedule_container()
    if not success:
        exit(1)
