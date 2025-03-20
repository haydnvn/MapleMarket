import re
import csv

def extract_names_from_text(file_path, output_csv):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove all HTML-like tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Split by new lines and filter out empty lines
    items = [line.strip() for line in content.split('\n') if line.strip()]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for item in items:
            writer.writerow([item])
    
    print(f"Extracted {len(items)} items and saved to {output_csv}")

# Example usage
extract_names_from_text('test.txt', 'output.csv')