#!/bin/bash
# to debug in localhost, enable the following two lines
# SCRIPT_DIR=`pwd`
# SHARED_DIR=$SCRIPT_DIR"/../data"

# to store run log
DATE_LOG=$(date +"%Y_%m_%d_%H_%M_%S")
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR
DATA_DIR_LOG="${DATA_DIR}/log"

# go to the scripts directory
cd ${SCRIPT_DIR}

# list of biomes to export data
BIOMES=("Cerrado" "Amazonia")

# read postgres params for each database from pgconfig file
for TARGET_BIOME in ${BIOMES[@]}
do
    # the log file for each biome
    LOG_FILE=${TARGET_BIOME}_${DATE_LOG}.log

    # load postgres parameters from config file in config/pgconfig
    . ./dbconf.sh "${TARGET_BIOME}" >> "${DATA_DIR_LOG}/config_${LOG_FILE}"
    
    # to read inside python
    export TARGET_BIOME=${TARGET_BIOME}
    
    # get cmask files scraping download page
    python3 wget_cmasks.py >> "${DATA_DIR_LOG}/download_${LOG_FILE}"
    
    # make cmask using download files
    python3 cmask_weeks.py >> "${DATA_DIR_LOG}/cmask_weeks_${LOG_FILE}"

    # search num of days of last observation for each polygon
    python3 deter_last_obs.py >> "${DATA_DIR_LOG}/deter_last_obs_${LOG_FILE}"
done