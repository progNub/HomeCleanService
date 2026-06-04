#!/bin/bash

# Stop script on error
set -e

# Extract queue name from arguments for logging
QUEUE="*"
for ((i=1; i<=$#; i++)); do
    if [[ "${!i}" == "--queue-name" ]]; then
        next_i=$((i+1))
        QUEUE="${!next_i}"
        break
    fi
done

echo "--> Starting Worker ($QUEUE)..."

# Execute the command passed as arguments
exec "$@"
