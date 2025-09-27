# Totem Tribe 2 UserDetails Scraping

## Overview
This repository contains a Python script (`main.py`) designed for scraping user details from the Totem Tribe 2 website. The scraped data is then stored in a CSV file (`dataset/tt2_players.csv`). The dataset includes user IDs, account names, and registration dates and times.

This project is automated to run every two hours using GitHub Actions, ensuring the dataset is regularly updated with the latest user information.

### What's the use of it?
It helps you find and friend anyone just by knowing their names. To do that head over to `https://totemtribe.com/account/{accoundId}` or `https://enkord.com/account/{accoundId}` replacing the `{accountId}` with the one you found out from the dataset by searching for the name.

## Automation
This repository is configured with a GitHub Actions workflow (`.github/workflows/run.yml`) that automatically runs the scraping script every two hours. The workflow executes the `python main.py --mode all` command, ensuring that the `dataset/tt2_players.csv` file is consistently updated with new user entries.

## Dataset
The `dataset/tt2_players.csv` file contains the following columns:
-   `User ID`: Unique identifier for each user.
-   `Enkord account full name`: Account name associated with the user.
-   `Registered`: Date and time when the account was registered.
