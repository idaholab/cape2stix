# Copyright 2023, Battelle Energy Alliance, LLC
import sys
import subprocess
import json
from pprint import pprint

MAC_PREFIX = "52:54:00:a0:cc:"


interface_data_proc = subprocess.run(["ip", "-j", "a"], capture_output=True, text=True)
interface_data = json.loads(interface_data_proc.stdout)
bridge = "virbr1"
d = {}
for item in interface_data:
    if "tap" in item["ifname"]:
        d[item["ifname"]] = item
        ifname = item["ifname"]
        args = ["sudo", "nmcli", "connection", "modify", ifname, "master", bridge]
        subprocess.run(args)
        args = ["sudo", "nmcli", "connection", "down", ifname]
        subprocess.run(args)
        args = ["sudo", "nmcli", "connection", "up", ifname]
        subprocess.run(args)


# args = 'nmcli connection add type bridge ifname virbr1 con-name virbr1 ipv4.method manual ipv4.addresses 192.168.13.1/24'.split(' ')
# subprocess.run(args)
for x in range(2, 10):
    ifname = f"tap{str(x)}"
    if ifname in d:
        continue
    else:
        #nmcli connection add type bridge ifname br0 con-name br0 ipv4.method manual ipv4.addresses "10.10.10.1/24"
        
        args = [
            "sudo",
            "nmcli",
            "connection",
            "add",
            "type",
            "tun",
            "tun.mode",
            "tap",
            "slave-type",
            "bridge",
            "tun.owner",
            "1001",
            "autoconnect",
            "yes",
            "802-3-ethernet.cloned-mac-address",
            f"{MAC_PREFIX}{hex(x)[2:].zfill(2)}",
            "con-name",
            ifname,
            "ifname",
            ifname,
            "master",
            bridge,
        ]
        subprocess.run(args)
        args = [
            "sudo",
            "nmcli",
            "con",
            "add",
            "type",
            "bridge-slave",
            # "connection.slave-type",
            # "bridge"
            "ifname",
            ifname,
            "master",
            bridge,
        ]
        # subprocess.run(args)
        # subprocess.run(["sudo", "nmcli", "con", "up", ifname])

# nmcli connection add type tun ifname tap0 con-name tap0 mode tap owner 0 ip4 0.0.0.0/24
# nmcli con add type bridge-slave ifname tap0 master br0
# nmcli con add type bridge-slave ifname tap0 master br0
