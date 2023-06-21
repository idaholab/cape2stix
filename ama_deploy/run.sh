#!/bin/bash
# Copyright 2023, Battelle Energy Alliance, LLC
CURPWD=$(pwd)
export PACKER_LOG=1
cd bento
packer build -except=vagrant -only=qemu.vm -var-file=os_pkrvars/ubuntu/ubuntu-22.04-x86_64.pkrvars.hcl ./packer_templates
cd $CURPWD
baseimg="bento/builds/packer-ubuntu-22.04-x86_64-qemu/ubuntu-22.04-amd64"
PACKER_LOG=1 packer build -except=vagrant -only=qemu -on-error=ask packer/kvm_virtmanager.json
PACKER_LOG=1 packer build -except=vagrant -only=qemu -on-error=ask packer/capemain.json
PACKER_LOG=1 packer build -except=vagrant -only=qemu -on-error=ask packer/capeextra.json


