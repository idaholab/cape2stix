# Copyright 2023, Battelle Energy Alliance, LLC
import json
import argparse
from pprint import pprint


parser = argparse.ArgumentParser()
parser.add_argument("f_path")
args = parser.parse_args()

with open(args.f_path, "r") as f:
    data = json.load(f)


def search(data, base, depth):
    if depth == 5:
        return []
    l = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ["log", "icon"]:
                continue
            l.extend(search(value, key, depth + 1))
            l.append(key)
    # if isinstance(data, list):
    #     for index, item in enumerate(data):
    #         l.extend(search(item, str(index), to_find))
    if isinstance(data, str):
        l.append(data)
    if isinstance(data, int) or isinstance(data, float):
        l.append(str(data))

    return [base + "/" + item for item in l]


pprint(search(data, "/", 0))
