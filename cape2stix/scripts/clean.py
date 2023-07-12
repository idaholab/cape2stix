# Copyright 2023, Battelle Energy Alliance, LLC
"Script to clean benign system call objects from CAPE to STIX output"

import logging
import json
import stix2
import os
import re
# def idea(file_name):
#     "called async-ish by convert.py whenever it has a new file written" 
#     objects = json.parse(file_name)
#     for obj in objects:
#         json.loads(x)
#         # if obj matches objectInBenign:
#             # objects[obj] 
#ATTN: make sure you get rid of relationships too

stix_uuid5 = '[a-z0-9-]+--[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-5[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'


def parse_benign(benign_file):
    """parses a stix file and builds a list of UUIDv5s such 
       that they can be removed from the converted file"""
    if os.path.exists(benign_file):
        with open(benign_file) as b:
            benign = stix2.parse(b, allow_custom=True)
            return {obj.type: obj.id for obj in benign.objects if re.match(stix_uuid5, obj.id)}

def parse_malign(malign_stix, benign_list):
    """Compares potentially malign objects to benign objects. 
    If the objects match, the potentially malign object is benign. 
    It is then removed from the output."""
    print(benign_list)
    for obj in malign_stix.objects:
        if obj.type in benign_list and obj.id in benign_list[obj.type]: #TODO: -wb I would like to test this over just iterating over a list, but I need to change parse_benign
            print(malign_stix.relationships(obj))
            print("todo:remove obj")
        

with open("cape2stix/tests/test_converted.json", 'r') as w:
    mal = stix2.parse(w, allow_custom=True)

parse_malign(mal, parse_benign("cape2stix/tests/test_benign.json"))