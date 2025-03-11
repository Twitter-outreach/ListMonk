#!/usr/bin/env python3
"""
MongoDB to ListMonk Integration

This script extracts new users from MongoDB, formats them for ListMonk,
and exports them to a CSV file.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime

import pymongo
import requests

class MongoToListmonk:
    """MongoDB to ListMonk integration class."""
    
    def __init__(self, config_file):
        """Initialize with the given configuration file."""
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from the config file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def connect_to_mongo(self):
        """Connect to MongoDB and return the database object."""
        try:
            client = pymongo.MongoClient(self.config["mongo_uri"])
            db = client[self.config["mongo_db"]]
            return db
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None
    
    def get_last_sync_timestamp(self, db):
        """Get the timestamp of the last successful sync."""
        try:
            tracking_collection = db[self.config["tracking_collection"]]
            last_sync = tracking_collection.find_one({"_id": self.config["last_sync_key"]})
            
            if last_sync:
                return last_sync.get("timestamp")
            return None
        except Exception as e:
            print(f"Error getting last sync timestamp: {e}")
            return None
    
    def update_last_sync_timestamp(self, db):
        """Update the timestamp of the last successful sync."""
        try:
            tracking_collection = db[self.config["tracking_collection"]]
            current_time = datetime.utcnow()
            
            tracking_collection.update_one(
                {"_id": self.config["last_sync_key"]},
                {"$set": {"timestamp": current_time}},
                upsert=True
            )
            
            return True
        except Exception as e:
            print(f"Error updating last sync timestamp: {e}")
            return False
    
    def extract_new_users(self, db):
        """Extract new users from MongoDB since the last sync."""
        try:
            collection = db[self.config["mongo_collection"]]
            last_sync = self.get_last_sync_timestamp(db)
            
            query = {}
            if last_sync:
                query = {self.config["created_at_field"]: {"$gt": last_sync}}
            
            # Get all fields we need
            projection = {
                self.config["email_field"]: 1,
                self.config["name_field"]: 1,
                self.config["created_at_field"]: 1
            }
            
            users = list(collection.find(query, projection))
            print(f"Found {len(users)} new users since last sync")
            
            return users
        except Exception as e:
            print(f"Error extracting users: {e}")
            return []
    
    def export_to_csv(self, users):
        """Export users to a CSV file."""
        try:
            # Create temp directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config["raw_csv_path"]), exist_ok=True)
            
            with open(self.config["raw_csv_path"], 'w', newline='') as f:
                # Define CSV fields
                fieldnames = [
                    self.config["email_field"],
                    self.config["name_field"],
                    self.config["created_at_field"]
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write user data
                for user in users:
                    row = {
                        self.config["email_field"]: user.get(self.config["email_field"], ""),
                        self.config["name_field"]: user.get(self.config["name_field"], ""),
                        self.config["created_at_field"]: user.get(self.config["created_at_field"], "")
                    }
                    writer.writerow(row)
            
            print(f"Exported {len(users)} users to {self.config['raw_csv_path']}")
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def format_csv(self):
        """Format the raw CSV file for ListMonk."""
        try:
            # Import the CSV formatter module
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            import csv_formatter
            
            # Process the CSV file
            result = csv_formatter.process_csv(
                self.config["raw_csv_path"],
                self.config["processed_csv_path"]
            )
            
            return result
        except Exception as e:
            print(f"Error formatting CSV: {e}")
            return False
    
    def run(self, skip_timestamp_update=False):
        """Run the integration process."""
        print(f"Starting MongoDB to ListMonk integration at {datetime.now()}")
        
        # Connect to MongoDB
        db = self.connect_to_mongo()
        if db is None:
            return False
        
        # Extract new users
        users = self.extract_new_users(db)
        if not users:
            print("No new users found")
            return True
        
        # Export users to CSV
        if not self.export_to_csv(users):
            return False
        
        # Format CSV for ListMonk
        if not self.format_csv():
            return False
        
        # Update last sync timestamp
        if not skip_timestamp_update and not self.update_last_sync_timestamp(db):
            return False
        
        print("MongoDB to ListMonk integration completed successfully")
        return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='MongoDB to ListMonk Integration')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--extract-only', action='store_true', help='Only extract and format users, don\'t update timestamp')
    parser.add_argument('--update-timestamp', action='store_true', help='Only update the last sync timestamp')
    args = parser.parse_args()
    
    integration = MongoToListmonk(args.config)
    
    if args.update_timestamp:
        # Only update the timestamp
        db = integration.connect_to_mongo()
        if db is None:
            sys.exit(1)
        success = integration.update_last_sync_timestamp(db)
        sys.exit(0 if success else 1)
    elif args.extract_only:
        # Only extract and format users
        db = integration.connect_to_mongo()
        if db is None:
            sys.exit(1)
        
        # Extract new users
        users = integration.extract_new_users(db)
        if not users:
            print("No new users found")
            sys.exit(0)
        
        # Export users to CSV
        if not integration.export_to_csv(users):
            sys.exit(1)
        
        # Format CSV for ListMonk
        if not integration.format_csv():
            sys.exit(1)
        
        print("Successfully extracted and formatted users")
        sys.exit(0)
    else:
        # Run the full process except updating timestamp
        success = integration.run(skip_timestamp_update=True)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
