import csv
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def requests_retry_session(retries=5,
                           backoff_factor=1.5,
                           status_forcelist=(500, 502, 503, 504, 429),
                           session=None):
    """Create a retry-enabled session with safe backoff."""
    session = session or requests.Session()
    retry = Retry(total=retries,
                  read=retries,
                  connect=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def scrape_user_details(user_id):
    """Scrape user details for the given user_id."""
    url = f"https://www.enkord.com/account/{user_id}/"

    try:
        time.sleep(random.uniform(1.0, 3.0))

        response = requests_retry_session().get(url)

        if response.status_code == 200:
            html_content = response.text
            user_details = parse_user_details(html_content, user_id)
            return user_details

        elif response.status_code == 404:
            logging.warning(f"User not found: ID {user_id}")
        elif response.status_code == 429:
            logging.warning("Rate limit hit. Sleeping for safety...")
            time.sleep(5)
        else:
            response.raise_for_status()

    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")

    return None


def parse_user_details(html_content, user_id):
    """Parse the HTML content and extract user details."""
    user_details = {'User ID': user_id}
    soup = BeautifulSoup(html_content, 'html.parser')

    user_info = soup.find('div', class_='account-info')
    if user_info:
        user_details['Enkord account full name'] = user_info.find(
            'b').text.strip()

        registered_span = user_info.find('span', title=True)
        if registered_span:
            user_details['Registered'] = registered_span['title']

        accounts_in_games_div = user_info.find('div', class_='text-box')
        if accounts_in_games_div:
            accounts_in_games_ul = accounts_in_games_div.find('ul')
            if accounts_in_games_ul:
                accounts_in_games = accounts_in_games_ul.find_all('li')
                games_list = []

                for account in accounts_in_games:
                    game_name = account.find('b').text.strip()
                    accounts_list = [
                        item.text.strip()
                        for item in account.find_all('li')[1:]
                    ]
                    games_list.append({game_name: accounts_list})

                user_details['Accounts in games'] = games_list

    return user_details


def write_to_csv(user_details):
    """Write user details to the CSV file."""
    with open('tt2_players.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(user_details.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow(user_details)


def process_user(user_id):
    """Process a single user by scraping and writing to CSV."""
    user_details = scrape_user_details(user_id)
    if user_details:
        logging.info(f"✅ Fetched ID: {user_id}")
        write_to_csv(user_details)


def check_and_scrape_missing_user_ids():
    """Check for missing user IDs and scrape them using threading."""
    start_id = 0
    end_id = 999999
    iteration = 0

    while True:
        existing_user_ids = set()

        try:
            with open('tt2_players.csv', newline='',
                      encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        user_id = int(row['User ID'])
                        existing_user_ids.add(user_id)
                    except ValueError:
                        logging.warning(f"Invalid User ID: {row['User ID']}")
        except FileNotFoundError:
            logging.info("No CSV found, starting fresh.")

        missing_user_ids = [
            user_id for user_id in range(start_id, end_id + 1)
            if user_id not in existing_user_ids
        ]

        if missing_user_ids:
            iteration += 1
            logging.info(
                f"Iteration {iteration}: Scraping {len(missing_user_ids)} IDs")

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(process_user, user_id): user_id
                    for user_id in missing_user_ids
                }

                for future in as_completed(futures):
                    user_id = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Error processing ID {user_id}: {e}")

        else:
            logging.info("No missing IDs found. Exiting.")
            break


if __name__ == "__main__":
    check_and_scrape_missing_user_ids()
