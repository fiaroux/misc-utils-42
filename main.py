import re
import requests
from bs4 import BeautifulSoup
import time
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

# Charger les variables d'environnement
load_dotenv()

def send_email(subject, body, to_email):
    from_email = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not from_email or not password:
        print("Variables d'environnement EMAIL_USER et EMAIL_PASSWORD non configurées. Email non envoyé.")
        return
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email envoyé avec succès")
    except Exception as e:
        print(f"Erreur lors de l'envoi d'email: {e}")

def create_driver():
    """Crée et retourne un driver Chrome configuré. Selenium 4.6+ gère automatiquement ChromeDriver."""
    options = webdriver.ChromeOptions()
    
    # Detect environment and set appropriate Chrome binary path
    if os.path.exists('/usr/bin/google-chrome-stable'):
        options.binary_location = '/usr/bin/google-chrome-stable'
    elif os.path.exists('/usr/bin/google-chrome'):
        options.binary_location = '/usr/bin/google-chrome'
    elif os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Selenium 4.6+ gère automatiquement le téléchargement du bon ChromeDriver
    return webdriver.Chrome(options=options)

def get_residence_links(driver):
    base_url = "https://www.fac-habitat.com/fr/residences-ile-de-france"
    links = []
    
    for page in range(1, 8):  # Assuming 7 pages
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/page-{page}?"
        try:
            driver.get(url)
            time.sleep(5)  # Wait for JS to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.visuel-liste')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            matching_a = soup.find_all('a', class_='visuel-liste')
            for a in matching_a:
                href = a['href']
                if href.startswith('fr/'):
                    full_link = "https://www.fac-habitat.com/" + href
                else:
                    full_link = "https://www.fac-habitat.com" + href
                if full_link not in links:
                    links.append(full_link)
        except Exception as e:
            print(f"Erreur lors de la récupération de la page {page}: {e}")
        time.sleep(2)  # Respectful delay
    return links

