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
    """Scrape user details from the webpage."""
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
    """Parse the scraped HTML to extract user details."""
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
    """Recheck each anonymous account in the CSV and only update if it's no longer anonymous."""
    accounts_to_check = []

    # Step 1: Read existing CSV and find anonymous accounts (case-insensitive)
    try:
        with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
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

    # Step 2: Process each anonymous account and check if it's still anonymous
    if accounts_to_check:
        with ThreadPoolExecutor(max_workers=4) as executor:
            for account in accounts_to_check:
                user_id = account['User ID']
                executor.submit(recheck_and_update_user, user_id)
                time.sleep(random.uniform(0.2, 0.8))  # Simulate staggered processing
    else:
        logging.info("No Anonymous accounts found to check.")


def recheck_and_update_user(user_id):
    """Recheck a user account to see if their true name is available, then update CSV."""
    user_details = scrape_user_details(user_id)
    if user_details:
        if not user_details['Enkord account full name'].lower().startswith("anonymous#"):
            logging.info(f"True name found for User ID: {user_id} - {user_details['Enkord account full name']}")
            remove_previous_entry(user_id)  # Remove old entry from the CSV
            write_to_csv(user_details)  # Write updated details to the CSV
        else:
            logging.info(f"User ID: {user_id} is still Anonymous. No changes made.")


def remove_previous_entry(user_id):
    """Remove the previous entry of the given user ID from the CSV."""
    updated_data = []

    try:
        # Read the existing CSV and filter out the user with the matching ID
        with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['User ID'] != str(user_id):  # Keep only rows that do not match the user ID
                    updated_data.append(row)

        # Write the filtered data back to the CSV
        with open('tt2_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_data)
    except FileNotFoundError:
        logging.warning("CSV file not found. No previous entries to remove.")
    except Exception as e:
        logging.error(f"Error removing previous entry: {e}")


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
    # Recheck anonymous accounts one by one and only update if they are no longer anonymous
    check_and_update_anonymous_accounts()
