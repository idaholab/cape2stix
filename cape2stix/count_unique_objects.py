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
            if obj["id"] not in e:
                e.add(obj["id"])
                types.append(obj["type"])
        else:
            if obj["id"] not in n:
                n.add(obj["id"])
                types.append(obj["type"])

print(len(e))
print(len(n))
pprint(Counter(types))