def check_availability(driver, link):
    try:
        driver.get(link)
        
        # Extract city
        try:
            # Try common selectors for city/location
            city_selectors = [
                '.coordonnees-fiche div',  # Address section with full address
                '.bloc-adresse-fiche .coordonnees-fiche div',  # Specific address block
                '.breadcrumb li:last-child',  # Breadcrumb last item
                'h1',  # Main title
                '.ville',  # Ville class
                '.city',  # City class
                'span.location',  # Location span
                'div.location',  # Location div
                'h1 + p',  # Paragraph after h1
                '[class*="ville"]',  # Any element with ville in class
                '[class*="city"]',  # Any element with city in class
                '.breadcrumb a:last-child',  # Last breadcrumb link
                'title',  # Page title
            ]
            city = "Ville inconnue"
            for selector in city_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) < 150:  # Allow longer text for full addresses
                            print(f"Test sélecteur '{selector}': '{text}'")
                            
                            # Look for postal code pattern (5 digits) followed by city name
                            postal_match = re.search(r'(\d{5})\s+(.+)$', text)
                            if postal_match:
                                postal_code = postal_match.group(1)
                                # Capitaliser chaque mot correctement (gérer les accents)
                                raw_city = postal_match.group(2).strip()
                                city_name = '-'.join(w.capitalize() for w in raw_city.split('-'))
                                city_name = ' '.join(w.capitalize() if not w[0].isupper() else w for w in city_name.split())
                                if len(city_name) > 2:  # Valid city name
                                    city = city_name
                                    print(f"Ville extraite depuis adresse: {city} (CP: {postal_code})")
                                    break
                            
                            # Fallback: look for city patterns in the text
                            if any(keyword in text.lower() for keyword in ['noisy', 'paris', 'ville', 'boulogne', 'neuilly', 'issy', 'suresnes', 'puteaux', 'courbevoie', 'asnieres', 'colombes', 'argenteuil', 'sartrouville', 'versailles', 'saint-', 'le-', 'la-', 'les-', 'du-', 'des-', 'de ', 'sur-', 'sous-', 'aux-', 'bures', 'yvette']):
                                words = text.split()
                                for word in words:
                                    if len(word) > 3 and ('-' in word or word.isupper() or any(city_part in word.lower() for city_part in ['paris', 'noisy', 'boulogne', 'neuilly', 'issy', 'suresnes', 'puteaux', 'courbevoie', 'asnieres', 'colombes', 'argenteuil', 'sartrouville', 'versailles', 'bures', 'yvette'])):
                                        city = word.title()
                                        print(f"Ville trouvée avec sélecteur '{selector}': {city}")
                                        break
                                if city != "Ville inconnue":
                                    break
                            elif len(text) < 50 and not text.startswith('Résidence') and not text.startswith('3 ') and not text.startswith('Tél'):
                                city = text
                                print(f"Ville trouvée avec sélecteur '{selector}': {city}")
                                break
                    if city != "Ville inconnue":
                        break
                except Exception as e:
                    print(f"Erreur avec sélecteur '{selector}': {e}")
                    continue
        except Exception as e:
            print(f"Erreur lors de l'extraction de ville: {e}")
            city = "Ville inconnue"
        
        # Wait for main content or availability spans
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.find_element(By.CSS_SELECTOR, 'main#product') or 
                         d.find_element(By.CSS_SELECTOR, '#block_reservation') or 
                         d.find_elements(By.CSS_SELECTOR, 'span[id^="avail_area_"]')
            )
        except:
            print(f"Timeout waiting for content on {link}")
        # Scroll to bottom to load dynamic content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        # Switch to reservation iframe
        try:
            iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe.reservation')))
            driver.switch_to.frame(iframe)
            print(f"Switched to iframe for {link}")
        except:
            print(f"No iframe found for {link}")
            return (False, city)
        # Find all td containing avail_area spans
        avail_tds = driver.find_elements(By.XPATH, '//td[span[starts-with(@id,"avail_area_")]]')
        print(f"Found {len(avail_tds)} availability cells for {link}")
        if avail_tds:
            statuses = []
            for td in avail_tds:
                span = td.find_element(By.CSS_SELECTOR, 'span[id^="avail_area_"]')
                text = span.text.strip().lower()
                classes = span.get_attribute('class')
                buttons = td.find_elements(By.CSS_SELECTOR, 'a.btn_reserver')
                
                # Vérifier le texte du bouton s'il existe
                has_real_reservation = False
                if buttons:
                    btn_text = buttons[0].text.strip().lower()
                    # "Déposer une demande" = pas de vraie dispo, juste une liste d'attente
                    if 'réserver' in btn_text or 'reserver' in btn_text:
                        has_real_reservation = True
                    else:
                        print(f"  Bouton trouvé mais texte='{btn_text}' (pas une vraie réservation)")
                
                # Priorité au texte "aucune disponibilité" — même s'il y a un bouton
                if 'aucune disponibilité' in text:
                    statuses.append('indisponible')
                elif has_real_reservation:
                    statuses.append('disponible_immediat')
                elif 'disponibilité à venir' in text:
                    statuses.append('a_venir')
                elif 'disponible' in text or 'immédiate' in text:
                    statuses.append('disponible')
                elif 'red' in classes:
                    statuses.append('indisponible')
                elif 'orange' in classes:
                    statuses.append('a_venir')
                elif 'green' in classes:
                    statuses.append('disponible')
                else:
                    statuses.append('inconnu')
            # Prioritize: disponible_immediat > disponible > a_venir > indisponible
            if 'disponible_immediat' in statuses:
                return (True, city)
            elif 'disponible' in statuses:
                return (True, city)
            elif 'a_venir' in statuses:
                return ('soon', city)
            else:
                return (False, city)
        else:
            print(f"No availability cells found for {link}, assuming indisponible")
            return (False, city)
    except Exception as e:
        print(f"Erreur lors de la vérification de {link}: {e}")
        return (None, city)
    finally:
        # Revenir au contexte principal (hors iframe)
        driver.switch_to.default_content()

