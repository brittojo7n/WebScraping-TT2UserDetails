import csv
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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
    """Remove rows with anonymous accounts from the CSV file."""
    non_anonymous_data = []

    # Read existing CSV data and filter out anonymous accounts
    with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Logging each row for debugging
            logging.debug(f"Reading row: {row}")
            # Checking if the name starts with "Anonymous#", ignoring case and trimming
            if not row['Enkord account full name'].strip().lower().startswith("anonymous#"):
                non_anonymous_data.append(row)

    # Write back only non-anonymous data
    with open('tt2_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(non_anonymous_data)


def write_to_csv(user_details):
    """Write the new/updated user details to the CSV."""
    with open('tt2_players.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(user_details.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:  # Check if the file is empty
            writer.writeheader()

        writer.writerow(user_details)


def check_for_anonymous_accounts():
    """Checks and collects Anonymous accounts from the CSV."""
    anonymous_accounts = []

    with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Logging each row for debugging
            logging.debug(f"Checking row for anonymous: {row}")
            # Checking if the name starts with "Anonymous#", ignoring case and trimming
            if row['Enkord account full name'].strip().lower().startswith("anonymous#"):
                logging.info(f"Anonymous account found: {row['Enkord account full name']}")
                anonymous_accounts.append(row)

    logging.info(f"Total anonymous accounts found: {len(anonymous_accounts)}")
    return anonymous_accounts


def recheck_anonymous_accounts(anonymous_accounts):
    """Recheck anonymous accounts for their true names."""
    iteration = 0
    max_retries = 5

    for attempt in range(max_retries):
        iteration += 1
        print(f"Rechecking Anonymous accounts (Attempt {iteration}/{max_retries})")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            for account in anonymous_accounts:
                user_id = account['User ID']
                executor.submit(recheck_user, user_id)
                time.sleep(random.uniform(0.2, 0.8))

        # Sleep before next recheck attempt
        time.sleep(10)  # Example delay between rechecks

        # Exit if there are no more Anonymous accounts left
        anonymous_accounts = check_for_anonymous_accounts()
        if not anonymous_accounts:
            print("All Anonymous accounts have been updated.")
            break


def recheck_user(user_id):
    """Recheck a user account to see if their true name is available."""
    user_details = scrape_user_details(user_id)
    if user_details and not user_details['Enkord account full name'].lower().startswith("anonymous#"):
        logging.info(f"True name found for User ID: {user_id}")
        write_to_csv(user_details)  # Update with true name


if __name__ == "__main__":
    # Step 1: Filter out anonymous accounts from CSV
    filter_out_anonymous_from_csv()

    # Step 2: Check for anonymous accounts
    anonymous_accounts = check_for_anonymous_accounts()

    # Step 3: If there are anonymous accounts, start rechecking periodically
    if anonymous_accounts:
        recheck_anonymous_accounts(anonymous_accounts)
    else:
        print("No Anonymous accounts found.")
