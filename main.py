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
# from webdriver_manager.chrome import ChromeDriverManager  # Commented out for GitHub Actions

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

def get_residence_links():
    base_url = "https://www.fac-habitat.com/fr/residences-ile-de-france"
    links = []
    options = webdriver.ChromeOptions()
    
    # Detect environment and set appropriate Chrome binary path
    if os.path.exists('/usr/bin/google-chrome-stable'):
        # Ubuntu / GitHub Actions
        options.binary_location = '/usr/bin/google-chrome-stable'
    elif os.path.exists('/usr/bin/google-chrome'):
        # Alternative Ubuntu path
        options.binary_location = '/usr/bin/google-chrome'
    elif os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        # macOS
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # If none found, let Chrome use default path
    
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    # Detect environment and set appropriate chromedriver path
    if os.path.exists('/usr/local/bin/chromedriver'):
        # GitHub Actions / Ubuntu
        chromedriver_path = '/usr/local/bin/chromedriver'
    elif os.path.exists('/opt/homebrew/bin/chromedriver'):
        # macOS with Homebrew
        chromedriver_path = '/opt/homebrew/bin/chromedriver'
    else:
        # Fallback - let selenium find it automatically
        chromedriver_path = None
    
    if chromedriver_path:
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
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
    driver.quit()
    return links

def check_availability(link):
    options = webdriver.ChromeOptions()
    
    # Detect environment and set appropriate Chrome binary path
    if os.path.exists('/usr/bin/google-chrome-stable'):
        # Ubuntu / GitHub Actions
        options.binary_location = '/usr/bin/google-chrome-stable'
    elif os.path.exists('/usr/bin/google-chrome'):
        # Alternative Ubuntu path
        options.binary_location = '/usr/bin/google-chrome'
    elif os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        # macOS
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # If none found, let Chrome use default path
    
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    # Detect environment and set appropriate chromedriver path
    if os.path.exists('/usr/local/bin/chromedriver'):
        # GitHub Actions / Ubuntu
        chromedriver_path = '/usr/local/bin/chromedriver'
    elif os.path.exists('/opt/homebrew/bin/chromedriver'):
        # macOS with Homebrew
        chromedriver_path = '/opt/homebrew/bin/chromedriver'
    else:
        # Fallback - let selenium find it automatically
        chromedriver_path = None
    
    if chromedriver_path:
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)
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
                            import re
                            postal_match = re.search(r'\b(\d{5})\s+([A-Za-zÀ-ÿ\s\-]+(?:sur|le|la|les|du|des|de|aux|en)?\s*[A-Za-zÀ-ÿ\s\-]*)\b', text)
                            if postal_match:
                                postal_code = postal_match.group(1)
                                city_name = postal_match.group(2).strip().title()
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
                has_button = len(td.find_elements(By.CSS_SELECTOR, 'a.btn_reserver')) > 0
                
                # Priorité au texte "aucune disponibilité"
                if 'aucune disponibilité' in text:
                    statuses.append('indisponible')
                elif has_button:
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
        driver.quit()

def main():
    links = get_residence_links()
    print(f"Trouvé {len(links)} résidences.")
    
    available_residences = []
    
    for link in links:
        status, city = check_availability(link)
        
        if status is True:
            # Extraire le nom de la résidence depuis l'URL
            residence_name = link.split('/')[-1].replace('-', ' ').title()
            available_residences.append(f"{residence_name}\n{city}\n{link}")
            print(f"Disponibilité trouvée : {link}")
        elif status == 'soon':
            print(f"Disponibilité à venir : {link}")
        elif status is False:
            print(f"Aucune disponibilité : {link}")
        else:
            print(f"Statut inconnu : {link}")
        
        time.sleep(1)
    
    # Envoyer email quotidien avec les résidences disponibles
    if available_residences:
        subject = f"Résidences Fac Habitat Disponibles - {len(available_residences)} trouvées"
        body = "Voici les résidences actuellement disponibles :\n\n" + "\n\n".join(available_residences)
        to_email = os.getenv('EMAIL_TO')
        if to_email:
            send_email(subject, body, to_email)
            print(f"Email envoyé avec {len(available_residences)} résidences disponibles")
        else:
            print("Variable d'environnement EMAIL_TO non configurée. Aucun email envoyé.")
    else:
        print("Aucune résidence disponible trouvée.")
        # Envoyer un email de confirmation que le scraper fonctionne même s'il n'y a pas de disponibilité
        subject = "Rapport quotidien Fac Habitat - Aucune disponibilité"
        body = f"Le scraper a vérifié {len(links)} résidences ce {time.strftime('%d/%m/%Y à %H:%M')}.\n\nAucune résidence n'est actuellement disponible.\n\nLe scraper fonctionne correctement et continuera à vérifier automatiquement."
        to_email = os.getenv('EMAIL_TO')
        if to_email:
            send_email(subject, body, to_email)
            print("Email de confirmation envoyé (aucune disponibilité)")

if __name__ == "__main__":
    # Test d'une URL spécifique
    test_url = "https://www.fac-habitat.com/fr/residences-etudiantes/id-39-claude-monet"
    print(f"Test de l'URL : {test_url}")
    status, city = check_availability(test_url)
    print(f"Statut : {status}, Ville : {city}")
    
    # main()  # Commenté pour le test