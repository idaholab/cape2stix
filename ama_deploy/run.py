"Verifies dependencies and builds AMA-Deploy from scratch"
# Copyright 2023, Battelle Energy Alliance, LLC
import traceback
import subprocess # nosec B404
from subprocess import Popen, PIPE, STDOUT # nosec B404
import os
import sys
import argparse
import pwd
from pathlib import Path
from shutil import rmtree
import apt


from prep import main_prep
from log import log, log_helper, packer1, packer2, packer3, packer4
# pylint: disable=broad-except
# pylint: disable=logging-fstring-interpolation


# --------------Functions--------------
# --------------

def parse_args(args):
    "Helper function for parsing arguments from the command line"
    parser = argparse.ArgumentParser(
        description="Runs install and setup steps")
    parser.add_argument(
        "--log_level",
        choices=["debug", "info", "warn", "default"],
        metavar="{debug, info, warn}",
        default="default",
        help="defines lowest level of log recorded",
    )
    parser.add_argument(
        "--verbose", help="print logs to console", action="store_true")
    parser.add_argument(
        "--no_vinstall", help="disables vinstall.sh", action="store_true"
    )
    parser.add_argument(
        "--install_cape", help="installs cape and neo4j docker containers", action="store_true"
    )
    parser.add_argument(
        "--clean",
        help="deletes all existing builds, RUN WITH CARE",
        action="store_true",
    )
    return parser.parse_args(args)
# --------------


def clean():
    "removes previous build data if '--clean' flag is set"
    for build_path in [Path("./bento/builds"), Path("./builds")]:
        build_path.resolve()
        if build_path.exists():
            # pylint: disable=expression-not-assigned
            [
                rmtree(i) for i in build_path.iterdir() if not i.name.startswith(".")  # noqa: E501
            ]
    log.debug("clean() finished")
# --------------


def check_install():
    "Checks if the user really installed everything"
    apt_cache = apt.Cache()
    for pkg in pkgs:
        if pkg not in apt_cache:
            log.debug(f"{pkg} was not installed")
            args = ["./ubuntu.install"]
            subprocess.run(args, check=True) # nosec B603
            return None

    log.debug("checkInstall() finished")
# --------------

def cape_install():
    "Runs the script to build and run the cape and neo4j docker containers"
    print(os.getcwd())
    args = ["./bash_scripts/build_cape.sh"]
    with Popen( # nosec B603
        args, stdout=PIPE, stderr=subprocess.STDOUT
    ) as sub:   # noqa: E501 
        subi = iter(sub.stdout.readline, b"")
        for line in subi:
            log.debug(line.decode().rstrip('\n'))
 

def check_bento():
    "ensures the bento submodule is initialized"
    args = ["ls", "bento/packer_templates"]
    # pylint: disable=unspecified-encoding
    sub = subprocess.call( # nosec B603
        args, stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT
    )  # noqa: E501
    if sub != 0:
        log.debug("trying to git bento submodule")
        subprocess.call( # nosec B603, B607
            ["git", "submodule", "update", "--init", "--recursive"], user=UID   # noqa: E501
        ) 

    log.debug("checkBento() finished")
# --------------


# --------------Packer Functions--------------
# --------------
def packer_exc(arg, p_log):
    "runs subprocess.Popen for packer commands & sends output to packer_log()"
    with Popen(arg, **popen_kwargs) as packer: # nosec B603
        packer_log(packer, p_log)
        log.info(f"ATTN - {p_log.name} has finished")
# --------------


