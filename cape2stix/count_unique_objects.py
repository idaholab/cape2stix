import os
from tqdm import tqdm
import json
from collections import Counter
from pprint import pformat
import logging

logging.basicConfig(filename='LOG.log', encoding='utf-8', level=logging.DEBUG)

directory = "output"
types = []
e_dups = []
n_dups = []
edges = set()
nodes = set()

for item in tqdm(os.listdir(directory)):
    try:
        if item != ".gitkeep":
            with open(os.path.join(directory, item)) as f:
                bundle = json.load(f)
    except Exception as err:
        logging.error(f"Exception in file {directory}/{item}")
        logging.exception(err)

    temp_e = set()
    temp_n = set()
    for obj in bundle["objects"]:

        if obj["type"] == "relationship":
            edges.add(obj["id"])
            temp_e.add(obj["id"])
        else:
            nodes.add((obj["id"], obj["type"]))
            temp_n.add(obj["id"])
            # types.append(obj["type"])

    # removes any strange duplicates in single bundle
    e_dups.extend(list(temp_e))
    n_dups.extend(list(temp_n))

for _, typ in nodes:
    types.append(typ)

logging.info(f"Number of Total Edges: {len(e_dups)}")
logging.info(f"Number of Deduplicated Edges: {len(edges)}")
logging.info(f"Number of Total Nodes: {len(n_dups)}")
logging.info(f"Number of Deduplicated Nodes: {len(nodes)}")
logging.info(pformat(Counter(types)))
