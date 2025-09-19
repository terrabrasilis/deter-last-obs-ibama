#!/bin/bash
source /etc/environment

"$SCRIPT_DIR/start.sh"
echo "======================================"
echo $(date)
echo "======================================"
echo "State of env vars"
echo "BASE_URL=${BASE_URL}"
echo "======================================"
