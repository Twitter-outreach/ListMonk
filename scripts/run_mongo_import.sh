#!/bin/bash

# MongoDB to ListMonk Import Script
# This script runs the MongoDB to ListMonk integration and logs the output

# Set up variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="${SCRIPT_DIR}/../logs"
TEMP_DIR="${SCRIPT_DIR}/../temp"
LOG_FILE="${LOG_DIR}/mongo_import_$(date +%Y%m%d_%H%M%S).log"
LISTMONK_DIR="/root/CascadeProjects/listmonk"
CONFIG_FILE="${SCRIPT_DIR}/config.json"

# Load environment variables
if [ -f "${SCRIPT_DIR}/.env" ]; then
    source "${SCRIPT_DIR}/.env"
else
    echo "Error: .env file not found in ${SCRIPT_DIR}"
    exit 1
fi

# Telegram notification settings - use environment variables
BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
GC_CHAT_ID="${TELEGRAM_CHAT_ID}"
TOPIC_ID="${TELEGRAM_TOPIC_ID}"

# Verify required environment variables
if [ -z "${BOT_TOKEN}" ] || [ -z "${GC_CHAT_ID}" ] || [ -z "${TOPIC_ID}" ]; then
    echo "Error: Required environment variables not set. Please check your .env file."
    exit 1
fi

# Create directories if they don't exist
mkdir -p "${LOG_DIR}"
mkdir -p "${TEMP_DIR}"

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "${LOG_FILE}"
}

# Function to send Telegram notification
send_telegram_notification() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${GC_CHAT_ID}" \
        -d "message_thread_id=${TOPIC_ID}" \
        -d "text=${message}" \
        -d "parse_mode=HTML" > /dev/null
}

# Start the import process
log "Starting MongoDB to ListMonk import process"

# Extract users from MongoDB and create CSV
log "Extracting users from MongoDB"
EXTRACT_OUTPUT=$(python3 "${SCRIPT_DIR}/mongo_to_listmonk.py" --config "${CONFIG_FILE}" --extract-only 2>&1)
EXTRACT_STATUS=$?
echo "${EXTRACT_OUTPUT}" | tee -a "${LOG_FILE}"

# Get the number of users extracted
USER_COUNT=$(echo "${EXTRACT_OUTPUT}" | grep -o "Found [0-9]* new users" | awk '{print $2}')
if [ -z "${USER_COUNT}" ]; then
    USER_COUNT=0
fi

# Check if CSV was created successfully
if [ ! -f "${TEMP_DIR}/listmonk_import.csv" ] && [ "${USER_COUNT}" -gt 0 ]; then
    ERROR_MSG="Error: CSV file was not created. Aborting import."
    log "${ERROR_MSG}"
    send_telegram_notification "❌ <b>ListMonk Import Failed</b>
${ERROR_MSG}
Time: $(date +"%Y-%m-%d %H:%M:%S")"
    exit 1
fi

# If no new users, send notification and exit
if [ "${USER_COUNT}" -eq 0 ]; then
    log "No new users found. Nothing to import."
    send_telegram_notification "ℹ️ <b>ListMonk Import Summary</b>
No new users found since last import.
Time: $(date +"%Y-%m-%d %H:%M:%S")"
    exit 0
fi

# Import the CSV into ListMonk using curl
log "Importing users into ListMonk"

# Get credentials from config file
LISTMONK_URL=$(grep -o '"listmonk_api_url": "[^"]*"' "${CONFIG_FILE}" | cut -d'"' -f4)
LISTMONK_USERNAME=$(grep -o '"listmonk_username": "[^"]*"' "${CONFIG_FILE}" | cut -d'"' -f4)
LISTMONK_PASSWORD=$(grep -o '"listmonk_password": "[^"]*"' "${CONFIG_FILE}" | cut -d'"' -f4)
LISTMONK_LIST_ID=$(grep -o '"listmonk_list_id": [0-9]*' "${CONFIG_FILE}" | awk '{print $2}')
LISTMONK_LIST_NAME=$(grep -o '"listmonk_list_name": "[^"]*"' "${CONFIG_FILE}" | cut -d'"' -f4 || echo "Default List")

# First, get a session cookie by logging in
log "Authenticating with ListMonk"
COOKIE_JAR="${TEMP_DIR}/listmonk_cookies.txt"
rm -f "${COOKIE_JAR}"

curl -s -c "${COOKIE_JAR}" -X POST \
  "${LISTMONK_URL}/admin/login" \
  -d "username=${LISTMONK_USERNAME}&password=${LISTMONK_PASSWORD}" > >(tee -a "${LOG_FILE}") 2>&1

if [ $? -ne 0 ]; then
    ERROR_MSG="Error: Failed to authenticate with ListMonk"
    log "${ERROR_MSG}"
    send_telegram_notification "❌ <b>ListMonk Import Failed</b>
${ERROR_MSG}
Users found: ${USER_COUNT}
Time: $(date +"%Y-%m-%d %H:%M:%S")"
    exit 1
fi

# Now import the CSV file
log "Uploading CSV file to ListMonk"
IMPORT_RESPONSE=$(curl -s -b "${COOKIE_JAR}" -X POST \
  "${LISTMONK_URL}/admin/import/subscribers" \
  -F "file=@${TEMP_DIR}/listmonk_import.csv" \
  -F "list_ids=${LISTMONK_LIST_ID}" \
  -F "overwrite=false" \
  -F "status=confirmed")

echo "${IMPORT_RESPONSE}" >> "${LOG_FILE}"

# Check if import was successful
if [[ "${IMPORT_RESPONSE}" == *"error"* ]]; then
    ERROR_MSG="Error: Import failed"
    log "${ERROR_MSG}"
    send_telegram_notification "❌ <b>ListMonk Import Failed</b>
${ERROR_MSG}
Users found: ${USER_COUNT}
Time: $(date +"%Y-%m-%d %H:%M:%S")"
    exit 1
else
    log "Import completed successfully"
    
    # Update the last sync timestamp
    log "Updating last sync timestamp"
    python3 "${SCRIPT_DIR}/mongo_to_listmonk.py" --config "${CONFIG_FILE}" --update-timestamp > >(tee -a "${LOG_FILE}") 2>&1
    
    # Send success notification
    send_telegram_notification "✅ <b>ListMonk Import Successful</b>
Successfully imported ${USER_COUNT} new users to \"${LISTMONK_LIST_NAME}\"
Time: $(date +"%Y-%m-%d %H:%M:%S")"
fi

# Clean up old log files (keep last 7 days)
find "${LOG_DIR}" -name "mongo_import_*.log" -type f -mtime +7 -delete

log "MongoDB to ListMonk import process completed"
exit 0
