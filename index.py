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
            response.raise_for_status(
            )  # Raise exception for other bad responses (4xx or 5xx)
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
    return None


def parse_user_details(html_content, user_id):
    user_details = {'User ID': user_id}
    soup = BeautifulSoup(html_content, 'html.parser')

    user_info = soup.find('div', class_='account-info')
    if user_info:
        user_details['Enkord account full name'] = user_info.find(
            'b').text.strip()
        registered_span = user_info.find('span', title=True)
        if registered_span:
            registered_title = registered_span['title']
            user_details['Registered'] = registered_title

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


def process_user(user_id):
    user_details = scrape_user_details(user_id)
    if user_details:
        logging.info(f"Fetched user details for ID: {user_id}")
        write_to_csv(user_details)


def write_to_csv(user_details):
    with open('tt2_players.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(user_details.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        writer.writerow(user_details)


def check_and_scrape_missing_user_ids():
    start_id = 523000  # Initial start ID
    end_id = 999999  # Initial end ID
    iteration = 0

    while True:
        existing_user_ids = set()

        with open('tt2_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_user_ids.add(int(row['User ID']))

        missing_user_ids = [
            user_id for user_id in range(start_id, end_id + 1)
            if user_id not in existing_user_ids
        ]

        if missing_user_ids:
            iteration += 1
            print(f"Iteration {iteration}: Range {start_id} - {end_id}")
            with ThreadPoolExecutor(max_workers=4) as executor:
                for user_id in missing_user_ids:
                    executor.submit(process_user, user_id)
                    time.sleep(random.uniform(0.2, 0.8))

        else:
            print("No missing user IDs found. Exiting loop.")
            break


if __name__ == "__main__":
    check_and_scrape_missing_user_ids()
