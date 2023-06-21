# Copyright 2023, Battelle Energy Alliance, LLC
"""
1. Get listing of reports from cape, capture hash, tags, any other note.
2. Get listing of target dir
3. Get tag/run
4. Calculate hashes for all files
5. For each file, check if hash is in listing.
6. Submit x files until pending is greater then x, 
7. sleep, then ensure listing of reports is updated for next cycle
"""


from time import sleep
from cape2stix.core.CAPEAPI import CAPEClient, TaskStatus
from capesubd.config import machines, host, base_dir, target_tag
from pprint import pprint
import logging
from hashlib import sha256
import os
from itertools import cycle


def get_reports(cc: CAPEClient, target_tag: str):
    l = cc.list_tasks(status=TaskStatus.reported, limit=100000)
    l.extend(cc.list_tasks(status=TaskStatus.pending, limit=2000))
    d = {}
    for item in l:
        if item["tags_tasks"] is not None and target_tag in item["tags_tasks"]:
            d[item["sample"]["sha256"]] = {
                "tags": item["tags"],
                "task_tags": item["tags_tasks"],
            }

    return d


def get_num_pending(cc: CAPEClient):
    l = cc.list_tasks(status=TaskStatus.pending, limit=100)
    return len(l)


def get_file_hashes(directory: str):
    pathes = os.listdir(directory)
    for p in pathes:
        m = sha256()
        with open(os.path.join(directory, p), "rb") as f:
            m.update(f.read())
        yield m.hexdigest(), os.path.join(directory, p)


def submit_batch(cc: CAPEClient, file_pathes, size=8, machines=None, **kwargs):
    diff = size - get_num_pending(cc)
    l = []
    if diff > 0:
        for x in range(diff):
            f_hash, file_path = next(file_pathes)
            machine = next(machines)
            cc.submit_file(file_path, machines=machine, **kwargs)
            l.append(f_hash)
    return l

    # Get current report listing


def main_loop(sleep_time=10):
    
    machines2 = cycle(machines.split(","))
    cc = CAPEClient(host)
    while True:
        try:

            reports = get_reports(cc, target_tag)
            hashes_gen = get_file_hashes(base_dir)
            to_process_gen = ((h, f) for h, f in hashes_gen if h not in reports)
            logging.warning("submitting")
            submit_batch(cc, to_process_gen, machines=machines2, tags_tasks=target_tag)
            sleep(sleep_time)
        except Exception as e:
            logging.exception(e)


if __name__ == "__main__":
    main_loop()
