import csv
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def requests_retry_session(
        retries=5,
        backoff_factor=1,
        status_forcelist=(500, 502, 503, 504),
        session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def scrape_user_details(user_id):
    url = f"https://www.enkord.com/account/{user_id}/"
    try:
        response = requests_retry_session().get(url)
        if response.status_code == 200:
            html_content = response.text
            user_details = parse_user_details(html_content, user_id)
            return user_details
        elif response.status_code == 404:
            logging.warning(f"User details not found for ID: {user_id}")
        else:
            response.raise_for_status()  
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
    return None


def parse_user_details(html_content, user_id):
    user_details = {'User ID': user_id}
    soup = BeautifulSoup(html_content, 'html.parser')

    user_info = soup.find('div', class_='account-info')
    if user_info:
        user_details['Enkord account full name'] = user_info.find('b').text.strip()
        registered_span = user_info.find('span', title=True)
        if registered_span:
            registered_title = registered_span['title']
            user_details['Registered'] = registered_title

    return user_details


def check_and_update_anonymous_accounts():
    accounts_to_check = []

    try:
        with open('./dataset/tt2_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Enkord account full name'].lower().startswith("anonymous#"):
                    accounts_to_check.append(row)
    except FileNotFoundError:
        logging.warning("CSV file not found. Starting fresh.")
        return
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
        return

    if accounts_to_check:
        with ThreadPoolExecutor(max_workers=4) as executor:
            for account in accounts_to_check:
                user_id = account['User ID']
                executor.submit(recheck_and_update_user, user_id)
                time.sleep(random.uniform(0.2, 0.8)) 
    else:
        logging.info("No Anonymous accounts found to check.")


def recheck_and_update_user(user_id):
    user_details = scrape_user_details(user_id)
    if user_details:
        if not user_details['Enkord account full name'].lower().startswith("anonymous#"):
            logging.info(f"True name found for User ID: {user_id} - {user_details['Enkord account full name']}")
            remove_previous_entry(user_id)
            write_to_csv(user_details)
        else:
            logging.info(f"User ID: {user_id} is still Anonymous. No changes made.")


def remove_previous_entry(user_id):
    updated_data = []

    try:
        with open('./dataset/tt2_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['User ID'] != str(user_id):
                    updated_data.append(row)

        with open('./dataset/tt2_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_data)
    except FileNotFoundError:
        logging.warning("CSV file not found. No previous entries to remove.")
    except Exception as e:
        logging.error(f"Error removing previous entry: {e}")


def write_to_csv(user_details):
    try:
        with open('./dataset/tt2_players.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(user_details.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerow(user_details)
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")


if __name__ == "__main__":
    check_and_update_anonymous_accounts()