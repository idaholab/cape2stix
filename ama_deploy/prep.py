# Copyright 2023, Battelle Energy Alliance, LLC
# prep.py can be run to automatically setup VMs.
# Before running, config.py must be edited for number of machines and machines specifications
from uuid import uuid4
from glob import iglob
from pathlib import Path
# import subprocess
from subprocess import Popen, PIPE, STDOUT
import os
import contextlib
import config
from log import log


# ----------------------------------------------------------------


@contextlib.contextmanager
def remember_cwd():
    curdir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(curdir)


def remove_all_xml_qcow2():
    for file_path in iglob("./transfer/guest_images/*/*.xml"):
        if "BASE" not in file_path:
            os.remove(file_path)
    for file_path in iglob("./transfer/guest_images/*/*_[0-9].qcow2"):
        if "BASE" not in file_path:
            os.remove(file_path)


def make_backing(in_file, out_file):
    "Create qcow2 file corresponding to xml"

    with remember_cwd():
        os.chdir(Path(in_file).parents[0])
        if os.path.exists(out_file):
            os.remove(out_file)
        args = ["qemu-img", "create", "-f", "qcow2", "-F",
                "qcow2", "-b", in_file.name, out_file.name]

        sub = Popen(args, stdout=PIPE, stderr=STDOUT)
        with sub.stdout:
            for line in iter(sub.stdout.readline, b''): # b'\n'-separated lines
                log.warning(line)
# ----------------------------------------------------------------


def net_gen():
    "Generator for vm network information"

    for n in range(*config.tap_num):
        mac = config.MAC_PREFIX + (hex(n)[2:].zfill(2))
        ip = config.IP_PREFIX + str(n)
        tap_name = f"{config.tap_base}{n}"
        yield (mac, ip, tap_name, f"""<mac address="{mac}"/>
        <source bridge="virbr1"/>
        <target dev="{tap_name}"/>""")
# ----------------------------------------------------------------


def update_file(mapping: dict, file_in, file_out, match_chars=("{{", "}}")):
    "updates the xml and qcow2 files"
    with open(file_in) as f:
        data = f.read()

    for k, v in mapping.items():
        data = data.replace(f"{match_chars[0]}{k}{match_chars[1]}", v)
    with open(file_out, "w") as f:
        f.write(data)
# ----------------------------------------------------------------


def buildKVM(tap, name, k, mach, ip):
    "builds kvm.conf info"
    tempMachine = mach[k]
    build = f"""
[{name}]
label = {name}
platform = {tempMachine['platform']}
ip = {ip}
tags = {tempMachine['tags']}
interface = {tap}
arch = {tempMachine['arch']}

"""
    return build
# ----------------------------------------------------------------


def write_KVM(kvm_mach, build):
    "writes to kvm.conf"
    try:
        start = f"""[kvm]
machines = {','.join(kvm_mach)}
interface = {config.bridge}
"""
        f = open("./transfer/cape_conf/kvm.conf", "w")
        f.write(start+build)
        f.close()
        log.debug(f"\nWrote to kvm.conf:\n{start+build}")
    except Exception as e:
        log.warning("Failure in writeKVM")
        log.warning(e)
# ----------------------------------------------------------------


def main_prep():
    "Primary control function of prep.py"
    tgen = net_gen()  # setup generator
    kvmBuild = ""
    kvmMachines = []
    remove_all_xml_qcow2()
    # For every base file, create clones
    for file_path in iglob(config.BASE_FORMAT):
        path = Path(file_path)
        key = path.name.rsplit("_", 1)[0]
        # --------------------
        if key in config.machines:
            machine = config.machines[key]
        else:
            raise Exception("key not found in machines: " + str(key))
        # --------------------
        # For number of machines specified in config, make machines
        for x in range(machine["count"]):
            make_backing(
                path.parents[0].joinpath(Path(machine["disk_path"]).name),
                path.parents[0].joinpath(f"{machine['basename']}_{x}.qcow2"),
            )
            # --------------------
            disk_extra = f"""<backingStore type='file'>
            <format type='qcow2'/>
            <source file='{machine['disk_path']}'/>
            <backingStore/>
            </backingStore>"""
        # --------------------
            # Generate new information based off tap
            newMac, newIP, newTap, newXML = next(tgen)
            mapping = {  # Create the mapping to be placed in xml
                "name": f"{machine['basename']}_{x}",
                "uuid": str(uuid4()),
                "disk_extra": disk_extra,
                "network_extra": newXML,
                "disk_path": f"{config.IMG_DIR}{machine['basename']}_{x}.qcow2",
            }
            # --------------------
            machineName = f"{key}_{x}"
            kvmMachines.append(machineName)
            update_file(mapping, path, str(
                path).replace("_BASE", "_" + str(x)))
            kvmBuild = kvmBuild + \
                buildKVM(newTap, machineName, key, config.machines, newIP)
    # ----------------------------------------
    write_KVM(kvmMachines, kvmBuild)
    log.info("mainPrep() finished")
# ----------------------------------------------------------------


# mainPrep() # Run mainPrep()
if __name__ == '__main__':
    main_prep()
