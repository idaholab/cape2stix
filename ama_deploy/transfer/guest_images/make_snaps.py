# Copyright 2023, Battelle Energy Alliance, LLC
import subprocess # nosec B404
import time
import logging


def check_mac_in_list(mac, net="limited"):
    lines = subprocess.run(["virsh", "net-dhcp-leases", "--network", net],stdout=subprocess.PIPE).stdout.decode().split("\n") # nosec B603, B607
    for line in lines[2:]:
        if line == "":
            continue
        if line.split()[2] == mac:
           return True
    return False

if __name__ == "__main__":

    domain_cmd = "virsh list --all --name"

    output = subprocess.run(domain_cmd.split(' '), stdout=subprocess.PIPE).stdout.decode() # nosec B603

    domains = output.split('\n')
    for domain in domains:
        if domain == "":
            continue
        # get MAC
        line = subprocess.run(["virsh", "domiflist", domain], stdout=subprocess.PIPE).stdout.decode().split("\n")[2] # nosec B603, B607
        mac = line.split()[4]
        # start system
        subprocess.run(["virsh", "start", domain]) #nosec B607, B603
        
        for _ in range(10):
            # check if MAC in dhcp list
            try:
                if check_mac_in_list(mac):
                    logging.info('MAC found early in DHCP list')
                    break
            except Exception as e:
                logging.exception(e)
            time.sleep(5)
        # create the snapshot
        subprocess.run(["virsh", "snapshot-create-as", "--domain", domain, "--name", "init", "--halt"]) # nosec B603, B607
