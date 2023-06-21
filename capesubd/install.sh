#!/bin/bash
sudo cp capesubd.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable capesubd
sudo systemctl restart capesubd