# Copyright 2023, Battelle Energy Alliance, LLC
import json
import argparse
from pprint import pprint


parser = argparse.ArgumentParser()
parser.add_argument("f_path")
parser.add_argument("j_path")
args = parser.parse_args()

with open(args.f_path, "r") as f:
    data = json.load(f)


def search(data, base, to_find):
    l = []
    if isinstance(data, dict):
        for key, value in data.items():
            l.extend(search(value, key, to_find))
            if to_find in key:
                l.append(key)
    if isinstance(data, list):
        for index, item in enumerate(data):
            l.extend(search(item, str(index), to_find))
    if isinstance(data, str):
        if to_find in data:
            l.append(data)
    if isinstance(data, int) or isinstance(data, float):
        if to_find in str(data):
            l.append(str(data))

    return [base + "/" + item for item in l]


pprint(search(data, "/", args.j_path))
