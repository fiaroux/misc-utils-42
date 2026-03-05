import re
import requests
from bs4 import BeautifulSoup
import time
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# Charger les variables d'environnement
load_dotenv()

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

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
    """Récupère tous les liens de résidences via requests (sans Selenium)."""
    base_url = "https://www.fac-habitat.com/fr/residences-ile-de-france"
    links = []
    
    for page in range(1, 8):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}/page-{page}?"
        try:
            r = SESSION.get(url, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            matching_a = soup.find_all('a', class_='visuel-liste')
            for a in matching_a:
                href = a['href']
                if href.startswith('fr/'):
                    full_link = "https://www.fac-habitat.com/" + href
                else:
                    full_link = "https://www.fac-habitat.com" + href
                if full_link not in links:
                    links.append(full_link)
            if not matching_a:
                print(f"Page {page}: aucun lien trouvé, fin de la pagination.")
                break
        except Exception as e:
            print(f"Erreur lors de la récupération de la page {page}: {e}")
        time.sleep(0.5)
    return links

def extract_city(soup):
    """Extrait la ville depuis la page de résidence."""
    city = "Ville inconnue"
    
    # Chercher dans les divs d'adresse (coordonnees)
    selectors = [
        '.coordonnees-fiche div',
        '.bloc-adresse-fiche .coordonnees-fiche div',
        'h1',
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        for el in elements:
            text = el.get_text(strip=True)
            if text and len(text) < 150:
                postal_match = re.search(r'(\d{5})\s+(.+)$', text)
                if postal_match:
                    raw_city = postal_match.group(2).strip()
                    city_name = '-'.join(w.capitalize() for w in raw_city.split('-'))
                    city_name = ' '.join(w.capitalize() if not w[0].isupper() else w for w in city_name.split())
                    if len(city_name) > 2:
                        return city_name
        
    return city

def check_availability(link):
    """Vérifie la disponibilité en appelant directement l'iframe via requests."""
    city = "Ville inconnue"
    try:
        # 1. Récupérer la page de résidence pour trouver l'iframe et la ville
        r = SESSION.get(link, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extraire la ville
        city = extract_city(soup)
        
        # 2. Trouver l'URL de l'iframe de réservation
        iframe = soup.find('iframe', class_='reservation')
        if not iframe or not iframe.get('src'):
            # Chercher aussi par pattern dans le src
            for ifr in soup.find_all('iframe'):
                src = ifr.get('src', '')
                if 'iframe_reservation' in src:
                    iframe = ifr
                    break
        
        if not iframe or not iframe.get('src'):
            print(f"Pas d'iframe de réservation trouvée pour {link}")
            return (False, city)
        
        iframe_url = iframe['src']
        
        # 3. Appeler directement l'iframe
        r2 = SESSION.get(iframe_url, timeout=15)
        iframe_soup = BeautifulSoup(r2.text, 'html.parser')
        
        # 4. Chercher les spans de disponibilité
        avail_spans = iframe_soup.find_all('span', id=lambda x: x and x.startswith('avail_area_'))
        print(f"  {len(avail_spans)} zones de disponibilité pour {link.split('/')[-1]}")
        
        if not avail_spans:
            print(f"  Aucune zone de disponibilité trouvée")
            return (False, city)
        
        statuses = []
        for span in avail_spans:
            text = span.get_text(strip=True).lower()
            classes = ' '.join(span.get('class', []))
            
            # Chercher le bouton de réservation dans le td parent
            td = span.find_parent('td')
            has_real_reservation = False
            if td:
                buttons = td.find_all('a', class_='btn_reserver')
                if buttons:
                    btn_text = buttons[0].get_text(strip=True).lower()
                    if 'réserver' in btn_text or 'reserver' in btn_text:
                        has_real_reservation = True
                    else:
                        print(f"    Bouton '{btn_text}' (pas une vraie réservation)")
            
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
        
        if 'disponible_immediat' in statuses:
            return (True, city)
        elif 'disponible' in statuses:
            return (True, city)
        elif 'a_venir' in statuses:
            return ('soon', city)
        else:
            return (False, city)
            
    except Exception as e:
        print(f"Erreur lors de la vérification de {link}: {e}")
        return (None, city)

def main():
    start_time = time.time()
    
    links = get_residence_links()
    print(f"Trouvé {len(links)} résidences.")
    
    available_residences = []
    new_available_residences = []
    soon_residences = []

    # Charger l'état précédent
    previous_status = {}
    if os.path.exists('availability_status.json'):
        try:
            with open('availability_status.json', 'r') as f:
                raw_status = json.load(f)
                for key, value in raw_status.items():
                    if isinstance(value, bool):
                        rid = key.split('/')[-1]
                        previous_status[rid] = {'status': value, 'city': 'Ville inconnue', 'link': key}
                    elif isinstance(value, dict):
                        previous_status[key] = value
        except Exception as e:
            print(f"Erreur lors du chargement de l'état précédent: {e}")
            previous_status = {}

    current_status = {}
    
    for link in links:
        status, city = check_availability(link)
        residence_id = link.split('/')[-1]
        current_status[residence_id] = {'status': status, 'city': city, 'link': link}
        
        if status is True:
            residence_name = link.split('/')[-1].replace('-', ' ').title()
            available_residences.append(f"{residence_name}\n{city}\n{link}")
            
            was_available_before = previous_status.get(residence_id, {}).get('status') is True
            if not was_available_before:
                new_available_residences.append(f"{residence_name}\n{city}\n{link}")
                print(f"  => NOUVELLE disponibilité !")
            else:
                print(f"  => Toujours disponible")
        elif status == 'soon':
            residence_name = link.split('/')[-1].replace('-', ' ').title()
            was_soon_before = previous_status.get(residence_id, {}).get('status') == 'soon'
            if not was_soon_before:
                soon_residences.append(f"{residence_name}\n{city}\n{link}")
                print(f"  => NOUVELLE disponibilité à venir !")
            else:
                print(f"  => Toujours disponibilité à venir")
        elif status is False:
            print(f"  => Aucune disponibilité")
        else:
            print(f"  => Statut inconnu")
        
        time.sleep(0.5)  # Délai respectueux
    
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
        subject = f"Alerte - {len(new_available_residences)} dispo + {len(soon_residences)} à venir"
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
    
    elapsed = time.time() - start_time
    print(f"\nTerminé en {elapsed:.1f} secondes.")

if __name__ == "__main__":
    main()