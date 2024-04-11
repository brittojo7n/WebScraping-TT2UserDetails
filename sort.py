import csv

def sort_csv(filename):
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)
        sorted_data = sorted(reader, key=lambda row: int(row[0]))
    return sorted_data

def write_sorted_csv(sorted_data, output_filename):
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['User ID', 'Enkord account full name', 'Registered'])
        writer.writerows(sorted_data)

input_filename = 'tt2_players.csv'
output_filename = 'tt2_players.csv'

sorted_data = sort_csv(input_filename)

write_sorted_csv(sorted_data, output_filename)

print("Data sorted and written to", output_filename)
