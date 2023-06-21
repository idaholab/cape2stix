#!/bin/bash
#Copyright 2023, Battelle Energy Alliance, LLC
cd ../
pwd
docker build -t cape2stix .
docker run cape2stix --rm $@

cd cape2stix/todb/
pwd
sudo docker-compose up -d