def packer_log(packer_pipe, p_log):
    "Logs output from packer builds appropriately"
    pipe = packer_pipe.stdout
    # set iterable of pipe as variable for easier use
    p_iter = iter(pipe.readline, b"")
    for line in p_iter:
        line = line.decode().rstrip('\n')
        # check line for specific qemu outputs and handle them
        if line.find("==> qemu:") > -1:
            if line.find("error") > -1:
                p_log.info(line)

            elif line.find('failed') > -1:
                p_log.error(
                    """==> qemu: [c] Clean up and exit,
                        [a] abort without cleanup, or
                        [r] retry step
                        (build may fail even if retry succeeds)?"""
                )
                # skip the next two lines of stdout
                _ = [next(p_iter) for x in range(2)]

            else:
                p_log.info(line)

        # catch build failures
        elif (
            line.find(
                "Builds finished but no artifacts were created") > -1
        ):
            while True:
                if packer_pipe.poll() is not None:
                    raise Exception("builds were not able to complete")
        elif (
            line.find(
                "Builds finished but no artifacts were created") > -1
        ):
            while True:
                if packer_pipe.poll() is not None:
                    raise Exception("build was killed:")
        else:
            # if no special handling needs to be done, log the line
            p_log.debug(line)
# --------------


def packer_run():
    "Runs the same processes as run.sh"

    log.info("Starting run.sh. This may take awhile. . .")
    os.environ['PACKER_LOG'] = "1"
    p2_4 = ["packer", "build", "-except=vagrant",
            "-only=qemu", "-on-error=ask"]

    os.chdir("bento/")
    packer_exc([
        "packer", "build", "-except=vagrant", "-only=qemu.vm",
        "-var-file=os_pkrvars/ubuntu/ubuntu-22.04-x86_64.pkrvars.hcl",
        "./packer_templates"], packer1)
    os.chdir(DIR)

    packer_exc(p2_4+["packer/kvm_virtmanager.json"], packer2)
    packer_exc(p2_4+["packer/capemain.json"], packer3)
    packer_exc(p2_4+["packer/capeextra.json"], packer4)

    log.info("run.sh finished!")
# --------------
# --------------eof packer--------------


def vinstall():
    "runs vinstall.sh"

    def slog(pipe):
        log.debug("START vinstall")
        try:
            for line in iter(pipe.readline, b""):
                if line.find(b"ERROR") > -1:
                    log.error(line)
                    return line
                if line.find(b"..........") < 0:
                    log.debug(line)
        finally:
            log.info("vinstall has finished")

    log.info(
        """The following scripts will be run:
        \n\tvinstall\n
        This will delete the current VM"""
    )
    cin = input("Do you want to continue? [Y/n]").strip()
    if cin not in ("Y", "y", ""):
        log.info("aborting")
        return

    with Popen(["bash", "./vinstall.sh"], # nosec B603, B607
               stdout=PIPE, stderr=STDOUT) as vin: 
        slog(vin.stdout)
    log.debug("FINISH vinstall")


# --------------Main--------------
def main():
    "Excutes functions within run.py"
    args = parse_args(sys.argv[1:])
    log_helper(args)
    log.debug("Init Logs")

    if args.clean:
        clean()
    check_install()
    _ = cape_install() if args.install_cape else log.debug("cape build not run")
    check_bento()
    main_prep()
    packer_run()
    _ = vinstall() if not args.no_vinstall else log.debug("vinstall not run")
# --------------


# --------------Run __main__--------------
if __name__ == "__main__":
    if os.getuid() != 0:
        log.critical('The UID is not 0! This script must be ran with "sudo"!')
        sys.exit()
    UID = int(os.environ["SUDO_UID"])
    GID = int(os.environ["SUDO_GID"])
    DIR = os.getcwd()
    os.environ["HOME"] = pwd.getpwuid(UID).pw_dir
    # ----------Variables----------
    extra_groups = ["kvm", "libvirt", "libvirt-qemu"]
    popen_kwargs = {"stdout": PIPE, "stderr": STDOUT,
                    "user": UID, "group": GID, "extra_groups": extra_groups}
    pkgs = [
        "qemu-system-x86",
        "libvirt-daemon-system",
        "libvirt-clients",
        "bridge-utils",
        "python-pip",
        "sshpass",
        "virt-manager",
        "qemu-utils",
        "docker-compose"
    ]
    # ----------run main()----------
    try:
        main()
    except Exception as err:
        log.exception(err)
        exit()
