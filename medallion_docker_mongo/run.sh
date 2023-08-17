#!/bin/bash
pip install pymongo
docker-compose up -d
python3 mongo_init.py   