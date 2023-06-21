"""Provides logging for ama_deploy"""
# Copyright 2023, Battelle Energy Alliance, LLC

import logging
import sys
import os
# import getpass

log = logging.getLogger("LOGS")  # global logging variable
packer1 = logging.getLogger("packer1")
packer2 = logging.getLogger("packer2")
packer3 = logging.getLogger("packer3")
packer4 = logging.getLogger("packer4")

logs = [log, packer1, packer2, packer3, packer4]

def log_helper(args):
    "Helper function for setting up logging "
    #make sure that uid is set appropriately
    wasRoot = False
    if os.getuid() == 0:
        wasRoot = True
        uid = int(os.environ["SUDO_UID"])
        gid = int(os.environ["SUDO_GID"])
        os.setegid(gid)
        os.seteuid(uid)


    # get log level from argparse
    log_level = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "default": logging.NOTSET}[
        args.log_level
    ]
    # initial log setups
    for l in logs:
        
        if log_level == 0 :
            if l.name == "LOGS":
                log_level = 30
            else:
                log_level=20
            
        l.setLevel(level=log_level)
        formatter = logging.Formatter(
            fmt="%(levelname)s %(asctime)s (%(relativeCreated)d) %(pathname)s:%(lineno)s: %(message)s",
            datefmt="%m.%d-%H:%M:%S",
        )
        #

        consoleHandler = logging.StreamHandler(stream=sys.stdout)
        consoleHandler.setFormatter(formatter)
        if args.verbose is True:
            consoleHandler.setLevel(level=log_level)
        else:
            consoleHandler.setLevel(level=logging.INFO)

        l.addHandler(consoleHandler)

        if not os.path.exists('logging/'):
            os.mkdir('logging/')
        if not os.path.isfile(f'logging/{l.name}.log'):
            open(f'logging/{l.name}.log', 'w')

        fileHandler = logging.FileHandler(filename=f'logging/{l.name}.log')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(level=log_level)
        l.addHandler(fileHandler)
    
    if wasRoot:
        os.seteuid(0)
        os.setegid(0)


