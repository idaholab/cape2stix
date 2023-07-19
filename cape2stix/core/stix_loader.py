# Copyright 2023, Battelle Energy Alliance, LLC
import logging
from stix2 import MemoryStore
from stix2.v20.common import MarkingProperty, TLPMarking, TLP_WHITE
from stix2.base import STIXJSONEncoder
import json
import os
from cape2stix.core.util import gen_uuid, openaw
from aiofile import async_open


class StixLoader:
    """Class to manage creation, adding to and writing out our stix data."""

    def __init__(self, file_path=None, allow_custom=True):
        logging.debug("init succeeded")
        self.allow_custom = allow_custom
        self.create_bundle(file_path=file_path)

    def create_bundle(self, file_path=None):
        logging.debug("creating bundle")
        self.ms = MemoryStore(allow_custom=self.allow_custom)
        self.ms_source = self.ms.source
        self.ms_sink = self.ms.sink
        if file_path is not None:
            self.ms.load_from_file(file_path)

    # NOTE: this looks like it is depricated and will not work
    def stix_out(self, name=None):
        if not self.stix_loader:
            return None
        if name is None:
            logging.error("No name for STIX output.")
        else:
            path_name = f"{name}.json"
        self.sl.write_out(os.path.join(self.dir, path_name))

    def merge(self, items):
        logging.debug("Merging:")
        for item in items:
            logging.debug(f"Adding:\n {item}")
            self.ms_sink.add(item)

    def add_item(self, items):
        logging.debug("Adding:")
        self.ms_sink.add(items, version=2.1)

    def rm_item(self, id):
        try:
            self.ms._data.pop(id)
            logging.debug(f"Removing:{id}") 
        except Exception as err:
            logging.warning(f"\033[31m {err} \033[0m")
    def get_item(self, id):
        return self.ms.get(id)

    def get_sink_data(self):
        return self.ms.sink._data

    async def write_out(self, path2):
        Written = False
        # if path2[0] == "/":
        #     path2 = path2.replace("/", "", 1)
        # path2 = os.path.join("./" + path2)

        # We are not using the built in .save_to_file as its slow for some reason
        logging.debug(f"attempting to write_out to path: {path2}")
        logging.debug("Starting save to file")
        # self.ms.save_to_file(path)
        d = {
            "type": "bundle",
            "id": gen_uuid("bundle"),
            "objects": [item for item in self.ms_source.query()],
        }

        if d["objects"]:
            logging.debug(d)
            logging.debug(path2)
            async with async_open(path2, "w") as f:
                await f.write(json.dumps(d, cls=STIXJSONEncoder))

            Written = True
            logging.info(
                f"Finished save to file, number of objects: {len(list(self.ms_source.query()))}"
            )

        return Written
