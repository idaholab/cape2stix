# Copyright 2023, Battelle Energy Alliance, LLC
import asyncio
from neo4j import GraphDatabase
from neo4j.exceptions import ConstraintError
import json
from cape2stix.core.stix_loader import StixLoader
from stix2.utils import STIXdatetime
import logging
from glob import glob
import aiofiles
from datetime import datetime
import os
import csv
from io import StringIO
from itertools import zip_longest
from tqdm import tqdm


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


STIXOBJCLASS = "STIXObj"

# driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test"))


def process_dict(d):
    new_d = {}
    for k, v in d.items():
        if k == "type":
            v = v.replace("-", "_")
        elif type(v) == dict:
            v = (
                json.dumps(v)
                .replace("'", '"')
                .replace('"', "")
                .replace(",", "")
                .replace(":", "")
                .replace("\\", "/")
            )
        new_d[k.replace("-", "_")] = (
            str(v)
            .replace("'", '"')
            .replace('"', "")
            .replace(",", "")
            .replace(":", "")
            .replace("\\", "/")
        )
    return new_d


def hashschema(stixobj):
    key = stixobj["type"] + ";;;" + ":::".join(stixobj.keys())
    return key


async def load_file(path, s, d):
    async with aiofiles.open(path, mode="r") as f:
        contents = await f.read()
    try:
        data = json.loads(contents)
    except json.decoder.JSONDecodeError:
        # logging.exception(e)
        logging.warning(f"{path} is not valid json!")
        return
    for i in data["objects"]:
        if i["id"] not in s:
            s.add(i["id"])
        else:
            continue
        key = hashschema(i)
        i = process_dict(i)
        if key not in d:
            f = StringIO("")
            writer = csv.DictWriter(f, fieldnames=list(i.keys()))
            d[key] = (f, writer, i)
            writer.writeheader()
            writer.writerow(i)
        else:
            f, writer, _ = d[key]
            writer.writerow(i)


async def main_():
    here_base_dir = "/home/cutsma/code/neo4j/neo4jdata/import/csvdata"
    cont_base_dir = "/csvdata"

    # if not os.path.exists(here_base_dir):
    #     os.mkdir(here_base_dir)
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test"))
    with driver.session(database="neo4j") as session:
        session.run(
            """MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS"""
        )
    local_lookup = set()
    path_sets = grouper(glob("output/*"), 50)
    for pathes in path_sets:
        schemas = {}
        tasks = []
        for path in pathes:
            if path is None:
                continue
            f = load_file(path, local_lookup, schemas)
            tasks.append(f)
        await asyncio.gather(*tasks)
        for k, v in tqdm(schemas.items()):
            with driver.session(database="neo4j") as session:
                flush_csv(v[0], v[2], cont_base_dir, here_base_dir, session)


# params {employeeId: row.Id, email: row.Email}


def flush_csv(strio, example_item, cont_base_dir, here_base_dir, session):
    obj_type = example_item["type"]
    here_csv_path = os.path.join(here_base_dir, "1.csv")
    params = "{" + ", ".join([f"{key}: row.{key}" for key in example_item.keys()]) + "}"
    with open(here_csv_path, "w") as f:
        f.write(strio.getvalue())
        strio.close()
    cont_csv_path = os.path.join(cont_base_dir, "1.csv")
    query = f"""
    LOAD CSV WITH HEADERS FROM 'file:///{cont_csv_path}' AS row
    CALL {{
    with row
    CREATE (e:{STIXOBJCLASS}:{obj_type} {params})}} IN TRANSACTIONS OF 10000 ROWS"""
    session.run(query)


if __name__ == "__main__":
    a = datetime.now()
    asyncio.run(main_())

    print(datetime.now() - a)
