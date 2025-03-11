#!/usr/bin/env python3
"""
CSV Formatter for ListMonk

This module converts a MongoDB CSV export to the format expected by ListMonk.
"""

import csv
import json
import sys
from datetime import datetime

def process_csv(input_file, output_file):
    """
    Process the input CSV file and convert it to Listmonk format.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            # Setup CSV reader and writer
            reader = csv.DictReader(infile)
            
            # Write header row directly to ensure no quoting issues
            outfile.write('email,name,attributes,status\n')
            
            # Process each row
            for row in reader:
                email = row.get('email', '').strip()
                if not email:
                    continue  # Skip rows without email
                
                name = row.get('name', '').strip()
                created_at = row.get('createdAt', '').strip()
                
                # Extract first name if possible
                first_name = ''
                if name:
                    first_name = name.split()[0] if name.split() else ''
                
                # Create attributes dictionary
                attributes = {}
                
                # Add first name to attributes if available
                if first_name:
                    attributes['firstName'] = first_name
                
                # Add full name to attributes if available
                if name:
                    attributes['fullName'] = name
                
                # Add created date to attributes if available
                if created_at:
                    attributes['createdAt'] = created_at
                
                # Convert attributes to JSON string
                attributes_json = json.dumps(attributes)
                
                # Write the row with CSV quoting
                writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
                writer.writerow([email, name, attributes_json, 'confirmed'])
                
        print(f"Conversion completed successfully. Output saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_formatter.py input.csv [output.csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'listmonk_import.csv'
    
    if not process_csv(input_file, output_file):
        sys.exit(1)
