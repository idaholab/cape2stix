# Automated Malware Analysis Deployment

CAPE (Config And Payload Extraction) is a malware sandbox. It was derived from Cuckoo with the goal of adding automated malware unpacking and config extraction. Automated unpacking allows classification based on Yara signatures to complement network (Suricata) and behavior (API) signatures.
There is a free community instance online which anyone can use: [CAPE Sandbox](https://capesandbox.com)

Automated Malware Analysis Deployment is the repository containing all setup for building CAPE from scrath using virtual machine images.

## Initial Setup

Please follow each step for initial setup

1. clone the repository. This project contains submodules which must be cloned recursively

   ```
   git clone --recursive
   ```

   If the repository has already been cloned, but new submodules need to be added, run:

   ```
   git submodule update --init --recursive
   ```
2. Edit the number of CAPE virtual machines and their settings in [config.py](config.py) for automated VM creation
3. Ensure there is a valid BASE.xml file and qcow2 file located under [/transfer/guest_images/*/](transfer/guest_images/)

   - Note: if there are no valid files, contact project maintainers
4. Run the command

   ```
   python3 run.py [-h][--log_level {warn,debug,info}] [--verbose] [--no_vinstall]
   ```

### Command Description

- [run.py](run.py): packages several build steps together for simplified deployment
  - run.py contains the following functionalities:
    - runs [ubuntu.install](ubuntu.install) installs all dependencies necessary to run on ubuntu
    - ensures bento dependencies
    - runs [prep.py](prep.py): generates VM images based off of config.py, and template files
    - runs [run.sh](run.sh): builds 4 stacked packer images
    - runs [vinstall.sh](vinstall.sh)
  - run.py is run from the command line in the following way:
    ```
    python3 run.py [-h][--log_level {warn,debug,info}] [--verbose] [--no_vinstall]
    ```
    - **`[-h]`** shows the help message and exits
      - *exclusive*
      - *takes precedence*
    - **`[--log_level {warn,debug,info}]`** defines lowest level of log recorded
      - *only one flag is necessary*
      - *default is **warn***
    - **`[--verbose]`** prints logs to the console
    - **`[--no_vinstall]`** disables running vinstall.sh - vinstall.sh deletes the current VM and makes a new VM using the current disk in the path
    - **`[--clean]`** cleans out all previous build data. Only use when necessary.

## Using CAPE
- http://localhost:8000
- [test_samples/](test_samples/) contain non-malware programs that can be detonated in CAPE to replicate the effects of malware in the sandbox

### Virtual Machine Manager

- spawned virtual machines can be accessed through Virtual Machine Manager by connecting with ssh
- credentials are vagrant:vagrant
- connecting to cape via ssh must be done with an ssh key. An ssh key can be created with the command:
  ```
  ssh-keygen
  ```

### Notes:
- The CAPE web-browser may not appear to load properly if using virtualization. This can be amended by adjusting the size of the browser with Ctrl (+/-)

- run.sh has strange output. If a build is succeeding it will have output similar to the following:
  ![](/img/run_success.png)
        - Soon after the command executes, the download bar appears. If that appears, there has been no error in run.sh
        - If run.py is executing run.sh commands, it will log everything except for the download bar    
        - Failure in execution will quickly result in the following error appearing:
        ![](/img/run_error.png)
        - This error is color coded and will wait for user input. This error ouput is the same in both run.sh and the implementation of run.sh in run.py
        - If an error will occur, it will occur relatively soon in the build process

- MongoDB created some with gpg keys. A quick solution was to store a copy of a key in [cape.sh](bash_scripts/cape.sh). If MongoDB updates, that key may not work. The user may need to generate a key and paste it in place.

