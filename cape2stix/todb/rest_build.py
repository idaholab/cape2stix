# Copyright 2023, Battelle Energy Alliance, LLC
# Rest API stix to orient db script

import sys
import os
import json
import logging
import argparse
from tqdm import tqdm
from typing import List, Dict

from cape2stix.todb.restWrapper import RestAPIWrapper
from cape2stix.todb import schema


def format_stix_to_db(stix_objs: List[Dict]) -> List[Dict]:
    db_stix: List[Dict] = []
    relations: List[Dict] = []

    for obj in stix_objs:
        if obj["type"] != "relationship":
            db_stix.append(obj)
        else:
            relations.append(obj)

    return db_stix + relations


class Rest_Builder:
    def __init__(self, HOST, USER, DB_NAME, PASS, PORT, DESTROY):
        self.client = RestAPIWrapper(HOST, PORT, USER, PASS, DB_NAME)
        self.DESTROY = DESTROY
        self.local_lookup = {}

    def insert_bundle(self, stix_objs: List[Dict], bundle_name: str):

        stix_objs = format_stix_to_db(stix_objs)

        for stixObj in tqdm(stix_objs, bundle_name):
            # o['bundle_ref'] = bundle_name #delete this
            logging.debug("\nObject:")
            logging.debug(stixObj)
            o_type = stixObj["type"].replace("-", "_")
            if stixObj["id"] in self.local_lookup:
                logging.debug("Duplicate item! Skipping")
                continue

            if o_type != "relationship":
                if o_type not in schema.nodes:
                    self.client.createNodeSchema(o_type)
                    schema.nodes.append(o_type)

                response = self.client.insertNodeDocument(stixObj, o_type)
                self.local_lookup[stixObj["id"]] = response["@rid"]
            else:
                if stixObj["relationship_type"] not in schema.edges:
                    self.client.createEdgeSchema(stixObj["relationship_type"])
                    schema.edges.append(stixObj["relationship_type"])

                response = self.client.insertEdgeDocument(
                    stixObj,
                    stixObj["relationship_type"].replace("-", "_"),
                    self.local_lookup[stixObj["source_ref"]],
                    self.local_lookup[stixObj["target_ref"]],
                )
                self.local_lookup[stixObj["id"]] = response["result"][0]["@rid"]

    def process_file(self, stix_file):

        with open(stix_file, "r") as f:
            name = os.path.basename(stix_file)
            logging.debug(f"Adding file {name}")
            try:
                # Load json file
                irl = json.load(f)
                # Weed out any objects that aren't formatted correctly (sometimes strings cloud the data) and add bundle name to nodes
                for stixObj in irl["objects"]:
                    if type(stixObj) == dict:
                        stixObj["bundle_ref"] = name
                    else:
                        logging.error(f"Bad object in file {name}, removing from file")
                        irl["objects"].remove(stixObj)
                        continue
                # Insert bundle into graph db
                self.insert_bundle(irl["objects"], name)
            except Exception as e:  # Not expecting any errors that haven't been caught elsewhere. If one is caught, exit right away.
                logging.error(f"Error in file: {name}")
                logging.exception(e)

    def populate_local_list(self):
        nodes = self.client.query("SELECT @rid, id from V")["result"]
        self.local_lookup.update({node["id"]: node["@rid"] for node in nodes})
        edges = self.client.query("SELECT @rid, id from E")["result"]

        self.local_lookup.update({edge["id"]: edge["@rid"] for edge in edges})

    def stix2orient(self, PATH):
        if not os.path.exists(PATH):  # check if exists
            logging.exception("path does not exist")
            sys.exit(-1)

        if self.DESTROY:
            logging.info("Destroying and recreating database!")
            self.client.deleteDB()
            self.client.createDB()
            self.client.createSchema()
        else:
            self.populate_local_list()
        # ### Load JSONs
        # Loop through directory and load JSON files one at a tim
        if os.path.isdir(PATH):  # Loading a directory
            # Loop through jsons in pool
            for stix_bundle in tqdm(os.listdir(PATH), "Files"):
                self.process_file(os.path.join(PATH, stix_bundle))
        else:
            self.process_file(PATH)

        logging.info("Finished!")


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", default="../input", help="Path to stix files to be uploaded"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="IP Address of the orientdb server you are uploading data to",
    )
    parser.add_argument(
        "--user", default="root", help="Username to the orientdb server"
    )
    parser.add_argument(
        "--password", default="root", help="Password to the orientdb server"
    )
    parser.add_argument("--db", default="demodb", help="Database name")
    parser.add_argument(
        "--port", default="2480", help="Port the orientdb server is listening on"
    )
    parser.add_argument(
        "--log_level",
        default="warn",
        help="log level",
        choices=["warn", "debug", "info"],
    )
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Either True or False. Do you want to delete the named database and start fresh or not?",
    )
    return parser.parse_args(args)


if __name__ == "__main__":

    log_level_dict = {
        "warn": logging.WARN,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    args = parse_args(sys.argv[1:])
    logging.basicConfig(level=log_level_dict[args.log_level])

    try:
        tracker = Rest_Builder(
            args.host, args.user, args.db, args.password, args.port, args.destroy
        )
        tracker.stix2orient(args.path)

    except Exception as e:
        logging.warning("Wrong or invalid arguments")
        logging.exception(e)
