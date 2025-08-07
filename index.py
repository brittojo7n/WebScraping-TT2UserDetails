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

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Sorting and Cleaning Functions (from sort.py) ---

def clean_user_id(user_id):
    """Extracts the numerical part of a user ID string."""
    # Substitutes any non-digit characters at the beginning with an empty string
    cleaned_id = re.sub(r'\D*(\d+)', r'\1', user_id)
    return cleaned_id if cleaned_id.isdigit() else None


def sort_csv(filename):
    """
    Reads a CSV file, cleans user IDs, and sorts the data.
    Rows with invalid IDs are separated and moved to the end.
    """
    sorted_data = []
    invalid_rows = []

    try:
        with open(filename, 'r', encoding='utf-8', errors='replace') as file:
            # Read the file and remove any NULL bytes which can break CSV parsing
            content = file.read().replace('\0', '')
    except FileNotFoundError:
        logging.warning(f"File {filename} not found. A new file will be created during scraping.")
        return None, None, None

    reader = csv.reader(StringIO(content))

    try:
        header = next(reader)
    except StopIteration:
        logging.error("The file is empty after cleaning.")
        return [], [], []

    for row in reader:
        # Skip empty rows
        if not row or not row[0].strip():
            continue
        
        cleaned_id = clean_user_id(row[0])
        if cleaned_id:
            row[0] = cleaned_id
            sorted_data.append(row)
        else:
            logging.warning(
                f"Invalid User ID found: {row[0]}. Moving row to the bottom: {row}"
            )
            invalid_rows.append(row)

    # Sort the data numerically based on the cleaned user ID
    sorted_data = sorted(sorted_data, key=lambda r: int(r[0]))

    return header, sorted_data, invalid_rows


def overwrite_sorted_csv(header, sorted_data, invalid_rows, filename):
    """Overwrites the CSV file with the sorted data."""
    if not header:
        logging.error("No header found. Cannot overwrite the file.")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(sorted_data)
        writer.writerows(invalid_rows)

    logging.info(
        f"✅ Sorted data with invalid rows at the bottom updated in {filename}.")


# --- Web Scraping Functions (from index.py) ---

def requests_retry_session(retries=5,
                           backoff_factor=1.5,
                           status_forcelist=(500, 502, 503, 504, 429),
                           session=None):
    """Create a retry-enabled session with exponential backoff."""
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
    """Scrape user details for a given user_id."""
    url = f"https://www.enkord.com/account/{user_id}/"

    try:
        # Add a random delay to be respectful to the server
        time.sleep(random.uniform(1.0, 3.0))

        response = requests_retry_session().get(url, timeout=15)

        if response.status_code == 200:
            html_content = response.text
            user_details = parse_user_details(html_content, user_id)
            return user_details

        elif response.status_code == 404:
            logging.warning(f"❌ User not found: ID {user_id}")
        elif response.status_code == 429:
            logging.warning("🛑 Rate limit hit. The script will back off and retry.")
            # The retry session handles the sleep, but an extra log is useful
        else:
            # Raise an exception for other HTTP errors (e.g., 500, 503)
            response.raise_for_status()

    except requests.RequestException as e:
        logging.error(f"⚠ Error fetching {url}: {e}")

    return None


def parse_user_details(html_content, user_id):
    """Parse the HTML content and extract user details."""
    user_details = {'User ID': user_id}
    soup = BeautifulSoup(html_content, 'html.parser')

    user_info = soup.find('div', class_='account-info')
    if user_info:
        # Find user's full name
        name_tag = user_info.find('b')
        if name_tag:
            user_details['Enkord account full name'] = name_tag.text.strip()

        # Find registration date
        registered_span = user_info.find('span', title=True)
        if registered_span:
            user_details['Registered'] = registered_span['title']

        # Find games the user plays
        accounts_in_games_div = user_info.find('div', class_='text-box')
        if accounts_in_games_div:
            accounts_in_games_ul = accounts_in_games_div.find('ul')
            if accounts_in_games_ul:
                accounts_in_games = accounts_in_games_ul.find_all('li')
                games_list = []

                for account in accounts_in_games:
                    game_name_tag = account.find('b')
                    if game_name_tag:
                        game_name = game_name_tag.text.strip()
                        # Assuming the structure is consistent
                        accounts_list = [
                            item.text.strip()
                            for item in account.find_all('li')[1:]
                        ]
                        games_list.append({game_name: accounts_list})

                user_details['Accounts in games'] = games_list

    return user_details


