import csv

# Function to read the CSV file and return sorted data
def sort_csv(filename):
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file)
        # Skip the header row
        next(reader)
        # Sort rows based on the first column (User ID)
        sorted_data = sorted(reader, key=lambda row: int(row[0]))
    return sorted_data

# Function to write sorted data to a new CSV file
def write_sorted_csv(sorted_data, output_filename):
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write header row
        writer.writerow(['User ID', 'Enkord account full name', 'Registered'])
        # Write sorted data
        writer.writerows(sorted_data)

# Input and output filenames
input_filename = 'tt2_players.csv'
output_filename = 'tt2_players_s.csv'

# Sort the data
sorted_data = sort_csv(input_filename)

# Write sorted data to a new CSV file
write_sorted_csv(sorted_data, output_filename)

print("Data sorted and written to", output_filename)
