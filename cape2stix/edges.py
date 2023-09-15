import os
from tqdm import tqdm
import json
from collections import Counter
from pprint import pprint
import logging

directory = "output"
wdups = []      # array with duplicates
dedup = set()   # set de-duplicated

# loop through files in dir
for item in tqdm(os.listdir(directory)):
    try:
        if item[0] != ".":
            with open(os.path.join(directory, item)) as f:
                bundle = json.load(f)
    except Exception as err:
        logging.error(f"Exception in file {directory}/{item}")
        logging.exception(err)

    #loop through rels in bundle
    tempSet = set()

    for obj in bundle["objects"]:
        if obj["type"] == "relationship":
            id_ = obj["id"]
            tempSet.add(id_)
            dedup.add(id_)

    # NOTE: tempSet is used to avoid any accidental duplications *within* a single bundle
    wdups.extend(list(tempSet))

print(f"Total Relationships: {len(wdups)}")
print(f"Deduplicated Relationships: {len(dedup)}")
