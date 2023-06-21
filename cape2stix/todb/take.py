# Copyright 2023, Battelle Energy Alliance, LLC
# Rest API creating stix from orientdb
# Auth: Taylor McCampbell, Michael Cutshaw

import sys
import logging
import argparse
from cape2stix.core.stix_loader import StixLoader
import asyncio
from restWrapper import RestAPIWrapper


class Rest_Retrieve:
    def __init__(self, HOST, USER, DB_NAME, PASS, PORT, keep_bundle_ref=False):
        self.client = RestAPIWrapper(HOST, PORT, USER, PASS, DB_NAME)
        self.keep_bundle_ref = keep_bundle_ref

    def translate(self):
        nodes = self.client.query("SELECT * FROM V")
        edges = self.client.query("SELECT * FROM E")

        # Create STIX bundle
        bundle = []

        for node in nodes["result"]:
            new_node = self.clean_object(node)
            bundle.append(new_node)

        for edge in edges["result"]:
            new_edge = self.clean_object(edge)
            bundle.append(new_edge)

        self.bundle = bundle

    def clean_object(self, stix_obj):
        to_remove = [
            "@type",
            "@rid",
            "@class",
            "@fieldTypes",
            "@version",
        ]  # could prob be simplified to just starts with @
        if (
            "@fieldTypes" in stix_obj
        ):  # fieldTypes contains a list of all of the "edge" attrs
            to_remove += [
                edge.split("=")[0] for edge in stix_obj["@fieldTypes"].split(",")
            ]

        for key in list(
            stix_obj.keys()
        ):  # casting to a list copies it, so we don't get object changed during iteration errors
            if key in to_remove:
                stix_obj.pop(key)
        if not self.keep_bundle_ref and "bundle_ref" in stix_obj:
            stix_obj.pop("bundle_ref")
        return stix_obj

    def write_to_file(self, file_name):
        stixloader = StixLoader()
        for obj in self.bundle:
            stixloader.add_item(obj)
        asyncio.run(stixloader.write_out(file_name))


def parse_args(args):
    parser = argparse.ArgumentParser()
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
        "--keep_bundle_ref",
        action="store_true",
        help="whether to keep the bundle_ref attribute added when pushing to OrientDB",
    )
    parser.add_argument(
        "outpath", default="new_bundle.json", help="Name of the file to ouput to"
    )
    parser.add_argument(
        "--log_level",
        default="warn",
        help="log level",
        choices=["warn", "debug", "info"],
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
        tracker = Rest_Retrieve(
            args.host,
            args.user,
            args.db,
            args.password,
            args.port,
            keep_bundle_ref=args.keep_bundle_ref,
        )
        tracker.translate()
        tracker.write_to_file(args.outpath)

    except Exception as e:
        logging.warning("General failure")
        logging.exception(e)
