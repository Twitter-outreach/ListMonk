# MongoDB to ListMonk Integration

This integration automatically imports new users from MongoDB into ListMonk on a daily basis.

## Features

- **Incremental Import**: Only imports new users since the last successful import
- **Automatic Scheduling**: Runs daily at 12:30 AM EST via cron job
- **Confirmed Subscribers**: Imports users as confirmed subscribers (no confirmation emails)
- **Error Handling**: Robust error handling with detailed logs
- **Field Mapping**: Configurable field mapping between MongoDB and ListMonk

## Configuration

The integration is configured via the `config.json` file:

```json
{
    "mongo_uri": "mongodb://username:password@localhost:27017/?authSource=admin",
    "mongo_db": "your_database",
    "mongo_collection": "users",
    
    "email_field": "email",
    "name_field": "name",
    "created_at_field": "createdAt",
    
    "listmonk_api_url": "http://localhost:9000",
    "listmonk_username": "admin",
    "listmonk_password": "password",
    "listmonk_list_id": 1,
    
    "temp_dir": "/path/to/temp/dir",
    "raw_csv_path": "/path/to/temp/dir/mongo_users.csv",
    "processed_csv_path": "/path/to/temp/dir/listmonk_import.csv",
    
    "tracking_collection": "listmonk_sync",
    "last_sync_key": "last_sync_timestamp"
}
```

### Configuration Options

- **MongoDB Settings**:
  - `mongo_uri`: MongoDB connection string
  - `mongo_db`: Database name
  - `mongo_collection`: Collection containing user data
  - `email_field`: Field name containing email addresses
  - `name_field`: Field name containing user names
  - `created_at_field`: Field name containing user creation date

- **ListMonk Settings**:
  - `listmonk_api_url`: URL of the ListMonk instance
  - `listmonk_username`: ListMonk admin username
  - `listmonk_password`: ListMonk admin password
  - `listmonk_list_id`: ID of the list to import users into

- **File Paths**:
  - `temp_dir`: Directory for temporary files
  - `raw_csv_path`: Path for the raw CSV export from MongoDB
  - `processed_csv_path`: Path for the processed CSV ready for ListMonk import

- **Tracking Settings**:
  - `tracking_collection`: Collection name for tracking import status
  - `last_sync_key`: Key for storing the last successful import timestamp

## How It Works

1. The script connects to MongoDB and queries for users created after the last successful import
2. New users are exported to a CSV file
3. The CSV is processed to match ListMonk's expected format
4. The processed CSV is imported into ListMonk via the web interface
5. Upon successful import, the last sync timestamp is updated in MongoDB

This ensures that only new users are imported on each run, preventing duplicate imports.

## Running Manually

To run the integration manually:

```bash
cd /root/CascadeProjects/listmonk/scripts
./run_mongo_import.sh
```

## Logs

Logs are stored in the `/root/CascadeProjects/listmonk/logs` directory with filenames in the format `mongo_import_YYYYMMDD_HHMMSS.log`. Logs older than 7 days are automatically deleted.

## Cron Job

The integration is scheduled to run daily at 12:30 AM EST via a cron job in `/etc/cron.d/mongo_listmonk`.

## Troubleshooting

If you encounter issues:

1. Check the log files for error messages
2. Verify MongoDB and ListMonk credentials in the config file
3. Ensure the ListMonk instance is running and accessible
4. Check that the MongoDB collection contains the expected fields
