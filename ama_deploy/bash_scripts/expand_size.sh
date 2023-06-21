#!/bin/sh -eux
# Copyright 2023, Battelle Energy Alliance, LLC
sudo lvextend -l +100%FREE /dev/mapper/ubuntu--vg-ubuntu--lv || true
resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
df -h
