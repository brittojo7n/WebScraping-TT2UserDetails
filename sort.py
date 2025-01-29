import csv
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def clean_user_id(user_id):
    # Remove non-numeric characters from the start of the User ID
    cleaned_id = re.sub(r'\D*(\d+)', r'\1', user_id)
    return cleaned_id if cleaned_id.isdigit() else None

def sort_csv(filename):
    sorted_data = []
    invalid_rows = []

    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the header row

        for row in reader:
            cleaned_id = clean_user_id(row[0])
            if cleaned_id:
                row[0] = cleaned_id  # Update the User ID with the cleaned version
                sorted_data.append(row)
            else:
                logging.warning(f"Invalid User ID found: {row[0]}. Moving row to the bottom: {row}")
                invalid_rows.append(row)

    # Sort the valid rows by "User ID"
    sorted_data = sorted(sorted_data, key=lambda row: int(row[0]))

    return header, sorted_data, invalid_rows

def overwrite_sorted_csv(header, sorted_data, invalid_rows, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header row
        writer.writerows(sorted_data)  # Write the sorted valid rows
        writer.writerows(invalid_rows)  # Append invalid rows at the bottom

    logging.info(f"Sorted data with invalid rows at the bottom updated in {filename}.")

input_filename = 'tt2_players.csv'

# Sort the CSV and handle invalid rows
header, sorted_data, invalid_rows = sort_csv(input_filename)

# Overwrite the same file with sorted data
overwrite_sorted_csv(header, sorted_data, invalid_rows, input_filename)

print(f"Data sorted with invalid User IDs fixed and remaining invalid rows moved to the bottom in {input_filename}")
