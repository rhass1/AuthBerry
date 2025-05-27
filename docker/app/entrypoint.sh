#!/bin/bash

set -e

# Our container is already running as app-user, so we don't need to switch users

# Check the file_uploads directory permissions
FILE_UPLOAD_DIR=${FILE_UPLOAD_PATH:-/app/file_uploads}
echo "Starting Application..."

# Start the application without initializing the database
# Database must be initialized manually:
# docker exec -it auth_berry_flask bash -c "flask db init && flask db migrate && flask db upgrade"
python /app/run.py &

# Keep container running
tail -f /dev/null