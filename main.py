import csv
import time
import random
import requests
from bs4 import BeautifulSoup
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from io import StringIO
import sys

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# --- CORE UTILITIES ---
def clean_user_id(user_id):
    if not isinstance(user_id, str):
        return None
    cleaned_id = re.sub(r'\D*(\d+)', r'\1', user_id)
    return cleaned_id if cleaned_id.isdigit() else None


def requests_retry_session(retries=5,
                           backoff_factor=1.5,
                           status_forcelist=(500, 502, 503, 504, 429),
                           session=None):
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


# --- SORTING AND FILE I/O ---
def sort_and_clean_csv(filename):
    try:
        with open(filename, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read().replace('\0', '')
    except FileNotFoundError:
        logging.warning(
            f"⚠️  File '{filename}' not found. Will be created upon scraping.")
        return
    except PermissionError:
        logging.error(f"❌ Permission denied to read '{filename}'.")
        return

    if not content.strip():
        logging.warning("⚠️  File is empty, nothing to sort.")
        return

    reader = csv.reader(StringIO(content))
    try:
        header = next(reader)
    except StopIteration:
        return

    sorted_data, invalid_rows = [], []
    seen_ids = set()
    duplicates_found = 0

    for row in reader:
        if not row or not row[0].strip():
            continue

        cleaned_id = clean_user_id(row[0])

        if cleaned_id:
            if cleaned_id not in seen_ids:
                row[0] = cleaned_id
                sorted_data.append(row)
                seen_ids.add(cleaned_id)
            else:
                duplicates_found += 1
        else:
            invalid_rows.append(row)

    if duplicates_found > 0:
        logging.info(
            f"ℹ️  Found and removed {duplicates_found} duplicate user entries."
        )

    sorted_data.sort(key=lambda r: int(r[0]))

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(sorted_data)
            if invalid_rows:
                writer.writerows(invalid_rows)
        logging.info("✅ CSV cleaned, de-duplicated, and sorted successfully.")
    except IOError as e:
        logging.error(f"❌ Failed to write sorted data to '{filename}': {e}")


# --- SCRAPING AND PARSING ---
def scrape_user_details(user_id):
    url = f"https://www.enkord.com/account/{user_id}/"
    try:
        time.sleep(random.uniform(1.0, 3.0))
        session = requests_retry_session()
        response = session.get(url, timeout=20)

        if response.status_code == 429:
            logging.warning(f"🛑 Rate limit hit for ID {user_id}. Retrying...")
            return None

        response.raise_for_status()
        return parse_user_details(response.text, user_id)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"❌ User not found: ID {user_id}")
        else:
            logging.error(f"❌ HTTP Error for ID {user_id}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Network error for ID {user_id}: {e}")
    return None


def parse_user_details(html_content, user_id):
    soup = BeautifulSoup(html_content, 'html.parser')
    user_info = soup.find('div', class_='account-info')
    if not user_info:
        return {
            'User ID': user_id,
            'Enkord account full name': 'N/A',
            'Registered': 'N/A'
        }

    name_tag = user_info.find('b')
    name = name_tag.text.strip() if name_tag else "N/A"

    registered_span = user_info.find('span', title=True)
    registered = registered_span['title'] if registered_span else "N/A"

    return {
        'User ID': user_id,
        'Enkord account full name': name,
        'Registered': registered
    }


# --- MODULE 1: SCRAPE MISSING IDs ---
def write_to_csv(user_details, filename):
    try:
        file_exists = False
        try:
            with open(filename, 'r') as f:
                file_exists = bool(f.read(1))
        except FileNotFoundError:
            pass

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'User ID', 'Enkord account full name', 'Registered'
            ]
            writer = csv.DictWriter(csvfile,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            writer.writerow(user_details)
    except IOError as e:
        logging.error(f"❌ Could not write to '{filename}': {e}")


def process_new_user(user_id, filename):
    user_details = scrape_user_details(user_id)
    if user_details:
        logging.info(f"✅ Fetched new user: ID {user_id}")
        write_to_csv(user_details, filename)


def run_missing_ids_scraper(filename):
    start_id, end_id = 333333, 999999
    existing_user_ids = set()
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_id = clean_user_id(row.get('User ID'))
                if user_id:
                    existing_user_ids.add(int(user_id))
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"❌ Error reading existing IDs from '{filename}': {e}")
        return

    missing_user_ids = [
        uid for uid in range(start_id, end_id + 1)
        if uid not in existing_user_ids
    ]
    if not missing_user_ids:
        logging.info("✅ No missing user IDs found in the range.")
        return

    logging.info(
        f"Found {len(missing_user_ids)} IDs from {start_id} to {end_id}.")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(process_new_user, uid, filename): uid
            for uid in missing_user_ids
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(
                    f"❌ Worker thread failed for ID {futures[future]}: {e}")


