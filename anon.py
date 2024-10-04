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
            response.raise_for_status()  # Raise exception for other bad responses (4xx or 5xx)
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


def filter_out_anonymous_from_csv():
    """Remove rows with anonymous accounts (case-insensitive) from the CSV file and return non-anonymous data."""
    non_anonymous_data = []
    anonymous_accounts = []

    try:
        with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Case-insensitive check for "anonymous#"
                if row['Enkord account full name'].lower().startswith("anonymous#"):
                    anonymous_accounts.append(row)
                else:
                    non_anonymous_data.append(row)

        # Write back only non-anonymous data to the CSV file
        with open('tt2_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(non_anonymous_data)
    except FileNotFoundError:
        logging.warning(f"File 'tt2_players.csv' not found. Starting fresh.")
    except Exception as e:
        logging.error(f"Error reading or writing to file: {e}")

    return anonymous_accounts  # Return the list of removed anonymous accounts


def recheck_and_update_anonymous_accounts(anonymous_accounts):
    """Recheck anonymous accounts, fetch their true names, and write the updated data to CSV."""
    logging.info(f"Rechecking {len(anonymous_accounts)} anonymous accounts...")

    with ThreadPoolExecutor(max_workers=4) as executor:
        for account in anonymous_accounts:
            user_id = account['User ID']
            executor.submit(recheck_user, user_id)
            time.sleep(random.uniform(0.2, 0.8))  # Simulate staggered processing


def recheck_user(user_id):
    """Recheck a user account, fetch the true name if available, and write updated data to CSV."""
    user_details = scrape_user_details(user_id)
    if user_details:
        if not user_details['Enkord account full name'].lower().startswith("anonymous#"):
            logging.info(f"True name found for User ID: {user_id} - {user_details['Enkord account full name']}")
        else:
            logging.info(f"No change for User ID: {user_id}, still Anonymous.")
        
        write_to_csv(user_details)


def write_to_csv(user_details):
    """Append the new/updated user details to the CSV."""
    try:
        with open('tt2_players.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(user_details.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # If the file is empty, write the header
            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerow(user_details)
    except Exception as e:
        logging.error(f"Error writing to CSV: {e}")


if __name__ == "__main__":
    # Step 1: Remove anonymous accounts (case-insensitive) from the CSV and get the list of removed accounts
    anonymous_accounts = filter_out_anonymous_from_csv()

    # Step 2: Recheck each anonymous account for updates and write the updated info to the CSV
    if anonymous_accounts:
        recheck_and_update_anonymous_accounts(anonymous_accounts)
    else:
        logging.info("No Anonymous accounts found.")
