#!/bin/sh -eux
# Copyright 2023, Battelle Energy Alliance, LLC
# add network
sudo -u cape pip3 install -U git+https://github.com/DissectMalware/batch_deobfuscator.git
sudo -u cape pip3 install -U git+https://github.com/CAPESandbox/httpreplay.git
sudo -u cape pip3 install https://github.com/CAPESandbox/peepdf/archive/20eda78d7d77fc5b3b652ffc2d8a5b0af796e3dd.zip#egg=peepdf==0.4.2
sudo -u cape pip3 install -U flare-floss
pip3 install flare-floss
pip3 install git+https://github.com/DissectMalware/batch_deobfuscator.git
pip3 install git+https://github.com/CAPESandbox/httpreplay.git
pip3 install https://github.com/CAPESandbox/peepdf/archive/20eda78d7d77fc5b3b652ffc2d8a5b0af796e3dd.zip#egg=peepdf==0.4.2
BASEDIR="/home/vagrant/transfer/guest_images/"
rm /etc/netplan/*
echo "
network:
  version: 2
  renderer: NetworkManager
" > /etc/netplan/01_all_nm.yaml
# echo "
# unmanaged-devices=
# " > /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
netplan apply
chmod 666 /dev/kvm
systemctl start NetworkManager
systemctl enable NetworkManager
nmcli con
nmcli device
ip a

virsh net-undefine default
virsh net-destroy --network default
virsh net-define --file $BASEDIR"network_limited.xml"
virsh net-autostart --network limited
virsh net-start --network limited
virsh net-list 
virsh net-info limited
# python3 $BASEDIR"make_taps.py"
nmcli con
nmcli device
ip a
mv $BASEDIR""*/*.qcow2 /var/lib/libvirt/images/
cd $BASEDIR
for i in $(ls -d $PWD/*/*.xml | grep -v BASE); do
    virsh define --file $i
done
BASEDIR="/home/vagrant/transfer/cape_conf/"
mkdir /opt/CAPEv2/custom/conf
cp $BASEDIR""* /opt/CAPEv2/custom/conf/.
chown cape:cape /opt/CAPEv2/custom/conf/*
python3 /home/vagrant/transfer/guest_images/make_snaps.py


