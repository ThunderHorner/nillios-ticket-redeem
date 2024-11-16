# docker-entrypoint.sh
#!/bin/bash
set -e

# Wait for nillion-devnet to be ready
echo "Waiting for nillion-devnet to be ready..."
sleep 10  # Add appropriate wait mechanism here

# Start Flask application
echo "Starting Flask application..."
python -m flask run --host=0.0.0.0