#!/bin/sh -eux
# Copyright 2023, Battelle Energy Alliance, LLC
cd /tmp
wget https://raw.githubusercontent.com/kevoreilly/CAPEv2/master/installer/kvm-qemu.sh
chmod +x /tmp/kvm-qemu.sh
/tmp/kvm-qemu.sh virtmanager cape | tee /home/vagrant/virtmanager.log
reboot now