def write_to_csv(user_details, filename):
    """Appends a dictionary of user details to the CSV file."""
    try:
        # Check if the file exists to determine if we need to write a header
        file_exists = False
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                if csvfile.read(1):
                    file_exists = True
        except FileNotFoundError:
            file_exists = False

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            # Dynamically get fieldnames from the keys of the dictionary
            # This makes the function more flexible if new fields are added
            fieldnames = list(user_details.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(user_details)
    except IOError as e:
        logging.error(f"Could not write to file {filename}: {e}")


def process_user(user_id, filename):
    """Process a single user: scrape details and write to CSV."""
    user_details = scrape_user_details(user_id)
    if user_details:
        logging.info(f"✅ Fetched ID: {user_id}")
        write_to_csv(user_details, filename)


def check_and_scrape_missing_user_ids(filename):
    """Check for missing user IDs in a range and scrape them using threading."""
    start_id = 533000
    end_id = 999999
    iteration = 0

    while True:
        existing_user_ids = set()

        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Ensure 'User ID' key exists and value is not None
                        if 'User ID' in row and row['User ID']:
                            user_id = int(row['User ID'])
                            existing_user_ids.add(user_id)
                    except (ValueError, TypeError):
                        logging.warning(f"Skipping invalid User ID in existing file: {row.get('User ID')}")
        except FileNotFoundError:
            logging.info("No existing CSV found, starting fresh.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading {filename}: {e}")
            return # Exit if we can't read the file

        missing_user_ids = [
            user_id for user_id in range(start_id, end_id + 1)
            if user_id not in existing_user_ids
        ]

        if missing_user_ids:
            iteration += 1
            logging.info(
                f"Iteration {iteration}: Found {len(missing_user_ids)} missing IDs to scrape."
            )

            with ThreadPoolExecutor(max_workers=6) as executor:
                # Submit scraping tasks to the thread pool
                futures = {
                    executor.submit(process_user, user_id, filename): user_id
                    for user_id in missing_user_ids
                }

                # Process results as they complete
                for future in as_completed(futures):
                    user_id = futures[future]
                    try:
                        future.result()  # Check for exceptions from the thread
                    except Exception as e:
                        logging.error(f"Error processing ID {user_id}: {e}")
        else:
            logging.info("✅ All user IDs in the specified range have been scraped. Exiting.")
            break


# --- Main Execution Block ---
if __name__ == "__main__":
    input_filename = './dataset/tt2_players.csv'

    # --- 1. Sort and Clean Existing Data First ---
    logging.info("--- Step 1: Cleaning and Sorting Existing CSV ---")
    header, sorted_data, invalid_rows = sort_csv(input_filename)

    if header is not None and sorted_data is not None:
        overwrite_sorted_csv(header, sorted_data, invalid_rows, input_filename)
    else:
        # This handles FileNotFoundError or an empty file
        logging.info("Proceeding without pre-sorting (file is new or empty).")

    # --- 2. Prompt User to Continue with Scraping ---
    logging.info("--- Step 2: User Confirmation ---")
    while True:
        try:
            choice = input("Proceed with scraping missing user IDs? (y/n): ").lower().strip()
            if choice in ['y', 'yes']:
                logging.info("--- Step 3: Starting Web Scraping ---")
                check_and_scrape_missing_user_ids(input_filename)
                break
            elif choice in ['n', 'no']:
                logging.info("Exiting program as requested.")
                sys.exit()
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
        except KeyboardInterrupt:
            logging.info("\nProgram interrupted by user. Exiting.")
            sys.exit()

