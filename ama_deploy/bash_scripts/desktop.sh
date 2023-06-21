#!/bin/sh -eux
# Copyright 2023, Battelle Energy Alliance, LLC
echo """
  [openssl_init]
  # providers = provider_sect  # commented out

  # added
  ssl_conf = ssl_sect

  # added
  [ssl_sect]
  system_default = system_default_sect

  # added
  [system_default_sect]
  Options = UnsafeLegacyRenegotiation

  # List of providers to load
  [provider_sect]
  default = default_sect
  """ >> /usr/lib/ssl/openssl.cnf
apt update
apt install -y ubuntu-gnome-desktop network-manager git
apt install -y firefox
