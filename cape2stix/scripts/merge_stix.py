# Copyright 2023, Battelle Energy Alliance, LLC
import json
from uuid import uuid4
from tqdm import tqdm
from glob import glob
import argparse
import os


def merge(in_pathes, out_path):
    d = {}
    for path in tqdm(in_pathes, total=len(in_pathes)):
        try:
            with open(path) as f:
                data = json.load(f)
            stix = data["objects"]
            for obj in stix:
                if obj["id"] in d:
                    continue
                d[obj["id"]] = obj
        except:
            print(path, "failed")
    with open(out_path, "w") as f:
        d = {
            "type": "bundle",
            "id": f"bundle--{str(uuid4())}",
            "objects": list(d.values()),
        }
        json.dump(d, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parser.add_argument('outpath')
    args = parser.parse_args()
    merge(glob(f'{args.dir}/*.json'), args.outpath)
