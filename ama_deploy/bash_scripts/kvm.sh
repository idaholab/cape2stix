#!/bin/sh -eux
# Copyright 2023, Battelle Energy Alliance, LLC
cd /tmp
useradd cape -m -s /bin/bash -U -G sudo
wget https://raw.githubusercontent.com/kevoreilly/CAPEv2/master/installer/kvm-qemu.sh
chmod +x /tmp/kvm-qemu.sh
/tmp/kvm-qemu.sh all cape | tee /home/vagrant/kvm.log
reboot now
