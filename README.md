# Totem Tribe 2 UserDetails Scraping

## Overview
This repository contains a Python script (`main.py`) for scraping user details from the Totem Tribe 2 website and storing them in a CSV file (`tt2.csv`). The dataset includes user IDs, account names, and registration dates and times.

**Note:** This project is purely educational and serves as an example of web scraping techniques. The creator of this script and dataset is not affiliated with Enkord, Ltd., the company behind Totem Tribe 2. Please be aware that web scraping may violate a website's Terms of Service.

## Usage
1. Clone this repository to your local machine:
   ```
   git clone https://github.com/brittojo7n/totem-tribe-2-userdetails.git
   ```

2. Navigate to the project directory:
   ```
   cd totem-tribe-2-userdetails
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
- `UserID`: Unique identifier for each user.
- `AccountName`: Username associated with the account.
- `RegisteredDateTime`: Date and time when the account was registered.

## Disclaimer
This project is for educational purposes only. The creator of this script and dataset is not responsible for any misuse or violation of website Terms of Service resulting from the use of this script.

**Warning:** Web scraping can lead to legal issues if not used responsibly and in compliance with a website's Terms of Service.

## Contribution
Contributions to this project are welcome! Feel free to open an issue or submit a pull request with any improvements or suggestions.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
