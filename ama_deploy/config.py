"config.py stores the data required for prep.py to generate VMs"
# Copyright 2023, Battelle Energy Alliance, LLC
# The following is standard and should not be edited by the user
dest_path = "./transfer/cape_conf/kvm.conf"
bridge = "virbr1" #this is the interface
tap_base = "tap"
tap_num = (2, 254)
BASE_FORMAT = "./transfer/guest_images/*/*_BASE.xml"
IMG_DIR = "/var/lib/libvirt/images/"
MAC_PREFIX = "52:54:00:a0:cc:"
IP_PREFIX = "192.168.13."
# ---- end of standard settings

# Begin Machines for edit
machines = {
    "ubuntu22": {
        "basename": "ubuntu22",
        "tags": "ubuntu22,x32",
        "platform": "linux",  # windows/darwin/linux
        "arch": "x64",
        "count": 1,
        "disk_path": IMG_DIR + "ubuntu22.qcow2",
    },
    "win7": {
        "basename": "win7",
        "tags": "win7,x86",
        "platform": "windows",  # windows/darwin/linux
        "arch": "x64",
        "count": 0,
        "disk_path": IMG_DIR + "win7.qcow2",
    },
    "win10": {
        "basename": "win10",
        "tags": "win10,x86",
        "platform": "windows",  # windows/darwin/linux
        "arch": "x64",
        "count": 1,
        "disk_path": IMG_DIR + "win10.qcow2",
    }
}
