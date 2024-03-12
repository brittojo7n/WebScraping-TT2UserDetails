# Totem Tribe 2 UserDetails Scraping

## Overview
This repository contains a Python script (`main.py`) designed for scraping user details from the Totem Tribe 2 website. The scraped data is then stored in a CSV file (`tt2.csv`). The dataset includes user IDs, account names, and registration dates and times.

Additionally, a self-hosted web application (`app.py`) is provided to allow users to view specific user details. By accessing `localhost:80` in a web browser and entering the account name, users can retrieve detailed information about the user from the scraped dataset.

**Note:** This project is purely educational and serves as an example of web scraping techniques. The creator of this script and dataset is not affiliated with Enkord, Ltd., the company behind Totem Tribe 2. Please be aware that web scraping may violate a website's Terms of Service.

## Usage
1. Clone this repository to your local machine:
   ```
   git clone https://github.com/brittojo7n/TotemTribe2-UserDetails.git
   ```

2. Navigate to the project directory:
   ```
   cd TotemTribe2-UserDetails
   ```

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the `main.py` script to update the `tt2.csv` file with newer user entries:
   ```
   python main.py
   ```

5. Optionally, customize the range of user IDs being checked and appended to `tt2.csv` by editing the `main.py` file.

## Dataset
The `tt2.csv` file contains the following columns:
- `User ID`: Unique identifier for each user.
- `Enkord account full name`: Account name associated with the user.
- `Registered`: Date and time when the account was registered.

## Disclaimer
This project is for educational purposes only. The creator of this script and dataset is not responsible for any misuse or violation of website Terms of Service resulting from the use of this script.

**Warning:** Web scraping can lead to legal issues if not used responsibly and in compliance with a website's Terms of Service.