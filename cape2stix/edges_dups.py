import os
from tqdm import tqdm
import json
from collections import Counter
from pprint import pprint
import logging

directory = "output"
types = []
n = set()
e = set()
for item in tqdm(os.listdir(directory)):
    try:
        with open(os.path.join(directory, item)) as f:
            bundle = json.load(f)
    except Exception as e:
        logging.exception(e)
    for obj in bundle["objects"]:
        if obj["type"] == "relationship":
            id_ = obj["source_ref"] + obj["target_ref"]
            if id_ not in e:
                e.add(id_)
            else:
                print('dup')
       

print(len(e))
print(len(n))
pprint(Counter(types))
