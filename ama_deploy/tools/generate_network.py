# Copyright 2023, Battelle Energy Alliance, LLC
from uuid import uuid4

NET_NAME = "default"
UUID = uuid4()
NET_MAC = "52:54:00:12:fe:01"
BRIDGE_NAME="virbr0"
MAC_PREFIX = "52:54:00:a0:cc:"

string = f"""
    <network>
    <name>{NET_NAME}</name>
    <uuid>{UUID}</uuid>
    <forward mode='nat'/>
    <bridge name='{BRIDGE_NAME}' stp='on' delay='0'/>
    <mac address='{NET_MAC}'/>
    <ip address='192.168.13.1' netmask='255.255.255.0'>
        <dhcp>
        <range start='192.168.13.2' end='192.168.13.254'/>
    """
    
for x in range(2, 255):
    string += f"\t<host mac='{MAC_PREFIX}{hex(x)[2:].zfill(2)}' name='VM{x}' ip='192.168.13.{x}'/>\n"
end_string = """    </dhcp>
    </ip>
    </network>
    """
    
    
string += end_string

    
print(string)