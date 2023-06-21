#!/bin/bash
# Copyright 2023, Battelle Energy Alliance, LLC
virsh undefine cape_test_auto
virsh destroy cape_test_auto
qemu-img convert -O qcow2 builds/packer-capeextra-qemu/capeextra /var/lib/libvirt/images/capeextra
virt-install --name cape_test_auto --memory 8096 --import --disk /var/lib/libvirt/images/capeextra --os-variant=ubuntu22.04 --wait 0
