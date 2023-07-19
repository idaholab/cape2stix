# Note For benign/

The json files in this directory are used by convert.py to remove known benign objects from stix. 
## Contents
The following contents are the result of giving certain benign scripts to CAPE and converting the results to STIX

- ps1_sleep.json: ps1 script with the command `start-sleep -s 9999`
- sh_sleep.json: shell script with the command `sleep 9999` 