def main():
    driver = create_driver()
    try:
        links = get_residence_links(driver)
        print(f"Trouvé {len(links)} résidences.")
        
        available_residences = []
        new_available_residences = []  # Nouvelles disponibilités seulement
        soon_residences = []  # Disponibilités à venir
    
        # Charger l'état précédent
        previous_status = {}
        if os.path.exists('availability_status.json'):
            try:
                with open('availability_status.json', 'r') as f:
                    raw_status = json.load(f)
                    # Gérer l'ancien format (URL complète -> bool) et le nouveau format (residence_id -> dict)
                    for key, value in raw_status.items():
                        if isinstance(value, bool):
                            # Ancien format: convertir URL -> residence_id avec dict
                            rid = key.split('/')[-1]
                            previous_status[rid] = {'status': value, 'city': 'Ville inconnue', 'link': key}
                        elif isinstance(value, dict):
                            # Nouveau format: déjà bon
                            previous_status[key] = value
                        else:
                            # Format inconnu, ignorer
                            pass
            except Exception as e:
                print(f"Erreur lors du chargement de l'état précédent: {e}")
                previous_status = {}
    
        current_status = {}
        
        for link in links:
            status, city = check_availability(driver, link)
            residence_id = link.split('/')[-1]
            current_status[residence_id] = {'status': status, 'city': city, 'link': link}
            
            if status is True:
                residence_name = link.split('/')[-1].replace('-', ' ').title()
                available_residences.append(f"{residence_name}\n{city}\n{link}")
                
                was_available_before = previous_status.get(residence_id, {}).get('status') is True
                if not was_available_before:
                    new_available_residences.append(f"{residence_name}\n{city}\n{link}")
                    print(f"NOUVELLE disponibilité : {link}")
                else:
                    print(f"Toujours disponible : {link}")
            elif status == 'soon':
                residence_name = link.split('/')[-1].replace('-', ' ').title()
                was_soon_before = previous_status.get(residence_id, {}).get('status') == 'soon'
                if not was_soon_before:
                    soon_residences.append(f"{residence_name}\n{city}\n{link}")
                    print(f"NOUVELLE disponibilité à venir : {link}")
                else:
                    print(f"Toujours disponibilité à venir : {link}")
            elif status is False:
                print(f"Aucune disponibilité : {link}")
            else:
                print(f"Statut inconnu : {link}")
            
            time.sleep(1)
        
        # Sauvegarder l'état actuel
        try:
            with open('availability_status.json', 'w') as f:
                json.dump(current_status, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du statut: {e}")
        
        # Construire et envoyer l'email si changements détectés
        email_parts = []
        
        if new_available_residences:
            email_parts.append(f"{len(new_available_residences)} NOUVELLES DISPONIBILITES :\n\n" + "\n\n".join(new_available_residences))
        
        if soon_residences:
            email_parts.append(f"{len(soon_residences)} DISPONIBILITES A VENIR :\n\n" + "\n\n".join(soon_residences))
        
        if email_parts:
            subject = f"Fac Habitat - {len(new_available_residences)} dispo + {len(soon_residences)} à venir"
            body = "\n\n---\n\n".join(email_parts)
            if available_residences:
                body += f"\n\n---\nAu total, {len(available_residences)} résidences sont actuellement disponibles."
            to_email = os.getenv('EMAIL_TO')
            if to_email:
                send_email(subject, body, to_email)
                print(f"Email envoyé ({len(new_available_residences)} nouvelles, {len(soon_residences)} à venir)")
            else:
                print("Variable d'environnement EMAIL_TO non configurée. Aucun email envoyé.")
        else:
            print("Aucun changement détecté, pas d'email envoyé.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()