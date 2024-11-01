#!/bin/sh

# Check if required environment variables are set
if [ -z "$EMAIL_ADDRESS" ]; then
    echo "Error: EMAIL_ADDRESS environment variable is not set."
    exit 1
fi

if [ -z "$EMAIL_PASSWORD" ]; then
    echo "Error: EMAIL_PASSWORD environment variable is not set."
    exit 1
fi

if [ -z "$KINDLE_EMAIL" ]; then
    echo "Error: KINDLE_EMAIL environment variable is not set."
    exit 1
fi

# If all environment variables are set, start the application
exec "$@"
