#!/bin/bash
## THE ENV VARS ARE NOT READED INSIDE A SHELL SCRIPT THAT RUNS IN CRON TASKS.
## SO, WE WRITE INSIDE THE /etc/environment FILE AND READS BEFORE RUN THE SCRIPT.
echo "export SHARED_DIR=\"$SHARED_DIR\"" >> /etc/environment
echo "export SCRIPT_DIR=\"$SCRIPT_DIR\"" >> /etc/environment
echo "export TZ=\"America/Sao_Paulo\"" >> /etc/environment
echo "export PATH=\"/usr/local/bin:$PATH\"" >> /etc/environment
#
# if defined as env var, its used to force the input BASE_URL from Stack.
if [[ -v BASE_URL ]]; then
    # Expected value is an URL string to load input files
    echo "export BASE_URL=\"$BASE_URL\"" >> /etc/environment
fi;
#
# run cron in foreground
cron -f