# Totem Tribe 2 UserDetails Scraping

## Overview
This repository contains a Python script (`main.py`) designed for scraping user details from the Totem Tribe 2 website. The scraped data is then stored in a CSV file (`dataset/tt2_players.csv`). The dataset includes user IDs, account names, and registration dates and times.

This project is automated to run every two hours using GitHub Actions, ensuring the dataset is regularly updated with the latest user information.

**Note:** This project is purely educational and serves as an example of web scraping techniques. The creator of this script and dataset is not affiliated with Enkord, Ltd., the company behind Totem Tribe 2. Please be aware that web scraping may violate a website's Terms of Service.

## Usage
1.  Clone this repository to your local machine:
    ```
    git clone https://github.com/brittojo7n/TotemTribe2-UserDetails.git
    ```

2.  Navigate to the project directory:
    ```
    cd TotemTribe2-UserDetails
    ```

3.  Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```

4.  Run the `main.py` script with the desired mode:
    * To scrape for new user IDs that are missing from the dataset:
        ```
        python main.py --mode missing
        ```
    * To re-check accounts that were previously scraped as "Anonymous" to see if they have been updated:
        ```
        python main.py --mode anonymous
        ```
    * To run both the 'missing' and 'anonymous' modes sequentially:
        ```
        python main.py --mode all
        ```

5.  Optionally, you can customize the range of user IDs to be checked by editing the `start_id` and `end_id` variables within the `main.py` file.

## Automation
This repository is configured with a GitHub Actions workflow (`.github/workflows/run.yml`) that automatically runs the scraping script every two hours. The workflow executes the `python main.py --mode all` command, ensuring that the `dataset/tt2_players.csv` file is consistently updated with new user entries and any changes to previously anonymous accounts.

## Dataset
The `dataset/tt2_players.csv` file contains the following columns:
-   `User ID`: Unique identifier for each user.
-   `Enkord account full name`: Account name associated with the user.
-   `Registered`: Date and time when the account was registered.

## Disclaimer
This project is for educational purposes only. The creator of this script and dataset is not responsible for any misuse or violation of website Terms of Service resulting from the use of this script.

**Warning:** Web scraping can lead to legal issues if not used responsibly and in compliance with a website's Terms of Service.
