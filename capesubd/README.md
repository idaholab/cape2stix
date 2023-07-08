# capesubd
capesubd is a systemd service which will continuously submit malware samples to CAPE given a directory containing malware samples.
The following documentation outlines all that is needed to start the capesubd.service. Edit each dependency according to system specifications.

## capesubd.service
- each instance of `{user}` needs to be replaced with the system's user name

## config.py
- `base_dir` is a string of the path to the malware binaries. This should not be a specific binary, but instead should be the folder containing the binaries
- `machines` is a string containing the virtual machines that will run the malware samples. This is a comma separated list with no spaces, as shown in the example

## install.sh
- run install.sh to install capesubd: `./install.sh`

## dir_to_reports.py
- Install poetry and enter the poetry shell: `python3 -m pip install poetry && poetry shell`
- Run [dir_to_reports.py](./dir_to_reports.py) `python3 dir_to_reports.py`
The python script will utilize the capesubd service to continuously submit malware samples to CAPE