# --- MODULE 2: RE-CHECK ANONYMOUS ACCOUNTS ---
def recheck_anonymous_user(user_id):
    user_details = scrape_user_details(user_id)
    if user_details and not user_details.get(
            'Enkord account full name', '').lower().startswith("anonymous#"):
        logging.info(
            f"✅ Name updated for ID {user_id}: {user_details['Enkord account full name']}"
        )
        return user_details
    elif user_details:
        logging.info(f"☑️  User ID: {user_id} is still Anonymous.")
    return None


def run_anonymous_checker(filename):
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            all_data = list(csv.DictReader(file))
            if not all_data:
                logging.warning(
                    "⚠️  CSV file is empty. Cannot check for anonymous accounts."
                )
                return
            fieldnames = all_data[0].keys()
    except FileNotFoundError:
        logging.error(f"❌ Cannot check: File '{filename}' not found.")
        return
    except (IndexError, KeyError):
        logging.error(f"❌ CSV file '{filename}' seems malformed or empty.")
        return

    accounts_to_check = [
        row for row in all_data if str(row.get(
            'Enkord account full name', '')).lower().startswith("anonymous#")
    ]
    if not accounts_to_check:
        logging.info("✅ No 'Anonymous' accounts found to check.")
        return

    logging.info(
        f"Found {len(accounts_to_check)} 'Anonymous' accounts to re-check.")
    updated_details = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_id = {
            executor.submit(recheck_anonymous_user, row['User ID']):
            row['User ID']
            for row in accounts_to_check
        }

        for future in as_completed(future_to_id):
            try:
                result = future.result()
                if result:
                    updated_details[result['User ID']] = result
            except Exception as e:
                logging.error(
                    f"❌ Worker thread failed during anonymous check for ID {future_to_id[future]}: {e}"
                )

    if not updated_details:
        logging.info(
            "⚠️  No 'Anonymous' accounts were updated after re-checking.")
        return

    logging.info(
        f"Found {len(updated_details)} updated names. Updating CSV file...")
    final_data = [updated_details.get(row['User ID'], row) for row in all_data]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file,
                                    fieldnames=fieldnames,
                                    extrasaction='ignore')
            writer.writeheader()
            writer.writerows(final_data)
        logging.info("✅ CSV file updated with new names.")
    except IOError as e:
        logging.error(f"❌ Failed to write updates to CSV: {e}")


# --- MAIN EXECUTION ---
def main_menu(filename):
    while True:
        choice = input(
            "\n[1] Scrape Missing IDs \n[2] Re-check Anonymous \n[3] Exit \n> "
        ).strip()

        if choice == '1':
            run_missing_ids_scraper(filename)
            logging.info(
                "✅ Scraping complete. Re-sorting and de-duplicating file...")
            sort_and_clean_csv(filename)
        elif choice == '2':
            run_anonymous_checker(filename)
            logging.info(
                "✅ Anonymous check complete. Re-sorting and de-duplicating file..."
            )
            sort_and_clean_csv(filename)
        elif choice == '3':
            break
        else:
            logging.warning("⚠️  Invalid choice. Please enter 1, 2, or 3.")
    logging.info("✅ Exiting program.")


if __name__ == "__main__":
    input_filename = './dataset/tt2_players.csv'
    try:
        logging.info(
            "Initializing: Cleaning, sorting, and de-duplicating existing CSV."
        )
        sort_and_clean_csv(input_filename)
        main_menu(input_filename)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"❌ A critical unexpected error occurred: {e}")
        sys.exit(1)
